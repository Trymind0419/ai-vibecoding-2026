# SPARK Plan: 매매 거래일지 스크롤 & 상세 카드 UI 개선

## 작업 체크리스트
- [x] DB 내 기존 거래일지 종목명(name)을 한글 기업명으로 마이그레이션 (`삼성전자`, `두산에너빌리티` 등)
- [x] `#closed-trades-list` 컨테이너 스크롤 높이 확장 (220px -> 350px) ([index.html](file:///d:/SourceBank/ai-vibecoding-2026/auto_trader/static/index.html))
- [x] 전용 커스텀 스크롤바 CSS 적용 ([style.css](file:///d:/SourceBank/ai-vibecoding-2026/auto_trader/static/style.css))
- [x] 프론트엔드 거래일지 API 요청 수량 확장 (`limit=50`) ([script.js](file:///d:/SourceBank/ai-vibecoding-2026/auto_trader/static/script.js))
- [x] 기업명 메인 표시 + 매수가/매도가/수량/총금액/수익·손실률 2단 카드 레이아웃 구현 ([script.js](file:///d:/SourceBank/ai-vibecoding-2026/auto_trader/static/script.js))
- [x] 브라우저 캐시 버스팅 (`script.js?v=9.2`) 및 동작 검증 완료
