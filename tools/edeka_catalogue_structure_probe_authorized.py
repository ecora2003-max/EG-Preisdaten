#!/usr/bin/env python3
"""EDEKA product and offer catalog structure probe - authorized user request.

One-time bounded read-only diagnostics. User reports authority for EDEKA data
download and GitHub storage; no credentials were provided. Require a deliberate
environment variable, and do not imply third-party permission was audited.
"""
from __future__ import annotations
import json,re,urllib.request,urllib.error,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
import os
if os.environ.get("EDEKA_PERMISSION_CONFIRMED")!="1":
    raise SystemExit("Authorization flag required: user claimed permission on 2026-10-31.")
UA="ErnaehrungsgedaechtnisResearch/3.0 (user-authorized EDEKA snapshot)"
def get(url,limit=1_600_000):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/xml,application/json,text/html;q=0.8"}),timeout=30) as f:
        b=f.read(limit+1)
        if len(b)>limit:raise RuntimeError("response too large")
        return b.decode("utf8","replace"),f.status,f.headers.get("Content-Type")
def probe(name,url):
    r={"probe":name,"url":url}
    try:
        raw,http,ct=get(url);r.update({"http":http,"size":len(raw),"content_type":ct})
        if name in ("market_offers_berlin","market_offers_hamburg","markets"):
            obj=json.loads(raw)
            r["root_keys"]=list(obj)[:30]
            for key in ("docs","markets"):
                if isinstance(obj.get(key),list):
                    r[key+"_count"]=len(obj[key]);r[key+"_sample_keys"]=[list(x)[:50] for x in obj[key][:2] if isinstance(x,dict)]
            for key in ("anzahl","national","totalCount","gueltig_von","gueltig_bis"):
                r[key]=obj.get(key)
            if name.startswith("market_offers"):
                for key in ("docs",):
                    r["sample_price_related"]=[{k:v for k,v in x.items() if re.search("preis|price|titel|title|angebo|produkt|artikel|gtin|ean|id",k,re.I)} for x in (obj.get(key) or [])[:2]]
        elif name=="robots":
            r["sitemap_lines"]=[x for x in raw.splitlines() if x.lower().startswith("sitemap:")][:20]
        elif "sitemap" in name:
            r["locs"]=re.findall(r"<loc>\s*(.*?)\s*</loc>",raw,re.I)[:30]
            r["loc_count"]=len(re.findall(r"<loc>\s*.*?\s*</loc>",raw,re.I))
            r["index"]=bool(re.search(r"<sitemapindex",raw,re.I))
        else:
            r["jsonld_count"]=len(re.findall(r'application/ld\+json',raw,re.I))
            r["product_jsonld_present"]=bool(re.search(r'"@type"\s*:\s*"Product"',raw))
            r["price_jsonld_present"]=bool(re.search(r'"price"\s*:',raw))
            r["title"]=(re.search(r"<title[^>]*>(.*?)</title>",raw,re.S|re.I).group(1).strip()[:120] if "<title" in raw else None)
        r["result"]="OK"
    except urllib.error.HTTPError as e:r.update({"http":e.code,"result":"HTTP_ERROR"})
    except Exception as e:r.update({"result":"ERROR","error":type(e).__name__+":"+str(e)[:160]})
    return r
data={"tested_utc":datetime.now(timezone.utc).isoformat(),
    "authorization_claim":"User reports authorization to download and store EDEKA catalogue on GitHub; contract scope not independently verified.",
    "checks":[]}
cases=[
 ("robots","https://www.edeka.de/robots.txt"),
 ("sitemap","https://www.edeka.de/sitemap.xml"),
 ("sortiment_sitemap","https://www.edeka.de/sortiment/sitemap.xml"),
 ("markets","https://www.edeka.de/api/marketsearch/markets?"+urlencode({"searchstring":"10405","size":5})),
 ("market_offers_berlin","https://www.edeka.de/eh/service/eh/offers?"+urlencode({"marketId":"10003451","limit":600})),
 ("market_offers_hamburg","https://www.edeka.de/eh/service/eh/offers?"+urlencode({"marketId":"913988","limit":300})),
 ("example_product","https://www.edeka.de/sortiment/4311596029167/"),
]
for name,url in cases:
    r=probe(name,url);data["checks"].append(r)
    print(json.dumps(r,ensure_ascii=False),flush=True)
out=Path("results/edeka_catalogue_structure_probe_20261031.json")
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
