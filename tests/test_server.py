"""FastAPI Uvicorn ?œë²„ ?¼ì´?„ì‚¬?´í´ ë°??”ë“œ?¬ì¸???µí•© ê²€ì¦??¤í¬ë¦½íŠ¸."""

import subprocess
import time
import urllib.request
import json
import sys


def run_integration_test():
    print("[1] Uvicorn ?œë²„ ë°±ê·¸?¼ìš´??êµ¬ë™ ì¤?(?¬íŠ¸ 8000)...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "auto_trader.main:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        # ?œë²„ ì¤€ë¹??€ê¸?(ìµœë? 5ì´?
        server_ready = False
        for _ in range(10):
            time.sleep(0.5)
            try:
                with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=2) as res:
                    if res.status == 200:
                        data = json.loads(res.read().decode("utf-8"))
                        print("[2] ?¬ìŠ¤ì²´í¬ ?±ê³µ:", data)
                        server_ready = True
                        break
            except Exception:
                pass

        if not server_ready:
            print("[ERROR] ?œë²„ê°€ ?•ìƒ?ìœ¼ë¡??œì‘?˜ì? ?Šì•˜?µë‹ˆ??")
            stdout, stderr = proc.communicate(timeout=2)
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return False

        # 3. ?”ê³  ì¡°íšŒ ?ŒìŠ¤??        with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/account/balance", timeout=2) as res:
            balance = json.loads(res.read().decode("utf-8"))
            print("[3] ?”ê³  ì¡°íšŒ ?±ê³µ (ê°€???”ê³ ):", balance["summary"]["dnca_tot_amt"], "??)

        # 4. ?œì„¸ ì¡°íšŒ ?ŒìŠ¤??        with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/market/quote/005930", timeout=2) as res:
            quote = json.loads(res.read().decode("utf-8"))
            print("[4] ?¼ì„±?„ì ?œì„¸ ì¡°íšŒ ?±ê³µ:", quote["current_price"], "??)

        # 5. ?˜ë™ ë§¤ìˆ˜ ì£¼ë¬¸ ?ŒìŠ¤??(POST)
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
            print("[5] ?˜ë™ ë§¤ìˆ˜ ì£¼ë¬¸ ?±ê³µ:", order_res["result"]["rsp_msg"])

        # 6. ì£¼ë¬¸ ?´ì—­ DB ì¡°íšŒ ?ŒìŠ¤??        with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/orders/history?limit=5", timeout=2) as res:
            history = json.loads(res.read().decode("utf-8"))
            print(f"[6] ì£¼ë¬¸ ?´ì—­ DB ì¡°íšŒ ?±ê³µ: {history['count']}ê±??€?¥ë¨")

        print("\n[SUCCESS] ëª¨ë“  FastAPI ?”ë“œ?¬ì¸???µí•© ê²€ì¦??„ë£Œ!")
        return True

    finally:
        print("[7] ?ŒìŠ¤???œë²„ ì¢…ë£Œ ì¤?..")
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    success = run_integration_test()
    sys.exit(0 if success else 1)

