# SPARK Spec: 나무증권(NH투자증권) 실거래(Live Trading) 연동 명세서

## 1. 개요
본 문서는 나무증권 Namuh PLUG OpenAPI를 활용하여 주식 가상(Paper) 매매에서 실제 자산이 거래되는 실거래(Live Trading) 및 모의투자(Mock Trading)로 안전하게 전환하고 실행할 수 있는 시스템 아키텍처 및 세부 기능 명세를 정의한다.

---

## 2. 모드 구분 및 동작 원칙
| 모드 (TRADING_MODE) | BASE_URL | 계좌 유형 (acct_type) | 주문 API 동작 | 목적 |
| :--- | :--- | :--- | :--- | :--- |
| **LIVE** (실전) | `https://api.nhplug.com:8443` | `01` / `02` (실거래 종합매매) | `/krstock/order/v1/cashBuy`<br>`/krstock/order/v1/cashSell` | 실제 돈으로 주식 매수/매도 |
| **MOCK** (모의) | `https://moapi.nhplug.com:8443` | `03` (모의투자 계좌) | `/krstock/order/v1/cashBuy` (모의) | 증권사 모의 서버 검증 |
| **PAPER** (가상) | `https://api.nhplug.com:8443` (시세만 실시간) | 가상 메모리 계좌 | 자체 시뮬레이션 | UI/전략 무위험 테스트 |

---

## 3. 핵심 안전 장치 (Safety Guards)
1. **2중 잠금 환경변수 검증**:
   - `TRADING_MODE=LIVE`와 함께 `CONFIRM_REAL_TRADING=true`가 명시적으로 설정되어야만 실거래 주문이 허용된다. 둘 중 하나라도 불일치하면 주문이 즉시 차단되고 에러 메시지를 반환한다.
2. **UI 2차 확인 모달 (Confirmation Modal)**:
   - 프론트엔드에서 실거래 모드 감지 시, 매수/매도 버튼 클릭 시 계좌번호, 종목명, 주문수량, 총 소요 원화 금액을 표시하는 경고 팝업을 띄워 사용자 승인을 획득한다.
3. **주문 파라미터 정밀 검증**:
   - 최소 주문 수량 (1주 이상) 및 양수 가격 검증
   - 증권사 수수료 및 유관기관 제비용 고려
   - 장 운영 시간 외 거부 코드 처리 (예: `14580` 장종료 등)

---

## 4. OpenAPI 규격 (NH PLUG)
1. **계좌 목록 조회**:
   - 엔드포인트: `POST /n2/acctinfo`
   - 페이로드: `Input_0: {}`
   - 응답: `Output_0` 내 `[{ "acct_no": "...", "acct_type": "01" | "03" }]`
2. **실시간 계좌 잔고 및 보유 종목**:
   - 엔드포인트: `POST /krstock/inquiry/v1/balance`
   - 페이로드:
     ```json
     {
       "Input_0": {
         "act_no": "21001461419",
         "bnc_bse_cd": "5",
         "ltg_aot_dit_cd": "1",
         "aet_bse": "2",
         "qut_dit_cd": "KRX",
         "aly_qut_cd": "1"
       }
     }
     ```
   - 응답:
     - `Output_0`: 예수금(`dca`), 총평가금액(`tot_aet_amt`), 출금가능금액(`drn_pbl_amt`)
     - `Output_1`: 보유 종목 리스트(`iem_cd`, `iem_nm`, `hldg_qty`, `by_uv`, `now_pr`, `pft_rt`)
3. **현금 매수 주문**:
   - 엔드포인트: `POST /krstock/order/v1/cashBuy`
   - 페이로드:
     ```json
     {
       "Input_0": {
         "act_no": "21001461419",
         "iem_cd": "005930",
         "orr_qty": 1,
         "orr_pr": 70000,
         "nmn_pr_tp_cd": "01",
         "orr_cnd_dit_cd": "00",
         "ssl_nmn_pr_dit_cd": "00",
         "rmt_mkt_cd": "KRX",
         "sor_mkt_sli_yn": "N"
       }
     }
     ```
4. **현금 매도 주문**:
   - 엔드포인트: `POST /krstock/order/v1/cashSell`
   - 페이로드 규격: 매수와 동일 구조 (`act_no`, `iem_cd`, `orr_qty`, `orr_pr`, `nmn_pr_tp_cd`, `rmt_mkt_cd`, `sor_mkt_sli_yn` 등)

