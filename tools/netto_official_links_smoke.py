#!/usr/bin/env python3
"""Real official Netto weekly booklet URLs for two independently selected stores."""
import json,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from adapters.retailer_offers import netto_store_prospects
results=[]
for store in ("7679","8135"):
    url="https://www.netto-online.de/ueber-netto/Online-Prospekte.chtm?stores_id="+store
    result={"store_id":store}
    try:
        with urlopen(Request(url,headers={"User-Agent":"Ernaehrungsgedaechtnis-Research/1.1 (read-only)","Accept":"text/html"}),timeout=19) as f:
            html=f.read(500_000).decode("utf-8","replace")
            result["http"]=f.status
        parsed=netto_store_prospects(html,store_id=store)
        result["prospects"]=parsed
        result["result"]="PASS" if any(p["iso_week"]==45 for p in parsed) else "FAIL no KW45"
    except Exception as e:
        result["result"]="FAIL";result["error"]=type(e).__name__+":"+str(e)[:150]
    results.append(result)
out={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
     "results":results,
     "limitations":"Product prices are not validated by this link parser; no automated scraping of blocked store pages"}
Path("results").mkdir(exist_ok=True)
Path("results/netto_official_links_smoke.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
if any(r["result"]!="PASS" for r in results):sys.exit(1)
