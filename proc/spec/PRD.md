# [PRD] 나무증권(NHPLUG) + FastAPI 주식 자동매매 시스템

> **문서 버전**: v1.3.0 (Compact Refactored)  
> **최종 수정일**: 2026-09-21  
> **상태**: 승인 완료 (Approved)  
> **원문 위치**: [proc/spec/PRD.md](proc/spec/PRD.md)  
> **핵심 기술**: Python 3.10+, FastAPI, NHPLUG OpenAPI (`nhplug` SDK), SQLite

---

## 1. 프로젝트 개요 및 핵심 원칙

### 1.1 시스템 목적
나무증권(NH투자증권) 차세대 **NHPLUG Open API**와 **FastAPI 비동기 웹 프레임워크**를 결합하여, 백그라운드에서 실시간 시세를 감시하고 매매를 집행하며 웹/모바일에서 원격 관제·제어할 수 있는 안정적인 주식 자동매매 백엔드를 구축함.

### 1.2 핵심 안전 철학
- **"가상 매매(Paper Trading) 우선 검증 후 실전 매매 승격"**: 실제 원금 손실을 원천 차단하기 위해 가상 자금으로 충분한 안정성을 검증한 후 설정 스위치 하나로 실계좌로 전환함.

### 1.3 AI 에이전트 개발 수칙
1. **비동기 블로킹 방지**: `nhplug` SDK 호출은 반드시 `await asyncio.to_thread(func, *args)`로 스레드 풀 격리.
2. **독립 워커**: 전략 감시 루프는 FastAPI 웹 요청과 분리된 백그라운드 태스크(`asyncio.create_task`)로 구동.
3. **안전 잠금장치**: 실거래(`LIVE`) 주문은 2중 확인 플래그(`CONFIRM_REAL_TRADING=true`)가 켜진 경우에만 허용.

---

## 2. 3단계 점진적 운영 정책 (가상 매매 → 실전 전환)

```
[Phase 1: 가상 매매 (PAPER)] ──▶ [Phase 2: 소액 실전 (Micro Live)] ──▶ [Phase 3: 풀 시드 (Full Live)]
 • 가상 시드 1,000만원            • 1회 1주 또는 자산 5~10%          • 정규 운용 자금 투입
 • 실시간 시세 기반 가상 체결     • 실제 주문 전송 및 지연/수수료 검증 • 일일 손실 한도(-2%) 강제
 • 실제 투입 원금 0원
```

### 2.1 운영 모드 (`TRADING_MODE`)
- **`PAPER` (기본값)**: 자체 가상 매매 엔진(`PaperTrader`)을 사용하여 실제 주문 없이 가상 체결 및 잔고 관리.
- **`MOCK`**: 나무증권 공식 모의투자 서버(`moapi.nhplug.com:8443`) 및 모의계좌(`acct_type="03"`) 연동.
- **`LIVE`**: 나무증권 실제 운영 서버(`api.nhplug.com:8443`) 및 실계좌(`acct_type="01"/"02"`) 실거래.

### 2.2 실전(`LIVE`) 승격 기준 (Promotion Checklist)
- [ ] 최소 **10영업일(2주)** 이상 연속 무중단 백그라운드 운용 성공
- [ ] API 429 에러 0건, 비정상 중단 0건, 미체결 방치 0건
- [ ] 누적 수익률 양수(+) 및 최대 낙폭(**MDD 5% 이내**) 방어
- [ ] 비상 킬스위치 발동 시 정상 전량 청산 완료 검증 1회 이상

---

## 3. 나무증권 OpenAPI 핵심 기술 규약 요약

| 항목 | 규약 및 메커니즘 | 주의 및 대응 수칙 |
|---|---|---|
| **토큰 인증** | OAuth2 Bearer 토큰 (24시간 유효) | 파일 캐시(`~/.nhplug/token-*.json`) 필수. 재발급은 오직 **HTTP 401** 시에만 수행. |
| **IP 등록** | **개인 고객 등록 불필요** | `APP_KEY` + `APP_SECRET`으로 유동 IP/서버 어디서나 호출 가능 (단, 해외 IP는 차단). |
| **호출 유량** | 실측 초당 5회 상한 | SDK 내부에서 초당 4회 자동 스로틀 처리. |
| **필수 파라미터** | KRX 시간연장 개정 규약 | 잔고 조회 시 **`aly_qut_cd="1"` (정규장)** 필수 누락 주의. 시세 시장구분은 `UNT`(통합). |
| **성공 판정** | **HTTP 200 ≠ 성공** | `rsp_cd=="00000"` 단일 코드 하드코딩 금지. `Output_0` 존재 및 `rsp_msg` 확인 후 주문. |
| **실시간 (WS)** | 포트 `7070` (시세/체결통보) / 경로 `/websocket` | 앱키당 동시 2세션, 세션당 10종목 상한. 국내 체결가 채널 `mc`, 체결통보 `d2`. |

---

## 4. FastAPI 시스템 아키텍처 & API 엔드포인트 명세

### 4.1 컴포넌트 아키텍처
- **Client**: Web Browser (Swagger UI `/docs`), 모바일, 텔레그램 알림
- **FastAPI Layer**:
  - `Lifespan`: 기동 시 토큰/마스터 초기화, 종료 시 백그라운드 태스크 및 웹소켓 세션 반납
  - `TradingBotState`: 봇 실행 여부, 현재 모드(`PAPER`/`LIVE`), 종목 감시 루프 관리
  - `PaperTrader` / `NamuhAutoTrader`: 모드에 따른 주문 및 잔고 분기 처리
- **Storage Layer**: SQLite (`data/trades.db`), 매매 리포트 (`output/`)

### 4.2 REST API 엔드포인트 명세
| 메서드 | URI 경로 | 설명 | 주요 파라미터 및 동작 |
|---|---|---|---|
| `GET` | `/health` | 서버 헬스체크 및 환경 확인 | 서버 상태, 현재 `trading_mode`, 기본 계좌 반환 |
| `GET` | `/api/v1/trading/status` | 봇 실행 상태 및 수익률 조회 | 봇 가동 여부, 감시 종목 리스트, 현재 모드 반환 |
| `POST` | `/api/v1/trading/start` | 자동매매 봇 시작 | 감시 종목 및 전략 지정 후 백그라운드 루프 기동 |
| `POST` | `/api/v1/trading/stop` | 자동매매 봇 일시 정지 | 백그라운드 루프 안전 정지 (보유 포지션 유지) |
| `POST` | `/api/v1/trading/kill-switch` | **비상 전체 청산 및 정지** | 봇 즉시 중단 후 보유 종목 전량 시장가 매도 청산 |
| `POST` | `/api/v1/trading/reset-paper` | **가상 매매 계좌 초기화** | PAPER 모드 가상 예수금 리셋 (기본 1,000만 원) |
| `GET` | `/api/v1/account/balance` | 잔고 및 보유 종목 조회 | PAPER: 가상 장부 반환 / LIVE: 나무증권 실계좌 조회 |
| `GET` | `/api/v1/market/quote/{ticker}` | 특정 종목 현재가 시세 조회 | 나무증권 REST API 실시간 시세 반환 |
| `POST` | `/api/v1/orders/manual` | 수동 주문 발주 | 종목, 수량, 단가(지정가/시장가), PAPER/LIVE 분기 |
| `GET` | `/api/v1/orders/history` | 주문 및 체결 내역 조회 | DB 체결 목록 반환 (모드별 필터링) |
| `WS` | `/api/v1/ws/stream` | 실시간 체결가 웹소켓 스트림 | 프론트엔드 대시보드 브로드캐스팅 |

---

## 5. 데이터베이스 스키마 (data/trades.db)

가상 매매(`PAPER`)와 실거래(`LIVE`) 데이터를 `trading_mode` 컬럼으로 명확히 분리 격리함:

```sql
-- 1. 주문 테이블
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

-- 2. 체결 테이블
CREATE TABLE IF NOT EXISTS executions (
    exec_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    trading_mode TEXT NOT NULL,      -- 'PAPER', 'MOCK', 'LIVE'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    exec_price INTEGER NOT NULL,
    exec_qty INTEGER NOT NULL,
    fee INTEGER DEFAULT 0,
    tax INTEGER DEFAULT 0,
    FOREIGN KEY(order_id) REFERENCES orders(order_id)
);

-- 3. 일별 스냅샷 테이블
CREATE TABLE IF NOT EXISTS daily_snapshots (
    date TEXT NOT NULL,              -- YYYY-MM-DD
    trading_mode TEXT NOT NULL,      -- 'PAPER', 'MOCK', 'LIVE'
    total_asset INTEGER NOT NULL,
    deposit INTEGER NOT NULL,
    realized_pnl INTEGER NOT NULL,
    return_rate REAL NOT NULL,
    PRIMARY KEY(date, trading_mode)
);
```

---

## 6. 개발 마일스톤 (WBS)

1. **Phase 1: 가상 매매 엔진 & FastAPI 구축 (완료)**
   - `src/paper_trader.py`, `src/nh_trader.py`, `src/main.py` 구현
   - Swagger UI(`/docs`)를 통한 시세 조회, 가상 주문, 봇 제어 인터페이스 검증
2. **Phase 2: 2주간 가상 매매 안정화 및 전략 튜닝 (진행 예정)**
   - 정규장(09:00~15:30) 동안 10영업일 연속 백그라운드 운용
   - 승률, 손익비, MDD 검증 및 에러율 0% 달성
3. **Phase 3: 나무증권 모의투자(`MOCK`) 서버 연동**
   - `moapi.nhplug.com:8443` 모의계좌 연동으로 증권사 시스템 주문 체결 정합성 확인
4. **Phase 4: 소액 실전 매매(`Micro Live`) 전환**
   - 원금의 5~10% 또는 1주 단위로 실전 주문 발주 검증
5. **Phase 5: 정규 실전 매매(`Full Live`) 및 무인 관제**
   - 최종 승격 기준 통과 후 정규 자금 운용 및 텔레그램 실시간 알림 연동
