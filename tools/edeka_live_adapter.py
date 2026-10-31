#!/usr/bin/env python3
"""Direct EDEKA marketId/region validity and parser smoke using official public JSON."""
import json,sys
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from adapters.retailer_offers import edeka_offers,Scope
UA="Ernaehrungsgedaechtnis-Research/0.9 (limited read-only API validation)"
tests=[]
def get(url):
    with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"application/json"}),timeout=22) as f:
        if f.status!=200:raise ValueError(f"HTTP {f.status}")
        b=f.read(3_000_000)
        if len(b)>=3_000_000:raise ValueError("unexpected EDEKA response size")
        return json.loads(b)
def search(postal):
    data=get("https://www.edeka.de/api/marketsearch/markets?"+urlencode({"searchstring":postal,"size":5}))
    m=next((m for m in data.get("markets",[]) if m.get("id")),None)
    if m is None:raise ValueError("No EDEKA market found")
    return str(m["id"]),m
sets={}
for postal in ("10405","20354"):
    try:
        mid,m=search(postal)
        p=get("https://www.edeka.de/eh/service/eh/offers?"+urlencode({"marketId":mid,"limit":300}))
        items=edeka_offers(p,market_id=mid)
        rec={"label":"EDEKA selected market "+postal,"result":"PASS" if items else "EMPTY",
             "market_id":mid,"name":m.get("name"),"region":m.get("region"),
             "reported_total":p.get("anzahl"),"response_docs":len(p.get("docs") or []),
             "normalized":len(items),"national":p.get("national"),
             "earliest":min((x.valid_from for x in items if x.valid_from),default=None),
             "latest":max((x.valid_to for x in items if x.valid_to),default=None),
             "scope_counts":{s.value:sum(x.scope==s for x in items) for s in Scope},
             "sample":[x.to_dict() for x in items[:2]]}
        tests.append(rec)
        sets[postal]={x.product_id for x in items}
    except Exception as e:
        tests.append({"label":"EDEKA selected market "+postal,
                      "result":"FAIL","error":type(e).__name__+":"+str(e)[:180]})
try:
    p=get("https://www.edeka.de/eh/service/eh/offers?"+urlencode({"marketId":"1","limit":60}))
    national=edeka_offers(p,market_id="1")
    tests.append({"label":"EDEKA national fallback",
                  "result":"PASS","national_flag":p.get("national"),
                  "normalized":len(national),"scope_counts":{s.value:sum(x.scope==s for x in national) for s in Scope}})
except Exception as e:tests.append({"label":"EDEKA national fallback","result":"FAIL","error":str(e)[:140]})
if len(sets)==2:
    a,b=sets.values()
    tests.append({"label":"EDEKA cross-region article identifiers","shared":len(a&b),
                  "only_berlin":len(a-b),"only_hamburg":len(b-a)})
out={"timestamp_utc":datetime.now(timezone.utc).isoformat(),"tests":tests}
Path("results").mkdir(exist_ok=True)
Path("results/edeka_live_adapter.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(out,ensure_ascii=False,indent=2))
if any(x.get("result")=="FAIL" for x in tests):sys.exit(1)
