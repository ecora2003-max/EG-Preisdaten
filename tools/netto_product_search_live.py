#!/usr/bin/env python3
"""Netto Marken-Discount: narrow read-only liveness check for known Retrofit GET.

APK evidence: GET rest/api/v2/productSearch?searchString=&storeId=.
Hostname still under test, so probe only three official host candidates.
Strictly no authentication, user identifiers, vouchers, transactions or writes.
"""
import json,urllib.request,urllib.error,urllib.parse
from pathlib import Path
from datetime import datetime,timezone
from urllib.robotparser import RobotFileParser

UA="ErnaehrungsgedaechtnisResearch/2.0 (Netto anonymous product price discovery)"
HOSTS=["https://app.netto-online.de","https://www.netto-online.de","https://sia.netto-online.de"]
SEARCH="/rest/api/v2/productSearch"
ARGS={"searchString":"Haferflocken","storeId":"7679"}
OUTPUT=Path("results/netto_product_search_live_20261031.json")

def check_robots(host,target):
    url=host+"/robots.txt"
    try:
        req=urllib.request.Request(url,headers={"User-Agent":UA})
        with urllib.request.urlopen(req,timeout=10) as r:
            raw=r.read(250000).decode("utf8","replace")
        parser=RobotFileParser();parser.parse(raw.splitlines())
        return ("ALLOW" if parser.can_fetch(UA,target) else "BLOCK")
    except urllib.error.HTTPError as e:
        return "ALLOW" if e.code==404 else "UNKNOWN_"+str(e.code)
    except Exception as e:
        return "UNKNOWN_"+type(e).__name__

def main():
    out={"checked_utc":datetime.now(timezone.utc).isoformat(),
         "package":"com.valuephone.vpnetto","method":"GET",
         "route":SEARCH,"query_params":list(ARGS),
         "store_id":"7679","goal":"Check whether anonymous filtered Netto product lookup yields actual numeric store prices.",
         "probes":[]}
    for host in HOSTS:
        url=host+SEARCH+"?"+urllib.parse.urlencode(ARGS)
        row={"host":host,"requested_path":SEARCH}
        row["crawler_access"]=check_robots(host,url)
        if row["crawler_access"]!="ALLOW":
            row["result"]="NOT_REQUESTED";out["probes"].append(row);continue
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=18) as r:
                data=r.read(800_001);row["http"]=r.status
                row["content_type"]=r.headers.get("Content-Type","")[:100]
            row["bytes_read"]=len(data)
            if len(data)>800000:
                row["result"]="RESPONSE_OVERSIZE"
            else:
                try:
                    obj=json.loads(data)
                    row["response_type"]=type(obj).__name__
                    if isinstance(obj,dict):
                        row["root_keys"]=sorted(obj)[:25]
                        for key in ("products","data","results","items","productList"):
                            if isinstance(obj.get(key),list):
                                rows=obj[key]
                                row["items_field"]=key;row["items_returned"]=len(rows)
                                row["sample_item_keys"]=[sorted(x)[:30] for x in rows[:2] if isinstance(x,dict)]
                                row["items_with_possible_price"]=sum(
                                    bool(set(k.lower() for k in x.keys())&
                                         {"price","currentprice","pricevalue","sellingprice","baseprice"})
                                    for x in rows if isinstance(x,dict))
                                break
                    elif isinstance(obj,list):
                        row["items_returned"]=len(obj)
                        row["sample_item_keys"]=[sorted(x)[:30] for x in obj[:2] if isinstance(x,dict)]
                    row["result"]="JSON_RESPONSE"
                except json.JSONDecodeError:
                    row["result"]="NON_JSON_RESPONSE"
        except urllib.error.HTTPError as e:
            row["http"]=e.code;row["result"]="HTTP_ERROR"
        except Exception as e:
            row["result"]="ERROR";row["type"]=type(e).__name__
        out["probes"].append(row)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
