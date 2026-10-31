#!/usr/bin/env python3
"""Netto Marken-Discount itemInfo: one real read-only price GET.

Uses publicly observed app.netto-online.de host, one published EAN
(Netto laktosefreie H-Milch) and one previously used Netto store ID.
No login, API key, customer data, transaction or bypass. HTTP 200 HTML
does not count as a successful price response.
"""
import json
import urllib.error
import urllib.parse
import urllib.request
from urllib.robotparser import RobotFileParser
from datetime import datetime, timezone
from pathlib import Path

HOST="https://app.netto-online.de"
STORE="7679"
EAN="4316268677943"
ROUTE=f"/api/v1/mpos/{STORE}/itemInfo"
UA="ErnaehrungsgedaechtnisResearch/2.1 (single read-only Netto price check)"
URL=HOST+ROUTE+"?"+urllib.parse.urlencode({"itemEAN":EAN,"allRelatedItems":"false"})
OUT=Path("results/netto_mpos_live_price_test_20261031.json")

def robots():
    try:
        req=urllib.request.Request(HOST+"/robots.txt",headers={"User-Agent":UA})
        with urllib.request.urlopen(req,timeout=12) as r: raw=r.read(240000).decode("utf-8","replace")
        parser=RobotFileParser()
        parser.parse(raw.splitlines())
        return "ALLOW" if parser.can_fetch(UA,URL) else "BLOCK"
    except urllib.error.HTTPError as e:
        return "ALLOW_404" if e.code==404 else "UNKNOWN_HTTP_"+str(e.code)
    except Exception as e:
        return "UNKNOWN_"+type(e).__name__

def main():
    result={"checked_utc":datetime.now(timezone.utc).isoformat(),
            "retailer":"Netto Marken-Discount","store_id":STORE,
            "ean":EAN,"host":HOST,"route":ROUTE,
            "method":"GET","authorisation":"anonymous",
            "test_kind":"single live MPOS price response validation",
            "price_verified":False}
    access=robots()
    result["robots"]=access
    if access not in ("ALLOW","ALLOW_404"):
        result["result"]="SKIPPED_ROBOTS"
    else:
        req=urllib.request.Request(URL,headers={"User-Agent":UA,"Accept":"application/json"})
        try:
            with urllib.request.urlopen(req,timeout=22) as r:
                raw=r.read(650001)
                result["http_status"]=r.status
                result["content_type"]=r.headers.get("Content-Type","")[:120]
            if len(raw)>650000:
                result["result"]="OVERSIZE"
            else:
                try:
                    obj=json.loads(raw)
                    result["json_root_type"]=type(obj).__name__
                    result["json_root_keys"]=sorted(obj)[:30] if isinstance(obj,dict) else []
                    entries=obj.get("ItemInfo") if isinstance(obj,dict) else None
                    items=[x for x in entries if isinstance(x,dict)] if isinstance(entries,list) else []
                    good=[]
                    for x in items:
                        v=x.get("ValidPrice")
                        if isinstance(v,dict) and v.get("Amount") is not None:
                            good.append({"amount_raw":str(v.get("Amount"))[:30],
                                         "currency":str(v.get("Currency"))[:8],
                                         "item_id_present":x.get("ItemID") is not None})
                    result["item_rows"]=len(items)
                    result["price_fields_found"]=good[:3]
                    result["price_verified"]=bool(good)
                    result["result"]="PRICE_RESPONSE_CONFIRMED" if good else "JSON_NO_PRICE"
                except json.JSONDecodeError:
                    result["result"]="NON_JSON_RESPONSE"
        except urllib.error.HTTPError as e:
            result["http_status"]=e.code
            result["result"]="HTTP_ERROR"
        except Exception as e:
            result["result"]="NETWORK_ERROR"
            result["error_type"]=type(e).__name__
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(result,ensure_ascii=False))

if __name__=="__main__":main()
