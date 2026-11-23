"""Gerbang update harian (penutupan) AS. Jadwal GitHub sering tertunda/terlewat, jadi workflow punya
beberapa jadwal cadangan; gerbang ini membuat cadangan itu murah: bila data sudah memuat penutupan
terakhir bursa AS (atau baru saja diperbarui), langkah berat dilewati. Mencetak SKIP=0/1 untuk GITHUB_ENV."""
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
RECENT_MIN = 90  # data yang baru diperbarui < 90 menit lalu tidak diambil ulang (hindari putaran berulang)
CLOSE_MARGIN = (16, 30)  # jam New York: setelah ini penutupan hari itu dianggap sudah tersedia


def _holidays():
    try:
        import notify_telegram
        return notify_telegram.HOLIDAYS
    except Exception:
        return set()


def expected_price_date(now_ny: datetime, hol: set) -> str:
    """Tanggal penutupan terakhir yang seharusnya sudah ada di data."""
    d = now_ny.date()
    after_close = (now_ny.hour, now_ny.minute) >= CLOSE_MARGIN
    if not after_close:
        d -= timedelta(days=1)
    while d.weekday() >= 5 or d.isoformat() in hol:
        d -= timedelta(days=1)
    return d.isoformat()


def main() -> str:
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        return "0"
    try:
        cur = json.loads((ROOT / "data" / "stocks.json").read_text())
    except Exception:
        return "0"
    exp = expected_price_date(datetime.now(ZoneInfo("America/New_York")), _holidays())
    have = cur.get("priceDate") or ""
    try:
        age = datetime.now(timezone.utc) - datetime.fromisoformat(cur["updatedAt"])
        recent = age < timedelta(minutes=RECENT_MIN)
    except Exception:
        recent = False
    if have >= exp:
        print(f"Data sudah memuat penutupan {have} (diharapkan {exp}); dilewati", file=sys.stderr)
        return "1"
    if recent:
        print(f"Data baru diperbarui (<{RECENT_MIN} menit) walau penutupan {exp} belum masuk; dilewati", file=sys.stderr)
        return "1"
    print(f"Data penutupan {have} tertinggal dari {exp}; update dijalankan", file=sys.stderr)
    return "0"


if __name__ == "__main__":
    print("SKIP=" + main())
