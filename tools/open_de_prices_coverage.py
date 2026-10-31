#!/usr/bin/env python3
"""Evaluate public DE grocery price dataset by source, freshness and barcode coverage.

Strictly research metadata; never mix Marktguru-derived data into the open-licensed
Open Prices subset. Uses one already-published CSV snapshot plus two tiny API reads.
"""
from __future__ import annotations
import csv,io,json,collections
from datetime import date,datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from pathlib import Path

TODAY=date(2026,10,31)
UA="Ernaehrungsgedaechtnis-Research/2.1 (research-only public price coverage check)"
URL="https://raw.githubusercontent.com/loukesio/german-supermarket-prices/main/data/prices.csv"
def grab(url,limit=4_000_000):
    with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"text/csv,application/json;q=0.9"}),timeout=25) as resp:
        raw=resp.read(limit+1)
        if len(raw)>limit:raise ValueError("Response larger than limit")
        return raw.decode("utf8","replace")
result={"checked_utc":datetime.now(timezone.utc).isoformat(),"date_basis":TODAY.isoformat(),"sources":[]}
try:
    records=list(csv.DictReader(io.StringIO(grab(URL))))
    hist=collections.defaultdict(list)
    for entry in records:hist[entry["retailer"]].append(entry)
    source_count=collections.Counter(r.get("source") for r in records)
    result["sources"].append({"source":"loukesio/german-supermarket-prices",
        "rows_total":len(records),
        "retailers":len(hist),"source_counts":dict(source_count),
        "licensing_caveat":"marktguru-offers may not have sufficient redistribution permissions; do not treat entire compiled repo as freely reusable",
        "row_schema":list(records[0]) if records else []})
    def age(r):
        try:return (TODAY-date.fromisoformat(r["price_date"])).days
        except Exception:return None
    stats=[]
    for name,rows in sorted(hist.items(),key=lambda k:-len(k[1])):
        ages=[age(r) for r in rows]
        stats.append({"retailer":name,"rows":len(rows),
            "by_source":dict(collections.Counter(r["source"] for r in rows)),
            "rows_price_30d":sum(a is not None and 0<=a<=30 for a in ages),
            "rows_price_90d":sum(a is not None and 0<=a<=90 for a in ages),
            "with_ean":sum(bool(r["ean_barcode"].strip()) for r in rows)})
    result["retailers"]=stats
except Exception as e:result["csv_error"]=type(e).__name__+": "+str(e)[:160]

for label,url in [
    ("Open Prices public recent-price sample","https://prices.openfoodfacts.org/api/v1/prices?size=3&date__gte=2026-10-01"),
    ("Open Prices public Berlin locations sample","https://prices.openfoodfacts.org/api/v1/locations?size=3&osm_address_city=Berlin"),
]:
    check={"source":label,"endpoint":url}
    try:
        data=json.loads(grab(url,300_000))
        check["type"]=type(data).__name__
        check["keys"]=list(data)[:20] if isinstance(data,dict) else []
        check["count"]=data.get("count") if isinstance(data,dict) else None
        rows=data.get("items",data.get("results")) if isinstance(data,dict) else None
        if isinstance(rows,list):
            check["sample_count"]=len(rows)
            if rows and isinstance(rows[0],dict):
                check["first_keys"]=list(rows[0])[:35]
                check["samples"]=[{k:r.get(k) for k in (
                     "id","product_code","price","currency","date","price_is_discounted","location_id",
                     "location_osm_display_name","location_osm_address_city","osm_name")}
                         for r in rows[:2]]
        check["result"]="PASS"
    except HTTPError as e:check["result"]="HTTP_ERROR "+str(e.code)
    except Exception as e:check["result"]="ERROR "+type(e).__name__+": "+str(e)[:140]
    result["sources"].append(check)

Path("results").mkdir(exist_ok=True)
Path("results/open_de_prices_coverage.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
print(json.dumps(result,indent=2,ensure_ascii=False))
