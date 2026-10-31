#!/usr/bin/env python3
"""Check official Netto storefront offer page with selected store query, one GET each."""
import json,re,hashlib
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from pathlib import Path
from datetime import datetime,timezone
ua="Ernaehrungsgedaechtnis-Research/1.1 (official store offers read-only study)"
out=[]
for sid in ("7679","8135"):
    url="https://www.netto-online.de/filialangebote?stores_id="+sid
    d={"store_id":sid,"url":url}
    try:
        with urlopen(Request(url,headers={"User-Agent":ua,"Accept":"text/html,application/xhtml+xml"}),timeout=18) as r:
            d["http"]=r.status;d["final_url"]=r.geturl()
            s=r.read(2_000_000).decode("utf-8","replace")
        d["bytes"]=len(s)
        d["sha256"]=hashlib.sha256(s.encode()).hexdigest()
        d["storeid_presence"]=s.count("stores_id="+sid)
        d["product_markers"]={k:s.count(k) for k in ("article-card","productTile","UVP","statt","angebot-preis","offer-price","product-details")}
        d["jsonld_count"]=s.count("application/ld+json")
        d["filialangebote_KW45"]=bool(re.search(r"filialangebote-KW45",s))
        d["blocker"]=bool(re.search(r"<title>Access Denied</title>|captcha",s,re.I))
        # Only metadata and relevant field keys, not product catalogue contents.
        d["structured_fields"]=list(dict.fromkeys(re.findall(r'"(offerPrice|price|offerTitle|articleName|productName|finalPrice|sellingRegion)"\s*:',s)))[:25]
    except HTTPError as e:d["http"]=e.code
    except Exception as e:d["error"]=type(e).__name__+":"+str(e)[:140]
    out.append(d)
Path("results").mkdir(exist_ok=True)
Path("results/netto_filialangebote_store.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(out,ensure_ascii=False,indent=2))
