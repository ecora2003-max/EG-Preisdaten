#!/usr/bin/env python3
"""Small read-only supermarket full-assortment feasibility checks (2026-10-31).

Focus: ordinary shelf price & catalogue coverage distinct from promotions.
No authenticated endpoints, no bot bypass; honours the target's robots policy.
Stores metadata and at most two product samples, not downloaded catalogues.
"""
import json,re,time
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse,quote
from pathlib import Path
ua="Ernaehrungsgedaechtnis-Research/1.2 (read-only 1-shot catalogue feasibility)"
robots={}
results=[]
def req(label,url,limit=3_000_000):
    parsed=urlparse(url);base=parsed.scheme+"://"+parsed.netloc
    o={"test":label,"host":parsed.netloc,"path":parsed.path}
    if base not in robots:
        try:
            with urlopen(Request(base+"/robots.txt",headers={"User-Agent":ua}),timeout=13) as res:
                rp=RobotFileParser();rp.parse(res.read(300000).decode("utf8","replace").splitlines());robots[base]=rp
        except HTTPError as e:robots[base]="allow" if e.code==404 else "unknown: robots HTTP "+str(e.code)
        except Exception as e:robots[base]="unknown: "+type(e).__name__
    r=robots[base]
    if (isinstance(r,str) and r!="allow") or (not isinstance(r,str) and not r.can_fetch(ua,url)):
        o["outcome"]="SKIPPED robots";o["detail"]=r if isinstance(r,str) else "disallows";results.append(o);return None
    try:
        with urlopen(Request(url,headers={"User-Agent":ua,"Accept":"application/json,text/html;q=0.9,*/*;q=0.3","Accept-Language":"de-DE,de;q=0.9"}),timeout=19) as res:
            o["http"]=res.status;o["content_type"]=res.headers.get("Content-Type","")[:80]
            raw=res.read(limit+1)
        o["bytes"]=len(raw)
        if len(raw)>limit:o["outcome"]="TOO_LARGE";results.append(o);return None
        o["outcome"]="HTTP_OK"
        try:
            doc=json.loads(raw)
            o["type"]=type(doc).__name__
            o["top_keys"]=list(doc)[:30] if isinstance(doc,dict) else []
            o["length"]=len(doc) if isinstance(doc,list) else None
            if isinstance(doc,dict):
                for k in ("categories","products","items","results","data","content"):
                    if isinstance(doc.get(k),list):
                        o["list_key"]=k;o["list_items"]=len(doc[k])
                        if doc[k] and isinstance(doc[k][0],dict):
                            o["first_list_item_keys"]=list(doc[k][0])[:55]
                            o["first_list_item_excerpt"]={k:v for k,v in doc[k][0].items() if k.lower() in
                                {"id","name","title","price","regularprice","saleprice","baseprice","sku","code","itemid","pricebox","productid","categoryid"}}
                        break
                if not o.get("list_key") and isinstance(doc.get("data"),dict):
                    o["data_keys"]=list(doc["data"])[:25]
            results.append(o);time.sleep(.4);return doc
        except (ValueError,TypeError):
            html=raw.decode("utf-8","replace")
            o["type"]="HTML_OR_OTHER"
            o["has_next_data"]="__NEXT_DATA__" in html
            o["product_jsonld"]="https://schema.org/Product" in html or '"@type":"Product"' in html
            o["price_markers"]=len(re.findall(r'(?:regularPrice|basePrice|salePrice|currentPrice|storePrice)',html,re.I))
            if "__NEXT_DATA__" in html:
                m=re.search(r'<script[^>]*id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',html,re.S|re.I)
                if m:
                    try:
                        obj=json.loads(m.group(1))
                        props=obj.get("props",{}).get("pageProps",{})
                        o["pageprops_keys"]=list(props)[:30]
                        api=props.get("apiData")
                        if isinstance(api,str):
                            try: api=json.loads(api)
                            except ValueError:pass
                        if isinstance(api,list):
                            o["api_operation_names"]=[str(x[0]) for x in api[:30] if isinstance(x,list) and x]
                    except Exception as ex:o["next_data_issue"]=str(ex)[:100]
            results.append(o);time.sleep(.4);return html
    except HTTPError as e:o["outcome"]="HTTP_ERROR";o["http"]=e.code
    except Exception as e:o["outcome"]="ERROR";o["detail"]=type(e).__name__+":"+str(e)[:150]
    results.append(o);return None

for store in ("DE7434","7434"):
    base=f"https://product-catalog.lidlplus.com/api/app/v1/DE/store/{store}"
    c=req("Lidl product-catalog category tree "+store,base+"/categories")
    if isinstance(c,dict):
        result=c.get("categories")
        if isinstance(result,list) and result and isinstance(result[0],dict):
            key=result[0].get("id") or result[0].get("categoryId")
            if key:
                req("Lidl product-catalog 1st category small page "+store,base+"/categories/"+quote(str(key),safe="")+"/products?skip=0&limit=5")
    # Search test: product query with real store id, no broad crawling
    req("Lidl product-catalog 1-word search "+store,base+"/search?q=Milch")

req("Lidl grocery ClickandPick sample","https://clickandpick.lidlplus.com/api/v1/clickandpick/DE/stores/DE7434/products")
req("ALDI Nord regular assortment","https://www.aldi-nord.de/sortiment.html")
req("PENNY regular assortment","https://www.penny.de/sortiment")
req("Kaufland regular assortment","https://filiale.kaufland.de/sortiment.html")
# EDEKA explicitly excluded because its website terms limit automated copying.

out={"checked_utc":datetime.now(timezone.utc).isoformat(),
     "scope":"one-shot ordinary public requests, no entire assortment harvesting",
     "tests":results}
Path("results").mkdir(exist_ok=True)
Path("results/full_catalogue_feasibility.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
