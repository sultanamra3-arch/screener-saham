"""Cari tautan data kepemilikan di situs KSEI (sekali jalan). Hasil: data/probe_ksei.json."""
import json, re
from pathlib import Path
import requests
OUT = Path(__file__).resolve().parent.parent / "data" / "probe_ksei.json"
H = {"User-Agent": "Mozilla/5.0"}
res = {}
pages = ["https://www.ksei.co.id/", "https://www.ksei.co.id/archive_download/holding_composition",
         "https://www.ksei.co.id/archive_download/master_securities", "https://www.ksei.co.id/publications/Data_Statistik_KSEI",
         "https://www.ksei.co.id/archive_download/stock_ownership", "https://www.ksei.co.id/archive_download/kepemilikan_efek"]
for u in pages:
    try:
        r = requests.get(u, headers=H, timeout=30)
        links = sorted(set(re.findall(r'href="([^"]+)"', r.text)))
        key = [l for l in links if re.search(r"(?i)kepemilikan|ownership|holding|5%|pemegang|archive|download|publication|statist", l)]
        res[u] = {"status": r.status_code, "n_links": len(links), "key_links": key[:120],
                  "text_hits": re.findall(r"(?i)[^<>]{0,60}(?:di atas 5|above 5|1%|kepemilikan efek)[^<>]{0,60}", r.text)[:30]}
    except Exception as e:
        res[u] = {"err": str(e)[:200]}
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False))
print("ok")
