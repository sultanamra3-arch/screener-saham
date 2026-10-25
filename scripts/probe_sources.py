"""Uji sumber data insider dan kalender dividen (sekali jalan). Hasil: data/probe.json."""
import json, os, time, traceback
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "probe.json"
res = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def run(name, fn):
    t = time.time()
    try:
        res[name] = {"ok": True, **fn()}
    except Exception as e:
        res[name] = {"ok": False, "err": f"{type(e).__name__}: {str(e)[:300]}", "tb": traceback.format_exc()[-600:]}
    res[name]["sec"] = round(time.time() - t, 1)


def finnhub_insider():
    import requests
    key = os.environ.get("FINNHUB_API_KEY", "")
    out = {}
    for t in ("AAPL", "JPM", "KO"):
        r = requests.get("https://finnhub.io/api/v1/stock/insider-transactions", params={"symbol": t, "token": key}, timeout=30)
        j = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        data = j.get("data") or []
        out[t] = {"status": r.status_code, "n": len(data), "sample": data[:3], "msg": None if data else str(j)[:200]}
        time.sleep(1.1)
    r = requests.get("https://finnhub.io/api/v1/stock/insider-sentiment", params={"symbol": "AAPL", "from": "2026-01-01", "to": "2026-10-25", "token": key}, timeout=30)
    out["sentiment"] = {"status": r.status_code, "body": r.text[:400]}
    return out


def yf_insider_us():
    import yfinance as yf
    out = {}
    for t in ("AAPL", "JPM", "KO"):
        df = yf.Ticker(t).insider_transactions
        out[t] = {"n": 0 if df is None else len(df), "cols": [] if df is None else list(map(str, df.columns)),
                  "sample": [] if df is None or df.empty else json.loads(df.head(4).to_json(orient="records", date_format="iso"))}
    return out


def sec_form4():
    import requests
    h = {"User-Agent": "screener-saham research contact sultanamra3-arch@users.noreply.github.com"}
    r = requests.get("https://www.sec.gov/cgi-bin/browse-edgar", params={"action": "getcurrent", "type": "4", "count": "40", "output": "atom"}, headers=h, timeout=30)
    r2 = requests.get("https://data.sec.gov/submissions/CIK0000320193.json", headers=h, timeout=30)
    return {"current_status": r.status_code, "current_len": len(r.text), "current_head": r.text[:300],
            "subm_status": r2.status_code, "subm_len": len(r2.text)}


def yf_insider_id():
    import yfinance as yf
    out = {}
    for t in ("BBCA.JK", "TLKM.JK", "ASII.JK"):
        tk = yf.Ticker(t)
        df = tk.insider_transactions
        mh = tk.major_holders
        out[t] = {"insider_n": 0 if df is None else len(df), "major_holders": None if mh is None else mh.to_dict()}
    return out


def idx_site():
    out = {}
    urls = {
        "home": "https://www.idx.co.id/id",
        "ann_all": "https://www.idx.co.id/primary/NewsAnnouncement/GetAllAnnouncement?keywords=Pemegang%20Saham&pageNumber=1&pageSize=10&dateFrom=&dateTo=&lang=id",
        "ann_list": "https://www.idx.co.id/primary/ListedCompany/GetAnnouncement?kodeEmiten=&emitenType=*&indexFrom=0&pageSize=10&dateFrom=20260901&dateTo=20261025&lang=id&keyword=Pemegang",
        "ksei_home": "https://www.ksei.co.id/",
    }
    import requests
    for k, u in urls.items():
        try:
            r = requests.get(u, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            out[k + "_requests"] = {"status": r.status_code, "len": len(r.text), "head": r.text[:200]}
        except Exception as e:
            out[k + "_requests"] = {"err": str(e)[:200]}
        try:
            from curl_cffi import requests as cr
            r = cr.get(u, timeout=30, impersonate="chrome")
            out[k + "_cffi"] = {"status": r.status_code, "len": len(r.text), "head": r.text[:300]}
        except Exception as e:
            out[k + "_cffi"] = {"err": str(e)[:200]}
    return out


def yf_dividend_cal():
    import yfinance as yf
    out = {}
    for t in ("AAPL", "KO", "JNJ", "BBCA.JK", "BBRI.JK", "TLKM.JK", "ASII.JK", "ITMG.JK", "PTBA.JK", "UNVR.JK"):
        tk = yf.Ticker(t)
        try:
            cal = tk.calendar
        except Exception as e:
            cal = {"err": str(e)[:100]}
        info = tk.info
        dv = tk.dividends
        out[t] = {"calendar": {k: str(v) for k, v in (cal or {}).items()} if isinstance(cal, dict) else str(cal)[:200],
                  "exDividendDate": info.get("exDividendDate"), "dividendRate": info.get("dividendRate"),
                  "lastDividendValue": info.get("lastDividendValue"), "lastDividendDate": info.get("lastDividendDate"),
                  "last_divs": [[str(i.date()), float(v)] for i, v in dv.tail(4).items()] if dv is not None else []}
    return out


def finnhub_div_cal():
    import requests
    key = os.environ.get("FINNHUB_API_KEY", "")
    r = requests.get("https://finnhub.io/api/v1/calendar/dividend", params={"from": "2026-10-25", "to": "2026-12-31", "token": key}, timeout=30)
    r2 = requests.get("https://finnhub.io/api/v1/stock/dividend", params={"symbol": "KO", "from": "2025-01-01", "to": "2026-12-31", "token": key}, timeout=30)
    return {"cal_status": r.status_code, "cal_body": r.text[:300], "stock_div_status": r2.status_code, "stock_div_body": r2.text[:300]}


for n, f in [("finnhub_insider", finnhub_insider), ("yf_insider_us", yf_insider_us), ("sec_form4", sec_form4),
             ("yf_insider_id", yf_insider_id), ("idx_site", idx_site), ("yf_dividend_cal", yf_dividend_cal), ("finnhub_div_cal", finnhub_div_cal)]:
    run(n, f)
OUT.write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False))
print(json.dumps({k: (v.get("ok") if isinstance(v, dict) else v) for k, v in res.items()}))
