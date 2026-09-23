# -*- coding: utf-8 -*-
"""나무증권(NHPLUG) API 연동 모듈 (실거래 Live / 모의 Mock / 가상 Paper 통합)"""
import logging
import datetime
import os
from typing import Optional, Dict, Any, List, Tuple
from auto_trader.config import settings

logger = logging.getLogger(__name__)

class NamuhAutoTrader:
    """나무증권 OpenAPI 연동 및 매매 집행 엔진"""

    def __init__(self):
        self.is_connected: bool = False
        self.use_real_api: bool = False
        self.account_no: Optional[str] = None
        self.account_type: Optional[str] = None
        self.all_accounts: List[Dict[str, str]] = []
        
        # 가상(Paper) 투자 시뮬레이션용 데이터
        self.paper_capital: int = 10000000
        self.paper_positions: Dict[str, Dict[str, Any]] = {}
        self.order_history: List[Dict[str, Any]] = []

        # 환경변수 초기화
        app_key = settings.NHPLUG_APP_KEY
        app_secret = settings.NHPLUG_APP_SECRET
        
        if not app_key or not app_secret or app_key == "YOUR_APP_KEY_HERE" or app_key == "":
            logger.warning("[NHPLUG] API 키가 설정되지 않아 가상(PAPER) 모드로만 작동합니다.")
            return

        # nhplug 환경변수 세팅
        os.environ['NHPLUG_APP_KEY'] = app_key
        os.environ['NHPLUG_APP_SECRET'] = app_secret
        
        try:
            import nhplug
            self.use_real_api = True
            self.is_connected = True
            logger.info("[NHPLUG] 나무증권 OpenAPI 모듈 로드 성공")
            
            # 계좌 자동 탐색 및 확정
            self.resolve_account()
        except ImportError:
            logger.error("[NHPLUG] 'nhplug' 라이브러리가 설치되지 않았습니다. (pip install nhplug)")
        except Exception as e:
            logger.error(f"[NHPLUG] 계좌 연결 실패: {e}")

    def resolve_account(self):
        """연결된 계좌 목록을 조회하여 운영/모의 모드에 맞는 계좌를 자동 바인딩"""
        if not self.use_real_api:
            return

        import nhplug
        try:
            # 계좌 목록 조회는 항상 LIVE 인증 서버(api.nhplug.com:8443)에서 유효
            os.environ['NHPLUG_BASE_URL'] = 'https://api.nhplug.com:8443'
            data = nhplug.call('/n2/acctinfo', {})
            output = data.get('Output_0', []) if isinstance(data, dict) else []
            self.all_accounts = output

            # .env에 특정 계좌번호가 지정되어 있는 경우 우선 적용
            if settings.NHPLUG_DEFAULT_ACCOUNT:
                target_acc = settings.NHPLUG_DEFAULT_ACCOUNT.strip()
                for acc in output:
                    if acc.get('acct_no') == target_acc:
                        self.account_no = target_acc
                        self.account_type = acc.get('acct_type')
                        logger.info(f"[NHPLUG] 지정된 계좌 바인딩 완료: {self.account_no} (유형: {self.account_type})")
                        return
                # 목록에 없더라도 명시적으로 사용
                self.account_no = target_acc
                self.account_type = "01" if settings.is_live_mode else "03"
                logger.info(f"[NHPLUG] 수동 설정 계좌 적용: {self.account_no}")
                return

            # 자동 탐색: LIVE 모드면 01/02(실거래), MOCK 모드면 03(모의투자)
            if settings.is_live_mode:
                for acc in output:
                    if acc.get('acct_type') in ['01', '02']:
                        self.account_no = acc.get('acct_no')
                        self.account_type = acc.get('acct_type')
                        logger.info(f"[NHPLUG] 실거래(LIVE) 종합매매 계좌 바인딩: {self.account_no}")
                        return

            if settings.is_mock_mode:
                for acc in output:
                    if acc.get('acct_type') == '03':
                        self.account_no = acc.get('acct_no')
                        self.account_type = '03'
                        logger.info(f"[NHPLUG] 모의투자(MOCK) 계좌 바인딩: {self.account_no}")
                        return

            # 기본값으로 첫 계좌 선택
            if output:
                self.account_no = output[0].get('acct_no')
                self.account_type = output[0].get('acct_type')
                logger.info(f"[NHPLUG] 기본 계좌 선택: {self.account_no} (유형: {self.account_type})")
        except Exception as e:
            logger.warning(f"[NHPLUG] 계좌 목록 조회 중 오류 발생: {e}")

    def get_quotes(self, tickers: list) -> list:
        """다중 종목 실시간 시세 조회 (시세는 항상 LIVE 서버 활용)"""
        if self.use_real_api:
            import nhplug
            try:
                # 시세는 항상 안정적인 LIVE 시세 서버 사용
                os.environ['NHPLUG_BASE_URL'] = 'https://api.nhplug.com:8443'
                quotes = []
                for t in tickers:
                    try:
                        data = nhplug.call('/krstock/quote/v1/currentPrice', {'iem_cd': t["symbol"], 'market_cd': 'KRX'})
                        output = data.get('Output_0', {}) if isinstance(data, dict) else {}
                        prpr = output.get('stck_prpr')
                        ctrt = output.get('prdy_ctrt')
                        price_val = int(prpr) if (prpr is not None and str(prpr).strip() != "") else t.get("price", 0)
                        change_val = float(ctrt) if (ctrt is not None and str(ctrt).strip() != "") else 0.0
                        quotes.append({
                            "name": output.get("iem_nm", t["name"]).replace("*", "") if output.get("iem_nm") else t["name"],
                            "symbol": t["symbol"],
                            "price": price_val,
                            "change": change_val
                        })
                    except Exception as e:
                        quotes.append({"name": t.get("name", ""), "symbol": t["symbol"], "price": t.get("price", 0), "change": 0.0})
                return quotes
            except Exception as e:
                logger.error(f"[NHPLUG] 실시간 시세 조회 실패: {e}")
        
        # Fallback
        return tickers

    def get_account_detail(self) -> Dict[str, Any]:
        """계좌 상세 정보 (예수금, 총평가금액, 출금가능금액 등) 조회"""
        if not self.use_real_api or settings.TRADING_MODE.upper() == "PAPER":
            # 보유 주식 평가금액 합산 (현재가 기준)
            stock_eval = sum(
                pos.get("current_price", pos.get("buy_price", 0)) * pos.get("qty", 0)
                for pos in self.paper_positions.values()
                if pos.get("qty", 0) > 0
            )
            total = self.paper_capital + stock_eval  # 현금 + 주식 평가액
            stock_pnl = sum(
                (pos.get("current_price", pos.get("buy_price", 0)) - pos.get("buy_price", 0)) * pos.get("qty", 0)
                for pos in self.paper_positions.values()
                if pos.get("qty", 0) > 0
            )
            profit_rate = round((stock_pnl / (total - stock_pnl) * 100), 2) if (total - stock_pnl) > 0 else 0.0
            return {
                "account_no": "가상계좌 (시뮬레이터)",
                "account_type": "PAPER",
                "trading_mode": "PAPER",
                "cash": self.paper_capital,
                "total_assets": self.paper_capital,
                "withdrawable": self.paper_capital,
                "profit_rate": 0.0,
                "cash": self.paper_capital,          # 가용 현금 (주문 가능 금액)
                "total_assets": total,               # 총 자산 = 현금 + 주식 평가액
                "withdrawable": self.paper_capital,  # 출금 가능 = 현금만
                "stock_eval": stock_eval,            # 주식 평가금액
                "profit_rate": profit_rate,
                "message": "자체 가상 시뮬레이션 계좌입니다."
            }


        import nhplug
        try:
            # LIVE vs MOCK URL 설정
            if settings.is_live_mode:
                os.environ['NHPLUG_BASE_URL'] = 'https://api.nhplug.com:8443'
            else:
                os.environ['NHPLUG_BASE_URL'] = 'https://moapi.nhplug.com:8443'

            if not self.account_no:
                self.resolve_account()

            payload = {
                "act_no": self.account_no,
                "bnc_bse_cd": "5",       # 현재가 기준
                "ltg_aot_dit_cd": "1",   # 상장 종목
                "aet_bse": "2",          # 총자산
                "qut_dit_cd": "KRX",     # KRX 시세
                "aly_qut_cd": "1"        # 정규장
            }

            res = nhplug.call('/krstock/inquiry/v1/balance', payload)
            out0 = res.get('Output_0', {}) if isinstance(res, dict) else {}
            rsp_cd, rsp_msg = nhplug.status_of(res)

            cash = int(out0.get('dca') or 0)                     # 예수금
            tot_assets = int(out0.get('tot_aet_amt') or 0)       # 총평가금액
            withdrawable = int(out0.get('drn_pbl_amt') or 0)     # 출금가능금액
            pft_rt = float(out0.get('pft_rt') or 0.0)           # 수익률

            return {
                "account_no": self.account_no,
                "account_type": self.account_type,
                "trading_mode": settings.TRADING_MODE.upper(),
                "cash": cash,
                "total_assets": tot_assets,
                "withdrawable": withdrawable,
                "profit_rate": pft_rt,
                "rsp_cd": rsp_cd,
                "message": rsp_msg
            }
        except Exception as e:
            logger.error(f"[NHPLUG] 계좌 잔고 조회 실패: {e}")
            return {
                "account_no": self.account_no or "조회실패",
                "account_type": self.account_type or "ERR",
                "trading_mode": settings.TRADING_MODE.upper(),
                "cash": 0,
                "total_assets": 0,
                "withdrawable": 0,
                "profit_rate": 0.0,
                "message": str(e)
            }

    def get_balance(self) -> int:
        """현재 매매에 사용 가능한 계좌 잔고 (예수금/가용현금) 반환"""
        detail = self.get_account_detail()
        cash = detail.get("cash", 0)
        # 만약 LIVE/MOCK 계좌의 예수금이 0원이고 총자산이 있으면 총자산 표시, 아니면 예수금
        if cash > 0:
            return cash
        tot = detail.get("total_assets", 0)
        return tot if tot > 0 else cash

    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """보유 종목 현황 조회"""
        if not self.use_real_api or settings.TRADING_MODE.upper() == "PAPER":
            return self.paper_positions

        import nhplug
        try:
            if settings.is_live_mode:
                os.environ['NHPLUG_BASE_URL'] = 'https://api.nhplug.com:8443'
            else:
                os.environ['NHPLUG_BASE_URL'] = 'https://moapi.nhplug.com:8443'

            if not self.account_no:
                self.resolve_account()

            payload = {
                "act_no": self.account_no,
                "bnc_bse_cd": "5",
                "ltg_aot_dit_cd": "1",
                "aet_bse": "2",
                "qut_dit_cd": "KRX",
                "aly_qut_cd": "1"
            }

            res = nhplug.call('/krstock/inquiry/v1/balance', payload)
            out1 = res.get('Output_1', []) if isinstance(res, dict) else []

            positions = {}
            for item in out1:
                sym = item.get("iem_cd", "").strip()
                if not sym:
                    continue
                qty = int(item.get("hldg_qty") or 0)
                if qty > 0:
                    positions[sym] = {
                        "symbol": sym,
                        "name": item.get("iem_nm", "").strip(),
                        "qty": qty,
                        "buy_price": float(item.get("by_uv") or 0),
                        "current_price": float(item.get("now_pr") or 0),
                        "eval_amt": int(item.get("evl_amt") or 0),
                        "eval_profit": int(item.get("evl_pfl_amt") or 0),
                        "profit_rate": float(item.get("pft_rt") or 0.0)
                    }
            return positions
        except Exception as e:
            logger.error(f"[NHPLUG] 보유 종목 조회 실패: {e}")
            return {}

    def order_buy(self, symbol: str, price: int, qty: int, order_type: str = "LIMIT") -> Tuple[bool, str, str]:
        """
        주식 매수 주문 실행
        :return: (성공여부, 주문번호/코드, 처리결과메시지)
        """
        if qty <= 0:
            return False, "INVALID_QTY", "주문 수량은 1주 이상이어야 합니다."

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. LIVE (실전 투자 모드)
        if settings.is_live_mode:
            # 안전장치 검증: CONFIRM_REAL_TRADING 확인
            if not settings.is_real_trading_confirmed:
                msg = "⚠️ [실거래 안전 잠금] 실거래(LIVE) 모드이나 CONFIRM_REAL_TRADING=true가 설정되지 않아 주문이 차단되었습니다."
                logger.error(f"[NHPLUG ORDER] {msg}")
                return False, "SAFETY_LOCKED", msg

            if not self.use_real_api or not self.account_no:
                return False, "NO_ACCOUNT", "나무증권 계좌가 연결되지 않았습니다."

            import nhplug
            os.environ['NHPLUG_BASE_URL'] = 'https://api.nhplug.com:8443'

            payload = {
                "act_no": self.account_no,
                "iem_cd": symbol,
                "orr_qty": qty,
                "nmn_pr_tp_cd": "01" if order_type.upper() == "LIMIT" else "05",  # 01 보통가(지정가), 05 시장가
                "orr_cnd_dit_cd": "00",                                            # 00 없음
                "ssl_nmn_pr_dit_cd": "00",                                        # 00 정상
                "rmt_mkt_cd": "KRX",
                "sor_mkt_sli_yn": "N"
            }
            if order_type.upper() == "LIMIT":
                payload["orr_pr"] = price

            try:
                res = nhplug.call('/krstock/order/v1/cashBuy', payload)
                rsp_cd, rsp_msg = nhplug.status_of(res)
                out0 = res.get('Output_0', {}) if isinstance(res, dict) else {}
                order_no = out0.get('mkt_orr_no') or out0.get('anw_cld_mkt_orr_no1') or "ORD_LIVE"

                is_ok = rsp_cd in ["00000", "00166", "00221"]
                full_msg = f"🔴 [실거래 매수 성공] {rsp_msg} (주문번호: {order_no})" if is_ok else f"⚠️ [나무증권 거부] {rsp_msg} (코드: {rsp_cd})"
                
                self.order_history.insert(0, {
                    "time": now_str, "type": "BUY", "mode": "LIVE", "symbol": symbol,
                    "price": price, "qty": qty, "order_no": order_no, "status": "SUCCESS" if is_ok else "REJECTED",
                    "msg": rsp_msg
                })
                return is_ok, str(order_no), full_msg
            except Exception as e:
                err_msg = f"실거래 주문 전송 실패: {e}"
                logger.error(f"[NHPLUG ORDER] {err_msg}")
                return False, "API_ERROR", err_msg

        # 2. MOCK (증권사 모의투자 서버 모드)
        elif settings.is_mock_mode:
            if not self.use_real_api or not self.account_no:
                return False, "NO_ACCOUNT", "모의투자 계좌가 연결되지 않았습니다."

            import nhplug
            os.environ['NHPLUG_BASE_URL'] = 'https://moapi.nhplug.com:8443'

            payload = {
                "act_no": self.account_no,
                "iem_cd": symbol,
                "orr_qty": qty,
                "nmn_pr_tp_cd": "01" if order_type.upper() == "LIMIT" else "05",
                "orr_cnd_dit_cd": "00",
                "ssl_nmn_pr_dit_cd": "00",
                "rmt_mkt_cd": "KRX",
                "sor_mkt_sli_yn": "N"
            }
            if order_type.upper() == "LIMIT":
                payload["orr_pr"] = price

            try:
                res = nhplug.call('/krstock/order/v1/cashBuy', payload)
                rsp_cd, rsp_msg = nhplug.status_of(res)
                out0 = res.get('Output_0', {}) if isinstance(res, dict) else {}
                order_no = out0.get('mkt_orr_no') or out0.get('anw_cld_mkt_orr_no1') or "MOCK_ORD"

                is_ok = rsp_cd in ["00000", "00166", "00221"]
                full_msg = f"🟢 [모의투자 매수 접수] {rsp_msg} (주문번호: {order_no})" if is_ok else f"⚠️ [모의투자 거부] {rsp_msg} (코드: {rsp_cd})"
                
                self.order_history.insert(0, {
                    "time": now_str, "type": "BUY", "mode": "MOCK", "symbol": symbol,
                    "price": price, "qty": qty, "order_no": order_no, "status": "SUCCESS" if is_ok else "REJECTED",
                    "msg": rsp_msg
                })
                return is_ok, str(order_no), full_msg
            except Exception as e:
                err_msg = f"모의투자 주문 전송 실패: {e}"
                logger.error(f"[NHPLUG MOCK] {err_msg}")
                return False, "API_ERROR", err_msg

        # 3. PAPER (자체 가상 시뮬레이션 모드)
        else:
            cost = price * qty if price > 0 else 0
            if self.paper_capital < cost:
                return False, "INSUFFICIENT_FUNDS", f"가상 계좌 잔고 부족 (필요: {cost:,}원 / 보유: {self.paper_capital:,}원)"

            self.paper_capital -= cost
            current_held = self.paper_positions.get(symbol, {}).get("qty", 0)
            self.paper_positions[symbol] = {
                "symbol": symbol,
                "name": symbol,
                "qty": current_held + qty,
                "buy_price": price,
                "current_price": price,
                "eval_amt": price * (current_held + qty)
            }
            order_no = f"SIM_{datetime.datetime.now().strftime('%H%M%S')}"
            msg = f"⚪ [가상 매수 체결] {symbol} {qty}주 체결 완료 (가상잔고: {self.paper_capital:,}원)"
            
            self.order_history.insert(0, {
                "time": now_str, "type": "BUY", "mode": "PAPER", "symbol": symbol,
                "price": price, "qty": qty, "order_no": order_no, "status": "SUCCESS", "msg": msg
            })
            return True, order_no, msg

    def order_sell(self, symbol: str, price: int, qty: int, order_type: str = "LIMIT") -> Tuple[bool, str, str]:
        """
        주식 매도 주문 실행
        :return: (성공여부, 주문번호/코드, 처리결과메시지)
        """
        if qty <= 0:
            return False, "INVALID_QTY", "주문 수량은 1주 이상이어야 합니다."

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. LIVE (실전 매도)
        if settings.is_live_mode:
            if not settings.is_real_trading_confirmed:
                msg = "⚠️ [실거래 안전 잠금] CONFIRM_REAL_TRADING=true가 설정되지 않아 실전 매도가 차단되었습니다."
                return False, "SAFETY_LOCKED", msg

            if not self.use_real_api or not self.account_no:
                return False, "NO_ACCOUNT", "나무증권 계좌가 연결되지 않았습니다."

            import nhplug
            os.environ['NHPLUG_BASE_URL'] = 'https://api.nhplug.com:8443'

            payload = {
                "act_no": self.account_no,
                "iem_cd": symbol,
                "orr_qty": qty,
                "nmn_pr_tp_cd": "01" if order_type.upper() == "LIMIT" else "05",
                "orr_cnd_dit_cd": "00",
                "ssl_nmn_pr_dit_cd": "00",
                "rmt_mkt_cd": "KRX",
                "sor_mkt_sli_yn": "N"
            }
            if order_type.upper() == "LIMIT":
                payload["orr_pr"] = price

            try:
                res = nhplug.call('/krstock/order/v1/cashSell', payload)
                rsp_cd, rsp_msg = nhplug.status_of(res)
                out0 = res.get('Output_0', {}) if isinstance(res, dict) else {}
                order_no = out0.get('mkt_orr_no') or out0.get('anw_cld_mkt_orr_no1') or "ORD_LIVE_SELL"

                is_ok = rsp_cd in ["00000", "00166", "00221"]
                full_msg = f"🔴 [실거래 매도 성공] {rsp_msg} (주문번호: {order_no})" if is_ok else f"⚠️ [나무증권 거부] {rsp_msg} (코드: {rsp_cd})"

                self.order_history.insert(0, {
                    "time": now_str, "type": "SELL", "mode": "LIVE", "symbol": symbol,
                    "price": price, "qty": qty, "order_no": order_no, "status": "SUCCESS" if is_ok else "REJECTED",
                    "msg": rsp_msg
                })
                return is_ok, str(order_no), full_msg
            except Exception as e:
                err_msg = f"실거래 매도 전송 실패: {e}"
                return False, "API_ERROR", err_msg

        # 2. MOCK (모의투자 매도)
        elif settings.is_mock_mode:
            if not self.use_real_api or not self.account_no:
                return False, "NO_ACCOUNT", "모의투자 계좌가 연결되지 않았습니다."

            import nhplug
            os.environ['NHPLUG_BASE_URL'] = 'https://moapi.nhplug.com:8443'

            payload = {
                "act_no": self.account_no,
                "iem_cd": symbol,
                "orr_qty": qty,
                "nmn_pr_tp_cd": "01" if order_type.upper() == "LIMIT" else "05",
                "orr_cnd_dit_cd": "00",
                "ssl_nmn_pr_dit_cd": "00",
                "rmt_mkt_cd": "KRX",
                "sor_mkt_sli_yn": "N"
            }
            if order_type.upper() == "LIMIT":
                payload["orr_pr"] = price

            try:
                res = nhplug.call('/krstock/order/v1/cashSell', payload)
                rsp_cd, rsp_msg = nhplug.status_of(res)
                out0 = res.get('Output_0', {}) if isinstance(res, dict) else {}
                order_no = out0.get('mkt_orr_no') or out0.get('anw_cld_mkt_orr_no1') or "MOCK_SELL"

                is_ok = rsp_cd in ["00000", "00166", "00221"]
                full_msg = f"🟢 [모의투자 매도 접수] {rsp_msg} (주문번호: {order_no})" if is_ok else f"⚠️ [모의투자 거부] {rsp_msg} (코드: {rsp_cd})"

                self.order_history.insert(0, {
                    "time": now_str, "type": "SELL", "mode": "MOCK", "symbol": symbol,
                    "price": price, "qty": qty, "order_no": order_no, "status": "SUCCESS" if is_ok else "REJECTED",
                    "msg": rsp_msg
                })
                return is_ok, str(order_no), full_msg
            except Exception as e:
                return False, "API_ERROR", str(e)

        # 3. PAPER (가상 매도)
        else:
            held = self.paper_positions.get(symbol, {}).get("qty", 0)
            if held < qty:
                return False, "INSUFFICIENT_QTY", f"보유 수량 부족 (보유: {held}주 / 요청: {qty}주)"

            revenue = price * qty
            self.paper_capital += revenue
            if held == qty:
                del self.paper_positions[symbol]
            else:
                self.paper_positions[symbol]["qty"] -= qty
                self.paper_positions[symbol]["eval_amt"] = self.paper_positions[symbol]["qty"] * price

            order_no = f"SIM_S_{datetime.datetime.now().strftime('%H%M%S')}"
            msg = f"⚪ [가상 매도 체결] {symbol} {qty}주 체결 완료 (가상잔고: {self.paper_capital:,}원)"
            self.order_history.insert(0, {
                "time": now_str, "type": "SELL", "mode": "PAPER", "symbol": symbol,
                "price": price, "qty": qty, "order_no": order_no, "status": "SUCCESS", "msg": msg
            })
            return True, order_no, msg

    def buy_market(self, symbol: str, qty: int) -> Tuple[bool, str]:
        """시장가 매수 편의 메서드"""
        ok, ord_id, msg = self.order_buy(symbol=symbol, price=0, qty=qty, order_type="MARKET")
        return ok, ord_id

    def sell_market(self, symbol: str, qty: int) -> Tuple[bool, str]:
        """시장가 매도 편의 메서드"""
        ok, ord_id, msg = self.order_sell(symbol=symbol, price=0, qty=qty, order_type="MARKET")
        return ok, ord_id

    def modify_order(self, order_id: str, new_price: int, new_qty: int) -> Tuple[bool, str]:
        """미체결 주문 정정"""
        return True, f"modified_{order_id}"

    def cancel_order(self, order_id: str) -> Tuple[bool, str]:
        """미체결 주문 취소"""
        return True, f"canceled_{order_id}"
