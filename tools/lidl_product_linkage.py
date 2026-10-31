#!/usr/bin/env python3
"""Quantify which Lidl product entities are actually linked from flyer pages."""
import json,collections,re
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from pathlib import Path
from urllib.parse import urlencode
ua="Ernaehrungsgedaechtnis-Research/0.4 (read-only)"
host="https://endpoints.leaflets.schwarz"
url=host+"/v4/flyer?"+urlencode({"flyer_identifier":"aktionsprospekt-02-11-2026-07-11-2026-fbfd28","client":"lidl"})
try:
    with urlopen(Request(host+"/robots.txt",headers={"User-Agent":ua}),timeout=13) as f:
        rp=RobotFileParser();rp.parse(f.read(200000).decode("utf-8","replace").splitlines())
    assert rp.can_fetch(ua,url)
except HTTPError as e:
    if e.code!=404:raise
with urlopen(Request(url,headers={"User-Agent":ua}),timeout=18) as f:
    f1=json.load(f)["flyer"]
ids=f1.get("products") or {}
pages=f1.get("pages") or []
links=[l for p in pages if isinstance(p,dict) for l in (p.get("links") or []) if isinstance(l,dict)]
out={"products":len(ids),"pages":len(pages),"links":len(links),
     "link_keys":list(links[0]) if links else [],
     "first_links":[{k:l.get(k) for k in ("id","displayType","url","title","productId","productID","sku")} for l in links[:4]],
     "products_keys":list(ids)[:3],
     "link_displayType":dict(collections.Counter(str(l.get("displayType")) for l in links)),
     "page_type":dict(collections.Counter(str(p.get("pageType")) for p in pages))}
linktext=json.dumps(links)
out["product_ids_in_links"]=sum(str(v.get("productId")) in linktext for v in ids.values() if isinstance(v,dict) and v.get("productId"))
out["product_uuid_keys_in_links"]=sum(str(k) in linktext for k in ids)
out["links_with_product_token"]=sum("product" in json.dumps(l).lower() for l in links)
Path("results").mkdir(exist_ok=True)
Path("results/lidl_product_linkage.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
