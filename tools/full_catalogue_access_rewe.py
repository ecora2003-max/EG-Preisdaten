#!/usr/bin/env python3
"""REWE: try to establish full store catalogue enumeration via stationary search.

Tests a blank term, wildcard, and alternative pagination parameters. None
claim to cover the complete assortment unless an independent total/iteration
mechanism is present. No login, customer info or checkout requests.
"""
import hashlib
import json
import time
import urllib.parse
import urllib.error
import urllib.request
from datetime import datetime,timezone
from pathlib import Path

BASE="https://www.rewe.de/api/stationary-product-search/products"
STORE="840174"
UA="ErnaehrungsgedaechtnisResearch/1.1 (catalogue page discovery)"
TRIALS=[
    ("baseline",{"query":"Haferflocken","wwIdent":STORE}),
    ("empty_query",{"query":"","wwIdent":STORE}),
    ("wildcard",{"query":"*","wwIdent":STORE}),
    ("short_prefix",{"query":"a","wwIdent":STORE}),
    ("page_1",{"query":"Haferflocken","wwIdent":STORE,"page":"1"}),
    ("page_2",{"query":"Haferflocken","wwIdent":STORE,"page":"2"}),
    ("from_12",{"query":"Haferflocken","wwIdent":STORE,"from":"12"}),
    ("size_50",{"query":"Haferflocken","wwIdent":STORE,"size":"50"}),
    ("limit_50",{"query":"Haferflocken","wwIdent":STORE,"limit":"50"}),
    ("offset_12",{"query":"Haferflocken","wwIdent":STORE,"offset":"12"}),
    ("page_size_50",{"query":"Haferflocken","wwIdent":STORE,"pageSize":"50"}),
    ("baseline_repeat",{"query":"Haferflocken","wwIdent":STORE}),
]

def one(label,q):
    req=urllib.request.Request(BASE+"?"+urllib.parse.urlencode(q),
            headers={"User-Agent":UA,"Accept":"application/json"})
    out={"test":label,"parameters":q,"checked_utc":datetime.now(timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            data=r.read(1_300_000)
            out["http"]=r.status
        js=json.loads(data)
        if not isinstance(js,dict) or not isinstance(js.get("products"),list):
            out["result"]="NOT_A_PRODUCT_ARRAY"
            out["root_keys"]=sorted(js)[:20] if isinstance(js,dict) else []
            return out
        rows=js["products"]
        pairs=[(str(x.get("id")),x.get("pricing",{}).get("current"))
               for x in rows if isinstance(x,dict) and isinstance(x.get("pricing"),dict)]
        out.update({"result":"PRODUCT_ARRAY",
            "products":len(rows),"distinct_ids":len(set(x[0] for x in pairs)),
            "priced":sum(type(x[1]) is int for x in pairs),
            "fingerprint":hashlib.sha256(
                json.dumps(pairs,sort_keys=True).encode()).hexdigest(),
            "root_keys":sorted(js)[:24],
            "state_keys":sorted(js.get("state",{}))[:25] if isinstance(js.get("state"),dict) else [],
            "possible_totals":{k:v for k,v in js.items()
                    if k.lower() in ("total","totalcount","count","page","pages","pagination")
                    and type(v) in (int,str)},
        })
    except urllib.error.HTTPError as ex:
        out.update({"http":ex.code,"result":"HTTP_ERROR"})
    except Exception as ex:
        out.update({"result":"EXCEPTION","error":type(ex).__name__})
    return out

def main():
    out={"retailer":"REWE","scope":"stationary store search","store":STORE,
         "started_utc":datetime.now(timezone.utc).isoformat(),
         "requests":[]}
    for label,q in TRIALS:
        out["requests"].append(one(label,q))
        time.sleep(.65)
    rows=out["requests"]
    ref=rows[0]
    out["all_pagination_variants_equal_baseline"]=all(
        x.get("fingerprint")==ref.get("fingerprint") for x in rows[4:11])
    out["unfiltered_query_returns_more_than_12"]=any(
        x.get("products",0)>12 for x in rows[1:4])
    out["found_full_enumeration_mechanism"]=(
        out["unfiltered_query_returns_more_than_12"] or
        not out["all_pagination_variants_equal_baseline"]
    )
    out["note"]="Candidate mechanisms only; even >12 or changed page does not establish a complete store total."
    out["finished_utc"]=datetime.now(timezone.utc).isoformat()
    path=Path("results/full_catalogue_access_20261031/rewe.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(out,ensure_ascii=False))

if __name__=="__main__":
    main()
