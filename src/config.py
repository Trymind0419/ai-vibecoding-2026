"""시스템 전역 환경설정 모듈.

.env 파일 및 환경변수를 우선 탐색하여 설정값을 로드합니다.
python-dotenv 패키지가 없어도 기본 동작하도록 내장 파서를 지원합니다.
"""

import os
from pathlib import Path

# 루트 디렉토리
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# .env 파일 수동 파싱 (python-dotenv 미설치 대비)
if ENV_FILE.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_FILE)
    except ImportError:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key not in os.environ:
                    os.environ[key] = val


class Settings:
    """자동매매 시스템 설정 클래스."""

    # 1. 운영 모드 (PAPER: 가상 매매 / MOCK: 모의투자 / LIVE: 실전 매매)
    TRADING_MODE: str = os.getenv("TRADING_MODE", "PAPER").upper()
    CONFIRM_REAL_TRADING: bool = os.getenv("CONFIRM_REAL_TRADING", "false").lower() in ("true", "1", "yes")

    # 가상 매매 초기 자본금 (기본 1,000만 원)
    INITIAL_PAPER_CASH: int = int(os.getenv("INITIAL_PAPER_CASH", "10000000"))

    # 2. 나무증권 API 자격증명
    APP_KEY: str = os.getenv("NHPLUG_APP_KEY", os.getenv("APP_KEY", ""))
    APP_SECRET: str = os.getenv("NHPLUG_APP_SECRET", os.getenv("APP_SECRET", ""))

    # 3. 엔드포인트 URL
    BASE_URL: str = os.getenv("NHPLUG_BASE_URL", "https://moapi.nhplug.com:8443")
    AUTH_URL: str = os.getenv("NHPLUG_AUTH_URL", "https://api.nhplug.com:8443")

    # 4. 기본 계좌번호
    DEFAULT_ACCOUNT: str = os.getenv("NHPLUG_DEFAULT_ACCOUNT", "")

    # 5. 리스크 관리 파라미터
    MAX_STOCK_WEIGHT: float = float(os.getenv("MAX_STOCK_WEIGHT", "0.20"))      # 1종목 최대 투자비중 (20%)
    DAILY_LOSS_LIMIT: float = float(os.getenv("DAILY_LOSS_LIMIT", "-0.02"))     # 일일 최대 손실한도 (-2%)
    STOP_LOSS_RATE: float = float(os.getenv("STOP_LOSS_RATE", "-0.03"))         # 개별 종목 손절선 (-3%)

    # 6. 데이터베이스 경로
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = DATA_DIR / "trades.db"

    @classmethod
    def validate(cls):
        """설정 유효성 검사."""
        if cls.TRADING_MODE == "LIVE":
            if not cls.CONFIRM_REAL_TRADING:
                raise ValueError(
                    "⚠️ 실전 매매(LIVE) 모드는 안전을 위해 CONFIRM_REAL_TRADING=true 가 설정되어야 합니다."
                )
            if not cls.APP_KEY or not cls.APP_SECRET:
                raise ValueError("⚠️ 실전 매매(LIVE) 모드에는 NHPLUG_APP_KEY 와 APP_SECRET 이 필수입니다.")


settings = Settings()
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
