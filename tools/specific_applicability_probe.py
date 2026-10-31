#!/usr/bin/env python3
import json,re,hashlib,time
from urllib.request import Request,urlopen
from urllib.robotparser import RobotFileParser
from urllib.error import HTTPError
from urllib.parse import urlparse,urlencode
from datetime import datetime,timezone
from pathlib import Path
U="Ernaehrungsgedaechnis-Research/0.3 (read-only market applicability)"
R={"utc":datetime.now(timezone.utc).isoformat(),"tests":[]}; robots={}
def get(label,url,headers=None,limit=9000000):
    origin=urlparse(url).scheme+"://"+urlparse(url).netloc
    test={"name":label,"url":url}
    if origin not in robots:
        try:
            with urlopen(Request(origin+"/robots.txt",headers={"User-Agent":U}),timeout=15) as f:
                r=RobotFileParser();r.parse(f.read(250000).decode("utf-8","replace").splitlines());robots[origin]=r
        except HTTPError as e:robots[origin]="allow" if e.code==404 else "robots HTTP "+str(e.code)
        except Exception as e:robots[origin]=type(e).__name__+" reading robots"
    rule=robots[origin]
    if (isinstance(rule,str) and rule!="allow") or (not isinstance(rule,str) and not rule.can_fetch(U,url)):
        test.update(status="skipped",reason=str(rule) if isinstance(rule,str) else "robots disallows")
        R["tests"].append(test);return None
    try:
        with urlopen(Request(url,headers={"User-Agent":U,"Accept":"application/json,text/html,*/*",**(headers or {})}),timeout=20) as f:
            test.update(status=f.status,content_type=f.headers.get("Content-Type",""))
            b=f.read(limit+1)
        test.update(size=len(b),sha256=hashlib.sha256(b).hexdigest())
        if len(b)>limit:
            test.update(status="size exceeded");R["tests"].append(test);return None
        R["tests"].append(test);time.sleep(.5)
        return b.decode("utf-8","replace")
    except HTTPError as e:test.update(status=e.code,error="http")
    except Exception as e:test.update(status="error",error=type(e).__name__+":"+str(e)[:100])
    R["tests"].append(test);return None
def record(label,**x):R["tests"].append({"name":label,**x})
# Official Kaufland weekly applicability list per named store, not stock level.
ids={}
for store in ("DE5220","DE1680"):
    url="https://filiale.kaufland.de/.kloffers.storeName="+store+".json"
    raw=get("Kaufland store validity "+store,url)
    if not raw:continue
    try:
        arr=json.loads(raw)
        filtered=[x for x in arr if isinstance(x,dict) and str(x.get("dateFrom",""))<="2026-11-08" and str(x.get("dateTo",""))>="2026-11-02"]
        offers={str(x["klNr"]) for x in filtered if x.get("klNr")}
        ids[store]=offers
        record("Kaufland product validity "+store,total_records=len(arr),week45_records=len(filtered),week45_article_ids=len(offers),item_keys=list(arr[0])[:15] if arr else [],samples=[{k:x.get(k) for k in ("klNr","dateFrom","dateTo")} for x in filtered[:3]])
    except Exception as e:record("Kaufland decode "+store,error=str(e)[:170])
if len(ids)==2:
    a,b=ids["DE5220"],ids["DE1680"]
    record("Kaufland validity delta between actual stores",total_a=len(a),total_b=len(b),shared_ids=len(a&b),only_DE5220=len(a-b),only_DE1680=len(b-a),sample_only_DE5220=sorted(a-b)[:8],sample_only_DE1680=sorted(b-a)[:8])
# Public Lidl leaflets: identify whether structured prices/products actually present.
for slug in ("aktionsprospekt-02-11-2026-07-11-2026-fbfd28","aktionsprospekt-09-11-2026-14-11-2026-5f57dc"):
    url="https://endpoints.leaflets.schwarz/v4/flyer?"+urlencode({"flyer_identifier":slug,"client":"lidl"})
    raw=get("Lidl future flyer "+slug,url)
    if not raw:continue
    try:
        obj=json.loads(raw)
        flyer=obj.get("flyer") or {}
        root_keys=list(flyer)[:90]
        counts=[]
        def walk(x,path="flyer",depth=0):
            if depth>14 or len(counts)>=14:return
            if isinstance(x,dict):
                for k,v in x.items():
                    if isinstance(v,list) and v and isinstance(v[0],dict):
                        counts.append({"path":path+"."+str(k),"count":len(v),"first_keys":list(v[0])[:30]})
                    walk(v,path+"."+str(k),depth+1)
            elif isinstance(x,list):
                for it in x[:2]:walk(it,path+"[]",depth+1)
        walk(flyer)
        record("Lidl flyer parsed "+slug,flyer_keys=root_keys,
               flyer_name=str(flyer.get("name") or flyer.get("title"))[:130],
               product_like_list_paths=counts[:12])
    except Exception as e:record("Lidl future parse "+slug,error=type(e).__name__+":"+str(e)[:120])
# PENNY: compare two genuinely distinct regions, excluding Berlin double-match.
raw=get("PENNY stores for regional differentiation","https://www.penny.de/.rest/market",limit=6500000)
if raw:
    try:
        data=json.loads(raw);regions={}
        for store in data:
            if not isinstance(store,dict):continue
            rg=store.get("nextWeekSellingRegion") or store.get("sellingRegion")
            if rg and store.get("wwIdent"):regions.setdefault(rg,store)
        berlin=next((x for x in data if x.get("city")=="Berlin" and x.get("nextWeekSellingRegion")),None)
        choose=[]
        if berlin:choose.append(berlin)
        choose.append(next((x for x in regions.values() if x.get("nextWeekSellingRegion") and x.get("nextWeekSellingRegion")!=(berlin or {}).get("nextWeekSellingRegion")),None))
        collected=[]
        for x in choose:
            if not x:continue
            rg=x.get("nextWeekSellingRegion")
            rawoffers=get("PENNY different region "+rg,"https://www.penny.de/.rest/offers/by-category/2026-45/top-angebote?"+urlencode({"region":rg}))
            if rawoffers:
                arr=json.loads(rawoffers).get("offerTiles",[])
                d={str(y.get("title")):y.get("price") for y in arr if isinstance(y,dict)}
                collected.append((rg,d))
                record("PENNY selected region offer sample",region=rg,city=x.get("city"),market_id=x.get("wwIdent"),count=len(arr),samples=[{k:y.get(k) for k in ("title","price","quantity")} for y in arr[:4] if isinstance(y,dict)])
        if len(collected)==2:
            (a,pa),(b,pb)=collected;common=set(pa)&set(pb)
            record("PENNY regions compare",regions=[a,b],common_names=len(common),price_differences=sum(pa[k]!=pb[k] for k in common),only_a=len(set(pa)-set(pb)),only_b=len(set(pb)-set(pa)))
        record("PENNY all regions count",num_distinct_regions=len(regions))
    except Exception as e:record("PENNY regional parse",error=str(e)[:120])
Path("results").mkdir(exist_ok=True)
Path("results/specific_applicability.json").write_text(json.dumps(R,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(R,ensure_ascii=False,indent=2))
