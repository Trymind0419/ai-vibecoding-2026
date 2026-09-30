# -*- coding: utf-8 -*-
"""
SQLite 기반 자동매매 영구 데이터베이스 엔진 (data/auto_trader.db)
DBeaver 등 DB 관리 도구에서 직접 조회 및 관리가 가능하며,
서버 재부팅 시에도 잔고, 포지션, 거래일지, 봇 로그를 완벽 복원합니다.
"""
import sqlite3
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "auto_trader.db"

class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def init_db(self):
        """테이블 및 DBeaver 분석용 뷰(Views) 생성"""
        with self._get_conn() as conn:
            # 1. 가상계좌 상태 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS account_state (
                    id INTEGER PRIMARY KEY,
                    paper_capital INTEGER NOT NULL,
                    initial_capital INTEGER NOT NULL DEFAULT 10000000,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. 보유 포지션 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    symbol TEXT PRIMARY KEY,
                    name TEXT,
                    qty INTEGER NOT NULL,
                    buy_price REAL NOT NULL,
                    current_price REAL NOT NULL,
                    highest_price REAL NOT NULL,
                    buy_time TEXT,
                    buy_reason TEXT DEFAULT '',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 3. 실현손익 청산 거래일지 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS closed_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    name TEXT,
                    buy_time TEXT,
                    sell_time TEXT,
                    buy_price REAL,
                    sell_price REAL,
                    qty INTEGER,
                    invested_amt INTEGER,
                    revenue_amt INTEGER,
                    realized_pnl INTEGER,
                    pnl_pct REAL,
                    exit_reason TEXT,
                    buy_reason TEXT DEFAULT '',
                    sell_reason TEXT DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 4. 주문 이력 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_no TEXT,
                    time TEXT,
                    type TEXT,
                    mode TEXT,
                    symbol TEXT,
                    name TEXT,
                    price REAL,
                    qty INTEGER,
                    status TEXT,
                    msg TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 5. 봇 활동 로그 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time TEXT,
                    type TEXT,
                    message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 6. DBeaver 전용 유용한 분석 뷰(Views) 생성
            conn.execute("""
                CREATE VIEW IF NOT EXISTS v_account_summary AS
                SELECT 
                    a.paper_capital AS cash_balance,
                    COALESCE(SUM(p.qty * p.current_price), 0) AS positions_eval_amt,
                    a.paper_capital + COALESCE(SUM(p.qty * p.current_price), 0) AS total_eval_assets,
                    (a.paper_capital + COALESCE(SUM(p.qty * p.current_price), 0)) - a.initial_capital AS total_profit_loss,
                    ROUND(((a.paper_capital + COALESCE(SUM(p.qty * p.current_price), 0) - a.initial_capital) * 100.0 / a.initial_capital), 2) AS total_return_pct,
                    a.updated_at
                FROM account_state a
                LEFT JOIN positions p ON 1=1
                GROUP BY a.id;
            """)

            conn.execute("""
                CREATE VIEW IF NOT EXISTS v_open_positions AS
                SELECT 
                    symbol,
                    name,
                    qty,
                    CAST(buy_price AS INTEGER) AS buy_price,
                    CAST(current_price AS INTEGER) AS current_price,
                    CAST(highest_price AS INTEGER) AS highest_price,
                    CAST(qty * buy_price AS INTEGER) AS buy_amount,
                    CAST(qty * current_price AS INTEGER) AS eval_amount,
                    CAST(qty * (current_price - buy_price) AS INTEGER) AS unrealized_pnl,
                    ROUND(((current_price - buy_price) * 100.0 / buy_price), 2) AS profit_rate_pct,
                    buy_time,
                    updated_at
                FROM positions;
            """)

            conn.execute("""
                CREATE VIEW IF NOT EXISTS v_closed_trades_journal AS
                SELECT 
                    id,
                    symbol,
                    name,
                    qty,
                    CAST(buy_price AS INTEGER) AS buy_price,
                    CAST(sell_price AS INTEGER) AS sell_price,
                    invested_amt,
                    revenue_amt,
                    realized_pnl,
                    pnl_pct,
                    CASE 
                        WHEN realized_pnl > 0 THEN 'WIN (익절)'
                        WHEN realized_pnl < 0 THEN 'LOSS (손절)'
                        ELSE 'EVEN (본전)'
                    END AS result,
                    exit_reason,
                    buy_time,
                    sell_time,
                    created_at
                FROM closed_trades
                ORDER BY id DESC;
            """)

            conn.execute("""
                CREATE VIEW IF NOT EXISTS v_trade_performance AS
                SELECT 
                    COUNT(*) AS total_trades,
                    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) AS win_trades,
                    SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) AS loss_trades,
                    ROUND(SUM(CASE WHEN realized_pnl > 0 THEN 1.0 ELSE 0.0 END) * 100.0 / MAX(COUNT(*), 1), 1) AS win_rate_pct,
                    SUM(realized_pnl) AS total_realized_pnl,
                    SUM(invested_amt) AS total_invested_amt,
                    ROUND(AVG(pnl_pct), 2) AS avg_return_pct
                FROM closed_trades;
            """)

            conn.execute("""
                CREATE VIEW IF NOT EXISTS v_daily_pnl_summary AS
                SELECT 
                    SUBSTR(sell_time, 1, 10) AS trade_date,
                    COUNT(*) AS trade_count,
                    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) AS win_count,
                    SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) AS loss_count,
                    SUM(realized_pnl) AS daily_realized_pnl,
                    ROUND(AVG(pnl_pct), 2) AS daily_avg_return_pct
                FROM closed_trades
                GROUP BY SUBSTR(sell_time, 1, 10)
                ORDER BY trade_date DESC;
            """)

            conn.commit()

    # ==========================================================
    # 1. 계좌 잔고 (Account State)
    # ==========================================================
    def get_paper_capital(self, default: int = 10000000) -> int:
        """가상계좌 잔고 조회 (없으면 기본값으로 초기화)"""
        try:
            with self._get_conn() as conn:
                row = conn.execute("SELECT paper_capital FROM account_state WHERE id = 1;").fetchone()
                if row:
                    return int(row["paper_capital"])
                conn.execute(
                    "INSERT INTO account_state (id, paper_capital, initial_capital, updated_at) VALUES (1, ?, ?, CURRENT_TIMESTAMP);",
                    (default, default)
                )
                conn.commit()
                return default
        except Exception as e:
            print(f"[DB] get_paper_capital 오류: {e}")
            return default

    def save_paper_capital(self, capital: int):
        """가상계좌 잔고 저장"""
        try:
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT INTO account_state (id, paper_capital, initial_capital, updated_at)
                    VALUES (1, ?, 10000000, CURRENT_TIMESTAMP)
                    ON CONFLICT(id) DO UPDATE SET paper_capital = excluded.paper_capital, updated_at = CURRENT_TIMESTAMP;
                """, (int(capital),))
                conn.commit()
        except Exception as e:
            print(f"[DB] save_paper_capital 오류: {e}")

    def reset_paper_account(self, initial_capital: int = 10000000):
        """가상계좌 원금 복원 및 포지션 전체 삭제"""
        try:
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT INTO account_state (id, paper_capital, initial_capital, updated_at)
                    VALUES (1, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(id) DO UPDATE SET paper_capital = ?, initial_capital = ?, updated_at = CURRENT_TIMESTAMP;
                """, (initial_capital, initial_capital, initial_capital, initial_capital))
                conn.execute("DELETE FROM positions;")
                conn.commit()
        except Exception as e:
            print(f"[DB] reset_paper_account 오류: {e}")

    # ==========================================================
    # 2. 보유 포지션 (Positions)
    # ==========================================================
    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """보유 포지션 딕셔너리 반환"""
        positions = {}
        try:
            with self._get_conn() as conn:
                rows = conn.execute("SELECT * FROM positions;").fetchall()
                for r in rows:
                    positions[r["symbol"]] = {
                        "name": r["name"] or r["symbol"],
                        "qty": int(r["qty"]),
                        "buy_price": float(r["buy_price"]),
                        "current_price": float(r["current_price"]),
                        "highest_price": float(r["highest_price"]),
                        "buy_time": r["buy_time"] or "",
                        "buy_reason": r["buy_reason"] if "buy_reason" in r.keys() else ""
                    }
        except Exception as e:
            print(f"[DB] get_positions 오류: {e}")
        return positions

    def save_position(self, symbol: str, name: str, qty: int, buy_price: float,
                      current_price: float, highest_price: Optional[float] = None,
                      buy_time: Optional[str] = None, buy_reason: str = ""):
        """포지션 등록 또는 업데이트"""
        high = highest_price if highest_price is not None else current_price
        b_time = buy_time or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT INTO positions (symbol, name, qty, buy_price, current_price, highest_price, buy_time, buy_reason, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(symbol) DO UPDATE SET
                        name = excluded.name,
                        qty = excluded.qty,
                        buy_price = excluded.buy_price,
                        current_price = excluded.current_price,
                        highest_price = MAX(positions.highest_price, excluded.highest_price),
                        buy_reason = CASE WHEN excluded.buy_reason != '' THEN excluded.buy_reason ELSE positions.buy_reason END,
                        updated_at = CURRENT_TIMESTAMP;
                """, (symbol, name, qty, buy_price, current_price, high, b_time, buy_reason))
                conn.commit()
        except Exception as e:
            print(f"[DB] save_position 오류: {e}")

    def update_position_price(self, symbol: str, current_price: float, highest_price: Optional[float] = None):
        """실시간 현재가 및 고점(Highest Price) 갱신"""
        try:
            with self._get_conn() as conn:
                if highest_price is not None:
                    conn.execute("""
                        UPDATE positions SET 
                            current_price = ?, 
                            highest_price = MAX(highest_price, ?),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE symbol = ?;
                    """, (current_price, highest_price, symbol))
                else:
                    conn.execute("""
                        UPDATE positions SET 
                            current_price = ?, 
                            highest_price = MAX(highest_price, ?),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE symbol = ?;
                    """, (current_price, current_price, symbol))
                conn.commit()
        except Exception as e:
            print(f"[DB] update_position_price 오류: {e}")

    def delete_position(self, symbol: str):
        """포지션 삭제 (청산 완료 시)"""
        try:
            with self._get_conn() as conn:
                conn.execute("DELETE FROM positions WHERE symbol = ?;", (symbol,))
                conn.commit()
        except Exception as e:
            print(f"[DB] delete_position 오류: {e}")

    # ==========================================================
    # 3. 주문 이력 (Orders)
    # ==========================================================
    def record_order(self, order: Dict[str, Any]):
        """매수/매도 주문 이력 기록"""
        try:
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT INTO orders (order_no, time, type, mode, symbol, name, price, qty, status, msg)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    str(order.get("order_no", "")),
                    str(order.get("time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
                    str(order.get("type", "BUY")),
                    str(order.get("mode", "PAPER")),
                    str(order.get("symbol", "")),
                    str(order.get("name", "")),
                    float(order.get("price", 0.0)),
                    int(order.get("qty", 0)),
                    str(order.get("status", "FILLED")),
                    str(order.get("msg", ""))
                ))
                conn.commit()
        except Exception as e:
            print(f"[DB] record_order 오류: {e}")

    def get_recent_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """최근 체결 주문 목록 조회"""
        try:
            with self._get_conn() as conn:
                rows = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?;", (limit,)).fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            print(f"[DB] get_recent_orders 오류: {e}")
            return []

    # ==========================================================
    # 4. 실현손익 청산 거래일지 (Closed Trades)
    # ==========================================================
    def record_closed_trade(self, symbol: str, name: str, buy_time: str, sell_time: str,
                            buy_price: float, sell_price: float, qty: int, exit_reason: str,
                            buy_reason: str = "", sell_reason: str = ""):
        """매도 청산 시 실현손익 및 거래일지 기록"""
        invested = int(buy_price * qty)
        revenue = int(sell_price * qty)
        realized_pnl = revenue - invested
        pnl_pct = round(((sell_price - buy_price) / buy_price * 100), 2) if buy_price > 0 else 0.0
        final_sell_reason = sell_reason or exit_reason

        try:
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT INTO closed_trades 
                    (symbol, name, buy_time, sell_time, buy_price, sell_price, qty, invested_amt, revenue_amt, realized_pnl, pnl_pct, exit_reason, buy_reason, sell_reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (symbol, name, buy_time, sell_time, buy_price, sell_price, qty, invested, revenue, realized_pnl, pnl_pct, exit_reason, buy_reason, final_sell_reason))
                conn.commit()
        except Exception as e:
            print(f"[DB] record_closed_trade 오류: {e}")

    def get_closed_trades(self, limit: int = 50) -> List[Dict[str, Any]]:
        """청산 완료된 거래일지 내역 조회"""
        try:
            with self._get_conn() as conn:
                rows = conn.execute("SELECT * FROM closed_trades ORDER BY id DESC LIMIT ?;", (limit,)).fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            print(f"[DB] get_closed_trades 오류: {e}")
            return []

    def get_trade_summary(self) -> Dict[str, Any]:
        """누적 거래 통계 (총 실현손익, 승률, 총 거래횟수 등) 집계"""
        summary = {
            "total_trades": 0,
            "win_trades": 0,
            "loss_trades": 0,
            "win_rate": 0.0,
            "total_realized_pnl": 0,
            "total_invested": 0,
            "avg_pnl_pct": 0.0
        }
        try:
            with self._get_conn() as conn:
                row = conn.execute("""
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as win_trades,
                        SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) as loss_trades,
                        SUM(realized_pnl) as total_pnl,
                        SUM(invested_amt) as total_invested,
                        AVG(pnl_pct) as avg_pnl_pct
                    FROM closed_trades;
                """).fetchone()

                if row and row["total_trades"]:
                    total = row["total_trades"]
                    wins = row["win_trades"] or 0
                    losses = row["loss_trades"] or 0
                    summary = {
                        "total_trades": total,
                        "win_trades": wins,
                        "loss_trades": losses,
                        "win_rate": round((wins / total) * 100, 1),
                        "total_realized_pnl": int(row["total_pnl"] or 0),
                        "total_invested": int(row["total_invested"] or 0),
                        "avg_pnl_pct": round(float(row["avg_pnl_pct"] or 0.0), 2)
                    }
        except Exception as e:
            print(f"[DB] get_trade_summary 오류: {e}")
        return summary

    # ==========================================================
    # 5. 자동매매 봇 로그 (Bot Logs)
    # ==========================================================
    def add_bot_log(self, log_type: str, message: str, time_str: Optional[str] = None):
        """자동매매 봇 로그 DB 기록"""
        t = time_str or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO bot_logs (time, type, message) VALUES (?, ?, ?);",
                    (t, log_type, message)
                )
                conn.commit()
        except Exception as e:
            print(f"[DB] add_bot_log 오류: {e}")

    def get_recent_bot_logs(self, limit: int = 80) -> List[Dict[str, str]]:
        """최근 봇 로그 조회"""
        try:
            with self._get_conn() as conn:
                rows = conn.execute(
                    "SELECT time, type, message FROM bot_logs ORDER BY id DESC LIMIT ?;",
                    (limit,)
                ).fetchall()
                logs = [{"time": r["time"], "type": r["type"], "message": r["message"]} for r in reversed(rows)]
                return logs
        except Exception as e:
            print(f"[DB] get_recent_bot_logs 오류: {e}")
            return []

db = Database()
