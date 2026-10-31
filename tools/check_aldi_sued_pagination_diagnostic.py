#!/usr/bin/env python3
"""Why did the ALDI Süd full-page quality scan receive 403?

Perform up to 3 standard anonymous GETs; compare exact previously working
12-item query with 60-item request. No retry on blocked requests.
"""
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

BASE="https://api.aldi-sued.de/v3/product-search"
UA="ErnaehrungsgedaechnisResearch/1.0 (one-off noncommercial API diagnostic)"
ARGS={"q":"","servicePoint":"B384","serviceType":"walk-in",
      "limit":"12","offset":"0","sort":"relevance","currency":"EUR"}


def probe(label, params, user_agent):
    url=BASE+"?"+urllib.parse.urlencode(params)
    out={"label":label,"query":params,"at_utc":datetime.now(timezone.utc).isoformat()}
    try:
        req=urllib.request.Request(url, headers={
            "User-Agent":user_agent,"Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=20) as r:
            body=r.read(1_500_000);out["http"]=r.status
            out["server_date"]=r.headers.get("Date")
            out["cache_control"]=r.headers.get("Cache-Control")
        j=json.loads(body)
        arr=j.get("data") if isinstance(j,dict) else None
        pg=(j.get("meta") or {}).get("pagination") if isinstance(j,dict) else None
        out["returned"]=len(arr) if isinstance(arr,list) else None
        out["total"]=pg.get("totalCount") if isinstance(pg,dict) else None
        out["numeric_price_count"]=sum(
            isinstance(x,dict) and isinstance(x.get("price"),dict) and
            type(x["price"].get("amountRelevant")) is int
            for x in (arr if isinstance(arr,list) else []))
    except urllib.error.HTTPError as e:
        out["http"]=e.code
        out["result"]="HTTP_ERROR"
    except Exception as e:
        out["result"]=type(e).__name__
    return out


def main():
    out={"test":"Compare previously successful query shape and two page sizes",
         "results":[]}
    first=probe("exact_former_12",ARGS,UA)
    out["results"].append(first)
    if first.get("http")==200:
        sixty=dict(ARGS,limit="60")
        out["results"].append(probe("same_query_60",sixty,UA))
        if out["results"][-1].get("http")==200:
            alt=dict(sixty,offset="60")
            out["results"].append(probe("next_page_60",alt,UA))
    path=Path("results/completeness_freshness/aldi_sued_diagnostic.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(out,ensure_ascii=False))

if __name__=="__main__":
    main()
