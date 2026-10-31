#!/usr/bin/env python3
"""Read-only tests for store scoping, regional offers and public Lidl leaflet fallback."""
import json, re, hashlib, time
from collections import Counter
from datetime import datetime, timezone
from html import unescape
from urllib.request import Request,urlopen
from urllib.parse import urlencode,urlparse
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from pathlib import Path
UA="Ernaehrungsgedaechtnis-Research/0.2 (polite noncommercial API study)"
robots={}
report={"timestamp_utc":datetime.now(timezone.utc).isoformat(),"test_method":"public read-only; robots verification; no access bypass","tests":[]}

def get(label,url,headers=None,maxbytes=8_000_000):
    domain=urlparse(url)
    base=domain.scheme+"://"+domain.netloc
    item={"test":label,"url":url}
    if base not in robots:
        try:
            with urlopen(Request(base+"/robots.txt",headers={"User-Agent":UA}),timeout=14) as r:
                b=r.read(250000).decode("utf-8","replace")
            rp=RobotFileParser();rp.parse(b.splitlines());robots[base]=rp
        except HTTPError as e:
            robots[base]="allow" if e.code==404 else f"robots status {e.code}; skipped"
        except Exception as e:
            robots[base]="robots unavailable; skipped ("+type(e).__name__+")"
    rp=robots[base]
    if (isinstance(rp,str) and rp!="allow") or (not isinstance(rp,str) and not rp.can_fetch(UA,url)):
        item["result"]="skipped";item["reason"]=rp if isinstance(rp,str) else "robots disallow";report["tests"].append(item);return None
    try:
        req=Request(url,headers={"User-Agent":UA,"Accept":"application/json,text/html;q=0.9,*/*;q=0.4",**(headers or {})})
        with urlopen(req,timeout=20) as r:
            item["status"]=r.status;item["content_type"]=r.headers.get("Content-Type","")[:90]
            item["final_url"]=r.url
            if urlparse(r.url).netloc!=domain.netloc:
                item["result"]="other-host redirect; not followed";report["tests"].append(item);return None
            b=r.read(maxbytes+1)
        item["bytes"]=len(b);item["sha256"]=hashlib.sha256(b).hexdigest()
        if len(b)>maxbytes:
            item["result"]="response exceeds bound";report["tests"].append(item);return None
        item["result"]="success";report["tests"].append(item)
        time.sleep(.5)
        return b.decode("utf-8","replace")
    except HTTPError as e:
        item["result"]="http_error";item["status"]=e.code;report["tests"].append(item)
    except Exception as e:
        item["result"]="request_error";item["reason"]=type(e).__name__+": "+str(e)[:120];report["tests"].append(item)
    return None

def note(name, **data):
    report["tests"].append({"test":name,**data})

def productlist_from_kaufland(html):
    m=html.find('"offerData":')
    if m<0:return []
    start=html.find("{",m+len('"offerData":'))
    if start<0:return []
    payload,_=json.JSONDecoder().raw_decode(html[start:])
    result=[]
    for cycle in payload.get("cycles",[]):
        for cat in cycle.get("categories",[]):
            for product in cat.get("offers",[]):
                if isinstance(product,dict):
                    result.append(product)
    return result

# PENNY: real store selection and regional catalogues.
raw=get("PENNY market catalog","https://www.penny.de/.rest/market",maxbytes=6_000_000)
if raw:
    try:
        stores=json.loads(raw);berlin=[x for x in stores if x.get("city","").casefold()=="berlin" and x.get("sellingRegion")]
        reg={}
        for s in berlin:reg.setdefault(s["sellingRegion"],[]).append(s)
        note("PENNY Berlin regional topology", total_markets=len(berlin), distinct_regions=len(reg),
             region_market_counts={k:len(v) for k,v in reg.items()},
             first_two_stores=[{k:s.get(k) for k in ("wwIdent","zipCode","streetWithHouseNumber","sellingRegion","nextWeekSellingRegion")} for s in berlin[:2]])
        selected=[]
        for region,ls in reg.items():
            if len(selected)>=2:break
            selected.append((region,ls[0]))
        catalogues=[]
        for region,s in selected:
            week = "2026-45"
            # Always use the next-week selling region, not assume it equals this week's.
            regnext=s.get("nextWeekSellingRegion") or region
            url="https://www.penny.de/.rest/offers/by-category/"+week+"/top-angebote?"+urlencode({"region":regnext})
            b=get("PENNY region "+region+" week45",url)
            if not b:continue
            obj=json.loads(b);arr=obj.get("offerTiles",[])
            mapped={str(x.get("uuid") or x.get("title")):str(x.get("price")) for x in arr if isinstance(x,dict)}
            catalogues.append((region,mapped))
            note("PENNY sample regional offers",region=region,store_id=s.get("wwIdent"),requested_selling_region=regnext,
                 count=len(arr),samples=[{k:x.get(k) for k in ("title","quantity","price","benefitPrice","uuid")} for x in arr[:3] if isinstance(x,dict)])
        if len(catalogues)==2:
            (r1,p1),(r2,p2)=catalogues
            shared=set(p1)&set(p2)
            note("PENNY cross-region comparison",first_region=r1,second_region=r2,
                 shared_product_identifiers=len(shared),different_prices_in_shared=sum(p1[k]!=p2[k] for k in shared),
                 only_first=len(set(p1)-set(p2)),only_second=len(set(p2)-set(p1)))
    except Exception as e:note("PENNY parsing",result="error",reason=str(e)[:150])

# Kaufland: normal retailer store-selector cookie to compare offers for two known stores.
kaufland={}
for store_id in ("DE5220","DE1680"):
    url="https://filiale.kaufland.de/angebote/uebersicht.html?kloffer-week=next"
    raw=get("Kaufland week45 store "+store_id,url,headers={"Cookie":"x-aem-variant="+store_id})
    if raw:
        try:
            lst=productlist_from_kaufland(raw)
            # Individual offerIDs may be region-specific, compare normalized product title.
            active=[x for x in lst if str(x.get("salesFrom","")).startswith("2026-11")]
            vals={re.sub(r"\s+"," ",str(x.get("title","")).strip()).casefold(): str(x.get("price")) for x in active if x.get("title")}
            kaufland[store_id]=vals
            note("Kaufland store-specific parsed offers",store_id=store_id,
                 total_embedded_offer_items=len(lst),november_count=len(active),
                 unique_titles=len(vals),
                 selected_examples=[{k:x.get(k) for k in ("offerId","title","price","salesFrom","salesTo")} for x in active[:3]])
        except Exception as e:note("Kaufland parse "+store_id,result="error",reason=str(e)[:170])
if len(kaufland)==2:
    a,b=kaufland.values();shared=set(a)&set(b)
    note("Kaufland two-store differential",stores=list(kaufland),shared_names=len(shared),
         different_prices_for_shared_names=sum(a[k]!=b[k] for k in shared),
         only_first=len(set(a)-set(b)),only_second=len(set(b)-set(a)),
         example_differing_prices=[{"title":k,"store1_price":a[k],"store2_price":b[k]} for k in list(shared) if a[k]!=b[k]][:5])

# ALDI Nord: verify whether future offer payload actually carries store/region filtering.
raw=get("ALDI Nord next week", "https://www.aldi-nord.de/angebote-vorschau.html",maxbytes=2_000_000)
if raw:
    try:
        m=re.search(r'<script[^>]*id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',raw,re.I|re.S)
        obj=json.loads(m.group(1));api=obj.get("props",{}).get("pageProps",{}).get("apiData")
        data=json.loads(api) if isinstance(api,str) else api
        get_calls=[e[1] for e in data if isinstance(e,list) and len(e)>1 and e[0]=="OFFER_GET"]
        if get_calls:
            o=get_calls[0];amap=o.get("res",{}).get("algoliaDataMap",{})
            note("ALDI Nord product store scoping",offer_get_request=o.get("req"),
                 total_products=len(amap),root_response_keys=list(o.get("res",{})),
                 representative_keys=list(next(iter(amap.values())))[:30] if amap else [],
                 presence_of_store_region_in_request=any(k in (o.get("req") or {}) for k in ("store","storeId","market","region","zipCode","postalCode")))
    except Exception as e:note("ALDI Nord parser",result="error",reason=type(e).__name__+": "+str(e)[:130])

# Lidl: public leaflet page is an alternative to app backend HTTP 400.
for url in ("https://www.lidl.de/c/online-prospekte/s10005610",):
    raw=get("Lidl official public leaflet page",url,maxbytes=5_000_000)
    if raw:
        identifiers=list(dict.fromkeys(re.findall(r'aktionsprospekt-[a-z0-9][a-z0-9-]{5,150}',unescape(raw),flags=re.I)))[:8]
        if not identifiers:
            identifiers=list(dict.fromkeys(re.findall(r'flyer_identifier[=\\": ]+([a-z0-9-]{8,120})',unescape(raw),flags=re.I)))[:8]
        note("Lidl leaflet discovery",has_flyer_string="flyer" in raw.lower(),flyer_identifier_candidates=identifiers)
        if identifiers:
            ident=identifiers[0]
            api="https://endpoints.leaflets.schwarz/v4/flyer?"+urlencode({"flyer_identifier":ident,"client":"lidl"})
            j=get("Lidl leaflet API for discovered public identifier",api,maxbytes=3_000_000)
            if j:
                try:
                    obj=json.loads(j);note("Lidl public leaflet JSON schema",root_keys=list(obj)[:30] if isinstance(obj,dict) else [],
                        flyer_keys=list(obj.get("flyer",{}))[:25] if isinstance(obj,dict) and isinstance(obj.get("flyer"),dict) else [],
                        response_length=len(j))
                except Exception as e:note("Lidl leaflet API parse",reason=str(e)[:120])

# Never retry guarded retailer endpoints merely because robots.txt returned HTTP 403.
for domain in ("www.edeka.de","www.netto-online.de"):
    get("Safe access check "+domain,"https://"+domain+"/robots.txt",maxbytes=100000)

Path("results").mkdir(exist_ok=True)
Path("results/store_scoping_20261031.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
