# -*- coding: utf-8 -*-
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
