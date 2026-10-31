#!/usr/bin/env python3
"""Check ALDI Nord two regular categories: official Algolia hydrated page response coverage."""
import json,re
from urllib.request import urlopen,Request
from urllib.robotparser import RobotFileParser
from urllib.error import HTTPError
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime,timezone
base="https://www.aldi-nord.de"
ua="Ernaehrungsgedaechtnis-Research/1.8 (two ordinary product category snapshots)"
routes=[
"/sortiment/milchprodukte/joghurt-quark-milchdesserts.html",
"/sortiment/milchprodukte/milch-milchgetraenke.html",
]
out=[]
try:
    with urlopen(Request(base+"/robots.txt",headers={"User-Agent":ua}),timeout=15) as f:
        rp=RobotFileParser();rp.parse(f.read(250000).decode("utf8","replace").splitlines())
except HTTPError as e:
    rp=None if e.code==404 else "blocked"
except Exception:rp="blocked"
for route in routes:
    item={"category_url":base+route}
    if rp=="blocked" or (rp is not None and not rp.can_fetch(ua,item["category_url"])):
        item["result"]="skipped robots";out.append(item);continue
    try:
        with urlopen(Request(item["category_url"],headers={"User-Agent":ua,"Accept":"text/html"}),timeout=20) as f:
            html=f.read(500000).decode("utf-8","replace");item["http"]=f.status
        m=re.search(r'<script[^>]*id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',html,re.S|re.I)
        if not m:raise ValueError("NEXT Data missing")
        data=json.loads(m.group(1)).get("props",{}).get("pageProps",{})
        state=data.get("algoliaState",{}).get("initialResults",{})
        item["indices"]=list(state)[:8]
        idx=state.get("an_prd_de_de_products2",{})
        item["state_keys"]=list(idx)[:15]
        arr=idx.get("results",[])
        if not arr:raise ValueError("No Algolia results array")
        first=arr[0]
        item["pagination"]={k:first.get(k) for k in ("nbHits","nbPages","hitsPerPage","page","query","processingTimeMS")}
        products=first.get("hits",[])
        item["received_items"]=len(products)
        item["distinct_product_ids"]=len({str(p.get("objectID")) for p in products if isinstance(p,dict)})
        item["with_price"]=sum(isinstance(p.get("currentPrice"),dict) and p["currentPrice"].get("priceValue") is not None for p in products if isinstance(p,dict))
        item["samples"]=[{"objectID":p.get("objectID"),"name":p.get("name"),"brand":p.get("brandName"),
                          "price":p.get("currentPrice",{}).get("priceValue"),
                          "salesUnit":p.get("salesUnit")} for p in products[:3] if isinstance(p,dict)]
    except HTTPError as e:item["http"]=e.code;item["result"]="HTTP error"
    except Exception as e:item["result"]=type(e).__name__+":"+str(e)[:140]
    out.append(item)
Path("results").mkdir(exist_ok=True)
Path("results/aldi_two_category_prices.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
print(json.dumps(out,indent=2,ensure_ascii=False))
