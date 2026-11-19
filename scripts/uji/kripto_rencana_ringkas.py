import json, random, statistics as stt, numpy as np, pandas as pd, glob, os
from kripto_rencana_uji import load, FEE, HOLD_DAYS
P = json.load(open("plans.json"))
btc = load("BTC"); s50 = btc.c.rolling(50).mean(); green = (btc.c > s50)
G = {str(d.date()): bool(v) for d, v in green.items()}
for r in P: r["lamp"] = G.get(r["d"])
F = [r for r in P if r.get("ret") is not None and r["res"] != "open"]
def summ(R, nm):
    if not R: print(f"{nm:38s} n=0"); return
    x = [r["ret"] for r in R]
    win = sum(v > 0 for v in x)/len(x)*100
    print(f"{nm:38s} n={len(x):5d} rata2 {np.mean(x):+6.2f}%  median {np.median(x):+6.2f}%  untung {win:4.0f}%  "
          f"target {sum(r['res']=='target' for r in R)/len(R)*100:3.0f}% stop {sum(r['res']=='stop' for r in R)/len(R)*100:3.0f}% waktu {sum(r['res']=='time' for r in R)/len(R)*100:3.0f}%  hari {np.mean([r['days'] for r in R]):4.1f}")
print("antrean tak terisi:", sum(r["res"]=="nofill" for r in P), "dari", sum(r["k"]=="queue" for r in P))
summ(F, "SEMUA")
summ([r for r in F if r["lamp"]], "Lampu HIJAU")
summ([r for r in F if r["lamp"] is False], "Lampu MERAH")
for k in ("now","queue"):
    summ([r for r in F if r["k"]==k and r["lamp"]], f"  {k} hijau"); summ([r for r in F if r["k"]==k and r["lamp"] is False], f"  {k} merah")
for z in ("kuat","sedang"):
    summ([r for r in F if r["z"]==z and r["lamp"]], f"  zona {z} hijau"); summ([r for r in F if r["z"]==z and r["lamp"] is False], f"  zona {z} merah")
print("\nper tahun (semua / hijau / merah):")
for y in range(2021, 2027):
    Y = [r for r in F if r["d"].startswith(str(y))]
    a = lambda R: f"{np.mean([r['ret'] for r in R]):+5.1f}% (n={len(R)})" if R else "-"
    print(y, a(Y), "|", a([r for r in Y if r["lamp"]]), "|", a([r for r in Y if r["lamp"] is False]))

# pembanding: masuk acak, koin & hari acak dengan status lampu sama, stop/target relatif sama
D = {os.path.basename(f)[:-5]: load(os.path.basename(f)[:-5]) for f in glob.glob("ohlc/*.json")}
D.pop("BTC")
pool = {True: [], False: []}
for t, df in D.items():
    ds = [str(x.date()) for x in df.index]
    for i, d in enumerate(ds):
        if d >= "2021-01-01" and i < len(ds) - 2 and G.get(d) is not None: pool[G[d]].append((t, i))
rng = random.Random(7)
def rand_trade(r):
    t, i = rng.choice(pool[r["lamp"]]); df = D[t]
    O,H,L,C = df.o.values, df.h.values, df.l.values, df.c.values
    e = C[i]; s = e*(1+r["stp"]); g = e*(1+r["tgp"]) if r["tgp"] is not None else None
    for j in range(i+1, min(len(C), i+1+HOLD_DAYS)):
        if g and H[j] >= g: return (max(g,O[j])*(1-FEE)/(e*(1+FEE))-1)*100
        if C[j] < s: return (C[j]*(1-FEE)/(e*(1+FEE))-1)*100
    j = min(len(C)-1, i+HOLD_DAYS); return (C[j]*(1-FEE)/(e*(1+FEE))-1)*100
print("\npembanding acak (stop/target sama, 20x per transaksi):")
for nm, R in (("semua", F), ("hijau", [r for r in F if r["lamp"]]), ("merah", [r for r in F if r["lamp"] is False])):
    rr = [rand_trade(r) for r in R for _ in range(20)]
    print(f"  {nm}: acak rata2 {np.mean(rr):+.2f}%  untung {sum(v>0 for v in rr)/len(rr)*100:.0f}%   vs rencana {np.mean([r['ret'] for r in R]):+.2f}%")
# selisih per tahun hijau
print("\nnow+hijau per tahun:")
for y in range(2021,2027):
    Y=[r['ret'] for r in F if r['d'].startswith(str(y)) and r['lamp']]
    print(y, f"{np.mean(Y):+.2f}% n={len(Y)}" if Y else "-")
print("\nsubset vs acak + interval 90% (bootstrap):")
def boot(x, n=2000):
    x=np.array(x); m=[np.mean(rng.choices(list(x),k=len(x))) for _ in range(n)]; return np.percentile(m,[5,95])
for nm, R in (("now hijau",[r for r in F if r["k"]=="now" and r["lamp"]]),("kuat hijau",[r for r in F if r["z"]=="kuat" and r["lamp"]]),("now+kuat hijau",[r for r in F if r["k"]=="now" and r["z"]=="kuat" and r["lamp"]])):
    rr=[rand_trade(r) for r in R for _ in range(20)]; x=[r["ret"] for r in R]; lo,hi=boot(x)
    print(f"  {nm}: n={len(x)} rencana {np.mean(x):+.2f}% [{lo:+.2f}..{hi:+.2f}]  acak {np.mean(rr):+.2f}%  tahun>0: {sum(np.mean([r['ret'] for r in R if r['d'].startswith(str(y))] or [0])>0 for y in range(2021,2027))}/6")
