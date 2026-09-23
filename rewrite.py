import os

files = {
    'auto_trader/config.py': '''# -*- coding: utf-8 -*-
"""설정 관리 모듈"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    NH_API_KEY: str = "demo_key"
    NH_API_SECRET: str = "demo_secret"
    NH_ACCOUNT: str = "demo_account"
    MODE: str = "PAPER" # PAPER or LIVE

    class Config:
        env_file = ".env"

settings = Settings()
''',
    'auto_trader/database.py': '''# -*- coding: utf-8 -*-
"""데이터베이스 모듈"""
import sqlite3
import os

class Database:
    def __init__(self, db_path="data/trades.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    price REAL,
                    quantity INTEGER,
                    side TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def log_trade(self, symbol, price, quantity, side):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('INSERT INTO trades (symbol, price, quantity, side) VALUES (?, ?, ?, ?)',
                         (symbol, price, quantity, side))

db = Database()
''',
    'auto_trader/strategy.py': '''# -*- coding: utf-8 -*-
"""전략 모듈"""
class VolatilityBreakoutStrategy:
    def __init__(self, k=0.5):
        self.k = k

    def get_target_price(self, current_price, high_price, low_price):
        range_diff = high_price - low_price
        target = current_price + (range_diff * self.k)
        return target

    def should_buy(self, current_price, target_price):
        return current_price >= target_price
''',
    'auto_trader/risk_manager.py': '''# -*- coding: utf-8 -*-
"""리스크 관리 모듈"""
class RiskManager:
    def __init__(self, max_loss_pct=0.02):
        self.max_loss_pct = max_loss_pct

    def calculate_position_size(self, capital, current_price):
        # 자산의 일정 비율만 투자
        return capital // current_price
''',
    'auto_trader/nh_trader.py': '''# -*- coding: utf-8 -*-
"""나무증권 API 연동 모듈"""
class NHTrader:
    def __init__(self, api_key, api_secret, account):
        self.api_key = api_key
        self.api_secret = api_secret
        self.account = account

    def get_balance(self):
        return 1000000 # Dummy

    def order_buy(self, symbol, price, qty):
        return True

    def order_sell(self, symbol, price, qty):
        return True
''',
    'auto_trader/paper_trader.py': '''# -*- coding: utf-8 -*-
"""모의투자(Paper Trading) 시뮬레이터"""
class PaperTrader:
    def __init__(self, initial_capital=10000000):
        self.capital = initial_capital
        self.positions = {}

    def get_balance(self):
        return self.capital

    def order_buy(self, symbol, price, qty):
        cost = price * qty
        if self.capital >= cost:
            self.capital -= cost
            self.positions[symbol] = self.positions.get(symbol, 0) + qty
            return True
        return False

    def order_sell(self, symbol, price, qty):
        if self.positions.get(symbol, 0) >= qty:
            self.capital += price * qty
            self.positions[symbol] -= qty
            return True
        return False
''',
    'auto_trader/bot.py': '''# -*- coding: utf-8 -*-
"""자동매매 봇 실행 엔진"""
import asyncio
from auto_trader.config import settings
from auto_trader.database import db
from auto_trader.paper_trader import PaperTrader
from auto_trader.strategy import VolatilityBreakoutStrategy
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

class TradingBot:
    def __init__(self):
        self.is_running = False
        self.strategy = VolatilityBreakoutStrategy()
        if settings.MODE == "PAPER":
            self.trader = PaperTrader()
        else:
            self.trader = PaperTrader() # fallback for now

    async def run_loop(self):
        self.is_running = True
        print("🚀 Trading Bot Started!")
        while self.is_running:
            await asyncio.sleep(5)
            print("⏳ Monitoring market...")

    def stop(self):
        self.is_running = False
        print("🛑 Trading Bot Stopped.")

bot = TradingBot()
''',
    'auto_trader/main.py': '''# -*- coding: utf-8 -*-
"""나무증권(NHPLUG) + FastAPI 주식 자동매매 봇"""
import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi import FastAPI
import asyncio
from auto_trader.bot import bot

app = FastAPI(title="Auto Trader API", version="0.1.0")
bot_task = None

@app.on_event("startup")
async def startup_event():
    global bot_task
    bot_task = asyncio.create_task(bot.run_loop())

@app.on_event("shutdown")
async def shutdown_event():
    bot.stop()
    if bot_task:
        bot_task.cancel()

@app.get("/")
def root():
    return {"status": "running", "mode": bot.trader.__class__.__name__}
''',
    'tests/test_v01.py': '''# -*- coding: utf-8 -*-
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
'''
}

for filepath, content in files.items():
    if os.path.exists(filepath):
        os.remove(filepath)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
print("Rewrite complete.")

