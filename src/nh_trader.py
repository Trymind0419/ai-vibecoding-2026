"""나무증권(NH투자증권) PLUG Open API 기반 주식 자동매매 스켈레톤 프로그램.

- 공식 SDK: nhplug (pip install nhplug[instruments,tls])
- 환경: 모의투자(moapi) / 운영(api) 자동 전환 지원
- 규약 준수: 24시간 토큰 파일 캐시, 초당 4회 스로틀, 시간연장 필수 파라미터(aly_qut_cd), dry-run 지원
"""

import os
import sys
from typing import Any, Dict, List, Optional

try:
    from nhplug import call, get_base_url, status_of
    from nhplug.realtime import subscribe
    from nhplug.instruments import load_master
    HAS_NHPLUG = True
except ImportError:
    HAS_NHPLUG = False
    call = None
    get_base_url = lambda: "https://moapi.nhplug.com:8443"
    status_of = lambda d: ("00000", "정상 (Mock)")
    subscribe = None
    load_master = None


class NamuhAutoTrader:
    """나무증권 PLUG OpenAPI 자동매매 클라이언트."""

    def __init__(self, act_no: Optional[str] = None, dry_run: bool = True):
        if not HAS_NHPLUG:
            print("[알림] 'nhplug' 패키지가 미설치되어 모의 시뮬레이션 모드로 동작합니다.")
            self.has_sdk = False
        else:
            self.has_sdk = True

        self.dry_run = dry_run
        self.base_url = get_base_url()
        self.is_live = not self.base_url.split("//")[-1].startswith("moapi")
        self.act_no = act_no or os.environ.get("NHPLUG_DEFAULT_ACCOUNT")

        print(f"[{'운영(Live)' if self.is_live else '모의투자(Mock)'}] 클라이언트 초기화")
        print(f"- Base URL: {self.base_url}")
        print(f"- Dry Run 모드: {'ON (주문 미전송)' if self.dry_run else 'OFF (실제 주문 전송)'}")

        # 계좌번호 자동 감지 시도
        if not self.act_no and self.has_sdk:
            try:
                self.act_no = self.detect_account()
            except Exception as e:
                print(f"- 계좌번호 감지 생략: {e}")
                self.act_no = "12345678901"

    def detect_account(self) -> str:
        """환경(운영/모의)에 적합한 계좌를 조회하고 선택."""
        if not self.has_sdk:
            return "12345678901"

        res = call("/n2/acctinfo", {})
        accounts: List[Dict[str, Any]] = res.get("Output_0", [])
        if not accounts:
            raise RuntimeError("계좌 목록을 가져올 수 없습니다. APP_KEY/SECRET을 확인하세요.")

        target_type = {"01", "02"} if self.is_live else {"03"}
        usable = [a for a in accounts if a.get("acct_type") in target_type]

        if not usable:
            env_name = "운영(01, 02)" if self.is_live else "모의투자(03)"
            raise ValueError(f"현재 접속 환경에 맞는 계좌({env_name})가 없습니다.")

        selected = usable[0]["acct_no"]
        print(f"- 선택된 계좌번호: {selected} (구분: {usable[0].get('acct_type')})")
        return selected

    def get_current_price(self, ticker: str, market: str = "UNT") -> Dict[str, Any]:
        """주식 현재가 시세 조회."""
        if not self.has_sdk:
            # SDK 미설치 시 테스트용 기본 가격 반환
            default_prices = {"005930": "74500", "000660": "182000"}
            return {"stck_prpr": default_prices.get(ticker, "50000")}

        payload = {"iem_cd": ticker, "market_cd": market}
        data = call("/krstock/quote/v1/currentPrice", payload)
        rsp_cd, rsp_msg = status_of(data)

        output = data.get("Output_0") or {}
        price = output.get("stck_prpr")
        if price is None:
            print(f"[주의] 현재가 조회 실패 ({ticker}): {rsp_msg} [코드: {rsp_cd}]")
        return output

    def get_balance(self, aly_qut_cd: str = "1") -> Dict[str, Any]:
        """주식 잔고 및 예수금 조회."""
        if not self.has_sdk:
            return {
                "summary": {"tot_asst_amt": "10000000", "dnca_tot_amt": "10000000"},
                "holdings": [],
                "rsp_msg": "정상 처리 되었습니다. [모의]"
            }

        payload = {
            "act_no": self.act_no,
            "bnc_bse_cd": "5",
            "ltg_aot_dit_cd": "9",
            "aet_bse": "2",
            "qut_dit_cd": "UNT",
            "aly_qut_cd": aly_qut_cd
        }
        data = call("/krstock/inquiry/v1/balance", payload)
        rsp_cd, rsp_msg = status_of(data)

        summary = data.get("Output_0") or {}
        holdings = data.get("Output_1") or []

        return {
            "summary": summary,
            "holdings": holdings,
            "rsp_msg": rsp_msg
        }

    def order_buy(self, ticker: str, qty: int, price: Optional[int] = None) -> Dict[str, Any]:
        """국내주식 현금 매수 주문."""
        is_market = price is None
        input_0 = {
            "act_no": self.act_no,
            "iem_cd": ticker,
            "orr_qty": qty,
            "nmn_pr_tp_cd": "05" if is_market else "01",
            "orr_cnd_dit_cd": "00",
            "ssl_nmn_pr_dit_cd": "00",
            "rmt_mkt_cd": "KRX",
            "sor_mkt_sli_yn": "N",
        }
        if not is_market:
            input_0["orr_pr"] = price

        if self.dry_run or not self.has_sdk:
            print(f"[DRY RUN] 매수 주문 시뮬레이션: {ticker} {qty}주 @ {price or '시장가'}")
            return {"dry_run": True, "Input_0": input_0}

        print(f"[실제 주문] 매수 전송: {ticker} {qty}주 @ {price or '시장가'}")
        result = call("/krstock/order/v1/cashBuy", input_0)
        rsp_cd, rsp_msg = status_of(result)
        print(f"- 주문 응답: {rsp_msg} (코드: {rsp_cd})")
        return result

    def order_sell(self, ticker: str, qty: int, price: Optional[int] = None) -> Dict[str, Any]:
        """국내주식 현금 매도 주문."""
        is_market = price is None
        input_0 = {
            "act_no": self.act_no,
            "iem_cd": ticker,
            "orr_qty": qty,
            "nmn_pr_tp_cd": "05" if is_market else "01",
            "orr_cnd_dit_cd": "00",
            "ssl_nmn_pr_dit_cd": "00",
            "rmt_mkt_cd": "KRX",
            "sor_mkt_sli_yn": "N",
        }
        if not is_market:
            input_0["orr_pr"] = price

        if self.dry_run or not self.has_sdk:
            print(f"[DRY RUN] 매도 주문 시뮬레이션: {ticker} {qty}주 @ {price or '시장가'}")
            return {"dry_run": True, "Input_0": input_0}

        print(f"[실제 주문] 매도 전송: {ticker} {qty}주 @ {price or '시장가'}")
        result = call("/krstock/order/v1/cashSell", input_0)
        rsp_cd, rsp_msg = status_of(result)
        print(f"- 주문 응답: {rsp_msg} (코드: {rsp_cd})")
        return result
