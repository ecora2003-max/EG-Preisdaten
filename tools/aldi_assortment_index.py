#!/usr/bin/env python3
"""Discover official ALDI Nord assortment category coverage, not a catalogue harvest.

One category-index HTML and up to 3 linked food-category pages. Output only
link counts, advertised product counts and normal-price coverage metadata.
"""
import json,re,time
from html import unescape
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin,urlparse
from pathlib import Path
from datetime import datetime,timezone

UA="Ernaehrungsgedaechtnis-Research/2.5 (bounded category price index)"
base="https://www.aldi-nord.de"
start=base+"/sortiment.html"
res={"date":datetime.now(timezone.utc).isoformat(),"categories":[]}
try:
    with urlopen(Request(base+"/robots.txt",headers={"User-Agent":UA}),timeout=12) as f:
        rp=RobotFileParser();rp.parse(f.read(250000).decode("utf8","replace").splitlines())
    if not rp.can_fetch(UA,start):raise ValueError("robots disallows index")
    with urlopen(Request(start,headers={"User-Agent":UA,"Accept":"text/html"}),timeout=20) as f:
        html=f.read(1_400_000).decode("utf8","replace")
        res["http"]=f.status
    raw_links=re.findall(r'href=["\x27]([^"\x27]+)["\x27]',html,re.I)
    names=[]
    for raw in raw_links:
        u=urljoin(base,unescape(raw))
        path=urlparse(u).path
        if urlparse(u).netloc!="www.aldi-nord.de" or not re.fullmatch(r"/sortiment/(?:[^/]+/)+[^/]+\.html",path):
            continue
        if any(x in path for x in ("/angebote/","/services/","/aktuelles/")):continue
        if u not in names:names.append(u)
    res["total_category_links_directly_in_assortment_index"]=len(names)
    res["sample_category_paths"]=[urlparse(u).path for u in names[:15]]
    candidates=[u for u in names if any(k in u for k in ("joghurt","milchprodukte","obst","gemuese","kaese","brot","snacks"))][:3]
    for url in candidates:
        row={"path":urlparse(url).path}
        try:
            if not rp.can_fetch(UA,url):raise ValueError("robots disallows linked category")
            with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"text/html"}),timeout=20) as f:
                page=f.read(900000).decode("utf8","replace");row["http"]=f.status
            m=re.search(r'<script[^>]*id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',page,re.S|re.I)
            if not m:raise ValueError("no NEXT data")
            ss=json.loads(m.group(1)).get("props",{}).get("pageProps",{}).get("algoliaState",{}).get("initialResults",{})
            first=ss.get("an_prd_de_de_products2",{}).get("results",[])
            if first and isinstance(first[0],dict):
                x=first[0];hits=x.get("hits") or []
                row["reported_hits"]=x.get("nbHits")
                row["returned_hits"]=len(hits)
                row["pages"]=x.get("nbPages")
                row["priced_products"]=sum(isinstance(h,dict) and isinstance(h.get("currentPrice"),dict) and h["currentPrice"].get("priceValue") is not None for h in hits)
                row["example_names"]=[h.get("name") for h in hits[:2] if isinstance(h,dict)]
        except HTTPError as e:row["http"]=e.code
        except Exception as e:row["error"]=str(e)[:125]
        res["categories"].append(row);time.sleep(.4)
except Exception as e:res["error"]=type(e).__name__+":"+str(e)[:150]
Path("results").mkdir(exist_ok=True)
Path("results/aldi_assortment_index.json").write_text(json.dumps(res,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
print(json.dumps(res,indent=2,ensure_ascii=False))
