# SPARK Plan: 거래 근거(Rationale) 팝업 모달 구현

## 작업 체크리스트
- [x] SQLite DB 스키마 업데이트 (`positions`에 `buy_reason`, `closed_trades`에 `buy_reason`, `sell_reason` 추가)
- [x] DB 액세스 계층 (`auto_trader/database.py`) 업데이트
- [x] 트레이더 주문 계층 (`auto_trader/nh_trader.py`) 업데이트
- [x] 자동매매봇 루프 (`auto_trader/bot.py`)에서 5대 단타 기법 진입/청산 사유 전달
- [x] 백엔드 API (`auto_trader/main.py`)에서 `buy_reason`, `sell_reason` 반환
- [x] 프론트엔드 HTML (`auto_trader/static/index.html`)에 `#trade-reason-modal` 모달 추가
- [x] 프론트엔드 JS (`auto_trader/static/script.js`)에 `[근거]` 버튼 렌더링 및 모달 팝업 로직 구현
- [x] 파이썬 모듈 무결성 및 구동 테스트 검증
