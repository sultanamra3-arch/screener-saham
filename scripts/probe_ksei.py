"""Lihat isi API kepemilikan efek dan file BalanceposEfek KSEI (sekali jalan). Hasil: data/probe_ksei.json."""
import io, json, zipfile
from pathlib import Path
import requests
OUT = Path(__file__).resolve().parent.parent / "data" / "probe_ksei.json"
H = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
B = "https://www.ksei.co.id"
res = {}
for path in ["/api/securities_ownerships", "/api/securities_ownerships?page=1", "/api/securities_ownerships?locale=id"]:
    try:
        r = requests.get(B + path, headers=H, timeout=30)
        res[path] = {"status": r.status_code, "ctype": r.headers.get("content-type"), "body": r.text[:3000]}
    except Exception as e:
        res[path] = {"err": str(e)[:200]}
try:
    r = requests.get(B + "/storage/Download/BalanceposEfek20260930.zip", headers=H, timeout=60)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    info = []
    for n in z.namelist()[:5]:
        raw = z.read(n)
        info.append({"name": n, "size": len(raw), "head": raw[:1500].decode("utf-8", "replace")})
    res["balancepos"] = {"status": r.status_code, "files": info}
except Exception as e:
    res["balancepos"] = {"err": str(e)[:300]}
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False))
print("ok")
