#!/usr/bin/env python3
"""ALDI Süd: check whether every advertised catalogue page can be accessed.

Requests 60-item pages by offset; stops on an error. Strictly read-only.
Only aggregate coverage and price-field counts; no raw catalogue persisted.
No alternate IP/user-agent, session keys or anti-blocking workarounds.
"""
import hashlib
import json
import time
import urllib.parse
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

ENDPOINT="https://api.aldi-sued.de/v3/product-search"
STORE="B384"
LIMIT=60
MAX_PAGES=64
UA="ErnaehrungsgedaechtnisResearch/1.0 (one-off noncommercial API diagnostic)"
DELAY=1.1

def fetch(offset):
    args={"q":"","servicePoint":STORE,"serviceType":"walk-in",
          "limit":str(LIMIT),"offset":str(offset),"sort":"relevance",
          "currency":"EUR"}
    url=ENDPOINT+"?"+urllib.parse.urlencode(args)
    req=urllib.request.Request(url, headers={
        "User-Agent":UA,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=28) as r:
        body=r.read(1_500_000)
        header={k.lower().replace("-","_"):r.headers.get(k)
                for k in ("Date","Cache-Control","Age","Last-Modified")
                if r.headers.get(k) is not None}
    js=json.loads(body)
    if not isinstance(js,dict) or not isinstance(js.get("data"),list):
        raise ValueError("Missing data")
    pg=(js.get("meta") or {}).get("pagination",{})
    if not isinstance(pg,dict):
        raise ValueError("Missing pagination")
    return js["data"],pg,header

def main():
    out={"retailer":"ALDI Süd","store":STORE,"started_utc":
         datetime.now(timezone.utc).isoformat(),"pages":[],"status":"RUNNING",
         "page_limit":LIMIT,"max_pages":MAX_PAGES}
    seen=set()
    overall=Counter()
    totals=[]
    error=None
    for page_no in range(MAX_PAGES):
        offset=page_no*LIMIT
        try:
            rows,pg,headers=fetch(offset)
            total=pg.get("totalCount")
            if type(total) is not int or total<0:
                raise ValueError("Non-integer pagination total")
            totals.append(total)
            cnt=Counter()
            for p in rows:
                cnt["returned"]+=1
                if not isinstance(p,dict):
                    cnt["non_objects"]+=1
                    continue
                sku=p.get("sku")
                if not isinstance(sku,str) or not sku:
                    cnt["missing_sku"]+=1
                elif sku in seen:
                    cnt["duplicate_sku"]+=1
                else:
                    seen.add(sku)
                price=p.get("price")
                if isinstance(price,dict) and type(price.get("amountRelevant")) is int:
                    cnt["priced"]+=1
                else:
                    cnt["missing_or_invalid_price"]+=1
            overall.update(cnt)
            out["pages"].append({
                "requested_offset":offset,
                "reported_offset":pg.get("offset"),
                "total_count":total,
                "returned":cnt["returned"],
                "valid_price":cnt["priced"],
                "duplicate_ids":cnt["duplicate_sku"],
                "missing_sku":cnt["missing_sku"],
                "http_cache_headers":headers if page_no==0 else None,
            })
            if offset+LIMIT>=total:break
            if not rows:
                error="EMPTY_PAGE_BEFORE_END";break
            time.sleep(DELAY)
        except urllib.error.HTTPError as e:
            error="HTTP_"+str(e.code)
            break
        except Exception as e:
            error=type(e).__name__
            break
    out["status"]="COMPLETE_SCAN" if not error and totals and len(out["pages"])*LIMIT>=totals[-1] else "PARTIAL_SCAN"
    out["first_error"]=error
    out["total_counts_seen"]=sorted(set(totals))
    out["unique_products_retrieved"]=len(seen)
    out["sum_rows"]=overall["returned"]
    out["priced_rows"]=overall["priced"]
    out["duplicate_ids"]=overall["duplicate_sku"]
    out["missing_product_ids"]=overall["missing_sku"]
    out["pages_requested"]=len(out["pages"])+(1 if error else 0)
    out["coverage_vs_reported_total"]=round(len(seen)/totals[-1],5) if totals and totals[-1] else None
    out["all_reported_items_retrieved_exactly_once"]=bool(
        out["status"]=="COMPLETE_SCAN" and len(set(totals))==1
        and len(seen)==totals[0] and
        overall["returned"]==totals[0] and
        overall["priced"]==totals[0] and
        overall["duplicate_sku"]==0 and
        overall["missing_sku"]==0)
    out["finished_utc"]=datetime.now(timezone.utc).isoformat()
    target=Path("results/full_catalogue_access_20261031/aldi_sued.json")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in out.items() if k!="pages"},ensure_ascii=False))

if __name__=="__main__":
    main()
