"""리스크 관리 모듈.

계좌 자산 보호를 위한 안전 규칙(손실 한도, 비중 제한, 손절선)을 강제합니다.
"""

from typing import Dict, Any, Tuple
from src.config import settings


class RiskManager:
    """리스크 관리자."""

    def __init__(self,
                 max_stock_weight: float = settings.MAX_STOCK_WEIGHT,
                 daily_loss_limit: float = settings.DAILY_LOSS_LIMIT,
                 stop_loss_rate: float = settings.STOP_LOSS_RATE):
        self.max_stock_weight = max_stock_weight  # 예: 0.20 (20%)
        self.daily_loss_limit = daily_loss_limit  # 예: -0.02 (-2%)
        self.stop_loss_rate = stop_loss_rate      # 예: -0.03 (-3%)

    def check_stop_loss(self, avg_price: int, current_price: int) -> bool:
        """개별 종목 손절선(-3%) 도달 여부 확인."""
        if avg_price <= 0:
            return False
        return_rate = (current_price - avg_price) / avg_price
        return return_rate <= self.stop_loss_rate

    def can_order_buy(self, ticker: str, total_asset: int, current_cash: int,
                      daily_pnl_rate: float, order_price: int) -> Tuple[bool, str, int]:
        """매수 주문 발주 전 리스크 검증 및 최대 매수 가능 수량 계산.

        반환: (허용여부: bool, 사유: str, 추천수량: int)
        """
        # 1. 일일 누적 손실 한도 체크
        if daily_pnl_rate <= self.daily_loss_limit:
            return False, f"일일 누적 손실한도 초과 (현재: {daily_pnl_rate*100:.2f}% / 한도: {self.daily_loss_limit*100:.2f}%)", 0

        # 2. 예수금 존재 여부
        if current_cash <= 0 or order_price <= 0:
            return False, "예수금 또는 주문 단가 부족", 0

        # 3. 1종목 최대 투자 한도 (총 자산의 20%)
        max_position_budget = total_asset * self.max_stock_weight
        available_budget = min(current_cash, max_position_budget)

        # 4. 수량 계산 (수수료 여유분 0.1% 반영)
        usable_cash = available_budget * 0.999
        max_qty = int(usable_cash // order_price)

        if max_qty <= 0:
            return False, f"투자 한도 대비 단가 초과 (단가: {order_price:,}원 / 배정예산: {available_budget:,.0f}원)", 0

        return True, "매수 승인", max_qty

