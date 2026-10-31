#!/usr/bin/env python3
"""Official ALDI SUED product/search prices – one plain read-only page, no scraping proxy.

A separate chain from ALDI Nord; verify whether a live store-related price catalog is
really accessible. One GET only, no retries or anti-bot workaround.
"""
import json
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from pathlib import Path
from datetime import datetime,timezone

ua="Ernaehrungsgedaechtnis-Research/2.3 (single public ALDI Sued catalogue query)"
base="https://api.aldi-sued.de"
url=base+"/v3/product-search?"+urlencode({
 "serviceType":"walk-in","servicePoint":"B384","currency":"EUR",
 "limit":"12","offset":"0","sort":"relevance","q":"Hafer"})
out={"timestamp":datetime.now(timezone.utc).isoformat(),"endpoint":url,"chain":"ALDI Sued"}
try:
    with urlopen(Request(base+"/robots.txt",headers={"User-Agent":ua}),timeout=12) as res:
        bot=RobotFileParser();bot.parse(res.read(300000).decode("utf8","replace").splitlines())
    if not bot.can_fetch(ua,url):
        out["result"]="SKIPPED robots disallow"
    else:
        with urlopen(Request(url,headers={"User-Agent":ua,"Accept":"application/json"}),timeout=22) as res:
            out["http"]=res.status
            data=json.load(res)
        out["keys"]=list(data) if isinstance(data,dict) else []
        if isinstance(data,dict):
            p=data.get("meta",{}).get("pagination",{})
            out["pagination"]={k:p.get(k) for k in ("offset","limit","totalCount")}
            vals=data.get("data") or []
            out["items_returned"]=len(vals)
            if vals and isinstance(vals[0],dict):
                out["product_fields"]=list(vals[0])[:35]
                out["price_fields"]=list(vals[0].get("price",{}))[:30] if isinstance(vals[0].get("price"),dict) else []
                out["samples"]=[{
                    "sku":x.get("sku"),"name":x.get("name"),"brand":x.get("brandName"),
                    "price_cents":x.get("price",{}).get("amountRelevant"),
                    "normal_price":x.get("price",{}).get("wasPriceDisplay"),
                    "base_price":x.get("price",{}).get("comparisonDisplay")
                } for x in vals[:2]]
        out["result"]="PASS"
except HTTPError as e:out["result"]="HTTP "+str(e.code)
except Exception as e:out["result"]=type(e).__name__+": "+str(e)[:160]
Path("results").mkdir(exist_ok=True)
Path("results/aldi_sued_real_catalogue.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
print(json.dumps(out,indent=2,ensure_ascii=False))
