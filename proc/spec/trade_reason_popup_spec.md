# SPARK Spec: 자동매매 거래 매수 및 매도 근거(Rationale) 팝업 모달

## 1. 개요 및 목적
- **배경**: 자동매매봇이 어떤 기술적 근거(5대 단타 기법 등)와 청산 기준(익절, 손절, 트레일링스탑)으로 매매했는지 사용자가 직관적으로 확인할 수 있도록 기능 제공.
- **목적**: 보유 포지션 및 청산 완료 내역에 `[근거]` 버튼을 배치하고, 클릭 시 상세 근거가 표시되는 팝업 모달을 제공.

---

## 2. 아키텍처 및 데이터 흐름

```
[MasterDayTradingStrategy]
       │ (1. 5대 단타기법 매수 시그널 & 사유 생성)
       ▼
  [TradingBot]
       │ (enter_reason / exit_reason)
       ▼
[NamuhAutoTrader]
       │ (order_buy / order_sell)
       ▼
 [SQLite Database] (auto_trader.db & trades.db)
  - positions: buy_reason, buy_time
  - closed_trades: buy_reason, sell_reason, exit_reason
       │
       ▼
[FastAPI REST API]
  - GET /api/v1/account/portfolio-pnl (buy_reason 포함)
  - GET /api/v1/trades/history (buy_reason, sell_reason 포함)
       │
       ▼
[Frontend UI]
  - 보유 종목 리스트: [근거] 버튼 -> showPositionReason(...)
  - 청산 일지 리스트: [근거] 버튼 -> showClosedTradeReason(...)
  - #trade-reason-modal (모달 팝업 표시)
```

---

## 3. UI/UX 명세
1. **보유 종목 리스트 (`#portfolio-pnl-section`)**:
   - 종목명 우측에 파란색 톤의 `[근거]` 버튼 배치.
   - 클릭 시: 종목명, 보유수량, 매수단가, 현재단가, 평가손익, **AI 실전 단타 매수 근거** 모달 노출.
2. **청산 내역 리스트 (`#closed-trades-list`)**:
   - 청산 종목명 및 청산뱃지 우측에 초록색 톤의 `[근거]` 버튼 배치.
   - 클릭 시: 종목명, 거래수량, 매수단가 -> 매도단가, 실현손익, **진입(매수) 근거**와 **청산(매도) 근거**를 카드형으로 명확히 구분하여 노출.
3. **모달 닫기**:
   - 우측 상단 '✕' 버튼, 배경 오버레이 클릭, 하단 '확인' 버튼 클릭 시 닫힘.
