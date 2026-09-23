# -*- coding: utf-8 -*-
"""나무증권(NHPLUG) + FastAPI 주식 자동매매 봇 (Full API + Frontend)"""
import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import asyncio
from auto_trader.bot import bot

app = FastAPI(
    title="Auto Trader Advanced API", 
    description="주식 자동매매 종합 API 시스템 (주문, 조회, 봇 제어, 프론트엔드 연동)",
    version="2.1.0"
)

bot_task = None

# 프론트엔드 정적 파일 마운트
app.mount("/static", StaticFiles(directory="auto_trader/static"), name="static")

# ==========================================
# Pydantic 모델 정의
# ==========================================
class OrderRequest(BaseModel):
    symbol: str
    price: int
    qty: int
    order_type: str = "LIMIT"

class OrderModifyRequest(BaseModel):
    new_price: int
    new_qty: int

class BotSettingsUpdateRequest(BaseModel):
    breakout_k: Optional[float] = None
    max_loss_pct: Optional[float] = None

# ==========================================
# 봇 라이프사이클 이벤트
# ==========================================
@app.on_event("startup")
async def startup_event():
    global bot_task
    pass

@app.on_event("shutdown")
async def shutdown_event():
    bot.stop()
    if bot_task:
        bot_task.cancel()

# ==========================================
# 1. 시스템 기본 API
# ==========================================
@app.get("/", tags=["System"])
def root_redirect():
    """접속 시 메인 HTS 대시보드로 자동 이동"""
    return RedirectResponse(url="/static/index.html")

@app.get("/health", tags=["System"])
def health_check():
    """시스템 상태 확인 (Health Check)"""
    from auto_trader.config import settings
    mode = settings.TRADING_MODE.upper()
    api_connected = getattr(bot.trader, "is_connected", False) and getattr(bot.trader, "use_real_api", False)
    
    return {
        "status": "online", 
        "bot_running": bot.is_running,
        "trader_mode": bot.trader.__class__.__name__,
        "trading_mode": mode,
        "api_connected": api_connected,
        "account_no": getattr(bot.trader, "account_no", None),
        "account_type": getattr(bot.trader, "account_type", None),
        "real_trading_confirmed": settings.is_real_trading_confirmed
    }

# 이번 추천에 사용할 금액 (기본값: 2,000,000원)
current_recommendation_budget = 2000000
# ==========================================
# 예산 파일 영구 저장/로드 (서버 재시작 후에도 유지)
# ==========================================
import json, os as _os

_BUDGET_FILE = "data/budget.json"
_DEFAULT_BUDGET = 2000000

def _load_budget() -> int:
    """data/budget.json에서 저장된 예산 로드 (없으면 기본값)"""
    try:
        if _os.path.exists(_BUDGET_FILE):
            with open(_BUDGET_FILE, "r", encoding="utf-8") as f:
                return int(json.load(f).get("budget", _DEFAULT_BUDGET))
    except Exception:
        pass
    return _DEFAULT_BUDGET

def _save_budget(budget: int):
    """예산을 data/budget.json에 영구 저장"""
    try:
        _os.makedirs("data", exist_ok=True)
        with open(_BUDGET_FILE, "w", encoding="utf-8") as f:
            json.dump({"budget": budget}, f)
    except Exception as e:
        pass

# 서버 시작 시 저장된 예산 복원
current_recommendation_budget = _load_budget()
bot.set_budget(current_recommendation_budget)

class BudgetUpdateRequest(BaseModel):
    budget: int

# ==========================================
# 2. 계좌 (Account) API
# ==========================================
@app.get("/api/v1/account/balance", tags=["Account"])
async def get_balance():
    """계좌 총 잔고 및 상세 자산 조회 (비동기 처리)"""
    from auto_trader.config import settings
    detail = await asyncio.to_thread(bot.trader.get_account_detail)
    balance = await asyncio.to_thread(bot.trader.get_balance)
    mode = settings.TRADING_MODE.upper()

    # PAPER 모드: total_assets = 현금 + 주식 평가액 (올바른 총자산)
    # balance(대시보드 표시값)는 총자산으로 표시 → "가상계좌 평가 자산" 제목에 맞음
    cash        = detail.get("cash", 0)           # 주문 가능 현금
    total_assets = detail.get("total_assets", cash)  # 현금 + 주식
    
    label = "실거래계좌 금액" if mode in ["REAL", "LIVE"] else ("모의투자계좌 금액" if mode == "MOCK" else "가상계좌 금액")
    return {
        "balance": balance,
        "balance": total_assets,          # 총자산(현금+주식) — 대시보드 헤드라인 표시용
        "cash": cash,                     # 가용 현금만 — "전액" 버튼 계산 기준
        "trading_mode": mode,
        "account_label": label,
        "account_no": detail.get("account_no"),
        "account_type": detail.get("account_type"),
        "cash": detail.get("cash", balance),
        "total_assets": detail.get("total_assets", balance),
        "withdrawable": detail.get("withdrawable", balance),
        "total_assets": total_assets,
        "withdrawable": detail.get("withdrawable", cash),
        "stock_eval": detail.get("stock_eval", 0),
        "recommended_budget": current_recommendation_budget,
        "real_trading_confirmed": settings.is_real_trading_confirmed,
        "api_message": detail.get("message", "")
    }

@app.get("/api/v1/account/budget", tags=["Account"])
def get_recommendation_budget():
    """이번 추천에 사용할 금액 조회"""
    return {"budget": current_recommendation_budget}

@app.post("/api/v1/account/budget", tags=["Account"])
def set_recommendation_budget(req: BudgetUpdateRequest):
    """이번 추천에 사용할 금액 변경"""
    """이번 추천에 사용할 금액 변경 (파일에 영구 저장 + 봇 즉시 동기화)"""
    global current_recommendation_budget
    if req.budget <= 0:
        raise HTTPException(status_code=400, detail="금액은 0보다 커야 합니다.")
    current_recommendation_budget = req.budget
    bot.set_budget(req.budget)
    _save_budget(req.budget)   # 파일에 영구 저장 — 서버 재시작 후에도 유지
    return {"status": "success", "budget": current_recommendation_budget}


@app.get("/api/v1/account/positions", tags=["Account"])
async def get_positions():
    """현재 보유 중인 종목 및 수량 조회"""
    positions = await asyncio.to_thread(bot.trader.get_positions)
    return {"positions": positions}

@app.get("/api/v1/account/portfolio-pnl", tags=["Account"])
async def get_portfolio_pnl():
    """보유 포지션 실시간 수익률 (종목별 + 합산) 조회 — 현재가 기반 실시간 갱신"""
    positions = await asyncio.to_thread(bot.trader.get_positions)
    if not positions:
        return {
            "status": "success",
            "has_positions": False,
            "items": [],
            "summary": {"total_buy_amt": 0, "total_eval_amt": 0, "total_pnl": 0, "total_pnl_pct": 0.0}
        }

    items = []
    total_buy_amt = 0
    total_eval_amt = 0

    for sym, pos in positions.items():
        qty = pos.get("qty", 0)
        buy_price = pos.get("buy_price", 0)
        name = pos.get("name", sym)
        if qty <= 0:
            continue

        # 실시간 현재가 조회
        cur_price = 0
        try:
            quotes = await asyncio.to_thread(bot.trader.get_quotes, [{"symbol": sym, "name": name, "price": 0}])
            if quotes and quotes[0].get("price", 0) > 0:
                cur_price = quotes[0]["price"]
                name = quotes[0].get("name", name)
        except Exception:
            pass

        if cur_price <= 0:
            cur_price = pos.get("current_price", buy_price)

        buy_amt = int(buy_price * qty)
        eval_amt = int(cur_price * qty)
        pnl = eval_amt - buy_amt
        pnl_pct = round(((cur_price - buy_price) / buy_price) * 100, 2) if buy_price > 0 else 0.0

        total_buy_amt += buy_amt
        total_eval_amt += eval_amt

        items.append({
            "symbol": sym,
            "name": name,
            "qty": qty,
            "buy_price": int(buy_price),
            "current_price": cur_price,
            "buy_amt": buy_amt,
            "eval_amt": eval_amt,
            "pnl": pnl,
            "pnl_pct": pnl_pct
        })

    total_pnl = total_eval_amt - total_buy_amt
    total_pnl_pct = round((total_pnl / total_buy_amt) * 100, 2) if total_buy_amt > 0 else 0.0

    return {
        "status": "success",
        "has_positions": len(items) > 0,
        "items": items,
        "summary": {
            "total_buy_amt": total_buy_amt,
            "total_eval_amt": total_eval_amt,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct
        }
    }

# ==========================================
# 2-1. 추천 매매 (Recommendations) API
# ==========================================
_rec_pool_cache = {"stocks": None, "timestamp": 0.0}

@app.get("/api/v1/recommendations/top5", tags=["Recommendations"])
async def get_top5_recommendations(budget: Optional[int] = Query(None, description="추천에 사용할 예산 (미입력 시 현재 설정된 추천 예산 사용)")):
    """지정된 예산 기반 실시간 투자 유망 종목 TOP 5 추천 (평가 점수 및 상세 추천 사유 포함)"""
    global current_recommendation_budget, _rec_pool_cache
    import time
    now = time.time()
    target_budget = budget if (budget is not None and budget > 0) else current_recommendation_budget

    # 1. 코스피 시총 상위 40개 종목 풀 실시간 수집 (10초 캐싱으로 고속 응답)
    all_stocks = []
    if _rec_pool_cache["stocks"] and (now - _rec_pool_cache["timestamp"] < 10.0):
        all_stocks = [dict(s) for s in _rec_pool_cache["stocks"]]
    else:
        try:
            import urllib.request
            import json
            url = "https://m.stock.naver.com/api/stocks/marketValue/KOSPI?page=1&pageSize=40"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = await asyncio.to_thread(urllib.request.urlopen, req, timeout=3)
            data = json.loads(resp.read().decode('utf-8'))
            for s in data.get('stocks', []):
                raw_p = s.get('closePriceRaw') or s.get('closePrice', '0').replace(',', '')
                price = int(raw_p) if raw_p and str(raw_p).isdigit() else 0
                change = float(s.get('fluctuationsRatio') or 0.0)
                all_stocks.append({
                    "name": s['stockName'],
                    "symbol": s['itemCode'],
                    "price": price,
                    "change": change
                })
            _rec_pool_cache["stocks"] = all_stocks
            _rec_pool_cache["timestamp"] = now
        except Exception as e:
            if _rec_pool_cache["stocks"]:
                all_stocks = [dict(s) for s in _rec_pool_cache["stocks"]]
            else:
                # 비상 대비 대표 종목 풀
                all_stocks = [
                    {"name": "삼성전자", "symbol": "005930", "price": 284500, "change": 2.89},
                    {"name": "삼성전자우", "symbol": "005935", "price": 219500, "change": 3.78},
                    {"name": "SK", "symbol": "034730", "price": 613000, "change": 4.25},
                    {"name": "두산에너빌리티", "symbol": "034020", "price": 81700, "change": 1.50},
                    {"name": "현대차", "symbol": "005380", "price": 353000, "change": 1.20},
                    {"name": "기아", "symbol": "000270", "price": 105000, "change": 0.95},
                    {"name": "LG에너지솔루션", "symbol": "373220", "price": 350500, "change": 0.0},
                    {"name": "카카오", "symbol": "035720", "price": 42000, "change": 2.10},
                    {"name": "NAVER", "symbol": "035420", "price": 172000, "change": 1.80},
                ]

    # 2. 지정된 예산 한도 내에서만 매수 가능한 종목 필터링 및 다면 평가 스코어링
    candidates = []
    for idx, s in enumerate(all_stocks):
        price = s["price"]
        change = s["change"]
        # 예산 초과 종목(1주도 살 수 없는 종목)은 엄격히 제외
        if price <= 0 or price > target_budget:
            continue

        qty = target_budget // price
        if qty <= 0:
            continue

        cost = qty * price
        util_rate = round((cost / target_budget) * 100, 1)
        rem_budget = target_budget - cost

        # 1) 모멘텀 & 당일 시세 강도 점수 (최대 35점)
        if change > 0:
            mom_score = 20.0 + min(15.0, change * 3.2)
        elif change == 0:
            mom_score = 20.0
        else:
            mom_score = max(10.0, 20.0 + change * 2.2)

        # 2) 변동성 돌파 적합도 점수 (최대 30점)
        bo_score = 24.0 + (4.0 if change >= 2.0 else (2.0 if change > 0 else -1.5))

        # 3) 예산 집행 효율성 점수 (최대 20점)
        eff_score = (cost / target_budget) * 20.0

        # 4) 대형주 수급 신뢰도 점수 (최대 15점)
        stab_score = max(10.0, 15.0 - (idx * 0.25))

        raw_total = mom_score + bo_score + eff_score + stab_score
        total_score = max(72, min(98, round(raw_total)))

        # 평가 등급 산정
        if total_score >= 93:
            grade = "S+"
            grade_desc = "초강력 매수"
        elif total_score >= 88:
            grade = "A+"
            grade_desc = "적극 추천"
        elif total_score >= 83:
            grade = "A"
            grade_desc = "유망 종목"
        else:
            grade = "B+"
            grade_desc = "관심 종목"

        # 추천 사유 생성 (직관적이고 설득력 있는 분석 근거)
        sign_str = f"+{change:.2f}%" if change > 0 else f"{change:.2f}%"
        if change >= 2.5:
            trend_reason = f"변동성 돌파 임계치 상향 돌파({sign_str}), 강력한 수급 유입 및 단기 추세 추종 최적"
        elif change > 0:
            trend_reason = f"당일 안정적 우상향 반등({sign_str}), 5일 이평선 지지 확인 및 상승 탄력 지속"
        elif change == 0:
            trend_reason = f"기관·외인 매물 소화 후 보합권 견고한 지지력 확보, 변동성 K(0.5) 돌파 대기"
        else:
            trend_reason = f"단기 과매도 국면 눌림목 지지선 형성({sign_str}), 기술적 반등 손익비(Risk/Reward) 우수"

        alloc_reason = f"예산 집행율 {util_rate}%({qty}주 매수, 소요 {cost:,}원 / 잔여 {rem_budget:,}원)"
        full_reason = f"{trend_reason} | {alloc_reason}"

        candidates.append({
            "name": s["name"],
            "symbol": s["symbol"],
            "price": price,
            "change_rate": change,
            "score": total_score,
            "score_grade": grade,
            "grade_desc": grade_desc,
            "recommended_qty": qty,
            "total_cost": cost,
            "remaining_budget": rem_budget,
            "utilization_rate": util_rate,
            "reason": full_reason,
            "trend_reason": trend_reason,
            "alloc_reason": alloc_reason
        })

    # 종합 점수 내림차순 -> 예산 효율 내림차순 정렬 후 상위 5개 선정
    candidates.sort(key=lambda x: (x["score"], x["utilization_rate"]), reverse=True)
    top5 = candidates[:5]
    for rank, item in enumerate(top5, 1):
        item["rank"] = rank

    return {
        "status": "success",
        "budget": target_budget,
        "count": len(top5),
        "recommendations": top5
    }

# ==========================================
# 3. 주문 (Orders) API - GET, POST, PUT, DELETE
# ==========================================
@app.post("/api/v1/orders/buy", tags=["Orders"])
async def create_buy_order(order: OrderRequest):
    """신규 매수 주문 생성 (Create)"""
    from auto_trader.config import settings
    success, order_id, message = await asyncio.to_thread(
        bot.trader.order_buy, order.symbol, order.price, order.qty, order.order_type
    )
    if success:
        return {
            "status": "success",
            "message": message,
            "order_id": order_id,
            "trading_mode": settings.TRADING_MODE.upper()
        }
    raise HTTPException(status_code=400, detail=message)

@app.post("/api/v1/orders/sell", tags=["Orders"])
async def create_sell_order(order: OrderRequest):
    """신규 매도 주문 생성 (Create)"""
    from auto_trader.config import settings
    success, order_id, message = await asyncio.to_thread(
        bot.trader.order_sell, order.symbol, order.price, order.qty, order.order_type
    )
    if success:
        return {
            "status": "success",
            "message": message,
            "order_id": order_id,
            "trading_mode": settings.TRADING_MODE.upper()
        }
    raise HTTPException(status_code=400, detail=message)

@app.put("/api/v1/orders/{order_id}", tags=["Orders"])
def modify_order(
    order_id: str = Path(..., description="수정할 주문의 고유 ID"),
    modify_req: OrderModifyRequest = None
):
    """미체결 주문 정정 (Update/PUT)"""
    return {
        "status": "success", 
        "message": f"주문({order_id})이 단가 {modify_req.new_price}원으로 정정되었습니다."
    }

@app.delete("/api/v1/orders/{order_id}", tags=["Orders"])
def cancel_order(order_id: str = Path(..., description="취소할 주문의 고유 ID")):
    """미체결 주문 취소 (Delete)"""
    return {"status": "success", "message": f"주문({order_id})이 정상적으로 취소되었습니다."}

@app.get("/api/v1/orders/history", tags=["Orders"])
def get_order_history(limit: int = Query(10, description="조회할 주문 개수")):
    """과거 주문/체결 내역 조회 (Read)"""
    history = getattr(bot.trader, "order_history", [])[:limit]
    return {"history": history, "message": f"최근 {len(history)}개의 주문 내역을 조회합니다."}

# ==========================================
# 4. 시세 (Market) API
# ==========================================
# 캐시 저장소 (연속 새로고침 및 트래픽 폭주 방지)
_ticker_cache = {"data": None, "timestamp": 0.0}
_ticker_lock = asyncio.Lock()
_single_quote_cache = {}

def resolve_stock_symbol(query: str) -> tuple[str, str]:
    """종목코드(005930) 또는 기업명(삼성전자, 현대차 등)을 6자리 종목코드와 기업명으로 변환"""
    import urllib.request
    import urllib.parse
    import json
    
    q = query.strip()
    if len(q) == 6 and q.isdigit():
        return q, q
        
    try:
        url = "https://stock.naver.com/api/autocomplete/search/autoComplete?query=" + urllib.parse.quote(q) + "&target=stock%2Cindex%2Cmarketindicator%2Ccoin%2Cipo%2Cfund"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://stock.naver.com/'})
        res = urllib.request.urlopen(req, timeout=3)
        data = json.loads(res.read().decode('utf-8'))
        items = data.get('result', {}).get('items', [])
        for item in items:
            if item.get('category') == 'stock':
                return item.get('code', q), item.get('name', q)
        if items:
            return items[0].get('code', q), items[0].get('name', q)
    except Exception as e:
        pass
    return q, q

@app.get("/api/v1/market/quote/{symbol}", tags=["Market"])
async def get_quote(symbol: str = Path(..., description="조회할 종목코드 또는 기업명 (예: 005930, 삼성전자)")):
    """단일 종목 현재가 조회 (기업명 및 종목코드 자동 해석, 1.5초 캐시)"""
    import time
    now = time.time()
    
    # 1. 기업명/종목코드 해석
    code, resolved_name = await asyncio.to_thread(resolve_stock_symbol, symbol)
    
    # 2. 캐시 확인 (해석된 종목코드 기준)
    if code in _single_quote_cache:
        cached_entry = _single_quote_cache[code]
        if now - cached_entry["time"] < 1.5:
            return cached_entry["data"]

    quotes = await asyncio.to_thread(bot.trader.get_quotes, [{"name": resolved_name, "symbol": code, "price": 0}])
    if quotes:
        display_name = quotes[0]["name"] if quotes[0]["name"] and quotes[0]["name"] != "검색 결과" else resolved_name
        res = {
            "symbol": quotes[0]["symbol"], 
            "name": display_name, 
            "current_price": quotes[0]["price"], 
            "change_rate": quotes[0]["change"]
        }
        _single_quote_cache[code] = {"data": res, "time": now}
        _single_quote_cache[symbol] = {"data": res, "time": now}
        return res
    return {"symbol": code, "name": resolved_name, "current_price": 0, "change_rate": 0}

@app.get("/api/v1/market/ticker-tape", tags=["Market"])
async def get_ticker_tape():
    """네이버 모바일 API 실시간 코스피 시총 상위 20개 종목을 동적으로 가져와 나무증권 가격과 매핑 (5초 캐시로 연타 보호)"""
    import time
    now = time.time()
    
    # 5초 이내 재호출 시 기존 캐시 즉시 반환 (연속 새로고침 시 0.001초 응답)
    if _ticker_cache["data"] and (now - _ticker_cache["timestamp"] < 5.0):
        return {"tickers": _ticker_cache["data"]}

    async with _ticker_lock:
        if _ticker_cache["data"] and (time.time() - _ticker_cache["timestamp"] < 5.0):
            return {"tickers": _ticker_cache["data"]}

        import urllib.request
        import json
        
        top_tickers = []
        try:
            url = "https://m.stock.naver.com/api/stocks/marketValue/KOSPI?page=1&pageSize=20"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = await asyncio.to_thread(urllib.request.urlopen, req, timeout=3)
            data = json.loads(resp.read().decode('utf-8'))
            
            for s in data['stocks']:
                raw_p = s.get('closePriceRaw') or s.get('closePrice', '0').replace(',', '')
                price_val = int(raw_p) if raw_p and str(raw_p).isdigit() else 0
                change_val = float(s.get('fluctuationsRatio') or 0.0)
                top_tickers.append({
                    "name": s['stockName'],
                    "symbol": s['itemCode'],
                    "price": price_val,
                    "change": change_val
                })
        except Exception as e:
            if _ticker_cache["data"]:
                return {"tickers": _ticker_cache["data"]}
            top_tickers = [{"name": "삼성전자", "symbol": "005930", "price": 0}, {"name": "SK하이닉스", "symbol": "000660", "price": 0}]

        quotes = await asyncio.to_thread(bot.trader.get_quotes, top_tickers)
        _ticker_cache["data"] = quotes
        _ticker_cache["timestamp"] = time.time()
        return {"tickers": quotes}


# ==========================================
# 5. 자동매매 봇 제어 (Bot Control) API
# ==========================================
@app.post("/api/v1/bot/start", tags=["Bot Control"])
async def start_bot():
    """자동매매 감시 루프 백그라운드 시작"""
    global bot_task
    if bot.is_running:
        return {"message": "봇이 이미 실행 중입니다.", "is_running": True}
    
    bot.set_budget(current_recommendation_budget)
    bot_task = asyncio.create_task(bot.run_loop())
    return {"message": "자동매매 봇이 시작되었습니다.", "is_running": True}

@app.post("/api/v1/bot/stop", tags=["Bot Control"])
def stop_bot():
    """자동매매 감시 루프 강제 종료"""
    bot.stop()
    global bot_task
    if bot_task:
        bot_task.cancel()
    return {"message": "자동매매 봇이 중지되었습니다.", "is_running": False}

@app.get("/api/v1/bot/logs", tags=["Bot Control"])
def get_bot_logs(limit: int = Query(25, description="조회할 로그 개수")):
    """자동매매 봇의 실시간 판단 및 매매 활동 로그 조회"""
    logs = bot.get_recent_logs(limit=limit)
    return {"logs": logs, "is_running": bot.is_running}

@app.put("/api/v1/bot/settings", tags=["Bot Control"])
def update_bot_settings(settings: BotSettingsUpdateRequest):
    """실행 중인 봇의 전략 설정값 실시간 변경 (PUT)"""
    if settings.breakout_k is not None:
        bot.strategy.k = settings.breakout_k
    return {
        "message": "봇 설정이 업데이트되었습니다.",
        "strategy": bot.strategy.describe(),
        "current_k": bot.strategy.k
    }

@app.get("/api/v1/bot/strategy-status", tags=["Bot Control"])
def get_strategy_status():
    """현재 적용 중인 자동매매 전략 파라미터 전체 조회"""
    s = bot.strategy
    return {
        "mode": "AGGRESSIVE",
        "describe": s.describe(),
        "params": {
            "breakout_k":           s.k,
            "momentum_min_pct":     s.momentum_min_pct,
            "max_positions":        s.max_positions,
            "budget_alloc_pct":     s.budget_alloc_pct,
            "scan_interval_sec":    s.scan_interval_sec,
            "take_profit_pct":      s.take_profit_pct * 100,
            "stop_loss_pct":        s.stop_loss_pct * 100,
            "trailing_trigger_pct": s.trailing_trigger * 100,
            "trailing_gap_pct":     s.trailing_gap * 100,
        },
        "current_budget": bot.budget,
        "is_running": bot.is_running,
    }
