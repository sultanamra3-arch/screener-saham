"""Gerbang update harga tiap jam: jalan hanya saat bursa AS buka (jam New York, ikut pergantian musim
panas/dingin otomatis). Mencetak SKIP=0/1 untuk GITHUB_ENV."""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        return "0"
    ny = datetime.now(ZoneInfo("America/New_York"))
    try:
        import notify_telegram
        hol = notify_telegram.HOLIDAYS
    except Exception:
        hol = set()
    hm = ny.hour * 60 + ny.minute
    if ny.weekday() >= 5 or ny.date().isoformat() in hol:
        return "1"
    if not (9 * 60 + 45 <= hm <= 16 * 60 + 20):
        return "1"
    # Ada dua pemicu per jam sebagai cadangan: lewati bila update terakhir masih baru.
    try:
        cur = json.loads((Path(__file__).resolve().parent.parent / "data" / "stocks.json").read_text())
        at = (cur.get("intraday") or {}).get("at")
        if at and datetime.now(timezone.utc) - datetime.fromisoformat(at) < timedelta(minutes=25):
            return "1"
    except Exception:
        pass
    return "0"


if __name__ == "__main__":
    print("SKIP=" + main())
