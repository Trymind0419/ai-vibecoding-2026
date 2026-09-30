# -*- coding: utf-8 -*-
"""
[주식 고수 5대 실전 단타 전략 엔진] Master Day-Trading Strategy
---------------------------------------------------------------------------
국내 실전투자대회 우승자 및 프랍 트레이더들의 5대 핵심 단타 기법 통합:
  1. 시가 갭 & 시초가 돌파 (OPENING_BREAKOUT - 09:00~09:30)
  2. 전고점 & VI 직전 돌파 (DAY_HIGH_BREAKOUT - 09:10~15:00)
  3. 첫 번째 눌림목 반등 (PULLBACK_DIP_BUY - 09:20~11:30)
  4. 상한가 굳히기 & 종가 베팅 (UPPER_LIMIT_OR_CLOSE_BET - 09:30~15:20)
  5. 급등 모멘텀 스캘핑 (SURGE_SCALPING - 장중 상시)

고수의 3대 리스크 관리:
  - 기계적 손절선: -2.0% (칼손절)
  - 트레일링 스탑: +2.5% 수익 달성 후 고점 대비 -1.2% 밀리면 이익 보존 청산
  - 목표 익절선: +4.5% 전량 청산
"""
import datetime
from typing import Tuple, Optional, Dict, Any


# ============================================================
# 5대 단타 전략 기본 설정 (MASTER STRATEGY CONFIG)
# ============================================================
MASTER_STRATEGY_CONFIG = {
    # 포지션 및 예산
    "max_positions":        3,      # 최대 동시 보유 종목 수
    "budget_alloc_pct":     1.0,    # 예산 대비 1종목 투입 비율 (1.0 = 100%)
    "max_stock_ratio_pct":  0.40,   # 단일 종목 총자산 대비 최대 비중 (40% 상한 제한)
    "scan_interval_sec":    2,      # 감시 주기 (초)

    # 리스크 관리 파라미터
    "stop_loss_pct":        0.02,   # 기계적 손절선 (-2.0%)
    "take_profit_pct":      0.045,  # 1차 목표 익절 (+4.5%)
    "trailing_trigger_pct": 0.025,  # 트레일링 스탑 활성화 기준 (+2.5% 수익 시)
    "trailing_gap_pct":     0.012,  # 트레일링 스탑 낙폭 허용 (고점 대비 -1.2%)

    # 기법별 세부 파라미터
    "breakout_k":           0.25,   # 변동성 돌파 계수 (K=0.25)
    "day_high_threshold":   0.995,  # 전고점 근접률 (99.5% 이상)
    "pullback_min_drop":    0.012,  # 1차 상승 후 최소 눌림 폭 (-1.2%)
    "pullback_max_drop":    0.038,  # 최대 허용 눌림 폭 (-3.8%, 이상은 지지 실패)
    "pullback_rebound_min": 0.005,  # 눌림 저점 대비 반등 폭 (+0.5%)
}

# 기존 코드 호환용 별칭
AGGRESSIVE_CONFIG = MASTER_STRATEGY_CONFIG


class MasterDayTradingStrategy:
    """
    주식 고수의 5대 실전 단타 전략 엔진
    """

    def __init__(self, config: dict = None):
        cfg = config or MASTER_STRATEGY_CONFIG
        self.max_positions      = cfg.get("max_positions", 3)
        self.budget_alloc_pct   = cfg.get("budget_alloc_pct", 1.0)
        self.max_stock_ratio    = cfg.get("max_stock_ratio_pct", 0.40)
        self.scan_interval_sec  = cfg.get("scan_interval_sec", 2)

        self.stop_loss_pct      = cfg.get("stop_loss_pct", 0.02)
        self.take_profit_pct    = cfg.get("take_profit_pct", 0.045)
        self.trailing_trigger   = cfg.get("trailing_trigger_pct", 0.025)
        self.trailing_gap       = cfg.get("trailing_gap_pct", 0.012)

        self.k                  = cfg.get("breakout_k", 0.25)
        self._peak_prices: dict = {}

    def get_target_price(self, open_price: float, high_price: float, low_price: float) -> float:
        """변동성 돌파 목표가 산출: Open + (High - Low) * K"""
        price_range = max(0.0, high_price - low_price)
        if price_range == 0:
            return open_price * (1.0 + 0.003 * self.k)
        return open_price + (price_range * self.k)

    def evaluate_5_techniques(
        self,
        current_price: float,
        open_price: float,
        high_price: float,
        low_price: float,
        change_rate: float,
        now_time: Optional[datetime.time] = None
    ) -> Tuple[bool, str, str]:
        """
        5대 실전 단타 기법을 실시간 순차 평가하여 가장 강력한 진입 신호 반환
        :return: (진입여부, 기법명, 상세사유)
        """
        if current_price <= 0 or open_price <= 0:
            return False, "NONE", "시세 데이터 없음"

        t = now_time or datetime.datetime.now().time()
        curr_min = t.hour * 60 + t.minute

        # ------------------------------------------------------------------
        # 1. 시가 갭 & 시초가 돌파 (OPENING_BREAKOUT)
        # 시간대: 09:00 ~ 09:30 (장초반 30분 골든타임)
        # 조건: 시가 대비 상승 (+0.8% 이상 돌파) + 전일대비 상승세 (+1.0% 이상)
        # ------------------------------------------------------------------
        if 9 * 60 <= curr_min <= 9 * 60 + 30:
            if current_price >= open_price * 1.008 and change_rate >= 1.0:
                target_p = self.get_target_price(open_price, high_price, low_price)
                if current_price >= target_p:
                    breakout_pct = ((current_price - open_price) / open_price) * 100
                    return True, "시초가돌파", (
                        f"[기법1:시초가돌파] 시가({open_price:,}원) 대비 +{breakout_pct:.1f}% 돌파 "
                        f"+ 당일등락 {change_rate:+.2f}% 장초반 강력 수급 유입"
                    )

        # ------------------------------------------------------------------
        # 2. 전고점 & VI 직전 돌파 (DAY_HIGH_BREAKOUT)
        # 시간대: 09:10 ~ 15:00
        # 조건: 당일 최고가의 99.5% 이상 도달 + 1차 VI 직전 슈팅 구간 (+3.5% ~ +9.8%)
        # ------------------------------------------------------------------
        if high_price > 0 and current_price >= (high_price * 0.995):
            if 3.5 <= change_rate <= 9.8:
                return True, "전고점·VI돌파", (
                    f"[기법2:전고점·VI돌파] 당일최고가({high_price:,}원) 99.5% 돌파 근접 "
                    f"+ 1차VI직전 매도벽 흡수 슈팅 (등락률 {change_rate:+.2f}%)"
                )

        # ------------------------------------------------------------------
        # 3. 첫 번째 눌림목 반등 (PULLBACK_DIP_BUY)
        # 시간대: 09:20 ~ 11:30 (1차 급등 후 차익 매물 소화 구간)
        # 조건: 오전 고점이 시가대비 +2.5% 이상 발생 후, 고점대비 -1.2% ~ -3.8% 눌림목 형성
        #       당일 저점 대비 +0.5% 이상 양봉 반등 턴어라운드 확인
        # ------------------------------------------------------------------
        if 9 * 60 + 20 <= curr_min <= 11 * 60 + 30:
            peak_gain = (high_price - open_price) / open_price if open_price > 0 else 0
            if peak_gain >= 0.025:
                pullback_drop = (high_price - current_price) / high_price if high_price > 0 else 0
                if 0.012 <= pullback_drop <= 0.038:
                    rebound = (current_price - low_price) / low_price if low_price > 0 else 0
                    if rebound >= 0.005 and current_price >= open_price:
                        return True, "첫눌림목반등", (
                            f"[기법3:첫눌림목반등] 1차상승(+{peak_gain*100:.1f}%) 후 -{pullback_drop*100:.1f}% 건전한 눌림목 "
                            f"→ 바닥대비 +{rebound*100:.1f}% 양봉 턴어라운드 포착"
                        )

        # ------------------------------------------------------------------
        # 4. 상한가 굳히기(상따) & 종가 베팅 (UPPER_LIMIT_OR_CLOSE_BET)
        # ------------------------------------------------------------------
        # 4-A. 상한가 굳히기 (09:30 ~ 14:30): +20% 이상 급등 대장주 상한가 도달 직전
        if change_rate >= 20.0 and current_price >= (high_price * 0.99):
            return True, "상한가굳히기", (
                f"[기법4:상한가굳히기] 당일 +{change_rate:.1f}% 폭등 상한가 굳히기 진입 (고점 99% 유지)"
            )

        # 4-B. 종가 베팅 (15:00 ~ 15:20): 주도주 종가 고가 마감 추종 (익일 시초가 갭 공략)
        if 15 * 60 <= curr_min <= 15 * 60 + 20:
            if 5.0 <= change_rate <= 18.0 and current_price >= (high_price * 0.985):
                return True, "종가베팅", (
                    f"[기법4:종가베팅] 장마감 주도주 종가 고가 마감({change_rate:+.1f}%) → 익일 갭상승 기대"
                )

        # ------------------------------------------------------------------
        # 5. 거래대금/급등 모멘텀 스캘핑 (SURGE_SCALPING)
        # 시간대: 장중 상시 (09:00 ~ 15:20)
        # 조건: 변동성 돌파(K=0.25) 달성 + 당일 모멘텀 +1.5% 이상 지속
        # ------------------------------------------------------------------
        target_price = self.get_target_price(open_price, high_price, low_price)
        if current_price >= target_price and change_rate >= 1.5:
            return True, "급등스캘핑", (
                f"[기법5:급등스캘핑] K변동성돌파({current_price:,}원 >= {int(target_price):,}원) "
                f"+ 모멘텀(+{change_rate:.2f}%) 추세 추종"
            )

        diff = ((current_price - target_price) / target_price) * 100 if target_price > 0 else 0
        return False, "NONE", f"5대 기법 조건 대기 중 (돌파이격 {diff:+.1f}%, 등락률 {change_rate:+.1f}%)"

    def should_buy(
        self,
        current_price: float,
        open_price: float = 0.0,
        high_price: float = 0.0,
        low_price: float = 0.0,
        change_rate: float = 0.0,
        current_positions: int = 0,
        *args, **kwargs
    ) -> Tuple[bool, str, str]:
        """
        신규 매수 진입 종합 판별
        :return: (진입여부, 기법태그, 상세사유)
        """
        if current_positions >= self.max_positions:
            return False, "MAX_POSITIONS", f"최대 보유 종목 수 도달 ({current_positions}/{self.max_positions})"

        # 구버전 호출 (cur_price, target_price, change_pct, cur_positions) 대응
        if args and len(args) >= 1 and high_price == 0.0:
            target_price = open_price
            chg = args[0]
            if current_price >= target_price and chg >= 0.5:
                return True, "급등스캘핑", f"돌파({current_price:,}원 >= {int(target_price):,}원) + 모멘텀({chg:+.2f}%)"
            return False, "NONE", "돌파 미달"

        return self.evaluate_5_techniques(current_price, open_price, high_price, low_price, change_rate)

    def calc_buy_qty(self, budget: float, price: float, total_assets: float = 0.0, current_held_qty: int = 0) -> int:
        """
        예산 대비 1종목 투입 수량 계산 (총 금액의 40% 비중 상한 엄격 적용)
        :param budget: 1회 가용 투입 예산
        :param price: 현재 매수가
        :param total_assets: 계좌 총 평가 자산 (0이면 budget 기준 적용)
        :param current_held_qty: 이미 보유 중인 동일 종목 주식 수
        :return: 40% 비중 상한을 준수하는 안전 매수 가능 수량
        """
        if price <= 0:
            return 0
        
        # 기본 예산 할당 금액
        alloc = budget * self.budget_alloc_pct
        
        # 총자산 기준 40% 상한선 적용 (총자산이 주어지면 총자산의 40%, 없으면 budget의 40%)
        ref_assets = total_assets if total_assets > 0 else budget
        if ref_assets > 0:
            max_stock_limit = ref_assets * self.max_stock_ratio
            already_invested = current_held_qty * price
            remaining_cap = max(0.0, max_stock_limit - already_invested)
            alloc = min(alloc, remaining_cap)

        return max(0, int(alloc // price))

    def update_peak(self, symbol: str, current_price: float):
        """종목별 최고점 갱신 (트레일링 스탑용)"""
        prev = self._peak_prices.get(symbol, 0)
        if current_price > prev:
            self._peak_prices[symbol] = current_price

    def reset_peak(self, symbol: str):
        """청산 시 최고점 캐시 초기화"""
        self._peak_prices.pop(symbol, None)

    def check_exit(
        self,
        symbol: str,
        buy_price: float,
        current_price: float
    ) -> Tuple[bool, str, float]:
        """
        고수의 리스크 관리 청산 규칙:
          1. 기계적 손절 (-2.0%)
          2. 트레일링 스탑 (최고점 수익이 +2.5% 이상 도달 후, 최고점 대비 -1.2% 하락 시 이익 보존)
          3. 목표 익절 (+4.5%)
        """
        if buy_price <= 0 or current_price <= 0:
            return False, "HOLD", 0.0

        pnl_pct = (current_price - buy_price) / buy_price

        # 1. 기계적 손절 (-2.0%)
        if pnl_pct <= -self.stop_loss_pct:
            self.reset_peak(symbol)
            return True, f"STOP_LOSS (기계적 손절 {pnl_pct*100:+.2f}% <= -{self.stop_loss_pct*100:.1f}%)", pnl_pct

        # 2. 고점 갱신
        self.update_peak(symbol, current_price)
        peak = self._peak_prices.get(symbol, current_price)

        # 3. 트레일링 스탑 (최고점 수익이 +2.5% 이상 도달 후, 최고점 대비 -1.2% 밀릴 때 이익 보존 청산)
        peak_gain_pct = (peak - buy_price) / buy_price if buy_price > 0 else 0
        if peak_gain_pct >= self.trailing_trigger:
            drop_from_peak = (peak - current_price) / peak if peak > 0 else 0
            if drop_from_peak >= self.trailing_gap:
                self.reset_peak(symbol)
                return (
                    True,
                    f"TRAILING_STOP (고점 {peak:,}원 대비 -{drop_from_peak*100:.1f}% 하락, 수익확정 {pnl_pct*100:+.2f}%)",
                    pnl_pct
                )

        # 4. 1차 목표 익절 (+4.5%)
        if pnl_pct >= self.take_profit_pct:
            self.reset_peak(symbol)
            return True, f"TAKE_PROFIT (목표달성 {pnl_pct*100:+.2f}% >= +{self.take_profit_pct*100:.1f}%)", pnl_pct

        return False, "HOLD", pnl_pct

    def describe(self) -> str:
        return (
            f"[고수5대단타] 1.시초가돌파 2.전고점/VI돌파 3.첫눌림목반등 4.상따/종가베팅 5.급등스캘핑 | "
            f"익절+{self.take_profit_pct*100:.1f}% / 손절-{self.stop_loss_pct*100:.1f}% / "
            f"트레일링+{self.trailing_trigger*100:.1f}%(낙폭-{self.trailing_gap*100:.1f}%)"
        )


# 기존 코드 호환용 별칭 (Alias)
AggressiveStrategy = MasterDayTradingStrategy
