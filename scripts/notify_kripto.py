"""Pesan Telegram untuk screener kripto (bot yang sama dengan screener saham, pesan terpisah berjudul ₿).

- Ringkasan harian: pembaruan pertama setelah candle harian ditutup (07.00 WIB).
- Selama hari berjalan (tiap jam): hanya bila ada koin yang BARU masuk area support kuat/sedang
  saat Lampu BTC hijau. Antara 22.00–06.00 WIB pesan dikirim tanpa bunyi.
Status yang sudah dikirim disimpan di kripto/data/notify_state.json supaya tidak berulang.
"""
from __future__ import annotations

import html
import json
import math
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notify_telegram import send  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "kripto" / "data"
STATE = D / "notify_state.json"
SITE = "https://sultanamra3-arch.github.io/screener-saham/kripto/"
WIB = timezone(timedelta(hours=7))
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def rp(v) -> str:
    if v is None or not isinstance(v, (int, float)) or not math.isfinite(v):
        return "–"
    d = 0 if v >= 1000 else 2 if v >= 1 else min(8, 3 - math.floor(math.log10(v)))
    return "Rp" + f"{v:,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def pc(v, d=1) -> str:
    if v is None:
        return "–"
    return ("+" if v > 0 else "") + f"{v:.{d}f}".replace(".", ",") + "%"


def tgl(s: str) -> str:
    y, m, d = s.split("-")
    return f"{int(d)} {BULAN[int(m) - 1]}"


def e(s) -> str:
    return html.escape(str(s))


def daily(d: dict, cyc: dict, st: dict) -> str:
    L, mo, rows = d["lamp"], d.get("mom") or {}, {o["ticker"]: o for o in d["stocks"]}
    lines = [f"<b>₿ Kripto · {tgl(L['date'])}</b>"]
    flip = st.get("g50") is not None and st.get("g50") != L["g50"]
    if L["g50"]:
        lines.append(("🟢 <b>Lampu BTC berubah HIJAU</b>" if flip else "🟢 Lampu BTC hijau") +
                     f": BTC {pc(L['d50'])} dari rata-rata 50 hari. Boleh aktif di altcoin, ikuti yang paling kuat.")
    else:
        lines.append(("🔴 <b>Lampu BTC berubah MERAH</b>" if flip else "🔴 Lampu BTC merah") +
                     f": BTC {pc(L['d50'])} dari rata-rata 50 hari. Jangan beli altcoin baru; yang di bawah rata-rata 50 hari pertimbangkan dijual.")
    if st.get("g200") is not None and st.get("g200") != L["g200"]:
        lines.append(f"{'📈' if L['g200'] else '📉'} <b>BTC {'kembali di atas' if L['g200'] else 'turun di bawah'} rata-rata 200 hari</b> ({rp(L['s200'])}): aturan BTC Tren 200 {'boleh simpan BTC lagi' if L['g200'] else 'menjual BTC'}.")
    held = [o for o in d["stocks"] if (o.get("m") or {}).get("mom90", {}).get("s") in ("buy", "hold")]
    new = [o for o in held if o["m"]["mom90"]["s"] == "buy"]
    sold = [o for o in d["stocks"] if (o.get("m") or {}).get("mom90", {}).get("s") == "sell" and o["m"]["mom90"].get("sd") == mo.get("lastCandle")]
    if new or sold:
        lines.append("")
        lines.append("<b>📊 Momentum 90 hari, hasil cek terbaru</b>")
        for o in new:
            lines.append(f"🟢 Beli <b>{e(o['ticker'])}</b> ~{rp(o['price'])} (90 hari {pc(o.get('perf90'), 0)}, peringkat #{o.get('rk90')})")
        for o in sold:
            m = o["m"]["mom90"]
            lines.append(f"🔴 Jual <b>{e(o['ticker'])}</b> ~{rp(o['price'])} ({e(m.get('why') or '')}, {pc(m.get('ret'))})")
    if held:
        lines.append("")
        lines.append("💼 Dipegang metode: " + ", ".join(f"{e(o['ticker'])} {pc(o['m']['mom90'].get('ret'), 0)}" for o in held))
    elif L["g50"]:
        lines.append(f"💼 Metode belum memegang koin. Cek berikutnya {tgl(mo['next'])}.")
    w = (cyc or {}).get("watch") or {}
    ins = [t for t in (w.get("new") or []) if t in rows and w.get("in", {}).get(t, {}).get("strength") in ("kuat", "sedang")]
    if ins:
        lines.append("")
        lines.append("📍 Baru masuk area support: " + ", ".join(f"{e(t)} ({w['in'][t]['strength']})" for t in ins[:8]) +
                     ("" if L["g50"] else " — lampu merah, support lebih gampang jebol."))
    spikes = sorted([o for o in d["stocks"] if (o.get("volR") or 0) >= 2.5 and (o.get("val1d") or 0) >= 20e9], key=lambda o: -o["volR"])[:4]
    if spikes:
        lines.append("🔥 Volume melonjak: " + ", ".join(f"{e(o['ticker'])} {o['volR']:.1f}×".replace(".", ",") for o in spikes))
    lines.append(f'\n<a href="{SITE}">Buka screener kripto</a> · hitungan otomatis, bukan nasihat keuangan')
    return "\n".join(lines)


def hourly(d: dict, cyc: dict, st: dict) -> str | None:
    L, rows = d["lamp"], {o["ticker"]: o for o in d["stocks"]}
    if not L["g50"]:
        return None
    w = (cyc or {}).get("watch") or {}
    sent = set(st.get("sentIn") or [])
    ins = [t for t, z in (w.get("in") or {}).items() if t in rows and z.get("strength") in ("kuat", "sedang") and t not in sent]
    if not ins:
        return None
    st["sentIn"] = sorted(sent | set(ins))
    lines = ["<b>₿ Masuk area support</b> (Lampu BTC hijau)"]
    for t in ins[:8]:
        z, o = w["in"][t], rows[t]
        lines.append(f"📍 <b>{e(t)}</b> {rp(o['price'])} · zona {rp(z['lo'])}–{rp(z['hi'])} ({z['strength']}), batal bila ditutup di bawah {rp(z['brk'])}")
    lines.append(f'<a href="{SITE}#watch">Lihat Watchlist</a>')
    return "\n".join(lines)


def main():
    d = json.loads((D / "stocks.json").read_text())
    cyc = json.loads((D / "cycles.json").read_text()) if (D / "cycles.json").exists() else {}
    st = json.loads(STATE.read_text()) if STATE.exists() else {}
    now = datetime.now(WIB)
    day = d["lamp"]["date"]
    msg, silent = None, now.hour >= 22 or now.hour < 6
    if st.get("day") != day:  # candle harian baru ditutup: ringkasan pagi
        msg = daily(d, cyc, st)
        st.update({"day": day, "g50": d["lamp"]["g50"], "g200": d["lamp"]["g200"],
                   "sentIn": sorted(((cyc or {}).get("watch") or {}).get("in", {}).keys())})
        silent = False
    else:
        msg = hourly(d, cyc, st)
    STATE.write_text(json.dumps(st))
    if not msg:
        print("Kripto: tidak ada pesan.")
        return
    if "--dry-run" in sys.argv:
        print(msg)
    else:
        send(msg, silent=silent)


if __name__ == "__main__":
    main()
