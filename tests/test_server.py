"""FastAPI Uvicorn 서버 라이프사이클 및 엔드포인트 통합 검증 스크립트."""

import subprocess
import time
import urllib.request
import json
import sys


def run_integration_test():
    print("[1] Uvicorn 서버 백그라운드 구동 중 (포트 8000)...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.main:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        # 서버 준비 대기 (최대 5초)
        server_ready = False
        for _ in range(10):
            time.sleep(0.5)
            try:
                with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=2) as res:
                    if res.status == 200:
                        data = json.loads(res.read().decode("utf-8"))
                        print("[2] 헬스체크 성공:", data)
                        server_ready = True
                        break
            except Exception:
                pass

        if not server_ready:
            print("[ERROR] 서버가 정상적으로 시작되지 않았습니다.")
            stdout, stderr = proc.communicate(timeout=2)
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return False

        # 3. 잔고 조회 테스트
        with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/account/balance", timeout=2) as res:
            balance = json.loads(res.read().decode("utf-8"))
            print("[3] 잔고 조회 성공 (가상 잔고):", balance["summary"]["dnca_tot_amt"], "원")

        # 4. 시세 조회 테스트
        with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/market/quote/005930", timeout=2) as res:
            quote = json.loads(res.read().decode("utf-8"))
            print("[4] 삼성전자 시세 조회 성공:", quote["current_price"], "원")

        # 5. 수동 매수 주문 테스트 (POST)
        order_payload = json.dumps({
            "ticker": "005930",
            "order_type": "BUY",
            "qty": 5,
            "price": 70000
        }).encode("utf-8")

        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/v1/orders/manual",
            data=order_payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=2) as res:
            order_res = json.loads(res.read().decode("utf-8"))
            print("[5] 수동 매수 주문 성공:", order_res["result"]["rsp_msg"])

        # 6. 주문 내역 DB 조회 테스트
        with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/orders/history?limit=5", timeout=2) as res:
            history = json.loads(res.read().decode("utf-8"))
            print(f"[6] 주문 내역 DB 조회 성공: {history['count']}건 저장됨")

        print("\n[SUCCESS] 모든 FastAPI 엔드포인트 통합 검증 완료!")
        return True

    finally:
        print("[7] 테스트 서버 종료 중...")
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    success = run_integration_test()
    sys.exit(0 if success else 1)

