# -*- coding: utf-8 -*-
"""테스트 코드"""
import unittest
import asyncio
from auto_trader.config import settings
from auto_trader.database import db
from auto_trader.strategy import VolatilityBreakoutStrategy
from auto_trader.risk_manager import RiskManager
from auto_trader.paper_trader import PaperTrader
from auto_trader.bot import bot

class TestV01(unittest.TestCase):
    def test_strategy(self):
        st = VolatilityBreakoutStrategy(k=0.5)
        target = st.get_target_price(100, 150, 90)
        self.assertEqual(target, 130)

    def test_paper_trader(self):
        pt = PaperTrader(1000000)
        self.assertTrue(pt.order_buy("005930", 50000, 10))
        self.assertEqual(pt.get_balance(), 500000)
