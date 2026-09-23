import urllib.request
import json

req = urllib.request.urlopen('http://127.0.0.1:8008/api/v1/market/ticker-tape')
data = json.loads(req.read())

for i, t in enumerate(data['tickers']):
    sign = "+" if t['change'] > 0 else ""
    print(f"{i+1}. {t['name']} ({t['symbol']}): {t['price']:,} 원 ({sign}{t['change']}%)")

