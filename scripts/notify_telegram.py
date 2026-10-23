"""
Kirim ringkasan screener ke Telegram setelah data diperbarui.

Butuh secret TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID. Jika belum diisi, skrip
hanya mencetak pesan dan selesai tanpa error.

  python scripts/notify_telegram.py            # ringkasan harian
  python scripts/notify_telegram.py --failed   # peringatan bila pengambilan data gagal
  python scripts/notify_telegram.py --dry-run  # cetak pesan saja
"""
from __future__ import annotations

import html
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "stocks.json"
SITE = "https://sultanamra3-arch.github.io/screener-saham/"
RUN_URL = "{server}/{repo}/actions/runs/{run}"
STOP, TARGET = 0.08, 0.25
TOP = 10
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
HARI = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
REASON = {"stop": "kena stop loss", "target": "target tercapai", "trend": "tren patah (di bawah SMA50)"}

# Kriteria default 7 metode (sama dengan website)
METHODS = {
    "Value": [("pe", ">", 0), ("pe", "<=", 15), ("pb", "<=", 1.5), ("graham", "<=", 22.5), ("de", "<=", 1), ("cr", ">=", 1.5)],
    "Growth": [("eps5y", ">=", 15), ("sales5y", ">=", 10), ("epsTTM", ">=", 15), ("peg", "<=", 1.5)],
    "Quality": [("roe", ">=", 15), ("gm", ">=", 40), ("om", ">=", 15), ("de", "<=", 0.5), ("eps5y", ">", 0)],
    "Dividen": [("div", ">=", 2.5), ("payout", ">", 0), ("payout", "<=", 70), ("de", "<=", 1), ("eps5y", ">=", 0)],
    "Momentum": [("perf1y", ">=", 20), ("perf6m", ">=", 10), ("sma200", ">", 0), ("sma50", ">", 0), ("hi52", ">=", -15)],
    "CAN SLIM": [("epsQ", ">=", 25), ("epsTTM", ">=", 25), ("salesQ", ">=", 20), ("hi52", ">=", -15), ("relSP", ">=", 10), ("sma50", ">", 0)],
    "Swing": [("sma200", ">", 0), ("sma50", ">", 0), ("sma20", ">=", -4), ("sma20", "<=", 2), ("rsi", ">=", 40), ("rsi", "<=", 60)],
}


def val(o: dict, k: str):
    if k == "graham":
        return o["pe"] * o["pb"] if (o.get("pe") or 0) > 0 and (o.get("pb") or 0) > 0 else None
    if k == "peg":
        return o["pe"] / o["eps5y"] if (o.get("pe") or 0) > 0 and (o.get("eps5y") or 0) > 0 else None
    v = o.get(k)
    return v if isinstance(v, (int, float)) else None


def passed_methods(o: dict) -> list[str]:
    out = []
    for name, crit in METHODS.items():
        ok = True
        for k, op, t in crit:
            v = val(o, k)
            if v is None or not {">": v > t, ">=": v >= t, "<=": v <= t, "<": v < t}[op]:
                ok = False
                break
        if ok:
            out.append(name)
    return out


def usd(v) -> str:
    if v is None:
        return "–"
    s = f"{v:,.2f}"  # 1,234.56
    return "$" + s.replace(",", "_").replace(".", ",").replace("_", ".")


def pct(v) -> str:
    return "–" if v is None else (("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v):.1f}".replace(".", ",") + "%")


def tanggal(d: str, hari: bool = False) -> str:
    dt = datetime.strptime(d, "%Y-%m-%d")
    return (f"{HARI[dt.weekday()]} " if hari else "") + f"{dt.day} {BULAN[dt.month - 1]} {dt.year}"


def b(t) -> str:
    return f"<b>{html.escape(str(t))}</b>"


def build_message(d: dict) -> str:
    day = d.get("priceDate") or d["updatedAt"][:10]
    rows = d["stocks"]
    tr_buy, tr_sell, inv_buy, inv_sell, multi = [], [], [], [], []
    for o in rows:
        t = o.get("trSig") or {}
        last = (t.get("trades") or [None])[-1]
        if last and last.get("b") == day and not last.get("s"):
            tr_buy.append((o, last))
        elif last and last.get("s") == day:
            tr_sell.append((o, last))
        g, plan = o.get("invSig") or {}, o.get("invPlan") or {}
        if g and not g.get("first") and g.get("since") == day:
            if g.get("s") == "buy":
                inv_buy.append((o, plan))
            elif g.get("s") == "sell":
                inv_sell.append((o, plan))
        pm = passed_methods(o)
        if len(pm) >= 4:
            multi.append((o, pm))

    big = lambda x: -(x[0].get("mcap") or 0)
    tr_buy.sort(key=big); tr_sell.sort(key=big); inv_buy.sort(key=big); inv_sell.sort(key=big)
    multi.sort(key=lambda x: (-len(x[1]), -(x[0].get("mcap") or 0)))

    L = [f"📊 {b('Screener Saham — ' + tanggal(day, True))}", f"{len(rows)} saham diperbarui (harga penutupan {tanggal(day)})", ""]

    def section(title, items, fmt):
        if not items:
            return
        L.append(title)
        for it in items[:TOP]:
            L.append(fmt(*it).rstrip("\n"))
            L.append("")
        if len(items) > TOP:
            L.append(f"…dan {len(items) - TOP} lainnya di website")
            L.append("")

    section("🟢 " + b("Baru jadi BELI (trader)"), tr_buy, lambda o, x: (
        f"{b(o['ticker'])} sekarang {usd(o.get('price'))}\n"
        f"Beli: {usd(x['bp'])} · Stop loss: {usd(x['bp'] * (1 - STOP))} · Target: {usd(x['bp'] * (1 + TARGET))}\n"))
    section("🔴 " + b("Baru jadi JUAL (trader)"), tr_sell, lambda o, x: (
        f"{b(o['ticker'])} sekarang {usd(o.get('price'))}, {REASON.get(x['r'], x['r'])}\n"
        f"Beli {tanggal(x['b'])} di {usd(x['bp'])}, hasil {pct(x['ret'])}\n"))
    section("🟢 " + b("Baru jadi BELI (investor)"), inv_buy, lambda o, p: (
        f"{b(o['ticker'])} sekarang {usd(o.get('price'))}\n"
        f"Beli ≤ {usd(p.get('buy'))} · Target (nilai wajar): {usd(p.get('fv'))} · Jual ≥ {usd(p.get('sell'))}\n"))
    section("🔴 " + b("Baru jadi JUAL (investor)"), inv_sell, lambda o, p: (
        f"{b(o['ticker'])} sekarang {usd(o.get('price'))}, sudah di atas harga jual {usd(p.get('sell'))}\n"
        f"Nilai wajar: {usd(p.get('fv'))}\n"))

    if not (tr_buy or tr_sell or inv_buy or inv_sell):
        L += ["Tidak ada sinyal beli atau jual baru hari ini.", ""]

    if multi:
        L.append("⭐ " + b(f"Lolos ≥4 metode ({len(multi)} saham)"))
        for o, pm in multi[:TOP]:
            L.append(f"{b(o['ticker'])} {usd(o.get('price'))} · {len(pm)}/7: {', '.join(pm)}")
        L.append("")

    L.append(f'🔗 <a href="{SITE}">Buka screener</a>')
    L.append("<i>Hitungan mekanis dengan pengaturan default, bukan saran investasi.</i>")
    return "\n".join(L)


def failed_message() -> str:
    run = RUN_URL.format(server=os.environ.get("GITHUB_SERVER_URL", "https://github.com"),
                         repo=os.environ.get("GITHUB_REPOSITORY", "sultanamra3-arch/screener-saham"),
                         run=os.environ.get("GITHUB_RUN_ID", ""))
    return ("⚠️ " + b("Screener Saham: pembaruan data gagal") + "\n"
            "Website masih menampilkan data sebelumnya.\n"
            f'<a href="{run}">Lihat penyebabnya di GitHub</a>')


def split(msg: str, limit: int = 3900) -> list[str]:
    parts, cur = [], ""
    for block in msg.split("\n\n"):
        if len(cur) + len(block) + 2 > limit and cur:
            parts.append(cur)
            cur = ""
        cur = (cur + "\n\n" + block) if cur else block
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
                          json={"chat_id": chat, "text": part, "parse_mode": "HTML",
                                "disable_web_page_preview": True}, timeout=30)
        if r.status_code != 200:
            desc = (r.json() or {}).get("description", r.text[:200]) if r.headers.get("content-type", "").startswith("application/json") else r.text[:200]
            sys.exit(f"Telegram menolak pesan (HTTP {r.status_code}): {desc}. Cek TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID, "
                     "dan pastikan Anda sudah mengirim pesan ke bot lebih dulu.")
    print(f"Terkirim ke Telegram ({len(split(msg))} pesan)")


def main():
    if "--failed" in sys.argv:
        msg = failed_message()
    else:
        msg = build_message(json.loads(DATA_FILE.read_text()))
    if "--dry-run" in sys.argv:
        print(msg)
    else:
        send(msg)


if __name__ == "__main__":
    main()
