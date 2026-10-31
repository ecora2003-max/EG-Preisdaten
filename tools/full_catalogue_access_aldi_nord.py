#!/usr/bin/env python3
"""Can ALDI Nord's own sitemap-listed assortment be fully enumerated?

Uses published sitemap and SSR product-category data, no query-based guesswork.
Records only counts/ID fingerprints (no full article dump). The test is complete
only when every discoverable category with Algolia hits has its whole page
count in the HTML response and ID coverage is stable.
"""
import argparse
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE="https://www.aldi-nord.de"
SITEMAP=BASE+"/.aldi-nord-sitemap.xml"
UA="ErnaehrungsgedaechtnisResearch/1.8 (two ordinary product category snapshots)"
LIMIT_SITEMAPS=20
LIMIT_CATEGORY_URLS=200
REQ_DELAY=.30
MAX_BODY=4_800_000
PRODUCT_INDEX="an_prd_de_de_products2"
OUT="results/full_catalogue_access_20261031/aldi_nord.json"

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xml"})
    with urllib.request.urlopen(req,timeout=27) as r:
        data=r.read(MAX_BODY+1)
        status=r.status
    if len(data)>MAX_BODY:raise ValueError("Response exceeds bounded bytes")
    return status,data.decode("utf-8","replace")

def sitemap_links():
    pending=[SITEMAP]
    seen=set()
    links=set()
    errors=[]
    while pending and len(seen)<LIMIT_SITEMAPS:
        url=pending.pop(0)
        if url in seen:continue
        seen.add(url)
        try:
            code,raw=get(url)
            root=ET.fromstring(raw)
            tag=root.tag.split("}")[-1]
            elements=[el.text for el in root.iter()
                      if el.tag.split("}")[-1]=="loc" and el.text]
            if tag=="sitemapindex":
                pending += [x for x in elements if x not in seen][:LIMIT_SITEMAPS]
            elif tag=="urlset":
                links.update(elements)
            else:
                errors.append({"source":url,"error":"UnexpectedRoot","root":tag})
        except Exception as e:
            errors.append({"source":url,"error":type(e).__name__,"detail":str(e)[:90]})
        time.sleep(.2)
    return links,{"sitemaps_read":len(seen),"pending_sitemaps":len(pending),"errors":errors}

def valid_category(link):
    parsed=urllib.parse.urlparse(link)
    if parsed.netloc not in ("www.aldi-nord.de","aldi-nord.de"):
        return None
    path=parsed.path
    if path.startswith("/sortiment/") and path.endswith(".html") and "/produkte/" not in path:
        # Product detail pages are filtered by their missing Algolia listing.
        return path
    return None

def category_data(text):
    m=re.search(r'<script[^>]+id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',text,re.S|re.I)
    if not m:
        return {"kind":"NO_NEXT_DATA"}
    state=json.loads(html.unescape(m.group(1))).get("props",{}).get("pageProps",{}).get("algoliaState",{}).get("initialResults",{})
    payload=state.get(PRODUCT_INDEX,{})
    segments=payload.get("results",[]) if isinstance(payload,dict) else []
    if not isinstance(segments,list) or not segments:
        return {"kind":"NO_ALGOLIA_PRODUCTS","indexes":sorted(state)[:8]}
    seg=segments[0]
    rows=seg.get("hits",[])
    if not isinstance(rows,list):
        return {"kind":"MALFORMED_HITS"}
    count=Counter()
    ids=[]
    for p in rows:
        count["rows"]+=1
        if not isinstance(p,dict):
            count["non_objects"]+=1;continue
        val=p.get("objectID")
        if val is not None:ids.append(str(val))
        price=p.get("currentPrice")
        if isinstance(price,dict) and type(price.get("priceValue")) in (int,float):
            count["priced"]+=1
        else:count["unpriced"]+=1
    keys=set(ids)
    return {
        "kind":"PRODUCT_LISTING","nbHits":seg.get("nbHits"),
        "nbPages":seg.get("nbPages"),"page":seg.get("page"),
        "hitsPerPage":seg.get("hitsPerPage"),"received":len(rows),
        "priced":count["priced"],"unpriced":count["unpriced"],
        "unique_ids_in_page":len(keys),"duplicate_ids_in_page":len(ids)-len(keys),
        "ids":keys
    }

def main():
    t0=datetime.now(timezone.utc).isoformat()
    summary={"retailer":"ALDI Nord","run_started_utc":t0,"status":"RUNNING",
             "scope":"All published /sortiment/*.html links in official sitemap",
             "limit_category_pages":LIMIT_CATEGORY_URLS,"results":[],
             "errors":[]}
    urls,info=sitemap_links()
    cats=sorted({p for u in urls if (p:=valid_category(u))})
    summary["sitemap"]=info
    summary["sitemap_total_urls"]=len(urls)
    summary["candidate_listing_paths"]=len(cats)
    summary["candidate_paths_exceed_limit"]=len(cats)>LIMIT_CATEGORY_URLS
    ids=set()
    priced_ids=set()
    max_pages=0
    total_pages=0
    for idx,path in enumerate(cats[:LIMIT_CATEGORY_URLS]):
        try:
            status,txt=get(BASE+path)
            obj=category_data(txt)
            row={k:v for k,v in obj.items() if k!="ids"}
            row["path"]=path;row["http"]=status
            if obj.get("kind")=="PRODUCT_LISTING":
                keys=obj["ids"]
                ids.update(keys)
                if obj.get("priced")==obj.get("received"):
                    priced_ids.update(keys)
                reported=obj["nbHits"]
                expected=reported if type(reported) is int else -1
                row["complete_within_page"]=(
                    obj.get("nbPages")==1 and obj.get("page")==0
                    and obj.get("received")==expected
                    and obj.get("unique_ids_in_page")==expected
                    and obj.get("priced")==expected
                )
                if obj.get("nbPages") not in (None,1):
                    max_pages+=1
                total_pages+=1
            summary["results"].append(row)
        except Exception as e:
            summary["errors"].append({"path":path,"error":type(e).__name__,
                                      "detail":str(e)[:120]})
        time.sleep(REQ_DELAY)
    listings=[x for x in summary["results"] if x.get("kind")=="PRODUCT_LISTING"]
    summary["listing_pages"]=len(listings)
    summary["single_page_complete_listings"]=sum(x["complete_within_page"] for x in listings)
    summary["multipage_listings"]=max_pages
    summary["total_rows_across_listings"]=sum(x.get("received",0) for x in listings)
    summary["total_priced_across_listings"]=sum(x.get("priced",0) for x in listings)
    summary["distinct_product_ids_across_listings"]=len(ids)
    summary["distinct_product_ids_on_entirely_priced_pages"]=len(priced_ids)
    summary["other_sitemap_paths_excluded"]=len(urls)-len(cats)
    summary["could_enumerate_all_sitemap_listings"]=(
        len(cats)<=LIMIT_CATEGORY_URLS and not summary["errors"]
        and not info["errors"] and not info["pending_sitemaps"]
        and len(listings)>0 and all(x.get("complete_within_page") for x in listings)
    )
    summary["limitations"]="Sitemap listings only; total physical shop assortment unverified. Empty categories may not carry Algolia. Multi-page category is not complete without more pages."
    summary["run_finished_utc"]=datetime.now(timezone.utc).isoformat()
    summary["status"]="DONE_WITH_LIMITATIONS"
    p=Path(OUT);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in summary.items() if k!="results"},ensure_ascii=False))

if __name__=="__main__":
    main()
