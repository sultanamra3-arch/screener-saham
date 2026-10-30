"""Screener kripto: 50 koin terbesar yang bisa dibeli di Indodax, harga dalam Rupiah.

Sumber data (semua gratis, tanpa kunci API):
  - Daftar koin & kapitalisasi pasar: CoinGecko
  - Harga harian (OHLCV): Binance (data-api.binance.vision, pasangan USDT)
  - Kurs USD/IDR: Yahoo Finance (IDR=X); harga Rupiah lokal & ketersediaan koin: Indodax

Metode (lolos uji mundur Jan 2021–Okt 2026, lihat kripto/README di halaman):
  - Lampu BTC: BTC di atas rata-rata 50 hari = boleh trading altcoin; di atas 200 hari = boleh simpan BTC.
  - Momentum 90 hari: tiap Senin (candle harian UTC) pegang 5 koin dengan kenaikan 90 hari terkuat
    yang lebih kuat dari BTC dan di atas rata-rata 50 hari, hanya saat lampu BTC hijau.

Dijalankan tiap jam. Candle hari ini (UTC, mulai 07.00 WIB) belum selesai: harga tampil memakai
harga terakhir, tetapi sinyal metode hanya memakai candle yang sudah ditutup.
"""
from __future__ import annotations

import json
import math
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cycles  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "kripto" / "data"
COINS_FILE = OUT / "coins.json"
OUT_FILE = OUT / "stocks.json"
CYC_FILE = OUT / "cycles.json"
CYC_STATE = OUT / "cycles_state.json"
SERIES_FILE = OUT / "series.json"
OHLC_DIR = OUT / "ohlc"
UA = {"User-Agent": "ScreenerKripto/1.0 (https://github.com/sultanamra3-arch/screener-saham)"}
TOP = 50
FEE = 0.003           # per sisi, perkiraan biaya Indodax/Tokocrypto
SLOTS, KEEP_TOP = 5, 8  # momentum: pegang 5, tetap dipegang selama masih 8 besar
BARS = 420

STABLE = {"usdt", "usdc", "dai", "fdusd", "tusd", "usde", "usds", "pyusd", "usd1", "busd", "usdd", "frax", "usdy", "usdx",
          "rlusd", "usd0", "gho", "crvusd", "lusd", "susd", "eurc", "usdb", "usdg", "buidl", "usyc", "usdtb", "usdf", "bfusd",
          "susde", "susds", "ustb", "ousg", "usdai", "usda", "idrt", "bidr", "xsgd", "eurs", "usat"}
WRAP = {"wbtc", "weth", "steth", "wsteth", "weeth", "cbbtc", "btcb", "reth", "meth", "jitosol", "wbeth", "lbtc", "solvbtc",
        "ezeth", "rseth", "msol", "bnsol", "jupsol", "cbeth", "oseth", "sweth", "tbtc", "fbtc", "clbtc", "wbnb", "xaut", "paxg"}
CAT = {
    "Layer 1": "BTC ETH SOL ADA AVAX TRX XLM NEAR SUI HBAR DOT ICP ALGO ATOM APT TON ETC LTC BCH VET KAS SEI EGLD XTZ IOTA "
               "KAIA FLR HYPE MON XPL S TIA INJ BSV XDC NIGHT",
    "Pembayaran": "XRP XLM LTC BCH DASH",
    "Exchange": "BNB CRO OKB LEO NEXO BGB KCS GT HTX",
    "Meme": "DOGE SHIB PEPE PUMP BONK FLOKI WIF PENGU TRUMP LUNC",
    "DeFi": "UNI AAVE ENA MORPHO SKY JUP CAKE ETHFI PENDLE AERO CRV LDO RAY COMP JST SUN CVX GNO KMNO JTO SYRUP ASTER WLFI",
    "Layer 2": "ARB POL OP STRK ZRO MNT",
    "Infrastruktur": "LINK PYTH QNT FIL GRT AR STX ENS BAT THETA JASMY ZAMA EIGEN",
    "AI": "TAO RENDER FET WLD VIRTUAL KITE",
    "Aset dunia nyata": "ONDO",
}
CAT_OF = {}
for k, v in CAT.items():
    for s in v.split():
        CAT_OF.setdefault(s, k)


def log(*a):
    print(*a, flush=True)


def summary(md: str):
    import os
    p = os.environ.get("GITHUB_STEP_SUMMARY")
    if p:
        with open(p, "a") as f:
            f.write(md + "\n")


def get(url, params=None, tries=3):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=30)
            if r.status_code == 429:
                time.sleep(20 * (i + 1))
                continue
            return r
        except Exception as e:
            log(f"  {url}: {e}")
            time.sleep(5)
    return None


# ---------------------------------------------------------------- daftar koin
def indodax() -> dict:
    r = get("https://indodax.com/api/tickers")
    if not r or not r.ok:
        return {}
    out = {}
    for k, v in (r.json().get("tickers") or {}).items():
        if k.endswith("_idr"):
            try:
                out[k[:-4].upper()] = {"last": float(v["last"]), "vol": float(v.get("vol_idr") or 0)}
            except Exception:
                pass
    return out


def klines(sym: str, n: int = 1000):
    rows, end = [], None
    while len(rows) < n:
        p = {"symbol": sym, "interval": "1d", "limit": min(1000, n - len(rows))}
        if end:
            p["endTime"] = end
        r = get("https://data-api.binance.vision/api/v3/klines", p)
        if not r or not r.ok:
            return None
        k = r.json()
        if not k:
            break
        rows = k + rows
        end = k[0][0] - 1
        if len(k) < p["limit"]:
            break
    if not rows:
        return None
    df = pd.DataFrame([[pd.to_datetime(x[0], unit="ms"), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[7])]
                       for x in rows], columns=["d", "o", "h", "l", "c", "qv"]).drop_duplicates("d").set_index("d")
    return df


def pick_coins(idx: dict) -> list[dict]:
    """Pilih ulang sekali sehari; bila CoinGecko gagal, pakai daftar kemarin."""
    old = json.loads(COINS_FILE.read_text()) if COINS_FILE.exists() else {}
    today = datetime.now(timezone.utc).date().isoformat()
    if old.get("date") == today and old.get("coins"):
        return old["coins"]
    cg = []
    for page in (1, 2):
        r = get("https://api.coingecko.com/api/v3/coins/markets",
                {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 100, "page": page})
        if r is not None and r.ok:
            cg += r.json()
        time.sleep(2)
    if len(cg) < 100 or not idx:
        log("  CoinGecko/Indodax gagal; memakai daftar koin sebelumnya")
        return old.get("coins") or []
    out = []
    for c in cg:
        s = (c.get("symbol") or "").lower()
        nm = (c.get("name") or "").lower()
        if s in STABLE or s in WRAP or any(w in nm for w in ("wrapped", "bridged", "staked", "stablecoin")):
            continue
        p = c.get("current_price")
        if p and 0.95 < p < 1.05 and "usd" in (s + nm):
            continue
        S = s.upper()
        if S not in idx or not S.isascii() or not S.isalnum():
            continue
        out.append({"t": S, "name": c["name"], "rank": c.get("market_cap_rank"), "mcap": c.get("market_cap"), "cgp": p,
                    "cat": CAT_OF.get(S, "Lainnya")})
        if len(out) >= TOP + 15:  # cadangan untuk koin yang tidak ada di Binance / harganya tidak cocok
            break
    COINS_FILE.write_text(json.dumps({"date": today, "coins": out}, ensure_ascii=False, indent=0))
    return out


# ---------------------------------------------------------------- indikator
def technicals(s: pd.Series) -> dict:
    s = s.dropna()
    out = {k: None for k in ("price", "sma20", "sma50", "sma200", "perf1w", "perf1m", "perf3m", "perf6m", "perf1y",
                             "perfYtd", "hi52", "perf90")}
    if len(s) < 25:
        return out
    p = float(s.iloc[-1])
    out["price"] = p
    for n in (20, 50, 200):
        if len(s) >= n:
            out[f"sma{n}"] = (p / float(s.iloc[-n:].mean()) - 1) * 100
    ago = lambda k: float(s.iloc[-1 - k]) if len(s) > k else None
    chg = lambda x, y: (x / y - 1) * 100 if x and y else None
    for k, d in (("perf1w", 7), ("perf1m", 30), ("perf3m", 90), ("perf6m", 182), ("perf1y", 365), ("perf90", 90)):
        out[k] = chg(p, ago(d))
    last = s.index[-1]
    py = s[s.index.year < last.year]
    out["perfYtd"] = chg(p, float(py.iloc[-1])) if len(py) else None
    out["hi52"] = chg(p, float(s[s.index > last - pd.Timedelta(days=365)].max()))
    return out


def rsi(s: pd.Series, n: int) -> float | None:
    d = s.diff().dropna()
    if len(d) < n + 5:
        return None
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up.iloc[-1] / dn.iloc[-1] if dn.iloc[-1] > 0 else float("inf")
    return 100 - 100 / (1 + rs)


def sig(v, n=5):
    if v is None or not math.isfinite(v) or v == 0:
        return v
    d = max(0, n - 1 - math.floor(math.log10(abs(v))))
    return round(float(v), d) if d else int(round(v))


def tgl(d: str) -> str:
    b = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    y, m, dd = d.split("-")
    return f"{int(dd)} {b[int(m) - 1]} {y}"


def rp(v) -> str:
    if v is None or not math.isfinite(v):
        return "–"
    d = 0 if v >= 100 else 2 if v >= 1 else max(2, 3 - math.floor(math.log10(v)))
    s = f"{v:,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return "Rp" + s


# ---------------------------------------------------------------- Momentum 90 hari (simulasi ulang)
def momentum(C: pd.DataFrame, today_px: dict, fx_now: float) -> tuple[dict, dict]:
    """C = harga penutupan USD candle yang sudah selesai. Simulasi deterministik dari awal data:
    hasil (posisi sekarang + riwayat) sama setiap kali dijalankan."""
    btc = C["BTC"]
    b50 = btc.rolling(50, min_periods=50).mean()
    green = btc > b50
    s50 = C.rolling(50, min_periods=50).mean()
    r90 = C / C.shift(90) - 1
    age = C.notna().cumsum()
    elig = lambda k, d: age.at[d, k] >= 60 and np.isfinite(C.at[d, k]) and np.isfinite(s50.at[d, k]) and np.isfinite(r90.at[d, k])
    start = C.index[0] + pd.Timedelta(days=120)
    pos, trades = {}, []
    eq, cash = [], 1.0
    dates = [d for d in C.index if d >= start]
    for d in dates:
        row = C.loc[d]
        reb = d.weekday() == 0
        top = []
        if reb:
            ok_ = [k for k in C.columns if elig(k, d)]
            top = list(r90.loc[d, ok_].sort_values(ascending=False).index[:KEEP_TOP])
        for k in list(pos):
            p = row[k]
            if not np.isfinite(p):
                continue
            below = p < s50.at[d, k]
            why = None
            if reb:
                if not green.at[d]:
                    why = "lampu BTC merah"
                elif below:
                    why = "turun di bawah rata-rata 50 hari"
                elif k not in top:
                    why = "keluar dari 8 terkuat"
            elif not green.at[d] and below:
                why = "lampu BTC merah dan di bawah rata-rata 50 hari"
            if why:
                q, bp, bd = pos.pop(k)
                cash += q * p * (1 - FEE)
                trades.append({"t": k, "b": bd, "bp": bp, "s": d.strftime("%Y-%m-%d"), "sp": p, "r": why,
                               "ret": round(((p * (1 - FEE)) / (bp * (1 + FEE)) - 1) * 100, 2)})
        val = cash + sum(q * row[k] for k, (q, _, _) in pos.items() if np.isfinite(row[k]))
        if reb and green.at[d] and len(pos) < SLOTS:
            cands = [k for k in top if k not in pos and k != "BTC" and row[k] > s50.at[d, k] and r90.at[d, k] > r90.at[d, "BTC"]]
            for k in cands[: SLOTS - len(pos)]:
                amt = min(cash, val / SLOTS)
                if amt <= 1e-9:
                    break
                pos[k] = (amt * (1 - FEE) / row[k], float(row[k]), d.strftime("%Y-%m-%d"))
                cash -= amt
        eq.append(cash + sum(q * row[k] for k, (q, _, _) in pos.items() if np.isfinite(row[k])))
    last = C.index[-1]
    ok_ = [k for k in C.columns if elig(k, last)]
    rank = {k: i + 1 for i, k in enumerate(r90.loc[last, ok_].sort_values(ascending=False).index)}
    nxt = last + timedelta(days=(7 - last.weekday()) % 7 or 7)
    st = {"green": bool(green.iloc[-1]), "rank": rank, "pos": {k: {"b": bd, "bp": bp} for k, (q, bp, bd) in pos.items()},
          "trades": trades, "s50": {k: float(s50.at[last, k]) for k in C.columns if np.isfinite(s50.at[last, k])},
          "r90": {k: float(r90.at[last, k]) for k in C.columns if np.isfinite(r90.at[last, k])},
          "lastCandle": last.strftime("%Y-%m-%d"), "next": nxt.strftime("%Y-%m-%d")}
    e = pd.Series(eq, index=dates)
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    fin = [t for t in trades]
    rets = [t["ret"] for t in fin]
    held = [(date.fromisoformat(t["s"]) - date.fromisoformat(t["b"])).days for t in fin]
    yearly = {}
    ye = e.resample("YE").last()
    prev = e.iloc[0]
    for d, v in ye.items():
        if (d - e.index[0]).days >= 30:
            yearly[str(d.year)] = round((v / prev - 1) * 100, 1)
        prev = v
    stats = {"n": len(rets), "win": round(sum(r > 0 for r in rets) / len(rets) * 100, 1) if rets else None,
             "avg": round(float(np.mean(rets)), 2) if rets else None, "med": int(np.median(held)) if held else None,
             "cagr": round(((e.iloc[-1] / e.iloc[0]) ** (1 / yrs) - 1) * 100, 1) if yrs > 0.5 else None,
             "dd": round(float((e / e.cummax() - 1).min()) * 100, 1), "from": dates[0].strftime("%Y-%m-%d"),
             "yearly": yearly, "eq": [[d.strftime("%Y-%m-%d"), round(float(v), 4)] for d, v in e.iloc[::7].items()]}
    return st, stats


def mom_state(t: str, M: dict, price_idr: float, fx_series_last: float, today: str) -> dict:
    """Status per koin dalam format yang sama dengan metode trader di screener saham."""
    green, rank = M["green"], M["rank"].get(t)
    s50 = M["s50"].get(t)
    r90, rb = M["r90"].get(t), M["r90"].get("BTC")
    s50_idr = s50 * fx_series_last if s50 else None
    above = s50_idr is not None and price_idr > s50_idr
    c = [
        ["Lampu BTC hijau (BTC di atas rata-rata 50 hari)", "hijau" if green else "merah", 1 if green else 0],
        ["Harga di atas rata-rata 50 hari", f"rata-rata 50 hari {rp(s50_idr)}" if s50_idr else "riwayat kurang", 1 if above else 0 if s50_idr else 2],
        ["Kenaikan 90 hari lebih kuat dari BTC", (f"{r90 * 100:+.1f}% vs BTC {rb * 100:+.1f}%".replace(".", ",")) if r90 is not None and rb is not None else "riwayat kurang",
         (1 if r90 > rb else 0) if r90 is not None and rb is not None and t != "BTC" else 2],
        ["Masuk 5 terkuat (peringkat kenaikan 90 hari)", f"peringkat {rank}" if rank else "–", (1 if rank and rank <= SLOTS else 0) if rank else 2],
    ]
    use = [x for x in c if x[2] != 2]
    k, n = sum(1 for x in use if x[2] == 1), len(use)
    hist = [x for x in M["trades"] if x["t"] == t]
    h = [{"b": x["b"], "bp": x["bp"] * fx_series_last, "s": x["s"], "sp": x["sp"] * fx_series_last, "r": x["r"], "ret": x["ret"]} for x in hist[-8:]]
    lv = {}
    if s50_idr:
        lv["exit"] = sig(s50_idr)
    res = {"s": "wait", "lv": lv, "k": k, "n": n, "p": k == n and n > 0, "c": c, "h": h}
    if t == "BTC":
        res.update({"s": "na", "r": "BTC adalah patokan pasar, bukan kandidat metode ini. Lihat Lampu BTC.", "rs": "patokan pasar"})
        return res
    if t in M["pos"]:
        p = M["pos"][t]
        bp_idr = p["bp"] * fx_series_last
        ret = (price_idr / bp_idr - 1) * 100
        new = (date.fromisoformat(today) - date.fromisoformat(p["b"])).days <= 1
        res.update({"s": "buy" if new else "hold", "b": p["b"], "bp": sig(bp_idr), "ret": round(ret, 2)})
        lv["buy"] = sig(bp_idr)
        res["r"] = (f"Masuk {tgl(p['b'])} di sekitar {rp(bp_idr)}, sekarang {ret:+.1f}%. ".replace(".", ",", 1) +
                    f"Tetap dipegang selama masih 8 terkuat, di atas rata-rata 50 hari ({rp(s50_idr)}), dan lampu BTC hijau. Cek berikutnya {tgl(M['next'])}.")
        res["rs"] = "beli baru" if new else f"peringkat {rank}" if rank else "dipegang"
        return res
    recent = [x for x in hist if (date.fromisoformat(today) - date.fromisoformat(x["s"])).days <= 7]
    if recent:
        x = recent[-1]
        res.update({"s": "sell", "sd": x["s"], "sp": sig(x["sp"] * fx_series_last), "b": x["b"], "bp": sig(x["bp"] * fx_series_last), "ret": x["ret"], "why": x["r"]})
        res["r"] = f"Dijual {tgl(x['s'])} karena {x['r']} ({x['ret']:+.1f}%).".replace(".", ",", 1).replace(",)", ".)")
        res["rs"] = x["r"]
        return res
    if not green:
        res["r"], res["rs"] = "Lampu BTC merah: metode ini tidak membeli koin apa pun sampai BTC kembali di atas rata-rata 50 hari.", "lampu BTC merah"
    elif res["p"]:
        res["r"], res["rs"] = f"Semua syarat terpenuhi. Akan dibeli pada cek {tgl(M['next'])} bila masih 5 terkuat dan ada slot kosong.", "calon beli"
    else:
        bad = [x[0] for x in c if x[2] == 0]
        res["r"], res["rs"] = "Belum memenuhi: " + "; ".join(b[0].lower() + b[1:] for b in bad[:2]) + ".", (bad[0] if bad else "tunggu")
    return res


# ---------------------------------------------------------------- utama
def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    idx = indodax()
    log(f"Indodax: {len(idx)} pasangan IDR")
    coins = pick_coins(idx)
    if not coins:
        raise RuntimeError("Daftar koin kosong")
    # harga
    data, meta = {}, {}
    for c in coins:
        if len(data) >= TOP:
            break
        t = c["t"]
        n = 3000 if t == "BTC" else 2200  # ±6 tahun: cukup untuk uji metode sejak 2021
        df = klines(t + "USDT", n)
        if df is None or len(df) < 30:
            continue
        p = float(df.c.iloc[-1])
        if c.get("cgp") and abs(p / c["cgp"] - 1) > 0.08:
            log(f"  {t}: harga Binance {p} tidak cocok dengan CoinGecko {c['cgp']}, dilewati")
            continue
        data[t], meta[t] = df, c
        time.sleep(0.1)
    if "BTC" not in data:
        raise RuntimeError("Harga BTC gagal diambil")
    log(f"Harga {len(data)} koin")
    # kurs
    fx = None
    try:
        import yfinance as yf
        f = yf.download("IDR=X", period="10y", interval="1d", auto_adjust=True, progress=False)
        fx = f["Close"].squeeze().dropna()
        fx.index = pd.to_datetime(fx.index).tz_localize(None)
    except Exception as e:
        log(f"  kurs Yahoo gagal: {e}")
    usdt_idr = (idx.get("USDT") or {}).get("last")
    days = pd.date_range(min(d.index[0] for d in data.values()), max(d.index[-1] for d in data.values()), freq="D")
    if fx is None or fx.empty:
        if not usdt_idr:
            raise RuntimeError("Kurs USD/IDR tidak tersedia")
        fxs = pd.Series(usdt_idr, index=days)
    else:
        fxs = fx.reindex(fx.index.union(days)).ffill().bfill().reindex(days)
    fx_now = float(fxs.iloc[-1])
    cols = list(data)
    Cu = pd.DataFrame({t: data[t].c for t in cols}).reindex(days)
    Hu = pd.DataFrame({t: data[t].h for t in cols}).reindex(days)
    Lu = pd.DataFrame({t: data[t].l for t in cols}).reindex(days)
    Ou = pd.DataFrame({t: data[t].o for t in cols}).reindex(days)
    QV = pd.DataFrame({t: data[t].qv for t in cols}).reindex(days)
    C, H, L, O = (x.mul(fxs, axis=0) for x in (Cu, Hu, Lu, Ou))
    QVi = QV.mul(fxs, axis=0)
    now = datetime.now(timezone.utc)
    today = days[-1]
    done = Cu.loc[:today - pd.Timedelta(days=1)]  # candle yang sudah ditutup
    M, mstats = momentum(done.loc["2020-09-01":], {}, fx_now)
    fx_done = float(fxs.loc[done.index[-1]])
    # lampu BTC
    bd = done["BTC"].dropna()
    b50, b200 = float(bd.tail(50).mean()), float(bd.tail(200).mean())
    bl = float(bd.iloc[-1])
    lamp = {"g50": bl > b50, "g200": bl > b200, "d50": round((bl / b50 - 1) * 100, 2), "d200": round((bl / b200 - 1) * 100, 2),
            "s50": sig(b50 * fx_done), "s200": sig(b200 * fx_done), "close": sig(bl * fx_done), "date": done.index[-1].strftime("%Y-%m-%d")}
    # sejak kapan warnanya sama
    gs = (done["BTC"] > done["BTC"].rolling(50).mean()).dropna()
    flip = gs[gs != gs.iloc[-1]]
    lamp["since"] = (flip.index[-1] + pd.Timedelta(days=1)).strftime("%Y-%m-%d") if len(flip) else None
    rows = []
    for t in cols:
        c, m = C[t].dropna(), meta[t]
        o = {"ticker": t, "company": m["name"], "sector": m.get("cat") or "Lainnya", "rank": m.get("rank"),
             "mcap": round(m["mcap"] * fx_now / 1e9, 1) if m.get("mcap") else None}
        o.update(technicals(c))
        o["price"] = sig(o["price"])
        o["usd"] = sig(float(Cu[t].dropna().iloc[-1]))
        ix = idx.get(t)
        if ix:
            o["idx"] = sig(ix["last"])
            o["idxVol"] = round(ix["vol"] / 1e9, 2)
        cd = done[t].dropna()
        o["chg1d"] = round((float(Cu[t].dropna().iloc[-1]) / float(cd.iloc[-1]) - 1) * 100, 2) if len(cd) else None
        v = QVi[t]
        avg = float(v.loc[done.index[-30:]].mean()) if len(done) >= 30 else None
        o["adv"] = round(avg / 1e9, 2) if avg else None
        avg20 = float(v.loc[done.index[-20:]].mean()) if len(done) >= 20 else None
        # volume candle hari ini dibanding rata-rata, disesuaikan dengan jam yang sudah berjalan sejak 07.00 WIB
        frac = max((now - today.tz_localize("UTC")).total_seconds() / 86400, 1 / 24)
        tv = float(v.iloc[-1]) if np.isfinite(v.iloc[-1]) else 0
        o["val1d"] = round(tv)
        o["volR"] = round(tv / (avg20 * frac), 2) if avg20 else None
        o["rsi14"] = round(rsi(c, 14), 1) if rsi(c, 14) is not None else None
        o["rsi2"] = round(rsi(cd * fx_done, 2), 1) if rsi(cd, 2) is not None else None
        o["liq"] = "L"
        o["days"] = int(Cu[t].notna().sum())
        o["rk90"] = M["rank"].get(t)
        o["m"] = {"mom90": mom_state(t, M, o["price"], fx_done, now.date().isoformat())}
        rows.append({k: (round(v, 3) if isinstance(v, float) and abs(v) >= 1 else v) for k, v in o.items()})
    rows.sort(key=lambda o: o.get("rank") or 999)
    # cycles (support/resistance, siklus waktu) memakai harga Rupiah
    cycles.ALLDAYS, cycles.SIG, cycles.WEEK = True, 5, 7
    try:
        state = json.loads(CYC_STATE.read_text()) if CYC_STATE.exists() else {}
        long = {"BTC": C["BTC"].dropna()}
        cfg = {"ramadan": False, "holidays": set()}
        out, series = cycles.run(C, {"BTC": "BTC"}, long, [t for t in cols if t != "BTC"], cols, cfg, state)
        CYC_FILE.write_text(json.dumps(out, separators=(",", ":")))
        SERIES_FILE.write_text(cycles.dump_series(series))
        CYC_STATE.write_text(json.dumps(state, separators=(",", ":")))
    except Exception as e:
        import traceback
        traceback.print_exc()
        log(f"Siklus gagal: {e}")
    # candlestick untuk grafik
    OHLC_DIR.mkdir(parents=True, exist_ok=True)
    keep = set()
    for t in cols:
        rows_ = []
        for d in C.index[-BARS:]:
            cv = C.at[d, t]
            if not np.isfinite(cv):
                continue
            ov, hv, lv = (x.at[d, t] for x in (O, H, L))
            ov = cv if not np.isfinite(ov) else ov
            hv = max(x for x in (hv, ov, cv) if np.isfinite(x))
            lv = min(x for x in (lv, ov, cv) if np.isfinite(x))
            vv = QV.at[d, t] / Cu.at[d, t] if np.isfinite(QV.at[d, t]) and Cu.at[d, t] else 0
            rows_.append([d.strftime("%Y-%m-%d"), sig(ov), sig(hv), sig(lv), sig(cv), int(round(vv)) if vv >= 100 else round(float(vv), 4)])
        if len(rows_) < 30:
            continue
        name = "BTC" if t == "BTC" else t
        txt = '{"t":' + json.dumps(name) + ',"b":[\n' + ",\n".join(json.dumps(r, separators=(",", ":")) for r in rows_) + "\n]}"
        (OHLC_DIR / f"{name}.json").write_text(txt)
        keep.add(name)
    for f in OHLC_DIR.glob("*.json"):
        if f.stem not in keep:
            f.unlink()
    try:  # garis tren: statistik & rekam jejak, sekali setiap candle harian baru (candle hari ini belum selesai)
        import trend
        ts = OUT / "trend_stats.json"
        last_done = done.index[-1].strftime("%Y-%m-%d")
        if not ts.exists() or json.loads(ts.read_text()).get("date") != last_done:
            trend.run(OUT, FEE * 2, skip_last=True, log=log)
    except Exception as e:
        log(f"Garis tren gagal: {e}")
    prev = json.loads(OUT_FILE.read_text()) if OUT_FILE.exists() else {}
    wib = now.astimezone(timezone(timedelta(hours=7)))
    d_ = {
        "updatedAt": now.isoformat(timespec="seconds"),
        "priceDate": today.strftime("%Y-%m-%d"),
        "prevPriceDate": done.index[-1].strftime("%Y-%m-%d"),
        "intraday": {"at": now.isoformat(timespec="seconds"), "date": today.strftime("%Y-%m-%d"), "wib": wib.strftime("%H.%M")},
        "started": prev.get("started") or now.date().isoformat(),
        "count": len(rows), "fx": round(fx_now, 1), "usdtIdr": usdt_idr,
        "sources": {"prices": "Binance", "coins": "CoinGecko", "fx": "Yahoo Finance", "idr": "Indodax"},
        "lamp": lamp, "mom": {**mstats, "next": M["next"], "lastCandle": M["lastCandle"], "green": M["green"],
                              "pos": sorted(M["pos"]), "fee": FEE * 100},
        "stats": {"mom90": {k: mstats[k] for k in ("n", "win", "avg", "med")}},
        "hasDetail": False,
        "stocks": rows,
    }
    OUT_FILE.write_text(json.dumps(d_, separators=(",", ":"), ensure_ascii=False))
    (OUT / "ver.json").write_text(json.dumps({"v": d_["intraday"]["at"] + "|" + d_["updatedAt"], "p": d_["priceDate"]}))
    log(f"Selesai {len(rows)} koin dalam {time.time() - t0:.0f} detik. Lampu BTC: {'hijau' if lamp['g50'] else 'merah'}; "
        f"momentum memegang {', '.join(sorted(M['pos'])) or '—'}")
    summary(f"### Kripto\n{len(rows)} koin, lampu BTC {'🟢' if lamp['g50'] else '🔴'}, momentum: {', '.join(sorted(M['pos'])) or 'kosong'}")


if __name__ == "__main__":
    main()
