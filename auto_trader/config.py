# -*- coding: utf-8 -*-
"""설정 관리 모듈"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # 1. 나무증권(NHPLUG) API 설정
    TRADING_MODE: str = "PAPER"               # PAPER(가상시뮬레이션), MOCK(모의투자서버), LIVE(실거래서버)
    CONFIRM_REAL_TRADING: str = "false"       # LIVE 모드 실전 주문 발주 2차 안전 잠금 (true 설정 시 실제 자산 주문 발주)
    NHPLUG_APP_KEY: str = ""
    NHPLUG_APP_SECRET: str = ""
    NHPLUG_BASE_URL: str = "https://api.nhplug.com:8443"
    NHPLUG_AUTH_URL: str = "https://api.nhplug.com:8443"
    NHPLUG_DEFAULT_ACCOUNT: Optional[str] = None
    NHPLUG_RATE_LIMIT: int = 4
    NHPLUG_TOKEN_CACHE: int = 1

    # 2. 봇(Bot) 매매 로직 설정
    TARGET_SYMBOLS: str = "005930,000660"
    BREAKOUT_K: float = 0.5
    MAX_LOSS_PCT: float = 0.02
    PORT: int = 8008
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    @property
    def is_live_mode(self) -> bool:
        """실거래(LIVE) 모드 활성화 여부"""
        return self.TRADING_MODE.upper() in ["LIVE", "REAL"]

    @property
    def is_mock_mode(self) -> bool:
        """모의투자(MOCK) 모드 활성화 여부"""
        return self.TRADING_MODE.upper() in ["MOCK", "SIMULATION"]

    @property
    def is_real_trading_confirmed(self) -> bool:
        """실거래 주문 발주 2차 잠금 해제 여부"""
        return self.CONFIRM_REAL_TRADING.strip().lower() in ["true", "1", "yes", "y"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
