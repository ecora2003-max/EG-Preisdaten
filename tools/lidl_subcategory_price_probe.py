#!/usr/bin/env python3
"""Validate a nested Lidl category path with real store prices, one small page.

No bulk catalogue export. The official public client requests are read-only;
results contain structural metadata and two sample price observations.
"""
import json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from urllib.parse import quote,urlencode
from datetime import datetime,timezone
host="https://product-catalog.lidlplus.com"
ua="Ernaehrungsgedaechtnis-Research/3.1 (small price taxonomy integration)"
out={"checked_utc":datetime.now(timezone.utc).isoformat(),"store":"DE7434"}
try:
    try:
        with urlopen(Request(host+"/robots.txt",headers={"User-Agent":ua}),timeout=12) as f:
            rp=RobotFileParser();rp.parse(f.read(200000).decode("utf-8","replace").splitlines())
    except HTTPError as e:
        rp=None if e.code==404 else "blocked"
    except Exception:rp="blocked"
    def get(path):
        url=host+path
        if rp=="blocked" or (rp is not None and not rp.can_fetch(ua,url)):
            raise ValueError("robots restrictions/unknown")
        h={"User-Agent":ua,"Accept":"application/json","Accept-Language":"de",
           "X-Client-Version":"17.0.5","X-Client-Platform":"android"}
        with urlopen(Request(url,headers=h),timeout=20) as f:
            body=f.read(200001)
            if len(body)>200000:raise ValueError("oversized bounded response")
            return f.status,json.loads(body)
    status,cats=get("/api/app/v1/DE/store/DE7434/categories/1004/categories")
    subs=cats.get("categories") or []
    out["subcategories_http"]=status
    out["subcategories_count"]=len(subs)
    out["subcategories"]=[{k:sub.get(k) for k in ("id","name","hasSubcategories")} for sub in subs[:15] if isinstance(sub,dict)]
    choose=next((sub for sub in subs if isinstance(sub,dict) and sub.get("id") and not sub.get("hasSubcategories")),None)
    if choose:
        sid=quote(str(choose["id"]),safe="")
        p=f"/api/app/v1/DE/store/DE7434/categories/1004/categories/{sid}/products?"
        p+=urlencode({"skip":0,"limit":10,"date":"2026-10-31"})
        status,data=get(p)
        products=data.get("products") or []
        out["product_page_http"]=status
        out["category"]=choose.get("name")
        out["advertised_total"]=data.get("totalProducts")
        out["received_products"]=len(products)
        out["priced_products"]=sum(isinstance(p,dict) and isinstance(p.get("price"),dict) and isinstance(p["price"].get("price"),(int,float)) for p in products)
        out["examples"]=[{"title":p.get("title"),"price_eur":p.get("price",{}).get("price"),
                          "old_price":p.get("price",{}).get("oldPrice")} for p in products[:2] if isinstance(p,dict)]
    else:
        out["result"]="no leaf subcategory in root first tier; not an error"
except Exception as exc:
    out["error"]=type(exc).__name__+":"+str(exc)[:150]
Path("results").mkdir(exist_ok=True)
Path("results/lidl_subcategory_price_probe.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(out,indent=2,ensure_ascii=False))
