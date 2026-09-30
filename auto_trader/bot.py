# -*- coding: utf-8 -*-
"""
[고수 5대 실전 단타 자동매매 봇] Master Day-Trading Auto Engine
---------------------------------------------------------------------------
실전투자대회 우승자 및 프랍 트레이더들의 5대 핵심 단타 기법 자동 수행:
  1. 시가 갭 & 시초가 돌파 (OPENING_BREAKOUT - 09:00~09:30)
  2. 전고점 & VI 직전 돌파 (DAY_HIGH_BREAKOUT - 09:10~15:00)
  3. 첫 번째 눌림목 반등 (PULLBACK_DIP_BUY - 09:20~11:30)
  4. 상한가 굳히기 & 종가 베팅 (UPPER_LIMIT_OR_CLOSE_BET - 09:30~15:20)
  5. 급등 모멘텀 스캘핑 (SURGE_SCALPING - 장중 상시)

고수의 3대 리스크 관리:
  - 기계적 손절: -2.0%
  - 트레일링 스탑: +2.5% 수익 달성 후 고점 대비 -1.2% 하락 시 이익 보존 청산
  - 목표 익절: +4.5% 전량 청산
"""
import asyncio
import datetime
import logging
import sys
from typing import List, Dict, Any, Optional

from auto_trader.config import settings
from auto_trader.nh_trader import NamuhAutoTrader
from auto_trader.strategy import MasterDayTradingStrategy, MASTER_STRATEGY_CONFIG

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = logging.getLogger(__name__)

# ============================================================
# 단타 감시 대상 종목 풀 (코스피 시총 주도주 + 변동성 급등주)
# ============================================================
TARGET_SYMBOLS = [
    # 코스피 시총 상위 (안정적 유동성 & 호가 두터운 대장주)
    "005930",  # 삼성전자
    "005935",  # 삼성전자우
    "000660",  # SK하이닉스
    "005380",  # 현대차
    "034730",  # SK
    "009150",  # 삼성전기
    "028260",  # 삼성물산
    "105560",  # KB금융
    "055550",  # 신한지주
    # 주도 테마주 (원전 / 방산 / 조선 / 바이오 등 변동성 주도주)
    "034020",  # 두산에너빌리티
    "012450",  # 한화에어로스페이스
    "329180",  # HD현대중공업
    "402340",  # SK스퀘어
    "207940",  # 삼성바이오로직스
    "373220",  # LG에너지솔루션
]


class TradingBot:
    def __init__(self):
        self.is_running: bool = False

        # 5대 단타 전략 엔진 탑재
        self.strategy = MasterDayTradingStrategy(MASTER_STRATEGY_CONFIG)
        self.trader = NamuhAutoTrader()
        from auto_trader.database import db
        self.logs: List[Dict[str, str]] = db.get_recent_bot_logs(limit=80)
        self.budget: int = 2000000   # 1회 매수 예산 (기본값)
        self.iteration: int = 0

        # 기존 보유 포지션의 트레일링 최고가 복원
        for sym, p in self.trader.get_positions().items():
            if p.get("highest_price", 0) > 0:
                self.strategy._peak_prices[sym] = p["highest_price"]

        self.add_log(
            "SYSTEM",
            f"[엔진 기동] 고수 5대 실전단타 봇 준비 완료 | {self.strategy.describe()}"
        )

    # ----------------------------------------------------------
    # 로그 관리
    # ----------------------------------------------------------
    def add_log(self, log_type: str, message: str):
        """실시간 활동 로그 기록 (DB 영구 저장 및 최근 80개 유지)"""
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        entry = {"time": now_str, "type": log_type, "message": message}
        self.logs.insert(0, entry)
        if len(self.logs) > 80:
            self.logs = self.logs[:80]
        
        try:
            from auto_trader.database import db
            db.add_bot_log(log_type, message, now_str)
        except Exception:
            pass
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
        combined = list(dict.fromkeys(configured + TARGET_SYMBOLS))
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
                prev = int(out.get('stck_prdy_clpr') or 0)
                opn = int(out.get('stck_oprc') or cur)
                hgh = int(out.get('stck_hgpr') or cur)
                low = int(out.get('stck_lwpr') or cur)
                nm  = out.get('iem_nm', symbol).replace("*", "").strip()
                raw_ctrt = float(out.get('prdy_ctrt') or 0.0)
                
                # 전일 종가 기준 상승/하락 부호 반영
                if prev > 0 and cur > 0:
                    if cur < prev:
                        chg = -abs(raw_ctrt)
                    elif cur > prev:
                        chg = abs(raw_ctrt)
                    else:
                        chg = 0.0
                else:
                    chg = raw_ctrt

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
                "open": int(p * (1 - 0.005)),   # 시가 추정
                "high": int(p * (1 + chg / 100 * 0.5 + 0.005)),  # 고가 추정
                "low":  int(p * (1 - abs(chg) / 100 * 0.5 - 0.005)),   # 저가 추정
                "change": chg
            }
        return None

    # ----------------------------------------------------------
    # 메인 매매 사이클
    # ----------------------------------------------------------
    async def step(self):
        """5대 단타 전략 자동매매 1사이클 실행"""
        self.iteration += 1

        # ======================================================
        # 1단계: 보유 포지션 리스크 관리, 40% 비중 상한 리밸런싱 및 청산 감시
        # ======================================================
        # (1) 단일 종목 총자산 40% 초과 보유 시 즉각 자동 리밸런싱 매도 실행
        rebal_results = await asyncio.to_thread(self.trader.rebalance_excess_positions, self.strategy.max_stock_ratio)
        for r in rebal_results:
            if r.get("success"):
                self.add_log("REBALANCE_SUCCESS",
                    f"⚖️ [비중 40% 리밸런싱 매도] {r['name']}({r['symbol']}) {r['sold_qty']}주 매도 "
                    f"(@ {r['sell_price']:,}원) → 잔여 {r['remaining_qty']}주 (40% 상한 유지)")
            else:
                self.add_log("REBALANCE_FAILED", f"⚠️ {r['name']} 40% 리밸런싱 매도 실패: {r.get('message')}")

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
                    label = "📈 [트레일링 익절]"
                    log_t = "TRAILING_EXIT"
                    exit_reason = "TRAILING_STOP"
                elif "TAKE_PROFIT" in reason:
                    label = "🎯 [목표 익절]"
                    log_t = "SELL_TRIGGER"
                    exit_reason = "TAKE_PROFIT"
                else:
                    label = "🛑 [기계적 칼손절]"
                    log_t = "SELL_TRIGGER"
                    exit_reason = "STOP_LOSS"

                self.add_log(log_t, f"{label} {s_name}({sym}) {reason} → 전량 {held_qty}주 매도 발주")
                ok, ord_id, msg = await asyncio.to_thread(
                    self.trader.order_sell, sym, cur_price, held_qty, "LIMIT", exit_reason, f"{label} {reason}"
                )
                if ok:
                    self.add_log("SELL_SUCCESS",
                        f"✅ 매도 체결: {s_name} {held_qty}주 | 실현수익률 {pnl_pct*100:+.2f}% (주문번호: {ord_id})")
                else:
                    self.add_log("SELL_FAILED", f"❌ {s_name} 매도 거부: {msg}")
            else:
                # 포지션 유지 — 시세 DB 갱신 및 수익률 로깅
                peak = self.strategy._peak_prices.get(sym, cur_price)
                try:
                    from auto_trader.database import db
                    db.update_position_price(sym, cur_price, peak)
                except Exception:
                    pass
                trailing_active = pnl_pct >= self.strategy.trailing_trigger
                trailing_tag = f" | 트레일링 고점 {peak:,}원" if trailing_active else ""
                if self.iteration % 3 == 0:
                    self.add_log("MONITOR",
                        f"📊 [포지션 유지] {s_name}({sym}) {held_qty}주 | "
                        f"수익률 {pnl_pct*100:+.2f}%{trailing_tag} "
                        f"| 목표 익절+{self.strategy.take_profit_pct*100:.1f}% "
                        f"손절-{self.strategy.stop_loss_pct*100:.1f}%")

        # ======================================================
        # 2단계: 5대 단타 기법 신규 매수 탐색 (Entry Management)
        # ======================================================
        positions = await asyncio.to_thread(self.trader.get_positions)
        current_pos_count = sum(1 for p in positions.values() if p.get("qty", 0) > 0)

        if current_pos_count >= self.strategy.max_positions:
            if self.iteration % 5 == 0:
                self.add_log("INFO",
                    f"🔒 최대 보유 종목 수({self.strategy.max_positions}개) 도달 — 신규 진입 대기 중")
            return

        balance       = await asyncio.to_thread(self.trader.get_balance)
        total_assets  = await asyncio.to_thread(self.trader.get_total_assets)
        usable_budget = min(balance, self.budget) if balance > 0 else 0

        if usable_budget <= 0:
            if self.iteration % 5 == 0:
                self.add_log("INFO", "💸 가용 예산 없음 — 매수 대기 중")
            return

        target_symbols = self.get_target_symbols()
        bought_this_cycle = 0

        for sym in target_symbols:
            if (current_pos_count + bought_this_cycle) >= self.strategy.max_positions:
                break

            if sym in positions and positions[sym].get("qty", 0) > 0:
                continue

            s_data = await self.fetch_stock_data(sym)
            if not s_data:
                continue

            cur_price  = s_data["price"]
            opn, hgh, low = s_data["open"], s_data["high"], s_data["low"]
            nm         = s_data["name"]
            change_pct = s_data["change"]

            # 5대 단타 기법 종합 평가
            should_enter, tech_tag, enter_reason = self.strategy.should_buy(
                current_price=cur_price,
                open_price=opn,
                high_price=hgh,
                low_price=low,
                change_rate=change_pct,
                current_positions=current_pos_count + bought_this_cycle
            )

            if should_enter and usable_budget >= cur_price:
                cur_held = positions.get(sym, {}).get("qty", 0) if sym in positions else 0
                buy_qty  = self.strategy.calc_buy_qty(
                    budget=usable_budget,
                    price=cur_price,
                    total_assets=total_assets,
                    current_held_qty=cur_held
                )
                if buy_qty <= 0:
                    if self.iteration % 4 == 0:
                        self.add_log("RISK_SKIP",
                            f"🛡️ [비중 한도 40% 도달] {nm}({sym}) 총자산({total_assets:,}원)의 40% 한도를 초과하여 매수 제외")
                    continue

                total_cost = cur_price * buy_qty
                self.add_log("BUY_SIGNAL",
                    f"⚡ [{tech_tag} 포착] {nm}({sym}) | {enter_reason} | "
                    f"{buy_qty}주 × {cur_price:,}원 = {total_cost:,}원 발주 (총자산 40% 한도 준수)")

                ok, ord_id, msg = await asyncio.to_thread(
                    self.trader.order_buy, sym, cur_price, buy_qty, "LIMIT", enter_reason
                )
                if ok:
                    self.add_log("BUY_SUCCESS",
                        f"🚀 [{tech_tag} 매수 완료] {nm}({sym}) {buy_qty}주 @ {cur_price:,}원 "
                        f"(총 {total_cost:,}원 | 주문번호: {ord_id})")
                    usable_budget -= total_cost
                    bought_this_cycle += 1
                    self.strategy.reset_peak(sym)
                else:
                    self.add_log("BUY_FAILED", f"⚠️ {nm} 매수 거부: {msg}")

            else:
                if self.iteration % 4 == 0:
                    self.add_log("SCAN",
                        f"👀 [스캔] {nm}({sym}) {cur_price:,}원 ({change_pct:+.2f}%) → {enter_reason}")

    # ----------------------------------------------------------
    # 메인 루프
    # ----------------------------------------------------------
    async def run_loop(self):
        """5대 단타 자동매매 감시 루프 (2초 주기)"""
        self.is_running = True
        self.add_log("START",
            f"🔥 [고수 5대 실전단타 봇 가동] {self.strategy.describe()} | "
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
