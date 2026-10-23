"""
Pengambil data untuk Screener Saham S&P 500 + Nasdaq-100.

Sumber:
  - Daftar anggota indeks: Wikipedia (diperbarui jika lebih tua dari 30 hari)
  - Fundamental: Finnhub /stock/metric (butuh FINNHUB_API_KEY, paket gratis)
  - Harga harian (SMA, RSI, kinerja, 52W high): Yahoo Finance lewat yfinance

Hasil: data/stocks.json dan data/constituents.json
"""
from __future__ import annotations

import io
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONST_FILE = DATA / "constituents.json"
OUT_FILE = DATA / "stocks.json"

FINNHUB = "https://finnhub.io/api/v1"
UA = {"User-Agent": "screener-saham/1.1 (https://github.com/sultanamra3-arch/screener-saham; personal stock screener) python-requests"}
SP500_CSV = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
WARNINGS: list[str] = []
ETFS = ["VOO", "SPY", "QQQ"]
# Cadangan jika Yahoo tidak memberi rasio biaya. Selalu cek situs penerbit.
ETF_FALLBACK = {
    "VOO": {"name": "Vanguard S&P 500 ETF", "index": "S&P 500", "expense": 0.03},
    "SPY": {"name": "SPDR S&P 500 ETF Trust", "index": "S&P 500", "expense": 0.0945},
    "QQQ": {"name": "Invesco QQQ Trust", "index": "Nasdaq-100", "expense": 0.20},
}


def log(*a):
    print(*a, flush=True)


def summary(md: str):
    """Tulis ke halaman ringkasan run GitHub Actions (terlihat tanpa membuka log)."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(md + "\n")


# ---------------------------------------------------------------- constituents
def _read_tables(url: str):
    import pandas as pd

    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    return pd.read_html(io.StringIO(r.text))


def _pick(table, *names):
    cols = {str(c).strip().lower(): c for c in table.columns}
    for n in names:
        if n.lower() in cols:
            return cols[n.lower()]
    return None


def _sp500_wikipedia():
    for t in _read_tables("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"):
        if _pick(t, "Symbol") is not None and _pick(t, "GICS Sector") is not None:
            return t
    raise RuntimeError("tabel S&P 500 tidak ditemukan di halaman Wikipedia")


def _sp500_github():
    import pandas as pd

    r = requests.get(SP500_CSV, headers=UA, timeout=60)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))


def _ndx_tables():
    for url in ("https://en.wikipedia.org/wiki/Nasdaq-100",
                "https://en.wikipedia.org/api/rest_v1/page/html/Nasdaq-100"):
        try:
            for t in _read_tables(url):
                if _pick(t, "Ticker", "Symbol") is not None and _pick(t, "Company", "Security") is not None and len(t) > 80:
                    return t
            log(f"  tabel Nasdaq-100 tidak ditemukan di {url}")
        except Exception as e:
            log(f"  Nasdaq-100 dari {url} gagal: {e}")
    return None


def fetch_constituents() -> dict:
    stocks: dict[str, dict] = {}

    sp = None
    for name, fn in (("Wikipedia", _sp500_wikipedia), ("GitHub datasets", _sp500_github)):
        try:
            sp = fn()
            log(f"  S&P 500 dari {name}: {len(sp)} baris")
            break
        except Exception as e:
            log(f"  S&P 500 dari {name} gagal: {e}")
    if sp is None:
        raise RuntimeError("Daftar S&P 500 tidak bisa diambil dari Wikipedia maupun GitHub datasets")
    cs, cn, cg = _pick(sp, "Symbol"), _pick(sp, "Security", "Name"), _pick(sp, "GICS Sector", "Sector")
    for _, r in sp.iterrows():
        tk = str(r[cs]).strip().upper()
        stocks[tk] = {"ticker": tk, "company": str(r[cn]).strip() if cn is not None else "",
                      "sector": str(r[cg]).strip() if cg is not None else "", "idx": ["SP500"]}

    ndx = _ndx_tables()
    if ndx is None:
        WARNINGS.append("Daftar Nasdaq-100 gagal diambil; hanya saham S&P 500 yang dipakai kali ini.")
    else:
        cs, cn = _pick(ndx, "Ticker", "Symbol"), _pick(ndx, "Company", "Security")
        cg = _pick(ndx, "GICS Sector", "ICB Industry[14]", "ICB Industry", "Industry")
        for _, r in ndx.iterrows():
            tk = str(r[cs]).strip().upper()
            if tk in stocks:
                stocks[tk]["idx"].append("NDX")
            else:
                stocks[tk] = {"ticker": tk, "company": str(r[cn]).strip(),
                              "sector": str(r[cg]).strip() if cg is not None else "", "idx": ["NDX"]}

    if len(stocks) < 450:
        raise RuntimeError(f"Daftar anggota indeks terlalu sedikit ({len(stocks)}), dibatalkan")
    return {
        "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stocks": sorted(stocks.values(), key=lambda s: s["ticker"]),
        "hasNdx": ndx is not None,
    }


def load_constituents() -> dict:
    if CONST_FILE.exists():
        cur = json.loads(CONST_FILE.read_text())
        age = datetime.now(timezone.utc) - datetime.fromisoformat(cur["updatedAt"])
        if age.days < 30 and cur.get("hasNdx", True) and os.environ.get("FORCE_CONSTITUENTS") != "1":
            log(f"Daftar indeks dipakai ulang (umur {age.days} hari, {len(cur['stocks'])} saham)")
            return cur
    log("Memperbarui daftar anggota S&P 500 dan Nasdaq-100 ...")
    try:
        new = fetch_constituents()
    except Exception as e:  # pakai daftar lama jika ada
        if CONST_FILE.exists():
            log(f"  Gagal ({e}); memakai daftar lama")
            return json.loads(CONST_FILE.read_text())
        raise
    CONST_FILE.write_text(json.dumps(new, indent=1))
    log(f"  {len(new['stocks'])} saham")
    return new


# ---------------------------------------------------------------- finnhub
def first(m: dict, *keys):
    for k in keys:
        v = m.get(k)
        if isinstance(v, (int, float)) and math.isfinite(v):
            return float(v)
    return None


def finnhub_metric(symbol: str, key: str) -> dict | None:
    for attempt in range(5):
        try:
            r = requests.get(
                f"{FINNHUB}/stock/metric",
                params={"symbol": symbol, "metric": "all", "token": key},
                timeout=30,
            )
        except requests.RequestException:
            time.sleep(5)
            continue
        if r.status_code == 429:
            time.sleep(15 * (attempt + 1))
            continue
        if r.status_code in (401, 403):
            raise RuntimeError(f"Finnhub menolak API key (HTTP {r.status_code}). Cek secret FINNHUB_API_KEY.")
        if r.status_code != 200:
            return None
        return (r.json() or {}).get("metric") or None
    return None


def from_metric(m: dict) -> dict:
    return {
        "mcap": first(m, "marketCapitalization"),  # juta USD
        "pe": first(m, "peTTM", "peBasicExclExtraTTM", "peExclExtraTTM", "peNormalizedAnnual"),
        "pb": first(m, "pbQuarterly", "pbAnnual", "ptbvQuarterly"),
        "div": first(m, "currentDividendYieldTTM", "dividendYieldIndicatedAnnual"),
        "payout": first(m, "payoutRatioTTM", "payoutRatioAnnual"),
        "roe": first(m, "roeTTM", "roeRfy", "roe5Y"),
        "gm": first(m, "grossMarginTTM", "grossMarginAnnual"),
        "om": first(m, "operatingMarginTTM", "operatingMarginAnnual"),
        "de": first(m, "totalDebt/totalEquityQuarterly", "totalDebt/totalEquityAnnual"),
        "cr": first(m, "currentRatioQuarterly", "currentRatioAnnual"),
        "eps5y": first(m, "epsGrowth5Y"),
        "sales5y": first(m, "revenueGrowth5Y"),
        "eps3y": first(m, "epsGrowth3Y"),
        "epsTTM": first(m, "epsGrowthTTMYoy"),
        "epsQ": first(m, "epsGrowthQuarterlyYoy"),
        "salesQ": first(m, "revenueGrowthQuarterlyYoy"),
        "beta": first(m, "beta"),
        "relSP": first(m, "priceRelativeToS&P50052Week"),
        # cadangan jika data harga harian gagal
        "_perf6m": first(m, "26WeekPriceReturnDaily"),
        "_perf1y": first(m, "52WeekPriceReturnDaily"),
        "_hi52": first(m, "52WeekHigh"),
    }


def check_key(key: str):
    log("Mengecek API key Finnhub ...")
    try:
        r = requests.get(f"{FINNHUB}/quote", params={"symbol": "AAPL", "token": key}, timeout=30)
    except requests.RequestException as e:
        raise RuntimeError(f"Finnhub tidak bisa dihubungi: {e}")
    if r.status_code in (401, 403):
        raise RuntimeError(
            f"Finnhub menolak API key (HTTP {r.status_code}). Salin ulang API key dari finnhub.io/dashboard "
            "lalu perbarui secret FINNHUB_API_KEY (tanpa spasi atau tanda kutip).")
    if r.status_code != 200:
        raise RuntimeError(f"Finnhub membalas HTTP {r.status_code}: {r.text[:200]}")
    log("  API key valid")


# ---------------------------------------------------------------- prices
def yahoo_symbol(t: str) -> str:
    return t.replace(".", "-")


def fetch_prices(tickers: list[str]):
    """Kembalikan DataFrame harga penutupan (kolom = ticker asli), atau None."""
    try:
        import pandas as pd
        import yfinance as yf
    except Exception as e:
        log(f"yfinance tidak tersedia: {e}")
        return None
    frames = []
    ymap = {yahoo_symbol(t): t for t in tickers}
    syms = list(ymap)
    for i in range(0, len(syms), 100):
        chunk = syms[i : i + 100]
        for attempt in range(3):
            try:
                df = yf.download(chunk, period="13mo", interval="1d", auto_adjust=True,
                                 progress=False, threads=True, group_by="column")
                close = df["Close"] if "Close" in df else None
                if close is not None and not close.empty:
                    if isinstance(close, pd.Series):
                        close = close.to_frame(chunk[0])
                    frames.append(close)
                    break
            except Exception as e:
                log(f"  harga batch {i}: {e}")
            time.sleep(10 * (attempt + 1))
        time.sleep(2)
    if not frames:
        return None
    allc = pd.concat(frames, axis=1)
    allc = allc.loc[:, ~allc.columns.duplicated()]
    allc.columns = [ymap.get(c, c) for c in allc.columns]
    return allc


def rsi14(s) -> float | None:
    d = s.diff().dropna()
    if len(d) < 15:
        return None
    up = d.clip(lower=0)
    dn = -d.clip(upper=0)
    au = up.ewm(alpha=1 / 14, adjust=False).mean().iloc[-1]
    ad = dn.ewm(alpha=1 / 14, adjust=False).mean().iloc[-1]
    if ad == 0:
        return 100.0
    return float(100 - 100 / (1 + au / ad))


def pct(a, b):
    if a is None or b is None or b == 0 or not (math.isfinite(a) and math.isfinite(b)):
        return None
    return (a / b - 1) * 100


def technicals(s) -> dict:
    import pandas as pd

    s = s.dropna()
    out = {k: None for k in ("price", "sma20", "sma50", "sma200", "rsi", "perf1m", "perf6m", "perf1y", "perfYtd", "hi52")}
    if len(s) < 25:
        return out
    p = float(s.iloc[-1])
    out["price"] = round(p, 2)
    for n in (20, 50, 200):
        if len(s) >= n:
            out[f"sma{n}"] = pct(p, float(s.iloc[-n:].mean()))
    out["rsi"] = rsi14(s)
    last = s.index[-1]

    def back(days):
        prev = s[s.index <= last - pd.Timedelta(days=days)]
        return float(prev.iloc[-1]) if len(prev) else None

    out["perf1m"] = pct(p, back(30))
    out["perf6m"] = pct(p, back(182))
    out["perf1y"] = pct(p, back(365))
    ytd = s[s.index.year == last.year]
    prev_year = s[s.index.year < last.year]
    if len(prev_year):
        out["perfYtd"] = pct(p, float(prev_year.iloc[-1]))
    elif len(ytd):
        out["perfYtd"] = pct(p, float(ytd.iloc[0]))
    yr = s[s.index > last - pd.Timedelta(days=365)]
    out["hi52"] = pct(p, float(yr.max()))
    return out


# ---------------------------------------------------------------- etf
def etf_info(prices) -> dict:
    res = {}
    try:
        import yfinance as yf
    except Exception:
        yf = None
    for t in ETFS:
        base = dict(ETF_FALLBACK[t])
        base["expenseSource"] = "cadangan"
        if yf is not None:
            try:
                info = yf.Ticker(t).info or {}
                er = info.get("netExpenseRatio") or info.get("annualReportExpenseRatio")
                if isinstance(er, (int, float)) and er > 0:
                    base["expense"] = er if er > 0.01 else er * 100
                    base["expenseSource"] = "Yahoo"
                aum = info.get("totalAssets")
                if isinstance(aum, (int, float)):
                    base["aum"] = aum
                y = info.get("yield") or info.get("dividendYield")
                if isinstance(y, (int, float)):
                    base["yield"] = y * 100 if y < 1 else y
            except Exception as e:
                log(f"  info {t}: {e}")
        if prices is not None and t in prices:
            tech = technicals(prices[t])
            base.update({k: tech[k] for k in ("price", "perf1m", "perf6m", "perf1y", "perfYtd", "hi52", "sma200")})
        res[t] = clean(base)
    return res


# ---------------------------------------------------------------- main
def clean(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, float):
            out[k] = round(v, 3) if math.isfinite(v) else None
        else:
            out[k] = v
    return out


def build(const: dict, metrics: dict, prices) -> list[dict]:
    rows = []
    for s in const["stocks"]:
        t = s["ticker"]
        row = dict(s)
        f = metrics.get(t) or {}
        row.update({k: v for k, v in f.items() if not k.startswith("_")})
        tech = technicals(prices[t]) if prices is not None and t in prices else {}
        for k, v in tech.items():
            row[k] = v
        # cadangan dari Finnhub bila harga harian kosong
        if row.get("perf6m") is None:
            row["perf6m"] = f.get("_perf6m")
        if row.get("perf1y") is None:
            row["perf1y"] = f.get("_perf1y")
        rows.append(clean(row))

    # Finnhub kadang memberi D/E dalam persen; samakan ke rasio
    des = sorted(r["de"] for r in rows if isinstance(r.get("de"), (int, float)))
    if des and des[len(des) // 2] > 10:
        for r in rows:
            if isinstance(r.get("de"), (int, float)):
                r["de"] = round(r["de"] / 100, 3)
    return rows


def main():
    key = os.environ.get("FINNHUB_API_KEY", "").strip()
    if not key:
        raise SystemExit("FINNHUB_API_KEY belum diisi. Tambahkan di Settings > Secrets and variables > Actions.")
    check_key(key)
    DATA.mkdir(exist_ok=True)
    const = load_constituents()
    tickers = [s["ticker"] for s in const["stocks"]]
    limit = int(os.environ.get("LIMIT", "0") or 0)
    if limit:
        tickers = tickers[:limit]
        const = {**const, "stocks": const["stocks"][:limit]}

    log(f"Mengambil fundamental Finnhub untuk {len(tickers)} saham (±{len(tickers)//55+1} menit) ...")
    metrics, missing = {}, []
    for i, t in enumerate(tickers, 1):
        m = finnhub_metric(t, key)
        if m:
            metrics[t] = from_metric(m)
        else:
            missing.append(t)
        if i % 50 == 0:
            log(f"  {i}/{len(tickers)}")
        time.sleep(1.05)  # paket gratis: ±60 panggilan per menit

    log("Mengambil harga harian ...")
    prices = fetch_prices(tickers + ETFS)
    if prices is None:
        log("  Harga harian gagal; SMA, RSI, dan 52W high akan kosong hari ini")

    rows = build(const, metrics, prices)
    out = {
        "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "constituentsUpdatedAt": const["updatedAt"],
        "sources": {
            "fundamentals": "Finnhub",
            "prices": "Yahoo Finance" if prices is not None else None,
            "constituents": "Wikipedia",
        },
        "count": len(rows),
        "missingFundamentals": missing,
        "stocks": rows,
        "etf": etf_info(prices),
    }
    OUT_FILE.write_text(json.dumps(out, separators=(",", ":")))
    log(f"Selesai: {len(rows)} saham, {len(missing)} tanpa fundamental -> {OUT_FILE.relative_to(ROOT)}")
    summary(f"### Berhasil\n- {len(rows)} saham diperbarui\n- {len(missing)} saham tanpa data fundamental\n"
            f"- Harga harian: {'ada' if prices is not None else 'GAGAL (SMA/RSI kosong)'}")
    for w in WARNINGS:
        summary(f"- Peringatan: {w}")
    if len(missing) > len(tickers) * 0.5:
        raise RuntimeError(f"Lebih dari separuh saham ({len(missing)}) gagal diambil dari Finnhub")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        if e.code not in (0, None):
            summary(f"### Gagal\n{e.code}")
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        summary(f"### Gagal\n**{type(e).__name__}**: {e}")
        sys.exit(1)
