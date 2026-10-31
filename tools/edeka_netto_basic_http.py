#!/usr/bin/env python3
"""Only one ordinary public GET per official EDEKA/Netto route, no retries/bypass.

Network diagnostics for a regular HTTP client. This is NOT a license to scrape.
"""
import json

# Website content terms prohibit automated collection absent explicit permission.
import os
if os.environ.get("EDEKA_PERMISSION_CONFIRMED") != "1":
    print("SKIPPED: EDEKA.de requires prior explicit permission for automated retrieval.")
    raise SystemExit(0)
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
UA="Ernaehrungsgedaechtnis-Research/0.7 (one-shot read-only public API check)"
checks=[]
cases=[
    ("EDEKA public national fallback offers",
     "https://www.edeka.de/eh/service/eh/offers?"+urlencode({"limit":5,"marketId":1})),
    ("EDEKA public search",
     "https://www.edeka.de/api/marketsearch/markets?"+urlencode({"searchstring":"10405","size":2})),
    ("Netto Marken public flyer page",
     "https://www.netto-online.de/ueber-netto/Online-Prospekte.chtm/1013"),
]
for name,url in cases:
    row={"source":name,"url":url,"method":"GET"}
    try:
        with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"application/json,text/html;q=0.9"}),timeout=15) as r:
            row["status"]=r.status
            row["content_type"]=r.headers.get("Content-Type","")[:70]
            raw=r.read(1_000_001)
        row["length"]=len(raw)
        if len(raw)>1_000_000:
            row["result"]="size exceeded"
        elif "application/json" in row.get("content_type",""):
            obj=json.loads(raw)
            row["json_root_type"]=type(obj).__name__
            row["keys"]=list(obj)[:25] if isinstance(obj,dict) else []
            for k in ("docs","markets","offers"):
                if isinstance(obj,dict) and isinstance(obj.get(k),list):
                    row["array_field"]=k;row["count"]=len(obj[k])
                    if obj[k] and isinstance(obj[k][0],dict):
                        row["first_fields"]=list(obj[k][0])[:26]
                    break
        else:
            html=raw.decode("utf-8","replace")
            row["contains_angebot"]="Angebote" in html or "angebote" in html
            row["contains_filiale"]="Filiale" in html or "filiale" in html
    except HTTPError as e:row["status"]=e.code;row["result"]="HTTP error"
    except Exception as e:row["result"]=type(e).__name__+":"+str(e)[:140]
    checks.append(row)
report={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
        "note":"single plain GET; no auth, fingerprint imitation, session spoofing, or retry",
        "checks":checks}
Path("results").mkdir(exist_ok=True)
Path("results/edeka_netto_basic_http.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
