"""나무증권(NHPLUG) + FastAPI 주식 자동매매 시스템 메인 애플리케이션.

실행 방법:
    uvicorn src.main:app --reload --port 8000
"""

import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.config import settings
from src.database import db
from src.bot import bot


# ---------------------------------------------------------
# Pydantic 요청/응답 모델
# ---------------------------------------------------------
class ManualOrderRequest(BaseModel):
    ticker: str = Field(..., description="종목코드 6자리 (예: 005930)")
    order_type: str = Field("BUY", description="주문 유형 (BUY 또는 SELL)")
    qty: int = Field(..., gt=0, description="주문 수량")
    price: Optional[int] = Field(None, description="주문 단가 (지정가). None이면 현재가 시장가 체결")


class StartTradingRequest(BaseModel):
    strategy: str = Field("volatility_breakout", description="적용할 매매 전략")
    target_tickers: List[str] = Field(default_factory=lambda: ["005930", "000660"], description="감시 대상 종목 리스트")


# ---------------------------------------------------------
# 백그라운드 자동매매 감시 루프
# ---------------------------------------------------------
async def trading_background_loop():
    """백그라운드에서 주기적으로 시세를 감시하고 시그널을 연산하는 비동기 루프."""
    print("[INFO] [백그라운드] 자동매매 감시 루프 가동 시작")
    try:
        while bot.is_running:
            await bot.run_single_cycle()
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        print("[INFO] [백그라운드] 자동매매 감시 루프가 정상 취소되었습니다.")
    except Exception as e:
        print(f"[ERROR] [백그라운드 루프 에러]: {e}")


# ---------------------------------------------------------
# FastAPI Lifespan (앱 시작 및 종료 리소스 관리)
# ---------------------------------------------------------
background_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # [Startup]
    print(f"[INFO] [서버 기동] 시스템 초기화 (모드: {bot.mode})")
    db.init_db()

    yield

    # [Shutdown]
    print("[INFO] [서버 종료] 백그라운드 태스크 및 세션 정리 중...")
    global background_task
    if bot.is_running and background_task:
        bot.is_running = False
        background_task.cancel()
        await asyncio.gather(background_task, return_exceptions=True)
    print("[INFO] 서버가 안전하게 종료되었습니다.")


# ---------------------------------------------------------
# FastAPI 앱 초기화
# ---------------------------------------------------------
app = FastAPI(
    title="나무증권(NHPLUG) 주식 자동매매 시스템 API",
    version="0.1.0",
    description="FastAPI 기반 NH투자증권 PLUG Open API 주식 자동매매 및 관제 서버 (v0.1)",
    lifespan=lifespan
)


# ---------------------------------------------------------
# API 라우터 정의
# ---------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """서버 상태, 활성 모드, 기본 정보 확인."""
    return {
        "status": "healthy",
        "version": "v0.1.0",
        "trading_mode": bot.mode,
        "is_bot_running": bot.is_running,
        "monitored_tickers": bot.monitored_tickers,
        "last_run_time": bot.last_run_time.isoformat() if bot.last_run_time else None
    }


@app.get("/api/v1/trading/status", tags=["Trading Bot"])
async def get_trading_status():
    """자동매매 봇 실행 상태 및 계좌 요약 조회."""
    balance_info = await bot.get_account_summary()
    return {
        "is_running": bot.is_running,
        "trading_mode": bot.mode,
        "strategy": "volatility_breakout",
        "monitored_tickers": bot.monitored_tickers,
        "account_summary": balance_info.get("summary", {})
    }


@app.post("/api/v1/trading/start", tags=["Trading Bot"])
async def start_trading_bot(req: StartTradingRequest):
    """자동매매 봇 백그라운드 루프 기동."""
    global background_task
    if bot.is_running:
        raise HTTPException(status_code=400, detail="자동매매 봇이 이미 실행 중입니다.")

    bot.is_running = True
    bot.monitored_tickers = req.target_tickers
    background_task = asyncio.create_task(trading_background_loop())

    return {
        "message": "자동매매 봇이 성공적으로 시작되었습니다.",
        "strategy": req.strategy,
        "tickers": req.target_tickers,
        "mode": bot.mode
    }


@app.post("/api/v1/trading/stop", tags=["Trading Bot"])
async def stop_trading_bot():
    """자동매매 봇 일시 정지 (현재 포지션은 유지)."""
    global background_task
    if not bot.is_running:
        return {"message": "자동매매 봇이 이미 정지 상태입니다."}

    bot.is_running = False
    if background_task:
        background_task.cancel()
        background_task = None

    return {"message": "자동매매 봇이 안전하게 정지되었습니다."}


@app.post("/api/v1/trading/kill-switch", tags=["Trading Bot"])
async def activate_kill_switch():
    """[비상 킬스위치] 봇 즉시 중단 및 전량 강제 시장가 청산."""
    global background_task
    if background_task:
        background_task.cancel()
        background_task = None

    result = await bot.kill_switch()
    return {
        "action": "kill_switch_activated",
        "result": result
    }


@app.post("/api/v1/trading/reset-paper", tags=["Trading Bot"])
async def reset_paper_trading(initial_cash: int = 10_000_000):
    """[가상 매매 전용] 가상 계좌 잔고를 초기화합니다."""
    bot.paper_trader.reset(initial_cash)
    return {
        "message": f"가상 계좌가 {initial_cash:,}원으로 초기화되었습니다.",
        "cash": initial_cash
    }


@app.get("/api/v1/account/balance", tags=["Account"])
async def get_account_balance():
    """실시간 계좌 잔고 및 보유 주식 목록 조회."""
    try:
        balance_data = await bot.get_account_summary()
        return balance_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/market/quote/{ticker}", tags=["Market Data"])
async def get_market_quote(ticker: str):
    """지정 종목의 현재가 시세 조회."""
    price = await bot.get_current_price(ticker)
    return {
        "ticker": ticker,
        "current_price": price
    }


@app.post("/api/v1/orders/manual", tags=["Orders"])
async def place_manual_order(req: ManualOrderRequest):
    """수동 주문 발주 (매수/매도, 모드별 분기 처리)."""
    exec_price = req.price
    if exec_price is None:
        exec_price = await bot.get_current_price(req.ticker)

    if req.order_type.upper() == "BUY":
        result = await bot.execute_buy(req.ticker, req.qty, exec_price)
    elif req.order_type.upper() == "SELL":
        result = await bot.execute_sell(req.ticker, req.qty, exec_price)
    else:
        raise HTTPException(status_code=400, detail="order_type 은 'BUY' 또는 'SELL' 이어야 합니다.")

    return {
        "ticker": req.ticker,
        "order_type": req.order_type,
        "qty": req.qty,
        "price": exec_price,
        "result": result
    }


@app.get("/api/v1/orders/history", tags=["Orders"])
async def get_order_history(limit: int = Query(50, ge=1, le=200),
                            mode: Optional[str] = Query(None, description="PAPER, MOCK, LIVE 필터")):
    """최근 주문 내역 조회 (DB)."""
    orders = db.get_recent_orders(limit=limit, trading_mode=mode)
    return {"count": len(orders), "orders": orders}


@app.get("/api/v1/executions/history", tags=["Orders"])
async def get_execution_history(limit: int = Query(50, ge=1, le=200),
                                mode: Optional[str] = Query(None, description="PAPER, MOCK, LIVE 필터")):
    """최근 체결 내역 조회 (DB)."""
    executions = db.get_recent_executions(limit=limit, trading_mode=mode)
    return {"count": len(executions), "executions": executions}
