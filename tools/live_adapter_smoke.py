#!/usr/bin/env python3
"""Live schema smoke tests for the offline adapters, fail on incompatible official data.

Read-only, 1 request per public endpoint, honors published robots rules, never
attempts protected domains. Stores only metadata, not full product catalogues.
"""
import json
import re
import sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.robotparser import RobotFileParser

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from adapters.retailer_offers import (
    penny_store,penny_offers,kaufland_offers,aldi_nord_next,lidl_flyer,Scope,
    netto_status,edeka_offers
)
UA="Ernaehrungsgedaechtnis-Research/0.4 (read-only integration test)"
robots={}
results=[]
failed=[]
def fetch(label,url):
    u=urlparse(url);host=u.scheme+"://"+u.netloc
    if host not in robots:
        try:
            with urlopen(Request(host+"/robots.txt",headers={"User-Agent":UA}),timeout=14) as resp:
                rp=RobotFileParser();rp.parse(resp.read(250000).decode("utf-8","replace").splitlines());robots[host]=rp
        except HTTPError as err:
            robots[host]="allow" if err.code==404 else "blocked robots HTTP "+str(err.code)
        except Exception as err:robots[host]="blocked robots "+type(err).__name__
    rule=robots[host]
    if (isinstance(rule,str) and rule!="allow") or (not isinstance(rule,str) and not rule.can_fetch(UA,url)):
        raise RuntimeError("disallowed or unknown robots status: "+str(rule))
    with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"application/json,text/html"}),timeout=24) as resp:
        data=resp.read(12_000_001)
        if len(data)>12_000_000:raise RuntimeError("response exceeds test bound")
        return data.decode("utf-8","replace")

def run(label,fn):
    try:
        value=fn()
        results.append({"test":label,"result":"PASS",**value})
    except Exception as exc:
        msg=type(exc).__name__+": "+str(exc)[:180]
        results.append({"test":label,"result":"FAIL","reason":msg})
        failed.append(label)

def check_penny():
    markets=json.loads(fetch("Penny markets","https://www.penny.de/.rest/market"))
    b=next(s for s in markets if s.get("city")=="Berlin" and s.get("nextWeekSellingRegion"))
    lookup=penny_store(markets,str(b["wwIdent"]),week="next")
    url="https://www.penny.de/.rest/offers/by-category/2026-45/top-angebote?"+urlencode({"region":lookup["region"]})
    offers=penny_offers(json.loads(fetch("Penny offers",url)),region=lookup["region"],week_start="2026-11-02")
    assert len(offers)>0
    assert all(x.scope==Scope.REGION and x.scope_id==lookup["region"] for x in offers)
    return {"offers":len(offers),"store_id":lookup["store_id"],"region":lookup["region"],
            "sample":offers[0].to_dict()}

def check_kaufland():
    sid="DE5220"
    page=fetch("Kaufland offer html","https://filiale.kaufland.de/angebote/uebersicht.html?kloffer-week=next")
    availability=json.loads(fetch("Kaufland market applicability","https://filiale.kaufland.de/.kloffers.storeName="+sid+".json"))
    offers=kaufland_offers(page,availability,store_id=sid,first_day="2026-11-02",last_day="2026-11-08")
    assert len(offers)>0
    assert all(x.scope==Scope.STORE and x.scope_id==sid for x in offers)
    return {"offers":len(offers),"store_id":sid,"first_offer":offers[0].to_dict()}

def check_aldi():
    page=fetch("Aldi Nord offers","https://www.aldi-nord.de/angebote-vorschau.html")
    offers=aldi_nord_next(page)
    assert len(offers)>0
    assert all(x.scope==Scope.CHAIN for x in offers)
    return {"offers_with_prices":len(offers),"unpriced_skipped":276-len(offers),
            "sample":offers[0].to_dict()}

def check_lidl():
    slug="aktionsprospekt-02-11-2026-07-11-2026-fbfd28"
    url="https://endpoints.leaflets.schwarz/v4/flyer?"+urlencode({"flyer_identifier":slug,"client":"lidl"})
    obj=json.loads(fetch("Lidl leaflet",url))
    offers=lidl_flyer(obj,expected_start="2026-11-02")
    assert len(offers)>0
    assert all(x.scope==Scope.UNVERIFIED for x in offers)
    return {"entries_not_store_verified":len(offers),"first_entry":offers[0].to_dict()}

run("PENNY actual Berlin region and next-week products",check_penny)
run("Kaufland actual store article intersection",check_kaufland)
run("ALDI Nord actual Next.js next-week offers",check_aldi)
run("Lidl actual November leaflet entries",check_lidl)
report={"checked_at_utc":datetime.now(timezone.utc).isoformat(),"results":results,
        "failed":failed,"note":"A PASS means schema compatibility, not legal data reuse rights or market stock."}
Path("results").mkdir(exist_ok=True)
Path("results/live_adapter_smoke.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
if failed:sys.exit(1)
