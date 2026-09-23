# -*- coding: utf-8 -*-
"""
[공격적 자동매매 봇] Aggressive Auto-Trading Engine
-----------------------------------------------------
기존 보수적 봇 대비 주요 변경:
  - AggressiveStrategy 탑재 (K=0.3, 모멘텀 필터, 트레일링 스탑)
  - 예산 100% 집행 (기존 50%)
  - 최대 3종목 동시 진입 (기존 1사이클 1종목 break)
  - 감시 주기 2초 (기존 4초)
  - 감시 종목 확대 (코스피 상위 + 테마 고성장주)
  - 진입 사유/청산 사유 터미널 콘솔 상세 로깅
"""
import asyncio
import datetime
import logging
import sys
from typing import List, Dict, Any, Optional

from auto_trader.config import settings
from auto_trader.nh_trader import NamuhAutoTrader
from auto_trader.strategy import AggressiveStrategy, AGGRESSIVE_CONFIG

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = logging.getLogger(__name__)

# ============================================================
# 공격적 감시 대상 종목 풀 (기본 5종목 → 15종목으로 확장)
# 시가총액 상위 + 당일 급등 가능 테마주 혼합
# ============================================================
AGGRESSIVE_TARGET_SYMBOLS = [
    # 코스피 시총 상위 (안정적 유동성)
    "005930",  # 삼성전자
    "005935",  # 삼성전자우
    "000660",  # SK하이닉스
    "005380",  # 현대차
    "034730",  # SK
    "009150",  # 삼성전기
    "028260",  # 삼성물산
    "105560",  # KB금융
    "055550",  # 신한지주
    # 고성장 테마주 (변동성 크고 돌파 수익 극대)
    "034020",  # 두산에너빌리티 (원자력)
    "012450",  # 한화에어로스페이스 (방산)
    "329180",  # HD현대중공업 (조선)
    "402340",  # SK스퀘어
    "207940",  # 삼성바이오로직스
    "373220",  # LG에너지솔루션
]


class TradingBot:
    def __init__(self):
        self.is_running: bool = False

        # 공격적 전략 탑재
        self.strategy = AggressiveStrategy(AGGRESSIVE_CONFIG)
        self.trader = NamuhAutoTrader()
        self.logs: List[Dict[str, str]] = []
        self.budget: int = 2000000   # 1회 매수 예산 (설정 가능)
        self.iteration: int = 0

        self.add_log(
            "SYSTEM",
            f"[공격모드] 자동매매 엔진 준비 완료 | {self.strategy.describe()}"
        )

    # ----------------------------------------------------------
    # 로그 관리
    # ----------------------------------------------------------
    def add_log(self, log_type: str, message: str):
        """실시간 활동 로그 기록 (최근 60개 유지)"""
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        entry = {"time": now_str, "type": log_type, "message": message}
        self.logs.insert(0, entry)
        if len(self.logs) > 80:
            self.logs = self.logs[:80]
        print(f"[{now_str}] [{log_type}] {message}")

    def get_recent_logs(self, limit: int = 25) -> List[Dict[str, str]]:
        return self.logs[:limit]

    # ----------------------------------------------------------
    # 예산 설정
    # ----------------------------------------------------------
    def set_budget(self, budget: int):
        if budget > 0:
            self.budget = budget
            self.add_log("CONFIG", f"매매 예산 변경: {budget:,}원 (전략: {self.strategy.describe()})")

    # ----------------------------------------------------------
    # 감시 종목 목록
    # ----------------------------------------------------------
    def get_target_symbols(self) -> List[str]:
        configured = [s.strip() for s in settings.TARGET_SYMBOLS.split(",") if s.strip()]
        combined = list(dict.fromkeys(configured + AGGRESSIVE_TARGET_SYMBOLS))
        return combined

    # ----------------------------------------------------------
    # 시세 조회
    # ----------------------------------------------------------
    async def fetch_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """종목 시가/고가/저가/현재가/등락률 조회"""
        if self.trader.use_real_api:
            import nhplug
            try:
                data = await asyncio.to_thread(
                    nhplug.call,
                    '/krstock/quote/v1/currentPrice',
                    {'iem_cd': symbol, 'market_cd': 'KRX'}
                )
                out = data.get('Output_0', {}) if isinstance(data, dict) else {}
                cur = int(out.get('stck_prpr') or 0)
                opn = int(out.get('stck_oprc') or cur)
                hgh = int(out.get('stck_hgpr') or cur)
                low = int(out.get('stck_lwpr') or cur)
                nm  = out.get('iem_nm', symbol).replace("*", "").strip()
                chg = float(out.get('prdy_ctrt') or 0.0)
                if cur > 0:
                    return {"symbol": symbol, "name": nm, "price": cur,
                            "open": opn, "high": hgh, "low": low, "change": chg}
            except Exception as e:
                logger.warning(f"시세 조회 실패 ({symbol}): {e}")

        # Fallback (PAPER 모드 또는 API 오류)
        quotes = await asyncio.to_thread(
            self.trader.get_quotes, [{"symbol": symbol, "name": symbol, "price": 0}]
        )
        if quotes and quotes[0]["price"] > 0:
            q = quotes[0]
            p = q["price"]
            chg = q.get("change", 0.0)
            return {
                "symbol": symbol, "name": q.get("name", symbol),
                "price": p,
                "open": int(p * (1 - 0.005)),   # 시가 추정: 현재가 -0.5%
                "high": int(p * (1 + chg / 100 * 0.5 + 0.005)),  # 고가 추정
                "low":  int(p * (1 - abs(chg) / 100 * 0.5 - 0.005)),   # 저가 추정
                "change": chg
            }
        return None

    # ----------------------------------------------------------
    # 메인 매매 사이클
    # ----------------------------------------------------------
    async def step(self):
        """공격적 자동매매 1사이클 실행"""
        self.iteration += 1

        # ======================================================
        # 1단계: 보유 포지션 청산 감시 (Exit Management)
        # ======================================================
        positions = await asyncio.to_thread(self.trader.get_positions)

        for sym, pos in list(positions.items()):
            held_qty = pos.get("qty", 0)
            if held_qty <= 0:
                continue

            buy_price = pos.get("buy_price", 0)
            s_data    = await self.fetch_stock_data(sym)
            cur_price = s_data["price"] if s_data else pos.get("current_price", buy_price)
            s_name    = pos.get("name") or (s_data["name"] if s_data else sym)

            should_sell, reason, pnl_pct = self.strategy.check_exit(sym, buy_price, cur_price)

            if should_sell:
                if "TRAILING" in reason:
                    label = "📈 [트레일링 스탑 익절]"
                    log_t = "TRAILING_EXIT"
                elif "TAKE_PROFIT" in reason:
                    label = "🎯 [익절 목표 달성]"
                    log_t = "SELL_TRIGGER"
                else:
                    label = "🛑 [손절]"
                    log_t = "SELL_TRIGGER"

                self.add_log(log_t, f"{label} {s_name}({sym}) {reason} → 전량 {held_qty}주 매도 발주")
                ok, ord_id, msg = await asyncio.to_thread(
                    self.trader.order_sell, sym, cur_price, held_qty
                )
                if ok:
                    self.add_log("SELL_SUCCESS",
                        f"✅ 매도 체결: {s_name} {held_qty}주 | 수익률 {pnl_pct*100:+.2f}% (주문번호: {ord_id})")
                else:
                    self.add_log("SELL_FAILED", f"❌ {s_name} 매도 거부: {msg}")
            else:
                # 포지션 유지 — 수익률 로깅 (3사이클마다)
                peak = self.strategy._peak_prices.get(sym, cur_price)
                trailing_active = pnl_pct >= self.strategy.trailing_trigger
                trailing_tag = f" | 트레일링 고점 {peak:,}원" if trailing_active else ""
                if self.iteration % 3 == 0:
                    self.add_log("MONITOR",
                        f"📊 [보유 유지] {s_name}({sym}) {held_qty}주 | "
                        f"수익률 {pnl_pct*100:+.2f}%{trailing_tag} "
                        f"| 목표 익절+{self.strategy.take_profit_pct*100:.0f}% "
                        f"손절-{self.strategy.stop_loss_pct*100:.0f}%")

        # ======================================================
        # 2단계: 신규 매수 탐색 (Entry Management)
        # ======================================================
        positions = await asyncio.to_thread(self.trader.get_positions)  # 갱신
        current_pos_count = sum(1 for p in positions.values() if p.get("qty", 0) > 0)

        # 최대 보유 종목 수 이미 채운 경우 스킵
        if current_pos_count >= self.strategy.max_positions:
            if self.iteration % 5 == 0:
                self.add_log("INFO",
                    f"🔒 최대 보유 종목 수({self.strategy.max_positions}개) 도달 — 신규 진입 대기 중")
            return

        balance       = await asyncio.to_thread(self.trader.get_balance)
        usable_budget = min(balance, self.budget) if balance > 0 else 0

        if usable_budget <= 0:
            if self.iteration % 5 == 0:
                self.add_log("INFO", "💸 가용 예산 없음 — 매수 대기 중")
            return

        target_symbols = self.get_target_symbols()
        bought_this_cycle = 0  # 이번 사이클에 매수한 종목 수

        for sym in target_symbols:
            # 최대 보유 도달 시 즉시 중단
            if (current_pos_count + bought_this_cycle) >= self.strategy.max_positions:
                break

            # 이미 보유 중인 종목 스킵
            if sym in positions and positions[sym].get("qty", 0) > 0:
                continue

            s_data = await self.fetch_stock_data(sym)
            if not s_data:
                continue

            cur_price  = s_data["price"]
            opn, hgh, low = s_data["open"], s_data["high"], s_data["low"]
            nm         = s_data["name"]
            change_pct = s_data["change"]

            # 변동성 돌파 목표가 계산
            target_price = self.strategy.get_target_price(opn, hgh, low)

            # 공격적 진입 판단 (돌파 + 모멘텀)
            should_enter, enter_reason = self.strategy.should_buy(
                cur_price, target_price, change_pct, current_pos_count + bought_this_cycle
            )

            if should_enter and usable_budget >= cur_price:
                buy_qty   = self.strategy.calc_buy_qty(usable_budget, cur_price)
                if buy_qty <= 0:
                    continue

                total_cost = cur_price * buy_qty
                self.add_log("BUY_SIGNAL",
                    f"⚡ [공격 진입 신호] {nm}({sym}) | {enter_reason} | "
                    f"{buy_qty}주 × {cur_price:,}원 = {total_cost:,}원 발주!")

                ok, ord_id, msg = await asyncio.to_thread(
                    self.trader.order_buy, sym, cur_price, buy_qty
                )
                if ok:
                    self.add_log("BUY_SUCCESS",
                        f"🚀 [매수 체결] {nm}({sym}) {buy_qty}주 @ {cur_price:,}원 "
                        f"(총 {total_cost:,}원 | 주문번호: {ord_id})")
                    usable_budget -= total_cost
                    bought_this_cycle += 1
                    # 트레일링 고점 초기화
                    self.strategy.reset_peak(sym)
                else:
                    self.add_log("BUY_FAILED", f"⚠️ {nm} 매수 거부: {msg}")

            else:
                # 조건 미달 — 주기적 스캔 로그
                if self.iteration % 4 == 0:
                    self.add_log("SCAN",
                        f"👀 [스캔] {nm}({sym}) {cur_price:,}원 "
                        f"(목표가 {int(target_price):,}원 | {change_pct:+.2f}%) → {enter_reason}")

    # ----------------------------------------------------------
    # 메인 루프
    # ----------------------------------------------------------
    async def run_loop(self):
        """공격적 자동매매 감시 루프 (2초 주기)"""
        self.is_running = True
        self.add_log("START",
            f"🔥 [공격적 자동매매 시작] {self.strategy.describe()} | "
            f"감시주기 {self.strategy.scan_interval_sec}초 | "
            f"예산 {self.budget:,}원")

        while self.is_running:
            try:
                await self.step()
            except Exception as e:
                self.add_log("ERROR", f"사이클 오류: {e}")
                logger.error(f"[BOT ERROR] {e}")

            await asyncio.sleep(self.strategy.scan_interval_sec)

        self.add_log("STOP", "🛑 자동매매 봇이 정상 중지되었습니다.")

    def stop(self):
        self.is_running = False


bot = TradingBot()
