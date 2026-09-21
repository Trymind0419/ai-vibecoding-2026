"""자동매매 오케스트레이터 봇 모듈.

시세 수집 -> 전략 시그널 평가 -> 리스크 검증 -> 모드별 주문 발주 -> DB 기록 전체 파이프라인을 관장합니다.
"""

import sys
# 윈도우 콘솔 인코딩 방어
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import asyncio
import datetime
import uuid
from typing import Dict, Any, List, Optional
from src.config import settings
from src.database import db
from src.paper_trader import PaperTrader
from src.nh_trader import NamuhAutoTrader
from src.strategy import VolatilityBreakoutStrategy
from src.risk_manager import RiskManager


class TradingBot:
    """자동매매 로봇 오케스트레이터."""

    def __init__(self, mode: Optional[str] = None):
        self.mode = (mode or settings.TRADING_MODE).upper()
        self.paper_trader = PaperTrader(initial_cash=settings.INITIAL_PAPER_CASH)
        self.nh_trader: Optional[NamuhAutoTrader] = None
        self.strategy = VolatilityBreakoutStrategy(k=0.5)
        self.risk_manager = RiskManager()
        
        self.is_running = False
        self.monitored_tickers: List[str] = ["005930", "000660"]  # 기본: 삼성전자, SK하이닉스
        self.last_run_time: Optional[datetime.datetime] = None

        # 나무증권 클라이언트 초기화 (MOCK or LIVE 일 때 필수, PAPER 일 때는 선택적)
        self._init_nh_client()

    def _init_nh_client(self):
        """나무증권 API 클라이언트 초기화 시도."""
        try:
            dry_run = (self.mode != "LIVE")
            self.nh_trader = NamuhAutoTrader(dry_run=dry_run)
            print(f"[OK] 나무증권 API 연동 성공 (모드: {self.mode})")
        except Exception as e:
            print(f"[WARN] 나무증권 API 연동 실패 (사유: {e})")
            if self.mode != "PAPER":
                print("[WARN] PAPER 모드가 아니면 실제 조회가 제한될 수 있습니다.")

    async def get_current_price(self, ticker: str) -> int:
        """현재가 조회 (나무증권 API 또는 시뮬레이션 폴백)."""
        if self.nh_trader:
            try:
                quote = await asyncio.to_thread(self.nh_trader.get_current_price, ticker)
                price_str = (quote or {}).get("stck_prpr")
                if price_str:
                    return int(price_str)
            except Exception as e:
                print(f"[WARN] [{ticker}] 시세 조회 에러: {e}")

        # 폴백 기본 시세
        fallback_prices = {"005930": 74500, "000660": 182000}
        return fallback_prices.get(ticker, 50000)

    async def get_account_summary(self) -> Dict[str, Any]:
        """현재 계좌 및 잔고 요약 반환."""
        if self.mode == "PAPER":
            # 가상 매매 현재가 반영
            current_prices = {}
            for t in self.paper_trader.positions.keys():
                current_prices[t] = await self.get_current_price(t)
            return self.paper_trader.get_balance(current_prices)
        else:
            if not self.nh_trader:
                raise RuntimeError("나무증권 클라이언트가 초기화되지 않았습니다.")
            return await asyncio.to_thread(self.nh_trader.get_balance, "1")

    async def execute_buy(self, ticker: str, qty: int, price: int) -> Dict[str, Any]:
        """매수 집행 및 DB 기록."""
        order_id = str(uuid.uuid4())[:8]
        order_type = "BUY"
        status = "REQUESTED"
        raw_res = ""

        if self.mode == "PAPER":
            res = self.paper_trader.order_buy(ticker, qty, price)
            status = "FILLED" if res.get("success") else "REJECTED"
            raw_res = res.get("rsp_msg", "")
            
            # DB 저장
            db.record_order(order_id, self.mode, ticker, order_type, "LIMIT", qty, price, status, raw_res)
            if status == "FILLED":
                exec_id = f"exec_{order_id}"
                fee = int(price * qty * 0.0001)
                db.record_execution(exec_id, order_id, self.mode, ticker, price, qty, fee=fee)
            return res
        else:
            # MOCK or LIVE
            if not self.nh_trader:
                raise RuntimeError("나무증권 클라이언트가 없습니다.")
            res = await asyncio.to_thread(self.nh_trader.order_buy, ticker, qty, price)
            raw_res = str(res)
            status = "FILLED" if "Output_0" in res else "REJECTED"
            db.record_order(order_id, self.mode, ticker, order_type, "LIMIT", qty, price, status, raw_res)
            return res

    async def execute_sell(self, ticker: str, qty: int, price: int) -> Dict[str, Any]:
        """매도 집행 및 DB 기록."""
        order_id = str(uuid.uuid4())[:8]
        order_type = "SELL"
        status = "REQUESTED"
        raw_res = ""

        if self.mode == "PAPER":
            res = self.paper_trader.order_sell(ticker, qty, price)
            status = "FILLED" if res.get("success") else "REJECTED"
            raw_res = res.get("rsp_msg", "")
            
            db.record_order(order_id, self.mode, ticker, order_type, "LIMIT", qty, price, status, raw_res)
            if status == "FILLED":
                exec_id = f"exec_{order_id}"
                fee = int(price * qty * 0.0001)
                tax = int(price * qty * 0.0018)
                db.record_execution(exec_id, order_id, self.mode, ticker, price, qty, fee=fee, tax=tax)
            return res
        else:
            if not self.nh_trader:
                raise RuntimeError("나무증권 클라이언트가 없습니다.")
            res = await asyncio.to_thread(self.nh_trader.order_sell, ticker, qty, price)
            raw_res = str(res)
            status = "FILLED" if "Output_0" in res else "REJECTED"
            db.record_order(order_id, self.mode, ticker, order_type, "LIMIT", qty, price, status, raw_res)
            return res

    async def kill_switch(self) -> Dict[str, Any]:
        """[비상 킬스위치] 모든 보유 포지션 전량 시장가 매도 및 봇 정지."""
        self.is_running = False
        liquidated = []

        if self.mode == "PAPER":
            positions = dict(self.paper_trader.positions)
            for ticker, pos in positions.items():
                qty = pos["qty"]
                price = await self.get_current_price(ticker)
                res = await self.execute_sell(ticker, qty, price)
                liquidated.append({"ticker": ticker, "qty": qty, "price": price, "res": res})
        else:
            # LIVE / MOCK 전량 청산
            summary = await self.get_account_summary()
            holdings = summary.get("holdings", [])
            for h in holdings:
                ticker = h.get("iem_cd")
                qty = int(h.get("hld_qty", 0))
                if ticker and qty > 0:
                    res = await asyncio.to_thread(self.nh_trader.order_sell, ticker, qty, None)
                    liquidated.append({"ticker": ticker, "qty": qty, "res": res})

        return {
            "status": "emergency_stopped",
            "liquidated_count": len(liquidated),
            "details": liquidated
        }

    async def run_single_cycle(self):
        """1회 전략 감시 및 매매 사이클 실행."""
        self.last_run_time = datetime.datetime.now()
        balance_info = await self.get_account_summary()
        summary = balance_info.get("summary", {})
        total_asset = int(summary.get("tot_asst_amt", settings.INITIAL_PAPER_CASH))
        current_cash = int(summary.get("dnca_tot_amt", settings.INITIAL_PAPER_CASH))
        
        # 1. 기존 보유 종목 스탑로스(-3%) 검사
        positions = {}
        if self.mode == "PAPER":
            positions = self.paper_trader.positions
        else:
            for item in balance_info.get("holdings", []):
                t = item.get("iem_cd")
                q = int(item.get("hld_qty", 0))
                p = int(item.get("pchs_avg_pric", 0))
                if t and q > 0:
                    positions[t] = {"qty": q, "avg_price": p}

        for ticker, pos in list(positions.items()):
            curr_price = await self.get_current_price(ticker)
            if self.risk_manager.check_stop_loss(pos["avg_price"], curr_price):
                print(f"[손절] [{ticker}] 손절선(-3%) 도달! 긴급 매도 실행")
                await self.execute_sell(ticker, pos["qty"], curr_price)

        # 2. 감시 종목 전략 평가 및 매수 탐색
        for ticker in self.monitored_tickers:
            curr_price = await self.get_current_price(ticker)
            market_data = {
                "current_price": curr_price,
                "open_price": int(curr_price * 0.99),
                "prev_high": int(curr_price * 1.02),
                "prev_low": int(curr_price * 0.98),
                "now": datetime.datetime.now()
            }

            pos = positions.get(ticker)
            signal = self.strategy.evaluate(ticker, market_data, pos)

            if signal == "BUY":
                can_buy, reason, qty = self.risk_manager.can_order_buy(
                    ticker, total_asset, current_cash, 0.0, curr_price
                )
                if can_buy:
                    print(f"[매수] [{ticker}] 변동성 돌파 시그널 발생! ({qty}주 @ {curr_price:,}원)")
                    await self.execute_buy(ticker, qty, curr_price)
                    current_cash -= curr_price * qty
                else:
                    print(f"[차단] [{ticker}] 매수 시그널 발생했으나 리스크 매니저가 차단함: {reason}")
            elif signal == "SELL" and pos and pos.get("qty", 0) > 0:
                print(f"[매도] [{ticker}] 장 마감 청산 시그널 발생!")
                await self.execute_sell(ticker, pos["qty"], curr_price)


# 싱글톤 봇 인스턴스
bot = TradingBot()

