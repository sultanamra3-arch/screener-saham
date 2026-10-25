"""Data tambahan: pembelian insider (Finnhub, laporan Form 4 SEC) dan kalender dividen (Yahoo)."""
from __future__ import annotations

import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

import divcal

DAYS = 90  # jendela pembelian insider yang ditampilkan


def _log(*a):
    print(*a, flush=True)


def insider(tickers: list[str], key: str, today: date) -> dict:
    """Pembelian di pasar terbuka (kode P) oleh direksi/komisaris dalam 90 hari terakhir, per saham."""
    frm = (today - timedelta(days=DAYS + 10)).isoformat()
    out, fails = {}, 0
    for i, t in enumerate(tickers, 1):
        try:
            r = requests.get("https://finnhub.io/api/v1/stock/insider-transactions",
                             params={"symbol": t, "from": frm, "token": key}, timeout=20)
            if r.status_code == 429:
                time.sleep(20)
                r = requests.get("https://finnhub.io/api/v1/stock/insider-transactions",
                                 params={"symbol": t, "from": frm, "token": key}, timeout=20)
            data = (r.json() or {}).get("data") or [] if r.ok else []
        except Exception:
            data, fails = [], fails + 1
        buys = []
        for x in data:
            if x.get("transactionCode") != "P" or x.get("isDerivative"):
                continue
            sh, px = x.get("change") or 0, x.get("transactionPrice") or 0
            d = x.get("transactionDate") or x.get("filingDate")
            if sh <= 0 or px <= 0 or not d or (today - date.fromisoformat(d[:10])).days > DAYS:
                continue
            buys.append({"d": d[:10], "f": (x.get("filingDate") or d)[:10], "n": x.get("name") or "", "sh": int(sh), "px": round(float(px), 2), "v": round(sh * px)})
        if buys:
            out[t] = sorted(buys, key=lambda b: b["d"], reverse=True)
        if i % 100 == 0:
            _log(f"  insider {i}/{len(tickers)}")
        time.sleep(1.05)
    if fails > len(tickers) // 3:
        _log(f"  ⚠ insider: {fails} saham gagal diambil")
    # jabatan dari Yahoo, hanya untuk saham yang ada pembelian
    try:
        import yfinance as yf
        for t in list(out):
            df = yf.Ticker(t).insider_transactions
            if df is None or df.empty:
                continue
            pos = {str(n).upper(): str(p) for n, p in zip(df.get("Insider", []), df.get("Position", []))}
            for b in out[t]:
                b["role"] = pos.get(b["n"].upper(), "")
    except Exception as e:
        _log(f"  jabatan insider: {str(e)[:80]}")
    return out


def insider_summary(buys: list[dict]) -> dict:
    people = {b["n"] for b in buys}
    ds = sorted(date.fromisoformat(b["d"]) for b in buys)
    cluster = False
    for i, d0 in enumerate(ds):
        win = {b["n"] for b in buys if 0 <= (date.fromisoformat(b["d"]) - d0).days <= 30}
        if len(win) >= 2:
            cluster = True
            break
    return {"n": len(buys), "p": len(people), "v": sum(b["v"] for b in buys), "d": buys[0]["d"], "f": max(b["f"] for b in buys), "cl": cluster}


def divcal_update(rows: list[dict], cache_file: Path, today: date, budget: int = 160) -> None:
    """Perbarui riwayat dan tanggal ex-dividen dari Yahoo secara bergilir, lalu isi row['dv']."""
    import yfinance as yf
    cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}
    payers = [r for r in rows if (r.get("div") or 0) > 0 or (r.get("dpsTTM") or 0) > 0]
    soon = lambda c: c.get("ex") and 0 <= (date.fromisoformat(c["ex"]) - today).days <= 10

    def age(r):
        c = cache.get(r["ticker"]) or {}
        return "" if soon(c) else c.get("asOf", "")
    todo = sorted(payers, key=age)[:budget]
    for r in todo:
        t = r["ticker"]
        try:
            tk = yf.Ticker(t)
            cal = tk.calendar or {}
            ex = cal.get("Ex-Dividend Date") if isinstance(cal, dict) else None
            dv = tk.dividends
            hist = [[str(i.date()), round(float(v), 4)] for i, v in dv[dv.index >= dv.index[-1] - __import__("pandas").Timedelta(days=800)].items()] if len(dv) else []
            cache[t] = {"asOf": today.isoformat(), "ex": str(ex)[:10] if ex else None, "hist": hist}
        except Exception as e:
            cache.setdefault(t, {})["asOf"] = today.isoformat()
            _log(f"  dividen {t}: {str(e)[:60]}")
        time.sleep(0.3)
    cache_file.write_text(json.dumps(cache, separators=(",", ":")))
    for r in rows:
        c = cache.get(r["ticker"])
        nd = divcal.next_div(c.get("hist"), c.get("ex"), today) if c else None
        if nd and r.get("price"):
            nd["y"] = round(nd["amt"] / r["price"] * 100, 2)
        if nd:
            r["dv"] = nd
    _log(f"  kalender dividen: {len(todo)} diperbarui, {sum(1 for r in rows if r.get('dv'))} dengan ex-date ≤ {divcal.HORIZON} hari")
