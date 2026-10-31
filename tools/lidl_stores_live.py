#!/usr/bin/env python3
"""Small, read-only direct Lidl Plus store-offer schema and market comparison."""
import json,re,collections,time
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from pathlib import Path
UA="Ernaehrungsgedaechnis-Research/0.7 (read-only offer validation)"
robots={}
results=[]
def request(label,url,headers=None):
    from urllib.parse import urlparse
    p=urlparse(url);host=p.scheme+"://"+p.netloc
    if host not in robots:
        try:
            with urlopen(Request(host+"/robots.txt",headers={"User-Agent":UA}),timeout=12) as f:
                rp=RobotFileParser();rp.parse(f.read(200000).decode("utf-8","replace").splitlines());robots[host]=rp
        except HTTPError as e:robots[host]="allow" if e.code==404 else "unknown robots HTTP "+str(e.code)
        except Exception as e:robots[host]="unknown robots "+type(e).__name__
    rp=robots[host]
    meta={"label":label,"url":url}
    if (isinstance(rp,str) and rp!="allow") or (not isinstance(rp,str) and not rp.can_fetch(UA,url)):
        meta["result"]="SKIPPED robots restrictions";results.append(meta);return None
    hs={"User-Agent":UA,"Accept":"application/json","Accept-Language":"de-DE,de;q=0.9"}
    hs.update(headers or {})
    try:
        with urlopen(Request(url,headers=hs),timeout=22) as f:
            meta["status"]=f.status;raw=f.read(3_000_000)
        obj=json.loads(raw)
        meta["type"]=type(obj).__name__
        meta["root_keys"]=list(obj)[:20] if isinstance(obj,dict) else []
        results.append(meta);time.sleep(.5);return obj
    except HTTPError as e:meta["status"]=e.code
    except Exception as e:meta["error"]=type(e).__name__+":"+str(e)[:140]
    results.append(meta)
    return None

s=request("Lidl store catalog","https://stores.lidlplus.com/api/v4/DE")
if isinstance(s,list):
    selected=[]
    for key in ["DE7434","DE7602"]:
        store=next((x for x in s if isinstance(x,dict) and x.get("storeKey")==key),None)
        if store:selected.append(store)
    for store in selected:
        key=str(store["storeKey"])
        url="https://offers.lidlplus.com/app/api/v4/DE/"+key+"/offers"
        payload=request("Lidl offers "+key,url,headers={"X-Client-Version":"17.0.5","X-Client-Platform":"android"})
        if not isinstance(payload,dict):continue
        offers=payload.get("offers") or []
        result={"label":"Lidl offer analysis "+key,
                "store_key":key,"locality":store.get("locality"),"postal_code":store.get("postalCode"),
                "reported_total":payload.get("totalOffers"),"offers_items":len(offers),
                "first_keys":list(offers[0]) if offers and isinstance(offers[0],dict) else [],
                "validity_starts":dict(collections.Counter(str(o.get("startValidityDate"))[:10] for o in offers if isinstance(o,dict))),
                "validity_ends":dict(collections.Counter(str(o.get("endValidityDate"))[:10] for o in offers if isinstance(o,dict))),
                "offer_types":dict(collections.Counter(str(o.get("offerType")) for o in offers if isinstance(o,dict))),
                "samples":[]}
        for o in offers[:5]:
            if not isinstance(o,dict):continue
            result["samples"].append({k:o.get(k) for k in
               ("id","title","brand","packaging","pricePerUnit","startValidityDate","endValidityDate","offerType","category","priceBox","loyaltyPriceBox")})
        ids={str(o.get("id") or o.get("title")) for o in offers if isinstance(o,dict)}
        result["_ids"]=sorted(ids)
        results.append(result)
if len([r for r in results if r.get("label","").startswith("Lidl offer analysis")])==2:
    a,b=[r for r in results if r.get("label","").startswith("Lidl offer analysis")]
    x,y=set(a.pop("_ids")),set(b.pop("_ids"))
    results.append({"label":"Lidl two-store catalogue comparison","stores":[a["store_key"],b["store_key"]],
                    "shared":len(x&y),"only_first":len(x-y),"only_second":len(y-x)})
else:
    for r in results:r.pop("_ids",None)
out={"checked_at_utc":datetime.now(timezone.utc).isoformat(),"tests":results}
Path("results").mkdir(exist_ok=True)
Path("results/lidl_stores_live.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
