# SPARK Plan: 나무증권(NHPLUG) 실거래(Live Trading) 구현 계획

## 1. 목표
가상 투자(PAPER)로 동작하던 주식 자동매매 시스템을 나무증권 OpenAPI 실서버(LIVE) 및 모의서버(MOCK)와 연동하여 실제 계좌 잔고 조회, 보유 종목 동기화, 실제 주식 매수/매도 주문이 가능한 실거래 시스템으로 완성한다.

---

## 2. 세부 실행 단계
- [x] **1단계: NH PLUG OpenAPI 규격 및 엔드포인트 실증 분석**
  - 토큰 발급 및 `/n2/acctinfo` 계좌 목록 확인 (실계좌 `21001461419`, 모의계좌 `50071004971`)
  - 잔고 조회 API (`/krstock/inquiry/v1/balance`) 및 주문 API (`/krstock/order/v1/cashBuy`, `/krstock/order/v1/cashSell`) 매개변수 검증
- [ ] **2단계: 설정 및 환경변수 확장 (`auto_trader/config.py`, `.env`)**
  - `TRADING_MODE` (LIVE / MOCK / PAPER) 및 `CONFIRM_REAL_TRADING` (true/false) 지원
  - `NHPLUG_DEFAULT_ACCOUNT` 명시적 지정 및 자동 탐색 로직
- [ ] **3단계: 나무증권 트레이더 모듈 구현 (`auto_trader/nh_trader.py`)**
  - `get_accounts()`, `get_balance()`, `get_positions()` 실시간 연동
  - `order_buy()`, `order_sell()`, `buy_market()`, `sell_market()` 구현
  - 2중 안전 장치 (CONFIRM_REAL_TRADING 검증 실패 시 주문 차단)
- [ ] **4단계: 백엔드 API 라우트 연동 및 에러 핸들링 (`auto_trader/main.py`)**
  - 계좌 잔고 API에 실계좌 정보 및 안전 락 상태 반환
  - 주문 접수 API에서 실거래 결과 메시지 및 시장주문번호 반환
- [ ] **5단계: 프론트엔드 실거래 대시보드 및 확인 모달 강화 (`script.js`, `index.html`)**
  - 실거래 계좌 배지 및 계좌번호 표기
  - LIVE 모드 시 2차 주문 확인 팝업 모달 제공
  - 추천 종목 즉시 매수 발주 기능 연동
- [ ] **6단계: 통합 검증 및 결과 안내**
  - 서버 구동 및 동작 확인, 가이드 작성

