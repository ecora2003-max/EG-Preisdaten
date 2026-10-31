#!/usr/bin/env python3
"""One-time snapshot of EDEKA official market offer and price records.

User asserted authorization to download/store EDEKA data in GitHub. This
implementation does not assume access to a protected complete POS catalogue.
Store exact public market-specific offer responses and separately normalized
product-and-offer rows, preserving missing/unknown fields as null.

No inventory changes, no credentials, no customer data, no session hijacking.
"""
from __future__ import annotations
import json, os, hashlib, urllib.request,urllib.error
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

if os.environ.get("EDEKA_PERMISSION_CONFIRMED")!="1":
    raise SystemExit("EDEKA permission flag missing. Do not request retailer data.")
UA="ErnaehrungsgedaechtnisResearch/3.0 (user-reported authorized catalog snapshot)"
BASE="https://www.edeka.de/eh/service/eh/offers"
MARKETS={
 "10003451":{"city":"Berlin","test_scope":"market offers"},
 "913988":{"city":"Hamburg","test_scope":"market offers"},
}
STAMP=datetime.now(timezone.utc)
DATE=STAMP.strftime("%Y-%m-%d")
ROOT=Path("data/edeka")/DATE
ROOT.mkdir(parents=True,exist_ok=True)
def read_json(url,maxbytes=7_000_000):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=40) as r:
        raw=r.read(maxbytes+1)
        if len(raw)>maxbytes:raise RuntimeError("Response exceeds expected limit")
        if r.status!=200:raise RuntimeError(f"HTTP {r.status}")
    return json.loads(raw),hashlib.sha256(raw).hexdigest(),len(raw)
def to_amount(value):
    if value is None or isinstance(value,bool) or not isinstance(value,(str,float,int)):
        return None
    try:
        v=Decimal(str(value).replace(",","."))
        if v.is_finite() and v>=0:return format(v,"f")
    except (ValueError,InvalidOperation):pass
    return None
def iso_utc(value):
    if not isinstance(value,(int,float)):return None
    try:return datetime.fromtimestamp(value/1000 if value>100_000_000_000 else value,tz=timezone.utc).isoformat()
    except (OverflowError,OSError,ValueError):return None
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
def main():
    manifest={
        "fetched_at_utc":STAMP.isoformat(),
        "data_source":"EDEKA.de official public market offer API",
        "authorization_basis":"User confirmed on 2026-10-31 that download and GitHub storage were authorized; contractual scope not independently inspected.",
        "repository_scope":"ecora2003-max/Try (public)",
        "snapshot_kind":"MARKET_PROMOTION_PRICE_NOT_FULL_PRODUCT_CATALOG",
        "regular_prices_verified":False,
        "complete_product_catalog_downloaded":False,
        "stores":[],
    }
    got=0
    for market_id,meta in MARKETS.items():
        url=BASE+"?"+urlencode({"marketId":market_id,"limit":800})
        result={"market_id":market_id,"city":meta["city"],"url":url,"queried_at_utc":datetime.now(timezone.utc).isoformat()}
        try:
            obj,digest,source_bytes=read_json(url)
            offers=obj.get("docs")
            total=obj.get("anzahl")
            if not isinstance(offers,list):raise ValueError("Missing docs array")
            if not isinstance(total,int) or total!=len(offers):
                raise ValueError(f"API incomplete response: returned {len(offers)}, reported {total}")
            if obj.get("national") is not False:raise ValueError("Not market-specific: national flag not false")
            names=[]
            seen=set()
            for x in offers:
                if not isinstance(x,dict):raise ValueError("Non-dictionary offer entry")
                id=x.get("angebotid")
                name=x.get("titel")
                price=to_amount(x.get("preis"))
                if not isinstance(name,str) or not name.strip() or id is None:
                    raise ValueError("Offer without product title or identifier")
                if str(id) in seen:raise ValueError("Duplicate offer ID")
                seen.add(str(id))
                # Preserve all original fields in raw JSON; record normalized subset separately.
                names.append({
                    "retailer":"EDEKA","market_id":market_id,
                    "offer_id":str(id),"title":name.strip(),
                    "price_eur":price,"price_kind":"OFFER",
                    "regular_price_eur":None,"currency":"EUR" if price is not None else None,
                    "quantity_note":x.get("beschreibung"),
                    "unit_price_text":x.get("basicPrice"),
                    "category":x.get("warengruppe"),
                    "source":"OFFICIAL_MARKET_OFFER_API",
                    "valid_from_utc":iso_utc(obj.get("gueltig_von")),
                    "valid_to_utc":iso_utc(x.get("gueltig_bis") or obj.get("gueltig_bis")),
                    "gtin":None,
                    "retail_checkout_price_confirmed":False,
                })
            raw_path=ROOT/f"offers_{market_id}_raw.json"
            products_path=ROOT/f"offer_products_{market_id}.json"
            write(raw_path,{"source_url":url,"checked_at_utc":result["queried_at_utc"],
                            "market_id":market_id,"raw_response":obj})
            write(products_path,{"market_id":market_id,"retrieved_at_utc":result["queried_at_utc"],
                                 "scope":"PRODUCTS_DERIVED_FROM_OFFERS_ONLY",
                                 "products":names})
            result.update({"status":"SAVED","source_bytes":source_bytes,
                "source_sha256":digest,"reported_offer_count":total,
                "saved_offer_count":len(offers),
                "numeric_price_count":sum(x["price_eur"] is not None for x in names),
                "price_missing_count":sum(x["price_eur"] is None for x in names),
                "national":False,"valid_from_utc":iso_utc(obj.get("gueltig_von")),
                "valid_to_utc":iso_utc(obj.get("gueltig_bis")),
                "source_lastModified":obj.get("lastModified"),
                "files":[str(raw_path),str(products_path)]})
            got+=1
        except Exception as e:
            result.update({"status":"ERROR","error_type":type(e).__name__,"error_details":str(e)[:175]})
        manifest["stores"].append(result)
        print(json.dumps(result,ensure_ascii=False),flush=True)
    write(ROOT/"manifest.json",manifest)
    print("MANIFEST="+json.dumps(manifest,ensure_ascii=False),flush=True)
    if got!=len(MARKETS):raise SystemExit(2)
if __name__=="__main__":main()
