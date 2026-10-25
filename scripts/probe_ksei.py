"""Cari API data kepemilikan efek di situs KSEI (sekali jalan). Hasil: data/probe_ksei.json."""
import json, re
from pathlib import Path
import requests
OUT = Path(__file__).resolve().parent.parent / "data" / "probe_ksei.json"
H = {"User-Agent": "Mozilla/5.0"}
B = "https://www.ksei.co.id"
res = {}
r = requests.get(B + "/id/publikasi/data-dan-statistik/kepemilikan-efek", headers=H, timeout=30)
html = r.text
res["page_status"] = r.status_code
res["page_urls"] = sorted(set(re.findall(r'https?://[^"\'\s<>]+', html)))[:150]
res["storage"] = sorted(set(re.findall(r'(?:https?://[^"\'\s<>]*)?/storage/[^"\'\s<>]+', html)))[:150]
res["kep_snips"] = re.findall(r'.{0,200}(?:Kepemilikan|kepemilikan|5%|1%|xlsx|pdf).{0,200}', html)[:40]
scripts = sorted(set(re.findall(r'src="([^"]+\.js)"', html)))
res["scripts"] = scripts
hits = set()
for s in scripts[:40]:
    u = s if s.startswith("http") else B + s
    try:
        js = requests.get(u, headers=H, timeout=30).text
        for m in re.findall(r'["\'`](https?://[^"\'`\s]+|/api/[^"\'`\s]+)["\'`]', js):
            hits.add(m)
    except Exception as e:
        hits.add("ERR " + str(e)[:80])
res["js_urls"] = sorted(hits)[:300]
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False))
print("ok")
