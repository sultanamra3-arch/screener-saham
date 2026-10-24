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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import strategies  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONST_FILE = DATA / "constituents.json"
OUT_FILE = DATA / "stocks.json"
SIG_FILE = DATA / "signals.json"

FINNHUB = "https://finnhub.io/api/v1"
UA = {"User-Agent": "ScreenerSahamBot/1.2 (https://github.com/sultanamra3-arch/screener-saham; sultanamra3@users.noreply.github.com)"}
BROWSER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
           "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US,en;q=0.9"}
SP500_CSV = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
WARNINGS: list[str] = []
ETFS = ["VOO", "SPY", "QQQ"]
INDICES = ["^GSPC", "^NDX", "^VIX"]
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


def _ndx_from_tables(tables):
    for t in tables:
        if _pick(t, "Ticker", "Symbol") is not None and _pick(t, "Company", "Security") is not None and len(t) > 80:
            return t
    return None


def _ndx_wiki_api():
    import pandas as pd

    r = requests.get("https://en.wikipedia.org/w/api.php",
                     params={"action": "parse", "page": "Nasdaq-100", "prop": "text",
                             "format": "json", "formatversion": "2"},
                     headers=UA, timeout=60)
    r.raise_for_status()
    return _ndx_from_tables(pd.read_html(io.StringIO(r.json()["parse"]["text"])))


def _ndx_wiki_page():
    return _ndx_from_tables(_read_tables("https://en.wikipedia.org/wiki/Nasdaq-100"))


def _ndx_nasdaq():
    import pandas as pd

    r = requests.get("https://api.nasdaq.com/api/quote/list-type/nasdaq100", headers=BROWSER, timeout=60)
    r.raise_for_status()
    rows = (((r.json() or {}).get("data") or {}).get("data") or {}).get("rows") or []
    if len(rows) < 80:
        return None
    return pd.DataFrame([{"Ticker": x.get("symbol"), "Company": x.get("companyName")} for x in rows])


def _ndx_tables():
    for name, fn in (("Wikipedia API", _ndx_wiki_api), ("Wikipedia", _ndx_wiki_page), ("Nasdaq.com", _ndx_nasdaq)):
        try:
            t = fn()
            if t is not None:
                log(f"  Nasdaq-100 dari {name}: {len(t)} baris")
                return t
            log(f"  Nasdaq-100 dari {name}: tabel tidak ditemukan")
        except Exception as e:
            log(f"  Nasdaq-100 dari {name} gagal: {e}")
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
                              "sector": (str(r[cg]).strip() if cg is not None and str(r[cg]) != "nan" else ""), "idx": ["NDX"]}

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
        j = r.json() or {}
        return j if j.get("metric") else None
    return None


def _series(series: dict, key: str, n: int = 11) -> list:
    pts = ((series or {}).get("annual") or {}).get(key) or []
    out = []
    for p in pts:
        v, per = p.get("v"), str(p.get("period", ""))[:4]
        if isinstance(v, (int, float)) and math.isfinite(v) and per.isdigit():
            out.append([int(per), round(float(v), 4)])
    out = sorted({y: v for y, v in out}.items())
    return [list(x) for x in out[-n:]]


SERIES_SEEN: dict[str, int] = {}


def from_metric(j: dict) -> dict:
    m = j.get("metric") or {}
    series = j.get("series") or {}
    for k in ((series.get("annual") or {}).keys()):
        SERIES_SEEN[k] = SERIES_SEEN.get(k, 0) + 1
    return {
        "epsA": _series(series, "eps"),
        "payA": _series(series, "payoutRatio"),
        "roic": first(m, "roicTTM", "roiTTM", "roiAnnual", "roi5Y"),
        "pfcf": first(m, "pfcfShareTTM", "pfcfShareAnnual"),
        "divGrowth5y": first(m, "dividendGrowthRate5Y"),
        "divInd": first(m, "dividendYieldIndicatedAnnual"),
        "dpsTTM": first(m, "dividendPerShareTTM", "dividendPerShareAnnual"),
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
        "eps": first(m, "epsTTM", "epsExclExtraItemsTTM", "epsBasicExclExtraItemsTTM", "epsInclExtraItemsTTM"),
        "bvps": first(m, "bookValuePerShareQuarterly", "bookValuePerShareAnnual"),
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
    """Kembalikan (harga penutupan, volume) sebagai DataFrame (kolom = ticker asli), atau (None, None)."""
    try:
        import pandas as pd
        import yfinance as yf
    except Exception as e:
        log(f"yfinance tidak tersedia: {e}")
        return None, None
    frames, vframes = [], []
    ymap = {yahoo_symbol(t): t for t in tickers}
    syms = list(ymap)
    for i in range(0, len(syms), 100):
        chunk = syms[i : i + 100]
        for attempt in range(3):
            try:
                df = yf.download(chunk, period="3y", interval="1d", auto_adjust=True,
                                 progress=False, threads=True, group_by="column")
                close = df["Close"] if "Close" in df else None
                if close is not None and not close.empty:
                    if isinstance(close, pd.Series):
                        close = close.to_frame(chunk[0])
                    frames.append(close)
                    if "Volume" in df:
                        vol = df["Volume"]
                        if isinstance(vol, pd.Series):
                            vol = vol.to_frame(chunk[0])
                        vframes.append(vol)
                    break
            except Exception as e:
                log(f"  harga batch {i}: {e}")
            time.sleep(10 * (attempt + 1))
        time.sleep(2)
    if not frames:
        return None, None

    def join(fr):
        a = pd.concat(fr, axis=1)
        a = a.loc[:, ~a.columns.duplicated()]
        a.columns = [ymap.get(c, c) for c in a.columns]
        return a

    allc = join(frames).dropna(how="all")
    allv = join(vframes).reindex(allc.index) if vframes else None
    return allc, allv


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


# ---------------------------------------------------------------- siklus & Fibonacci
CYC_FILE = DATA / "cycles.json"
SERIES_FILE = DATA / "series.json"
CYC_STATE = DATA / "cycles_state.json"


def run_cycles(close, indices: dict, cfg: dict, stock_cols: list, breadth_cols: list, tick=None, vix=None):
    """Tidak boleh menggagalkan pembaruan utama: kesalahan hanya dicatat."""
    try:
        import cycles
        import yfinance as yf

        long = {}
        for name, sym in indices.items():
            try:
                df = yf.download(sym, period="max", interval="1d", auto_adjust=True, progress=False)
                c = df["Close"].squeeze().dropna()
                if len(c) > 1000:
                    long[name] = c
            except Exception as e:
                log(f"  riwayat panjang {sym}: {e}")
        state = json.loads(CYC_STATE.read_text()) if CYC_STATE.exists() else {}
        out, series = cycles.run(close, indices, long, stock_cols, breadth_cols, cfg, state, tick=tick, vix=vix)
        CYC_FILE.write_text(json.dumps(out, separators=(",", ":")))
        SERIES_FILE.write_text(cycles.dump_series(series))
        CYC_STATE.write_text(json.dumps(state, separators=(",", ":")))
        lines = ["### Siklus & Fibonacci"]
        for name, t in out.get("tests", {}).items():
            if not t or "time" not in t:
                lines.append(f"- {name}: uji tidak tersedia ({(t or {}).get('error', 'riwayat kurang')})")
                continue
            useful = [k for sec in ("time", "price", "season") for k, v in t[sec].items() if v and v["verdict"] == "berguna"]
            lines.append(f"- {name}: data {t['from']}–{t['to']}, {t['pivots']} titik balik; unsur yang terbukti berguna: {', '.join(useful) or 'tidak ada'}")
        summary("\n".join(lines))
        log("Siklus & Fibonacci selesai")
    except Exception as e:
        import traceback

        traceback.print_exc()
        summary(f"- Peringatan: Siklus & Fibonacci gagal dihitung ({type(e).__name__}: {str(e)[:150]})")


# ---------------------------------------------------------------- main
def clean(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, float):
            out[k] = round(v, 3) if math.isfinite(v) else None
        else:
            out[k] = v
    return out


def load_state() -> dict:
    if SIG_FILE.exists():
        try:
            st = json.loads(SIG_FILE.read_text())
            if isinstance(st, dict) and st.get("v") == 2:
                return st
        except Exception:
            pass
    return {"v": 2}


def comparison_md(res: dict) -> str:
    def row(name, s):
        if not s or not s.get("n"):
            return f"| {name} | 0 | – | – | – |"
        return f"| {name} | {s['n']} | {s['win']}% | {s['avg']:+.2f}% | {s['med']} hari |"
    lr = res.get("legacyReasons") or {}
    tot = sum(lr.values()) or 1
    lines = ["### Uji mundur 1 tahun: aturan lama vs baru", "",
             "| Aturan | Transaksi | Untung | Rata-rata hasil | Lama dipegang (median) |", "|---|---|---|---|---|",
             row("Lama (stop 8%, target 25%, tren patah)", res.get("legacy"))]
    for m in strategies.TRADER:
        lines.append(row(f"Baru: {strategies.NAMES[m]}", res["stats"].get(m)))
    lines.append("")
    lines.append(f"Aturan lama: {lr.get('trend', 0) * 100 // tot}% transaksi ditutup oleh 'tren patah'.")
    return "\n".join(lines)


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
    prices, volume = fetch_prices(tickers + ETFS + INDICES)
    if prices is None:
        log("  Harga harian gagal; SMA, RSI, dan 52W high akan kosong hari ini")

    rows = build(const, metrics, prices)
    day = prices.index[-1].strftime("%Y-%m-%d") if prices is not None else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    prev_day = None
    if OUT_FILE.exists():
        try:
            prev_day = json.loads(OUT_FILE.read_text()).get("priceDate")
        except Exception:
            prev_day = None
    state = load_state()
    log("Menghitung 7 metode ...")
    res = strategies.run(rows, prices, volume, day, state)
    show_cmp = not state.get("comparisonShown")
    state["comparisonShown"] = True
    SIG_FILE.write_text(json.dumps(state, separators=(",", ":")))
    out = {
        "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "constituentsUpdatedAt": const["updatedAt"],
        "hasNdx": const.get("hasNdx", True),
        "sources": {
            "fundamentals": "Finnhub",
            "prices": "Yahoo Finance" if prices is not None else None,
            "constituents": "Wikipedia",
        },
        "count": len(rows),
        "missingFundamentals": missing,
        "priceDate": day,
        "prevPriceDate": prev_day,
        "newSession": prev_day != day,
        "showComparison": show_cmp,
        **res,
        "stocks": rows,
        "etf": etf_info(prices),
    }
    OUT_FILE.write_text(json.dumps(out, separators=(",", ":")))
    if prices is not None:
        import notify_telegram

        vix = float(prices["^VIX"].dropna().iloc[-1]) if "^VIX" in prices and prices["^VIX"].notna().any() else None
        run_cycles(prices, {"S&P 500": "^GSPC", "Nasdaq-100": "^NDX"},
                   {"ramadan": False, "holidays": set(notify_telegram.HOLIDAYS), "vix_for": "S&P 500"},
                   tickers, tickers, vix=vix)
    log(f"Selesai: {len(rows)} saham, {len(missing)} tanpa fundamental -> {OUT_FILE.relative_to(ROOT)}")
    summary(f"### Berhasil\n- {len(rows)} saham diperbarui (harga penutupan {day})\n- {len(missing)} saham tanpa data fundamental\n"
            f"- Harga harian: {'ada' if prices is not None else 'GAGAL (SMA/RSI kosong)'}"
            f" · volume: {'ada' if volume is not None else 'tidak ada'}")
    summary(comparison_md(res))
    cnt = lambda f: sum(1 for r in rows if f(r))
    summary("### Kelengkapan data\n"
            f"- Riwayat laba tahunan ≥5 tahun: {cnt(lambda r: len(r.get('epsA') or []) >= 5)} saham\n"
            f"- Riwayat payout tahunan ≥5 tahun: {cnt(lambda r: len(r.get('payA') or []) >= 5)} saham\n"
            f"- ROIC: {cnt(lambda r: r.get('roic') is not None)} · P/FCF: {cnt(lambda r: r.get('pfcf') is not None)} · "
            f"pertumbuhan dividen 5 thn: {cnt(lambda r: r.get('divGrowth5y') is not None)}\n"
            f"- Kunci series tahunan Finnhub: {', '.join(sorted(SERIES_SEEN)[:60]) or 'tidak ada'}")
    sig = {m: {s: sum(1 for r in rows if (r.get('m') or {}).get(m, {}).get('s') == s) for s in ('buy', 'hold', 'sell')} for m in strategies.METHODS}
    summary("### Sinyal hari ini\n" + "\n".join(f"- {strategies.NAMES[m]}: {v['buy']} beli, {v['hold']} tahan, {v['sell']} jual" for m, v in sig.items()))
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
