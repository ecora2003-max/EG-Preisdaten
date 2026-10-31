#!/usr/bin/env python3
import json,time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.robotparser import RobotFileParser
from urllib.error import HTTPError
UA="Ernaehrungsgedaechnis-Research/0.3 (read-only)"
checks=[]
robots={}
def get(label,url):
    origin=url.split("/")[0]+"//"+url.split("/")[2]
    rec={"label":label,"url":url}
    if origin not in robots:
        try:
            with urlopen(Request(origin+"/robots.txt",headers={"User-Agent":UA}),timeout=15) as z:
                p=RobotFileParser();p.parse(z.read(250000).decode("utf8","replace").splitlines());robots[origin]=p
        except HTTPError as e:robots[origin]="allow" if e.code==404 else "HTTP "+str(e.code)
        except Exception as e:robots[origin]="Error "+type(e).__name__
    r=robots[origin]
    if (isinstance(r,str) and r!="allow") or (not isinstance(r,str) and not r.can_fetch(UA,url)):
        rec["status"]="skip";checks.append(rec);return None
    try:
        with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"application/json"}),timeout=20) as z:
            data=z.read(5000000);rec["status"]=z.status
        obj=json.loads(data);checks.append(rec);time.sleep(.7);return obj
    except HTTPError as e:rec["status"]=e.code
    except Exception as e:rec["status"]=type(e).__name__;rec["error"]=str(e)[:160]
    checks.append(rec);return None
for slug in ("aktionsprospekt-02-11-2026-07-11-2026-fbfd28","aktionsprospekt-09-11-2026-14-11-2026-5f57dc"):
    url="https://endpoints.leaflets.schwarz/v4/flyer?"+urlencode({"flyer_identifier":slug,"client":"lidl"})
    obj=get("Lidl "+slug,url)
    if obj:
        f=obj.get("flyer") or {}
        out={"name":"Lidl flyer structured product detail","slug":slug,"startDate":f.get("startDate"),"endDate":f.get("endDate"),
             "offerStartDate":f.get("offerStartDate"),"offerEndDate":f.get("offerEndDate"),
             "region_codes":f.get("regions"),
             "products_type":type(f.get("products")).__name__,
             "products_count":len(f.get("products")) if isinstance(f.get("products"),(list,dict)) else None,
             "texts_type":type(f.get("texts")).__name__,
             "texts_count":len(f.get("texts")) if isinstance(f.get("texts"),(list,dict)) else None}
        p=f.get("products")
        if isinstance(p,list) and p and isinstance(p[0],dict):
            out["product_keys"]=list(p[0])[:50]
            out["product_sample"]={k:p[0].get(k) for k in ("id","name","title","price","articleNumber") if k in p[0]}
        checks.append(out)
stores={}
for store in ("DE5220","DE4620","DE4330"):
    dat=get("Kaufland article eligibility "+store,"https://filiale.kaufland.de/.kloffers.storeName="+store+".json")
    if isinstance(dat,list):
        ids={str(x.get("klNr")) for x in dat if isinstance(x,dict) and x.get("klNr") and x.get("dateFrom","")<="2026-11-08" and x.get("dateTo","")>="2026-11-02"}
        stores[store]=ids
        checks.append({"name":"Kaufland eligibility list summary","store":store,"all":len(dat),"week45":len(ids)})
if len(stores)>1:
    for a,b in [("DE5220","DE4620"),("DE5220","DE4330")]:
        if a in stores and b in stores:
            checks.append({"name":"Kaufland cross-region eligibility difference","store_a":a,"store_b":b,"common":len(stores[a]&stores[b]),"only_a":len(stores[a]-stores[b]),"only_b":len(stores[b]-stores[a])})
Path("results").mkdir(exist_ok=True)
Path("results/lidl_kaufland_deep.json").write_text(json.dumps(checks,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(checks,ensure_ascii=False,indent=2))
