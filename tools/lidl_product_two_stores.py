#!/usr/bin/env python3
"""Check one known Lidl product for two actual stores using official detail lookup."""
import json
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from urllib.parse import urlencode,quote
from pathlib import Path
from datetime import datetime,timezone
base="https://product-catalog.lidlplus.com"
ua="Ernaehrungsgedaechtnis-Research/2.8 (two-store product price validity check)"
with urlopen(Request(base+"/robots.txt",headers={"User-Agent":ua}),timeout=12) as f:
    rp=RobotFileParser();rp.parse(f.read(200000).decode("utf8","replace").splitlines())
checks=[]
product="8824326891371_DE"
for store in ("DE7434","DE7602"):
    url=base+"/api/app/v1/DE/store/"+store+"/products/"+quote(product,safe="")+"?"+urlencode({"date":"2026-10-31"})
    rec={"store":store,"product_id":product}
    if not rp.can_fetch(ua,url):
        rec["outcome"]="SKIP robots";checks.append(rec);continue
    req=Request(url,headers={"User-Agent":ua,"Accept-Language":"de","Accept":"application/json",
                            "X-Client-Version":"17.0.5","X-Client-Platform":"android"})
    try:
        with urlopen(req,timeout=18) as f:
            rec["http"]=f.status
            obj=json.load(f)
        rec["root_keys"]=list(obj)[:45] if isinstance(obj,dict) else []
        if isinstance(obj,dict):
            rec["name"]=obj.get("title")
            rec["price"]=obj.get("price")
            rec["oldPrice"]=obj.get("oldPrice")
            rec["discount"]=obj.get("discount")
            rec["stockAvailability"]=obj.get("stockAvailability")
            rec["lidlPlusOffer"]=obj.get("lidlPlusOffer")
    except HTTPError as e:rec["http"]=e.code
    except Exception as e:rec["error"]=type(e).__name__+":"+str(e)[:125]
    checks.append(rec)
result={"date":datetime.now(timezone.utc).isoformat(),"checks":checks}
Path("results").mkdir(exist_ok=True)
Path("results/lidl_one_product_two_stores.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
print(json.dumps(result,indent=2,ensure_ascii=False))
