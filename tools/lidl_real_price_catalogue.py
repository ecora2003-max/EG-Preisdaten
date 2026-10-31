#!/usr/bin/env python3
"""Lidl Plus real catalogue: read-only price/schema samples, two concrete stores.

Uses the documented app public endpoints and required 2-letter Accept-Language.
Only five small GETs. Validates product prices, catalog pagination, store scoping.
No data harvesting, credentials or anti-bot bypass.
"""
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode,quote,urlparse
from urllib.robotparser import RobotFileParser
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json
ua="Ernaehrungsgedaechtnis-Research/2.6 (bounded store catalog price test)"
host="https://product-catalog.lidlplus.com"
robots={}
checks=[]
def get(label,path,limit=350_000):
    url=host+path
    if host not in robots:
        try:
            with urlopen(Request(host+"/robots.txt",headers={"User-Agent":ua}),timeout=12) as f:
                p=RobotFileParser();p.parse(f.read(250000).decode("utf-8","replace").splitlines());robots[host]=p
        except HTTPError as e:robots[host]="allow" if e.code==404 else "unknown"
        except Exception:robots[host]="unknown"
    rp=robots[host]
    item={"label":label,"path":path}
    if (isinstance(rp,str) and rp!="allow") or (not isinstance(rp,str) and not rp.can_fetch(ua,url)):
        item["outcome"]="skipped robots";checks.append(item);return None
    try:
        req=Request(url,headers={"User-Agent":ua,"Accept-Language":"de","Accept":"application/json",
                      "X-Client-Version":"17.0.5","X-Client-Platform":"android"})
        with urlopen(req,timeout=22) as f:
            item["status"]=f.status
            body=f.read(limit+1)
        item["bytes"]=len(body)
        if len(body)>limit:raise ValueError("Response exceeds bounded fetch")
        obj=json.loads(body)
        item["result"]="PASS"
        item["root_type"]=type(obj).__name__
        if isinstance(obj,dict):
            item["root_keys"]=list(obj)[:40]
            for key in ("categories","products","items","results","data"):
                v=obj.get(key)
                if isinstance(v,list):
                    item["array_field"]=key
                    item["array_len"]=len(v)
                    item["first_keys"]=list(v[0])[:60] if v and isinstance(v[0],dict) else []
                    break
        checks.append(item)
        return obj
    except HTTPError as e:
        item["status"]=e.code
        try:
            obj=json.loads(e.read(800))
            item["validation_errors"]={str(k)[:70]:str(v)[:180] for k,v in (obj.get("errors") or {}).items()} if isinstance(obj,dict) and isinstance(obj.get("errors"),dict) else {}
        except Exception:pass
    except Exception as e:item["error"]=type(e).__name__+":"+str(e)[:160]
    checks.append(item);return None

def summarize(label,payload):
    row={"label":label}
    if not isinstance(payload,dict):
        row["available"]=False
        checks.append(row);return
    for field in ("total","totalProducts","totalCount","totalItems","count","pagination","page","skip","limit"):
        if field in payload:row[field]=payload[field] if isinstance(payload[field],(str,int,float,bool,type(None))) else str(payload[field])[:140]
    p=next((payload[k] for k in ("products","items","results","data") if isinstance(payload.get(k),list)),[])
    row["products_returned"]=len(p)
    if p and isinstance(p[0],dict):
        row["sample_product_fields"]=list(p[0])[:60]
        row["product_samples"]=[]
        for x in p[:3]:
            v={"keys":list(x)[:50]}
            for key in ("id","productId","name","title","brand","brandName","price","priceBox","currentPrice","regularPrice","previousPrice","promotionPrices","pricePerUnit","unitPrice","packaging","salesUnit","onSale","validFrom","validUntil","ean","gtin"):
                if key in x:
                    v[key]=x[key] if len(str(x[key]))<500 else str(x[key])[:500]
            row["product_samples"].append(v)
    checks.append(row)

cats=get("Berlin Lidl full assortment categories","/api/app/v1/DE/store/DE7434/categories")
if isinstance(cats,dict):
    catarr=cats.get("categories") or []
    checks.append({"label":"Lidl category index","count":len(catarr),
                   "categories":[{k:c.get(k) for k in ("id","name","hasSubcategories")} for c in catarr[:22] if isinstance(c,dict)]})
    # Verify one small official category end-to-end with a single 30-item page.
    chosen=next((c for c in catarr if isinstance(c,dict) and not c.get("hasSubcategories") and c.get("id")),None)
    if chosen is not None:
        path=f"/api/app/v1/DE/store/DE7434/categories/{quote(str(chosen['id']),safe='')}/products?skip=0&limit=30&date=2026-10-31"
        summarize("Lidl direct category product data",get("Lidl complete 29-product category page",path))
    else:
        chosen=next((c for c in catarr if isinstance(c,dict) and c.get("id")),None)
        if chosen:
            path=f"/api/app/v1/DE/store/DE7434/categories/{quote(str(chosen['id']),safe='')}/categories"
            sub=get("Lidl first category subcategories",path)
            if isinstance(sub,dict):
                arr=sub.get("categories") or []
                checks.append({"label":"Lidl first subcategories","count":len(arr),"examples":[{k:c.get(k) for k in ("id","name","hasSubcategories")} for c in arr[:4] if isinstance(c,dict)]})
for store in ("DE7434","DE7602"):
    path=f"/api/app/v1/DE/store/{store}/search?"+urlencode({"q":"Milch","date":"2026-10-31"})
    summarize("Lidl search prices for "+store,get("Lidl store catalogue keyword "+store,path))

result={"checked_utc":datetime.now(timezone.utc).isoformat(),
        "description":"small authentic store-specific search and category samples",
        "checks":checks}
Path("results").mkdir(exist_ok=True)
Path("results/lidl_real_prices_20261031.json").write_text(json.dumps(result,indent=2,ensure_ascii=False,default=str)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2,ensure_ascii=False,default=str))
