"""
Pesan Telegram ringkas untuk Screener Saham.

  python scripts/notify_telegram.py             # ringkasan pagi (setelah data diperbarui)
  python scripts/notify_telegram.py --reminder  # pengingat order 19.30 WIB sebelum bursa AS buka
  python scripts/notify_telegram.py --failed    # peringatan bila pembaruan data gagal
  tambahkan --dry-run untuk mencetak pesan tanpa mengirim

Butuh secret TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID. Jika belum diisi, pesan hanya dicetak.
"""
from __future__ import annotations

import html
import json
import os
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "stocks.json"
SITE = "https://sultanamra3-arch.github.io/screener-saham/"
TOP = 5
NY, WIB = ZoneInfo("America/New_York"), ZoneInfo("Asia/Jakarta")
NAMES = {"value": "Value", "growth": "Growth", "quality": "Quality", "dividend": "Dividen",
         "canslim": "CAN SLIM", "momentum": "Momentum", "swing": "Swing"}
# Urutan prioritas tampil: jangka panjang dulu, swing (paling sering dan paling pendek) terakhir
ORDER = ["canslim", "value", "growth", "quality", "dividend", "momentum", "swing"]
HARI = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
# Hari libur NYSE (bursa tutup penuh)
HOLIDAYS = {
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19", "2026-07-03",
    "2026-09-07", "2026-11-26", "2026-12-25",
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31", "2027-06-18", "2027-07-05",
    "2027-09-06", "2027-11-25", "2027-12-24",
}


def usd(v) -> str:
    if not isinstance(v, (int, float)):
        return "–"
    s = f"{v:,.2f}"
    return "$" + s.replace(",", "_").replace(".", ",").replace("_", ".")


def pct(v) -> str:
    if not isinstance(v, (int, float)):
        return "–"
    s = f"{abs(v):.1f}".replace(".", ",")
    return ("+" if v > 0 else "−" if v < 0 else "") + s + "%"


def ribu(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def b(t) -> str:
    return f"<b>{html.escape(str(t))}</b>"


def e(t) -> str:
    return html.escape(str(t or ""))


def hari(d: str, year=False) -> str:
    dt = date.fromisoformat(d)
    return f"{HARI[dt.weekday()]} {dt.day} {BULAN[dt.month - 1]}" + (f" {dt.year}" if year else "")


def plan_text(mid: str, st: dict) -> str:
    lv = st.get("lv") or {}
    if mid == "canslim":
        return f"stop {usd(lv.get('stop'))} · target {usd(lv.get('target'))}"
    if mid == "swing":
        return f"jual saat tutup > SMA5 ({usd(lv.get('exit'))}), tanpa stop"
    if mid == "momentum":
        return "tanpa stop, dicek tiap awal bulan"
    if mid == "value":
        return f"target {usd(lv.get('target'))} (+50%) atau 2 tahun"
    if mid == "growth":
        return f"jual ≥ {usd(lv.get('target'))} (PEG 2)"
    if mid == "quality":
        return "tanpa stop/target, tahan selama kualitas terjaga"
    if mid == "dividend":
        return "tanpa stop/target, tahan selama dividen aman"
    return ""


def signals(d: dict):
    day = d.get("priceDate")
    buys, sells, holds, first = [], [], 0, 0
    for o in d.get("stocks", []):
        npass = sum(1 for m in (o.get("m") or {}).values() if m.get("p"))
        for mid in ORDER:
            st = (o.get("m") or {}).get(mid) or {}
            s = st.get("s")
            if s == "buy" and st.get("b") == day:
                if st.get("first"):
                    first += 1
                else:
                    buys.append((o, mid, st, npass))
            elif s == "sell" and st.get("sd") == day:
                sells.append((o, mid, st, npass))
            elif s == "hold":
                holds += 1
    key = lambda x: (ORDER.index(x[1]), -x[3], -(x[0].get("mcap") or 0))
    buys.sort(key=key)
    sells.sort(key=key)
    return buys, sells, holds, first


def morning(d: dict) -> str | None:
    if d.get("newSession") is False:
        print("Tidak ada sesi bursa baru sejak pembaruan sebelumnya (libur bursa AS); pesan tidak dikirim.")
        return None
    day = d["priceDate"]
    buys, sells, holds, first = signals(d)
    L = [f"📊 {b('Screener Saham — ' + hari(day))}",
         f"🟢 Beli baru: {len(buys)} · 🔴 Jual: {len(sells)} · ⏳ Tahan: {holds}"]
    mk = d.get("market") or {}
    if mk.get("ok") is not None:
        L.append("Pasar AS: " + ("naik ✅" if mk["ok"] else "tertekan ⚠️ (CAN SLIM tidak membeli)"))
    if first:
        L += ["", f"ℹ️ Pencatatan sinyal investor dimulai hari ini: {first} posisi awal (lihat website)."]
    if buys:
        L += ["", b(f"Beli ({min(len(buys), TOP)} teratas)")]
        for o, mid, st, _ in buys[:TOP]:
            L.append(f"{b(o['ticker'])} {usd(st.get('bp'))} · {plan_text(mid, st)}")
            L.append(f"<i>{e(NAMES[mid])}: {e(st.get('rs'))}</i>")
        if len(buys) > TOP:
            L.append(f"…dan {len(buys) - TOP} lainnya di website")
    if sells:
        L += ["", b(f"Jual ({min(len(sells), TOP)} teratas)")]
        for o, mid, st, _ in sells[:TOP]:
            L.append(f"{b(o['ticker'])} {usd(st.get('sp'))} · <i>{e(NAMES[mid])}: {e(st.get('rs'))}</i>")
        if len(sells) > TOP:
            L.append(f"…dan {len(sells) - TOP} lainnya di website")
    if not buys and not sells:
        L += ["", "Tidak ada sinyal beli atau jual baru hari ini."]
    if d.get("showComparison") and d.get("stats"):
        L += ["", b("Aturan baru vs lama (uji mundur 1 tahun)")]
        lg = d.get("legacy") or {}
        if lg.get("n"):
            L.append(f"Lama: {ribu(lg['n'])} transaksi, {pct(lg['win']).lstrip('+')} untung, rata-rata {pct(lg['avg'])}, {lg['med']} hari")
        for mid in ("canslim", "momentum", "swing"):
            s = d["stats"].get(mid) or {}
            if s.get("n"):
                L.append(f"{NAMES[mid]}: {ribu(s['n'])} transaksi, {pct(s['win']).lstrip('+')} untung, rata-rata {pct(s['avg'])}, {s['med']} hari")
    L += ["", f'🔗 <a href="{SITE}">Detail dan alasan lengkap di website</a>']
    return "\n".join(L)


def reminder(d: dict, now: datetime | None = None) -> str | None:
    now = now or datetime.now(NY)
    today = now.astimezone(NY).date()
    if today.weekday() >= 5 or today.isoformat() in HOLIDAYS:
        print(f"Bursa AS tutup hari ini ({today}); pengingat tidak dikirim.")
        return None
    pd_ = d.get("priceDate")
    if not pd_ or (today - date.fromisoformat(pd_)).days > 4:
        print("Data belum diperbarui; pengingat tidak dikirim.")
        return None
    buys, _, _, _ = signals(d)
    if not buys:
        print("Tidak ada sinyal beli baru; pengingat tidak dikirim.")
        return None
    open_wib = datetime.combine(today, time(9, 30), NY).astimezone(WIB)
    L = [f"⏰ {b('Bursa AS buka ' + open_wib.strftime('%H.%M') + ' WIB')}",
         "Order dari sinyal pagi ini (harga beli = harga penutupan terakhir):", ""]
    for o, mid, st, _ in buys[:8]:
        L.append(f"{b(o['ticker'])} beli sekitar {usd(st.get('bp'))} · {plan_text(mid, st)} ({NAMES[mid]})")
    if len(buys) > 8:
        L.append(f"…dan {len(buys) - 8} lainnya di website")
    L += ["", "Pasang stop loss dan target sebagai order GTC bila broker Anda mendukung."]
    return "\n".join(L)


def failed_message() -> str:
    run = "{}/{}/actions/runs/{}".format(os.environ.get("GITHUB_SERVER_URL", "https://github.com"),
                                         os.environ.get("GITHUB_REPOSITORY", "sultanamra3-arch/screener-saham"),
                                         os.environ.get("GITHUB_RUN_ID", ""))
    return ("⚠️ " + b("Screener Saham: pembaruan data gagal") + "\n"
            "Website masih menampilkan data sebelumnya.\n"
            f'<a href="{run}">Lihat penyebabnya di GitHub</a>')


def split(msg: str, limit: int = 3900) -> list[str]:
    parts, cur = [], ""
    for line in msg.split("\n"):
        if len(cur) + len(line) + 1 > limit and cur:
            parts.append(cur)
            cur = ""
        cur = (cur + "\n" + line) if cur else line
    if cur:
        parts.append(cur)
    return parts


def send(msg: str):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat:
        print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum diisi; pesan tidak dikirim.\n")
        print(msg)
        return
    for part in split(msg):
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat, "text": part, "parse_mode": "HTML", "disable_web_page_preview": True},
                          timeout=30)
        if r.status_code != 200:
            try:
                desc = r.json().get("description", "")
            except Exception:
                desc = r.text[:200]
            sys.exit(f"Telegram menolak pesan (HTTP {r.status_code}): {desc}. Cek TELEGRAM_BOT_TOKEN dan "
                     "TELEGRAM_CHAT_ID, dan pastikan Anda sudah menekan Start di bot.")
    print(f"Terkirim ke Telegram ({len(split(msg))} pesan)")


def main():
    if "--failed" in sys.argv:
        msg = failed_message()
    else:
        d = json.loads(DATA_FILE.read_text())
        msg = reminder(d) if "--reminder" in sys.argv else morning(d)
    if not msg:
        return
    if "--dry-run" in sys.argv:
        print(msg)
    else:
        send(msg)


if __name__ == "__main__":
    main()
