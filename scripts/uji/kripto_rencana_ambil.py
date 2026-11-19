import json,urllib.request,time,sys,os
coins=[c["t"] for c in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "kripto", "data", "coins.json")))["coins"]]
print(len(coins))
for t in coins:
    sym=t+"USDT"; rows=[]; start=int(time.mktime((2020,1,1,0,0,0,0,0,0)))*1000
    try:
        while True:
            u=f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval=1d&limit=1000&startTime={start}"
            d=json.load(urllib.request.urlopen(u,timeout=30))
            if not d: break
            rows+=[[time.strftime("%Y-%m-%d",time.gmtime(k[0]/1000)),float(k[1]),float(k[2]),float(k[3]),float(k[4])] for k in d]
            start=d[-1][0]+86400000
            if len(d)<1000: break
    except Exception as e: print(t,"ERR",e); continue
    json.dump(rows[:-1],open(f"ohlc/{t}.json","w")); print(t,len(rows),rows[0][0] if rows else "-")
