#!/usr/bin/env python3
"""Determine whether official Netto brochure URL truly selects the requested store.

Targets only 2 page GETs and examines the existing public HTML. No browser
fingerprint alteration, no authentication, and no access-control bypass.
"""
import json,re
from html import unescape
from urllib.parse import urljoin
from urllib.request import Request,urlopen
from pathlib import Path
from datetime import datetime,timezone
UA="Ernaehrungsgedaechtnis-Research/1.0 (Netto public page HTML study)"
out=[]
for store in ("7679","8135"):
    url="https://www.netto-online.de/ueber-netto/Online-Prospekte.chtm?stores_id="+store
    data={"store_requested":store,"url":url}
    try:
        with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"text/html"}),timeout=17) as r:
            html=r.read(600_000).decode("utf-8","replace")
            data["status"]=r.status
        data["has_selected_address_block"]=bool(re.search(r'your-store__info__address',html))
        found=[]
        for m in re.finditer(r'<a\b[^>]*\bid=["\x27](filialangebote-KW\d+|getraenkemarkt|sonderbeilagen)["\x27][^>]*>',html,re.I):
            tag=m.group(0)
            href=re.search(r'\bhref=["\x27]([^"\x27]+)',tag,re.I)
            found.append({"id":m.group(1),"href":urljoin(url,unescape(href.group(1))) if href else None})
        data["brochure_offer_anchor_urls"]=found[:18]
        address_start=html.find("your-store__info__address")
        data["near_address_html"]=re.sub(r'\s+',' ',html[max(0,address_start-80):address_start+650]) if address_start>=0 else None
        data["store_url_marker_count"]=len(re.findall(r'stores_id[=:\\"]+'+store+r'\b',html))
        data["kw45_marker_count"]=len(re.findall(r'filialangebote-KW45',html))
        data["total_prospect_teaser_count"]=html.count("prospekt-teaser-item")
    except Exception as e:
        data["result"]=type(e).__name__+":"+str(e)[:125]
    out.append(data)
Path("results").mkdir(exist_ok=True)
Path("results/netto_brochure_ids.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(out,ensure_ascii=False,indent=2))
