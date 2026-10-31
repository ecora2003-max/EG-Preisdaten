#!/usr/bin/env python3
"""ALDI Süd: end-of-catalogue offset probe, no bulk collection."""
import json,time,urllib.request,urllib.parse,urllib.error
from datetime import datetime,timezone
from pathlib import Path
URL="https://api.aldi-sued.de/v3/product-search"
UA="ErnaehrungsgedaechnisResearch/1.0 (one-off noncommercial API diagnostic)"
OFFSETS=(3504,3538,3552,3600,4000)
out={"started_utc":datetime.now(timezone.utc).isoformat(),
     "retailer":"ALDI Süd","page_size":48,"samples":[]}
for pos in OFFSETS:
    q={"q":"","servicePoint":"B384","serviceType":"walk-in",
       "limit":"48","offset":str(pos),"sort":"relevance","currency":"EUR"}
    req=urllib.request.Request(URL+"?"+urllib.parse.urlencode(q),headers={
        "User-Agent":UA,"Accept":"application/json"})
    sample={"offset":pos}
    try:
        with urllib.request.urlopen(req,timeout=23) as f:
            payload=json.loads(f.read(1_000_000))
            sample["http"]=f.status
        rows=payload.get("data",[])
        pg=payload.get("meta",{}).get("pagination",{})
        sample["return_count"]=len(rows)
        sample["server_total"]=pg.get("totalCount")
        sample["priced"]=sum(isinstance(p,dict) and
                isinstance(p.get("price"),dict) and
                type(p["price"].get("amountRelevant")) is int for p in rows)
    except urllib.error.HTTPError as e:
        sample["http"]=e.code;sample["error"]="HTTP_ERROR"
    except Exception as e:
        sample["error"]=type(e).__name__
    out["samples"].append(sample)
    if sample.get("http")==403:break
    time.sleep(.5)
out["finished_utc"]=datetime.now(timezone.utc).isoformat()
p=Path("results/full_catalogue_access_20261031/aldi_sued_end_offsets.json")
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(out,ensure_ascii=False))
