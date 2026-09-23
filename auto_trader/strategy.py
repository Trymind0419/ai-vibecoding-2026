# -*- coding: utf-8 -*-
"""
[공격적 자동매매 전략] Aggressive Volatility Breakout + Momentum Strategy
---------------------------------------------------------------------------
기존 보수적 전략 대비 주요 변경점:
  - K=0.3  → 진입 장벽 낮춤 (돌파 신호 더 자주 발생)
  - 모멘텀 필터 → 당일 등락률 +0.5% 이상 상승 종목만 진입 (추세 추종)
  - 예산 집행률 100% → 1종목에 예산 전액 투입 (기존 50%)
  - 최대 동시 보유 종목 3개 → 포트폴리오 분산 공격
  - 익절선 +5% → 더 큰 수익 목표 (기존 +3%)
  - 손절선 -3% → 단기 눌림목 손절 방지 (기존 -2%)
  - 트레일링 스탑 → 수익 +3% 이상 시 고점 대비 -1.5% 하락 시 자동 익절
  - 감시 주기 2초 → 빠른 시세 반응 (기존 4초)
"""
from typing import Tuple, Optional


# ============================================================
# 공격적 전략 파라미터 (AGGRESSIVE MODE)
# ============================================================
AGGRESSIVE_CONFIG = {
    # 진입 관련
    "breakout_k":           0.3,    # 변동성 돌파 계수 (낮을수록 진입 쉬움)
    "momentum_min_pct":     0.5,    # 최소 당일 등락률 조건 (%, 이상만 진입)
    "max_positions":        3,      # 최대 동시 보유 종목 수
    "budget_alloc_pct":     1.0,    # 예산 대비 1종목 투입 비율 (1.0 = 100%)
    "scan_interval_sec":    2,      # 감시 주기 (초)

    # 청산 관련
    "take_profit_pct":      0.05,   # 1차 익절 목표 (+5%)
    "stop_loss_pct":        0.03,   # 손절선 (-3%)
    "trailing_trigger_pct": 0.03,   # 트레일링 스탑 활성화 기준 (+3% 수익 시 활성)
    "trailing_gap_pct":     0.015,  # 트레일링 스탑 하락 허용 폭 (고점 대비 -1.5%)
}


class AggressiveStrategy:
    """
    공격적 자동매매 전략 엔진
    - 낮은 K 변동성 돌파 + 모멘텀 필터로 상승 추세 종목 빠르게 진입
    - 트레일링 스탑으로 수익을 최대한 키운 뒤 자동 청산
    """

    def __init__(self, config: dict = None):
        cfg = config or AGGRESSIVE_CONFIG
        self.k                  = cfg.get("breakout_k", 0.3)
        self.momentum_min_pct   = cfg.get("momentum_min_pct", 0.5)
        self.max_positions      = cfg.get("max_positions", 3)
        self.budget_alloc_pct   = cfg.get("budget_alloc_pct", 1.0)
        self.scan_interval_sec  = cfg.get("scan_interval_sec", 2)

        self.take_profit_pct    = cfg.get("take_profit_pct", 0.05)
        self.stop_loss_pct      = cfg.get("stop_loss_pct", 0.03)
        self.trailing_trigger   = cfg.get("trailing_trigger_pct", 0.03)
        self.trailing_gap       = cfg.get("trailing_gap_pct", 0.015)

        # 종목별 고점 추적 (트레일링 스탑용)  { symbol: peak_price }
        self._peak_prices: dict = {}

    # ----------------------------------------------------------
    # 진입 조건 판별
    # ----------------------------------------------------------
    def get_target_price(self, open_price: float, high_price: float, low_price: float) -> float:
        """
        변동성 돌파 목표가 산출
        Target = Open + (High - Low) * K
        K=0.3이면 전일 변동폭의 30%만 올라가도 돌파 신호 발생 → 공격적 조기 진입
        """
        price_range = max(0.0, high_price - low_price)
        if price_range == 0:
            return open_price * (1.0 + 0.003 * self.k)
        return open_price + (price_range * self.k)

    def should_buy(
        self,
        current_price: float,
        target_price: float,
        change_rate: float = 0.0,
        current_positions: int = 0
    ) -> Tuple[bool, str]:
        """
        공격적 매수 진입 판단
        조건1: 현재가 >= 변동성 돌파 목표가  (기본 조건)
        조건2: 당일 등락률 >= momentum_min_pct  (상승 모멘텀 확인)
        조건3: 현재 보유 종목 수 < max_positions

        :return: (진입여부, 판단사유)
        """
        if current_price <= 0 or target_price <= 0:
            return False, "데이터 없음"

        if current_positions >= self.max_positions:
            return False, f"최대 보유 종목 도달 ({current_positions}/{self.max_positions})"

        breakout_ok = current_price >= target_price
        momentum_ok = change_rate >= self.momentum_min_pct

        if breakout_ok and momentum_ok:
            return True, (
                f"돌파({current_price:,}원 >= {int(target_price):,}원) + "
                f"모멘텀({change_rate:+.2f}% >= +{self.momentum_min_pct}%)"
            )
        elif breakout_ok and not momentum_ok:
            return False, f"돌파 OK, 모멘텀 부족 ({change_rate:+.2f}% < +{self.momentum_min_pct}%)"
        else:
            diff = ((current_price - target_price) / target_price) * 100
            return False, f"돌파 미달 ({diff:+.1f}%)"

    def calc_buy_qty(self, budget: float, price: float) -> int:
        """예산 전액을 1종목에 집행하는 수량 계산"""
        if price <= 0:
            return 0
        alloc = budget * self.budget_alloc_pct
        return max(0, int(alloc // price))

    # ----------------------------------------------------------
    # 청산 조건 판별 (트레일링 스탑 포함)
    # ----------------------------------------------------------
    def update_peak(self, symbol: str, current_price: float):
        """종목별 고점 갱신 (트레일링 스탑 계산용)"""
        prev = self._peak_prices.get(symbol, 0)
        if current_price > prev:
            self._peak_prices[symbol] = current_price

    def reset_peak(self, symbol: str):
        """포지션 청산 시 고점 데이터 초기화"""
        self._peak_prices.pop(symbol, None)

    def check_exit(
        self,
        symbol: str,
        buy_price: float,
        current_price: float
    ) -> Tuple[bool, str, float]:
        """
        공격적 청산 판단 (손절 / 익절 / 트레일링 스탑)
        :return: (매도여부, 사유, 수익률pct)
        """
        if buy_price <= 0 or current_price <= 0:
            return False, "HOLD", 0.0

        pnl_pct = (current_price - buy_price) / buy_price

        # 1. 손절 (-3%)
        if pnl_pct <= -self.stop_loss_pct:
            self.reset_peak(symbol)
            return True, f"STOP_LOSS ({pnl_pct*100:+.2f}% <= -{self.stop_loss_pct*100:.1f}%)", pnl_pct

        # 2. 고점 갱신
        self.update_peak(symbol, current_price)
        peak = self._peak_prices.get(symbol, current_price)

        # 3. 트레일링 스탑 (고점 대비 -1.5% 하락, 단 수익이 +3% 이상일 때만 활성)
        if pnl_pct >= self.trailing_trigger:
            drop_from_peak = (peak - current_price) / peak if peak > 0 else 0
            if drop_from_peak >= self.trailing_gap:
                self.reset_peak(symbol)
                return (
                    True,
                    f"TRAILING_STOP (고점 {peak:,}원 대비 -{drop_from_peak*100:.1f}% 하락, 현재수익 {pnl_pct*100:+.2f}%)",
                    pnl_pct
                )

        # 4. 1차 익절 (+5%)
        if pnl_pct >= self.take_profit_pct:
            self.reset_peak(symbol)
            return True, f"TAKE_PROFIT ({pnl_pct*100:+.2f}% >= +{self.take_profit_pct*100:.1f}%)", pnl_pct

        return False, "HOLD", pnl_pct

    def describe(self) -> str:
        """현재 전략 파라미터 요약 문자열"""
        return (
            f"[공격모드] K={self.k} / 모멘텀>={self.momentum_min_pct}% / "
            f"최대{self.max_positions}종목 / 익절+{self.take_profit_pct*100:.0f}% / "
            f"손절-{self.stop_loss_pct*100:.0f}% / 트레일링{self.trailing_gap*100:.1f}%"
        )
