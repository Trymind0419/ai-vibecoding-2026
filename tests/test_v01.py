"""자동매매 시스템 v0.1 기능 검증 단위 테스트."""

import unittest
import asyncio
from src.config import settings
from src.database import db
from src.strategy import VolatilityBreakoutStrategy
from src.risk_manager import RiskManager
from src.paper_trader import PaperTrader
from src.bot import bot


class TestAutoTraderV01(unittest.TestCase):

    def setUp(self):
        self.paper = PaperTrader(initial_cash=10_000_000)
        self.risk = RiskManager()
        self.strategy = VolatilityBreakoutStrategy(k=0.5)

    def test_database_init(self):
        """DB 초기화 및 주문/체결 저장 테스트."""
        order_id = "test_ord_1"
        db.record_order(order_id, "PAPER", "005930", "BUY", "LIMIT", 10, 70000, "FILLED")
        db.record_execution("test_exec_1", order_id, "PAPER", "005930", 70000, 10, fee=70)

        orders = db.get_recent_orders(10, "PAPER")
        self.assertTrue(any(o["order_id"] == order_id for o in orders))

        execs = db.get_recent_executions(10, "PAPER")
        self.assertTrue(any(e["order_id"] == order_id for e in execs))

    def test_paper_trading_flow(self):
        """가상 매매 매수 -> 잔고 확인 -> 매도 흐름 검증."""
        # 1. 10주 매수 @ 70,000원 (총 700,000원 + 수수료 70원)
        res_buy = self.paper.order_buy("005930", 10, 70000)
        self.assertTrue(res_buy["success"])
        self.assertEqual(self.paper.positions["005930"]["qty"], 10)
        self.assertEqual(self.paper.cash, 10_000_000 - 700_070)

        # 2. 75,000원에 10주 매도 (+5,000원 익절)
        res_sell = self.paper.order_sell("005930", 10, 75000)
        self.assertTrue(res_sell["success"])
        self.assertNotIn("005930", self.paper.positions)
        self.assertGreater(self.paper.cash, 10_000_000)

    def test_risk_manager(self):
        """리스크 관리자 비중 및 손실 한도 검증."""
        # 총 자산 1,000만 원일 때 20% 한도는 200만 원.
        # 단가 300,000원짜리면 최대 6주 매수 가능.
        can_buy, reason, qty = self.risk.can_order_buy("000660", 10_000_000, 10_000_000, 0.0, 300000)
        self.assertTrue(can_buy)
        self.assertEqual(qty, 6)

        # 일일 누적 손실 -2% 초과 시 매수 차단
        can_buy_blocked, reason_blocked, _ = self.risk.can_order_buy("000660", 10_000_000, 10_000_000, -0.025, 300000)
        self.assertFalse(can_buy_blocked)
        self.assertIn("손실한도 초과", reason_blocked)

        # -3% 손절 판정
        is_stop = self.risk.check_stop_loss(100000, 96000)  # -4%
        self.assertTrue(is_stop)

    def test_strategy_signal(self):
        """변동성 돌파 전략 시그널 연산 검증."""
        # 시가 70,000, 전일고가 72,000, 전일저가 68,000 -> 변동폭 4,000, k=0.5 -> 목표가 72,000
        target = self.strategy.calculate_target_price(70000, 72000, 68000)
        self.assertEqual(target, 72000)

        # 현재가 72,500 (돌파) -> BUY 시그널
        signal = self.strategy.evaluate("005930", {
            "current_price": 72500,
            "open_price": 70000,
            "prev_high": 72000,
            "prev_low": 68000
        })
        self.assertEqual(signal, "BUY")


if __name__ == "__main__":
    unittest.main()

