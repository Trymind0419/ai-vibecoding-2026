"""데이터베이스 관리 모듈.

SQLite(data/trades.db)를 사용하여 주문, 체결, 일별 자산 스냅샷을 영구 보관합니다.
비동기 및 동기 환경 모두에서 안전하게 사용할 수 있도록 표준 sqlite3를 기반으로 구현되었습니다.
"""

import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.config import settings


class DatabaseManager:
    """SQLite 데이터베이스 관리자."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = str(db_path or settings.DB_PATH)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """테이블 스키마 초기화."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. 주문 테이블
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                trading_mode TEXT NOT NULL,      -- 'PAPER', 'MOCK', 'LIVE'
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ticker TEXT NOT NULL,
                order_type TEXT NOT NULL,        -- 'BUY', 'SELL'
                price_type TEXT NOT NULL,        -- 'LIMIT', 'MARKET'
                order_price INTEGER,
                order_qty INTEGER NOT NULL,
                status TEXT NOT NULL,            -- 'REQUESTED', 'FILLED', 'CANCELLED', 'REJECTED'
                raw_response TEXT
            );
            """)

            # 2. 체결 테이블
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                exec_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                trading_mode TEXT NOT NULL,      -- 'PAPER', 'MOCK', 'LIVE'
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ticker TEXT NOT NULL,
                exec_price INTEGER NOT NULL,
                exec_qty INTEGER NOT NULL,
                fee INTEGER DEFAULT 0,
                tax INTEGER DEFAULT 0,
                FOREIGN KEY(order_id) REFERENCES orders(order_id)
            );
            """)

            # 3. 일별 스냅샷 테이블
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_snapshots (
                date TEXT NOT NULL,              -- YYYY-MM-DD
                trading_mode TEXT NOT NULL,      -- 'PAPER', 'MOCK', 'LIVE'
                total_asset INTEGER NOT NULL,
                deposit INTEGER NOT NULL,
                realized_pnl INTEGER NOT NULL,
                return_rate REAL NOT NULL,
                PRIMARY KEY(date, trading_mode)
            );
            """)

            conn.commit()

    def record_order(self, order_id: str, trading_mode: str, ticker: str,
                     order_type: str, price_type: str, order_qty: int,
                     order_price: Optional[int] = None, status: str = "REQUESTED",
                     raw_response: str = "") -> None:
        """주문 내역 저장."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO orders 
            (order_id, trading_mode, ticker, order_type, price_type, order_price, order_qty, status, raw_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_id, trading_mode, ticker, order_type, price_type, order_price, order_qty, status, raw_response))
            conn.commit()

    def record_execution(self, exec_id: str, order_id: str, trading_mode: str,
                         ticker: str, exec_price: int, exec_qty: int,
                         fee: int = 0, tax: int = 0) -> None:
        """체결 내역 저장."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO executions 
            (exec_id, order_id, trading_mode, ticker, exec_price, exec_qty, fee, tax)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (exec_id, order_id, trading_mode, ticker, exec_price, exec_qty, fee, tax))
            conn.commit()

    def record_daily_snapshot(self, date_str: str, trading_mode: str,
                              total_asset: int, deposit: int,
                              realized_pnl: int, return_rate: float) -> None:
        """일별 자산 스냅샷 저장."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO daily_snapshots 
            (date, trading_mode, total_asset, deposit, realized_pnl, return_rate)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (date_str, trading_mode, total_asset, deposit, realized_pnl, return_rate))
            conn.commit()

    def get_recent_orders(self, limit: int = 50, trading_mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """최근 주문 내역 조회."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if trading_mode:
                cursor.execute("""
                SELECT * FROM orders WHERE trading_mode = ? ORDER BY timestamp DESC LIMIT ?
                """, (trading_mode, limit))
            else:
                cursor.execute("""
                SELECT * FROM orders ORDER BY timestamp DESC LIMIT ?
                """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_recent_executions(self, limit: int = 50, trading_mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """최근 체결 내역 조회."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if trading_mode:
                cursor.execute("""
                SELECT * FROM executions WHERE trading_mode = ? ORDER BY timestamp DESC LIMIT ?
                """, (trading_mode, limit))
            else:
                cursor.execute("""
                SELECT * FROM executions ORDER BY timestamp DESC LIMIT ?
                """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


db = DatabaseManager()

