# Uji mundur "Rencana beli" kripto (20 Nov 2026). Jalankan berurutan dari folder kerja kosong:
#   python3 kripto_rencana_ambil.py   -> ohlc/*.json (Binance, USDT)
#   python3 kripto_rencana_uji.py     -> plans.json
#   python3 kripto_rencana_ringkas.py -> ringkasan per lampu BTC + pembanding acak
# Hasil dirangkum ke kripto/data/longtest.json ("plan").
import json, math, sys, os, random, glob
from multiprocessing import Pool
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cycles
cycles.ALLDAYS, cycles.SIG, cycles.WEEK = True, 5, 7
RR_MIN, UP_MIN, IN_ABOVE, NEAR_ABOVE, BRK = 2.0, 5.0, 0.02, 0.05, 0.01
QUEUE_DAYS, HOLD_DAYS, FEE = 10, 40, 0.003
START = "2021-01-01"

def load(t):
    b = json.load(open(f"ohlc/{t}.json"))
    df = pd.DataFrame(b, columns=["d","o","h","l","c"]); df["d"] = pd.to_datetime(df.d); return df.set_index("d")

def thr_np(c):
    r = np.abs(np.diff(c[-253:]) / c[-253:-1])
    return float(min(0.25, max(0.03, 8 * r.mean()))) if len(r) else 0.06

def analyse_at(c, idx):
    s = pd.Series(c, index=idx)
    thr = thr_np(c)
    piv, tent = cycles.zigzag(c, thr)
    sup, res = cycles.zones(s, thr, piv, tent, None)
    return sup, res

def floor_dn(v): return v  # tanpa tick: kripto memakai harga desimal

def plan_for(p, sup, res):
    # support_status
    st, z = None, None
    for zz in sup:
        if zz["lo"]*(1-BRK) <= p <= zz["hi"]*(1+IN_ABOVE): st, z = "in", zz; break
    if not z and sup and sup[0]["strength"] in ("kuat","sedang") and sup[0]["hi"]*(1+IN_ABOVE) < p <= sup[0]["hi"]*(1+NEAR_ABOVE):
        st, z = "near", sup[0]
    if not z or z["strength"] == "lemah": return None
    r1 = next((x for x in res if x["strength"] != "lemah"), None)
    brk = z["lo"]*(1-BRK)
    def mk(kind, e, stop, zz):
        risk = max(e-stop, e*0.005); up = (r1["lo"]/e-1)*100 if r1 else None; rr = (r1["lo"]-e)/risk if r1 else None
        ok = r1 is None or (rr >= RR_MIN and up >= UP_MIN)
        return dict(k=kind, e=e, s=stop, g=r1["lo"] if r1 else None, rr=rr, z=zz["strength"], ok=ok)
    if st == "in":
        x = mk("now", p, brk, z)
        if x["ok"]: return x
    else:
        x = mk("queue", z["hi"], brk, z)
        if x["ok"] and z["hi"] < p: return x
    below = sorted((s for s in sup if s["strength"] != "lemah" and s["hi"] < z["lo"]), key=lambda s: -s["hi"])
    if below:
        s2 = below[0]; x = mk("queue", s2["hi"], s2["lo"]*0.99, s2)
        if x["ok"]: return x
    return None

def simulate(df, i0, pl):
    """mulai dari bar i0+1. kembalikan dict hasil atau None (antrean tak terisi)."""
    O,H,L,C = df.o.values, df.h.values, df.l.values, df.c.values
    n = len(C); ip = None; held = 0; w = 0
    if pl["k"] == "now": ip = pl["e"]
    i = i0 + 1
    while i < n:
        if ip is None:
            w += 1
            if L[i] <= pl["e"]:
                ip = min(pl["e"], O[i])
                if C[i] < pl["s"]: return dict(res="stop", ip=ip, xp=C[i], xi=i, ei=i)
                ei = i; i += 1; continue
            if w >= QUEUE_DAYS: return dict(res="nofill", xi=i)
            i += 1; continue
        held += 1
        if pl["g"] and H[i] >= pl["g"]: return dict(res="target", ip=ip, xp=max(pl["g"], O[i]), xi=i)
        if C[i] < pl["s"]: return dict(res="stop", ip=ip, xp=C[i], xi=i)
        if held >= HOLD_DAYS: return dict(res="time", ip=ip, xp=C[i], xi=i)
        i += 1
    return dict(res="open", ip=ip, xp=C[n-1] if ip else None, xi=n-1) if ip else dict(res="nofill", xi=n-1)

def ret(ip, xp): return (xp*(1-FEE)/(ip*(1+FEE))-1)*100

def run_coin(t):
    df = load(t)
    if t == "BTC": return []
    c_all = df.c.values.astype(float); idx = df.index
    out = []; busy_until = -1
    for i in range(len(df)):
        if str(idx[i].date()) < START or i < 119: continue
        if i <= busy_until: continue
        lo = max(0, i-699); c = c_all[lo:i+1]
        try: sup, res = analyse_at(c, idx[lo:i+1])
        except Exception: continue
        pl = plan_for(float(c[-1]), sup, res)
        if not pl: continue
        r = simulate(df, i, pl)
        busy_until = r["xi"]
        rec = dict(t=t, d=str(idx[i].date()), k=pl["k"], z=pl["z"], e=pl["e"], s=pl["s"], g=pl["g"], res=r["res"])
        if r.get("ip"):
            rec.update(ip=r["ip"], xp=r["xp"], ret=ret(r["ip"], r["xp"]), days=r["xi"]-i,
                       stp=(pl["s"]/r["ip"]-1), tgp=(pl["g"]/r["ip"]-1) if pl["g"] else None, xd=str(idx[r["xi"]].date()))
        out.append(rec)
    return out

if __name__ == "__main__":
    ts = [os.path.basename(f)[:-5] for f in glob.glob("ohlc/*.json")]
    with Pool(os.cpu_count()) as p:
        allr = sum(p.map(run_coin, ts), [])
    json.dump(allr, open("plans.json","w"))
    print(len(allr), "rencana")
