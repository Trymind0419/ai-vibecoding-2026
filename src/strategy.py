"""매매 전략 엔진 모듈.

기본 전략으로 '래리 윌리엄스 변동성 돌파 전략(Volatility Breakout)'을 탑재하고 있습니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import datetime


class BaseStrategy(ABC):
    """전략 기본 추상 클래스."""

    @abstractmethod
    def evaluate(self, ticker: str, market_data: Dict[str, Any], current_position: Optional[Dict[str, Any]] = None) -> str:
        """시장 데이터를 분석하여 'BUY', 'SELL', 'HOLD' 시그널을 반환."""
        pass


class VolatilityBreakoutStrategy(BaseStrategy):
    """변동성 돌파 전략 (Volatility Breakout).

    - 매수 조건: 현재가 > 당일 시가 + (전일 고가 - 전일 저가) * k
    - 매도(청산) 조건: 장 마감 직전(15:15 ~ 15:20) 또는 손절/익절 조건 도달 시
    """

    def __init__(self, k: float = 0.5):
        self.k = k

    def calculate_target_price(self, open_price: int, prev_high: int, prev_low: int) -> int:
        """매수 목표가 계산."""
        volatility = prev_high - prev_low
        if volatility <= 0:
            return int(open_price * 1.02)  # 전일 변동폭이 없을 때 2% 상승선
        return int(open_price + (volatility * self.k))

    def evaluate(self, ticker: str, market_data: Dict[str, Any], current_position: Optional[Dict[str, Any]] = None) -> str:
        """시그널 판정.

        market_data 요구 필드:
            - current_price (현재가)
            - open_price (시가)
            - prev_high (전일 고가)
            - prev_low (전일 저가)
            - now (datetime.datetime, 선택)
        """
        now = market_data.get("now", datetime.datetime.now())
        current_price = market_data.get("current_price", 0)

        # 1. 장 마감 청산 조건 (15:15 이후 포지션 보유 중이면 당일 청산)
        if now.hour == 15 and now.minute >= 15:
            if current_position and current_position.get("qty", 0) > 0:
                return "SELL"
            return "HOLD"

        # 2. 이미 해당 종목을 보유 중이면 신규 매수 금지 (HOLD)
        if current_position and current_position.get("qty", 0) > 0:
            return "HOLD"

        # 3. 변동성 돌파 매수 판정 (09:00 ~ 15:10)
        open_price = market_data.get("open_price", 0)
        prev_high = market_data.get("prev_high", 0)
        prev_low = market_data.get("prev_low", 0)

        if current_price > 0 and open_price > 0 and prev_high > prev_low:
            target_price = self.calculate_target_price(open_price, prev_high, prev_low)
            if current_price >= target_price:
                return "BUY"

        return "HOLD"

