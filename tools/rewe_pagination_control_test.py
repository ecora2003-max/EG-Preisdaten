#!/usr/bin/env python3
"""REWE stationary search: validate suspected page/from pagination against controls."""
import hashlib, json, urllib.parse, urllib.request, urllib.error, time
from datetime import datetime,timezone
from pathlib import Path

URL="https://www.rewe.de/api/stationary-product-search/products"
UA="ErnaehrungsgedaechtnisResearch/1.1 (catalogue page discovery)"
BASE={"query":"Haferflocken","wwIdent":"840174"}
TESTS=[
 ("baseline_a",{}),
 ("page_0",{"page":"0"}),
 ("page_1_a",{"page":"1"}),
 ("page_2_a",{"page":"2"}),
 ("page_1_b",{"page":"1"}),
 ("page_2_b",{"page":"2"}),
 ("from_0",{"from":"0"}),
 ("from_12",{"from":"12"}),
 ("from_24",{"from":"24"}),
 ("page_3",{"page":"3"}),
 ("page_4",{"page":"4"}),
 ("page_20",{"page":"20"}),
 ("page_999",{"page":"999"}),
 ("baseline_b",{}),
]

def fetch(label,more):
    q=BASE|more
    req=urllib.request.Request(URL+"?"+urllib.parse.urlencode(q),
                               headers={"User-Agent":UA,"Accept":"application/json"})
    out={"label":label,"query_extra":more}
    try:
        with urllib.request.urlopen(req,timeout=24) as f:
            data=f.read(1_400_000)
            out["status"]=f.status
            out["cache_headers"]={k.lower().replace("-","_"):f.headers.get(k)
                                  for k in ("Cache-Control","Age","ETag")
                                  if f.headers.get(k) is not None}
        obj=json.loads(data)
        products=obj.get("products",[])
        if not isinstance(products,list):raise ValueError("no products")
        ids=[str(x.get("id")) for x in products if isinstance(x,dict) and x.get("id") is not None]
        ps=[(str(x.get("id")),x.get("pricing",{}).get("current")) for x in products
            if isinstance(x,dict) and isinstance(x.get("pricing"),dict)]
        out["count"]=len(products)
        out["unique_ids"]=len(set(ids))
        out["ids_hash"]=hashlib.sha256(json.dumps(ids).encode()).hexdigest()[:16]
        out["prices_hash"]=hashlib.sha256(json.dumps(ps).encode()).hexdigest()[:16]
        return out,set(ids)
    except urllib.error.HTTPError as e:
        out["status"]=e.code
        return out,set()
    except Exception as e:
        out["error"]=type(e).__name__
        return out,set()

def main():
    report={"started_utc":datetime.now(timezone.utc).isoformat(),"tests":[]}
    seen=[]
    for label,opts in TESTS:
        item, ids=fetch(label,opts)
        report["tests"].append(item)
        seen.append(ids)
        time.sleep(.4)
    ref=seen[0]
    for i,x in enumerate(report["tests"]):
        x["overlap_with_baseline"]=len(ref & seen[i])
        x["same_ids_as_baseline"]=seen[i]==ref
    report["page_1_repeated_same_ids"]=seen[2]==seen[4]
    report["page_2_repeated_same_ids"]=seen[3]==seen[5]
    report["page_1_page_2_overlapping_ids"]=len(seen[2]&seen[3])
    report["page_1_page_2_union"]=len(seen[2]|seen[3])
    report["page_999_products"]=report["tests"][12].get("count")
    report["finished_utc"]=datetime.now(timezone.utc).isoformat()
    p=Path("results/full_catalogue_access_20261031/rewe_pagination_followup.json")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps(report,ensure_ascii=False))

if __name__=="__main__":main()
