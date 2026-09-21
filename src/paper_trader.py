"""가상 매매(Paper Trading) 시뮬레이션 엔진.

- 실계좌 원금 투입 전 전략 검증 및 무위험 시뮬레이션용.
- 가상 시드머니(기본 1,000만 원), 증권사 수수료(0.01%) 및 슬리피지 반영.
"""

from typing import Dict, Any, List, Optional
import datetime


class PaperTrader:
    """가상 계좌 및 가상 체결 엔진."""

    def __init__(self, initial_cash: int = 10_000_000, fee_rate: float = 0.0001):
        self.initial_cash = initial_cash
        self.cash = initial_cash                  # 가상 예수금
        self.fee_rate = fee_rate                  # 증권사 수수료 0.01%
        self.positions: Dict[str, Dict[str, Any]] = {}  # 보유 종목 {ticker: {qty, avg_price}}
        self.order_history: List[Dict[str, Any]] = []

    def reset(self, initial_cash: Optional[int] = None):
        """가상 계좌 초기화."""
        if initial_cash:
            self.initial_cash = initial_cash
        self.cash = self.initial_cash
        self.positions.clear()
        self.order_history.clear()

    def get_balance(self, current_prices: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """가상 잔고 및 총 자산 평가액 반환."""
        current_prices = current_prices or {}
        total_eval_stock = 0
        holdings = []

        for ticker, pos in self.positions.items():
            qty = pos["qty"]
            avg_price = pos["avg_price"]
            curr_price = current_prices.get(ticker, avg_price)
            eval_amount = qty * curr_price
            pnl = (curr_price - avg_price) * qty
            return_rate = ((curr_price / avg_price) - 1) * 100 if avg_price > 0 else 0.0

            total_eval_stock += eval_amount
            holdings.append({
                "iem_cd": ticker,
                "hld_qty": str(qty),
                "pchs_avg_pric": str(avg_price),
                "evlu_amt": str(eval_amount),
                "evlu_pfls_amt": str(pnl),
                "evlu_pfls_rt": f"{return_rate:.2f}"
            })

        total_asset = self.cash + total_eval_stock
        total_pnl = total_asset - self.initial_cash
        total_return_rate = (total_pnl / self.initial_cash) * 100

        return {
            "summary": {
                "tot_asst_amt": str(total_asset),
                "dnca_tot_amt": str(self.cash),
                "tot_evlu_amt": str(total_eval_stock),
                "tot_evlu_pfls_amt": str(total_pnl),
                "tot_pnl_rate": f"{total_return_rate:.2f}%",
                "trading_mode": "PAPER"
            },
            "holdings": holdings,
            "rsp_msg": "정상 처리 되었습니다. [가상 매매 모드]"
        }

    def order_buy(self, ticker: str, qty: int, price: int) -> Dict[str, Any]:
        """가상 현금 매수 처리."""
        total_cost = price * qty
        fee = int(total_cost * self.fee_rate)
        required = total_cost + fee

        if self.cash < required:
            return {
                "success": False,
                "rsp_msg": f"예수금 부족 (필요: {required:,}원 / 보유: {self.cash:,}원)"
            }

        self.cash -= required
        if ticker in self.positions:
            old_qty = self.positions[ticker]["qty"]
            old_avg = self.positions[ticker]["avg_price"]
            new_qty = old_qty + qty
            new_avg = int(((old_qty * old_avg) + total_cost) / new_qty)
            self.positions[ticker] = {"qty": new_qty, "avg_price": new_avg}
        else:
            self.positions[ticker] = {"qty": qty, "avg_price": price}

        order_record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "BUY",
            "ticker": ticker,
            "qty": qty,
            "price": price,
            "fee": fee
        }
        self.order_history.append(order_record)
        return {
            "success": True,
            "rsp_msg": f"[가상 체결] {ticker} {qty}주 매수 완료 @ {price:,}원",
            "order": order_record
        }

    def order_sell(self, ticker: str, qty: int, price: int) -> Dict[str, Any]:
        """가상 현금 매도 처리."""
        if ticker not in self.positions or self.positions[ticker]["qty"] < qty:
            held = self.positions.get(ticker, {}).get("qty", 0)
            return {
                "success": False,
                "rsp_msg": f"보유 수량 부족 (매도요청: {qty}주 / 보유: {held}주)"
            }

        total_gain = price * qty
        fee = int(total_gain * self.fee_rate)
        tax = int(total_gain * 0.0018)  # 증권거래세 0.18%
        net_receive = total_gain - fee - tax

        self.cash += net_receive
        self.positions[ticker]["qty"] -= qty
        if self.positions[ticker]["qty"] == 0:
            del self.positions[ticker]

        order_record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "SELL",
            "ticker": ticker,
            "qty": qty,
            "price": price,
            "fee": fee,
            "tax": tax
        }
        self.order_history.append(order_record)
        return {
            "success": True,
            "rsp_msg": f"[가상 체결] {ticker} {qty}주 매도 완료 @ {price:,}원",
            "order": order_record
        }

