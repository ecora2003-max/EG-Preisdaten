#!/usr/bin/env python3
"""One-shot, read-only public supermarket offer probe. No login, no bypass."""
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser

UA = "Ernaehrungsgedaechtnis-Research/0.1 (public offer API validation)"
TIMEOUT = 13
MAX_BYTES = 12_000_000
robots = {}
tests = []

def safe_request(label, url, post=None):
    host = urlparse(url)
    origin = host.scheme + "://" + host.netloc
    entry = {"provider": label, "url": url, "method": "POST" if post else "GET"}
    if origin not in robots:
        try:
            with urlopen(Request(origin + "/robots.txt", headers={"User-Agent": UA}), timeout=TIMEOUT) as r:
                raw = r.read(300000).decode("utf-8", "replace")
                rp = RobotFileParser()
                rp.parse(raw.splitlines())
                robots[origin] = rp
        except HTTPError as e:
            robots[origin] = "allow" if e.code == 404 else "blocked: robots HTTP " + str(e.code)
        except Exception as e:
            robots[origin] = "blocked: robots " + type(e).__name__ + ": " + str(e)[:110]
    rule = robots[origin]
    if isinstance(rule, str) and rule != "allow":
        entry["result"] = "skipped"; entry["reason"] = rule
        tests.append(entry); return None
    if not isinstance(rule, str) and not rule.can_fetch(UA, url):
        entry["result"] = "skipped"; entry["reason"] = "robots disallows"
        tests.append(entry); return None
    try:
        headers = {"User-Agent": UA, "Accept": "application/json,text/html;q=0.9,*/*;q=0.5"}
        if post is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = urlencode(post).encode() if post else None
        req = Request(url, data=data, headers=headers)
        with urlopen(req, timeout=TIMEOUT) as r:
            entry["http_status"] = r.status
            entry["content_type"] = r.headers.get("Content-Type", "")[:90]
            entry["final_url"] = r.geturl()
            if urlparse(r.geturl()).netloc != host.netloc:
                entry["result"] = "cross-domain redirect"; tests.append(entry); return None
            content = r.read(MAX_BYTES + 1)
        entry["bytes"] = len(content)
        if len(content) > MAX_BYTES:
            entry["result"] = "too large"; tests.append(entry); return None
        try:
            obj = json.loads(content)
            entry["result"] = "json"
            entry["root_type"] = type(obj).__name__
            if isinstance(obj, dict):
                entry["root_keys"] = list(obj)[:30]
                for key in ("docs", "offers", "markets", "data", "store_items", "items", "results"):
                    if isinstance(obj.get(key), list):
                        entry["items_key"] = key
                        entry["items_count"] = len(obj[key])
                        if obj[key] and isinstance(obj[key][0], dict):
                            entry["first_item_keys"] = list(obj[key][0])[:60]
                            fields = ("name", "title", "titel", "preis", "price", "packaging",
                                      "sellingSize", "quantityUnit", "startValidityDate",
                                      "endValidityDate", "gueltig_von", "gueltig_bis",
                                      "validFrom", "validUntil", "basicPrice",
                                      "nextWeekSellingRegion", "sellingRegion", "wwIdent")
                            entry["samples"] = [{k: it[k] for k in fields if k in it}
                                                for it in obj[key][:2] if isinstance(it, dict)]
                        break
            elif isinstance(obj, list):
                entry["items_count"] = len(obj)
                if obj and isinstance(obj[0], dict):
                    entry["first_item_keys"] = list(obj[0])[:60]
                    fields = ("storeKey", "locality", "postalCode", "wwIdent",
                              "sellingRegion", "nextWeekSellingRegion", "nextWeekFlippingBookURL")
                    entry["samples"] = [{k: it[k] for k in fields if k in it}
                                        for it in obj[:1] if isinstance(it, dict)]
            entry["future_date_text_in_response"] = any(
                x in content.decode("utf-8", "replace") for x in
                ("2026-11-02", "02.11.2026", "2026-11-09", "09.11.2026"))
            tests.append(entry)
            time.sleep(0.7)
            return obj
        except (ValueError, UnicodeError):
            html = content.decode("utf-8", "replace")
            entry["result"] = "html_or_other"
            entry["has_next_data"] = "__NEXT_DATA__" in html
            entry["has_ld_json"] = "application/ld+json" in html
            entry["has_future_date"] = bool(re.search(
                r"2026-11-02|02[.]11[.]2026|2026-11-09|09[.]11[.]2026", html))
            entry["euro_signs"] = html.count("€")
            tests.append(entry)
            time.sleep(0.7)
            return html
    except HTTPError as e:
        entry["result"] = "http_error"; entry["http_status"] = e.code; tests.append(entry)
    except Exception as e:
        entry["result"] = "error"
        entry["reason"] = type(e).__name__ + ": " + str(e)[:160]
        tests.append(entry)
    return None

# One request per documented public endpoint; extra product requests only if
# a relevant store ID was obtained from an actual, successful public response.
ed = safe_request("EDEKA store search", "https://www.edeka.de/api/marketsearch/markets?size=5&searchstring=10115")
if isinstance(ed, dict):
    ls = next((ed[k] for k in ("markets","docs","items") if isinstance(ed.get(k), list)), [])
    mid = next((str(m.get("id") or m.get("marketId") or m.get("wwIdent"))
                for m in ls if isinstance(m,dict) and (m.get("id") or m.get("marketId") or m.get("wwIdent"))), None)
    if mid:
        safe_request("EDEKA offers", "https://www.edeka.de/eh/service/eh/offers?" +
                     urlencode({"marketId": mid, "limit": 15}))

safe_request("Netto Marken-Discount public offers HTML", "https://www.netto-online.de/angebote/")
safe_request("Netto Marken-Discount public store finder", "https://www.netto-online.de/INTERSHOP/web/WFS/Plus-NettoDE-Site/de_DE/-/EUR/ViewMMPStoreFinder-GetStoreItems",
             post={"s": "52.45","n":"52.55","w":"13.30","e":"13.50",
                   "netto":"true","city":"true","service":"true","beverage":"true","nonfood":"true"})

li = safe_request("Lidl store catalog", "https://stores.lidlplus.com/api/v4/DE")
if isinstance(li, list):
    store = next((s for s in li if isinstance(s,dict) and str(s.get("locality","")).lower()=="berlin" and s.get("storeKey")), None)
    if store:
        safe_request("Lidl offers Berlin store", "https://offers.lidlplus.com/app/api/v4/DE/"+str(store["storeKey"])+"/offers")

safe_request("REWE public offers HTML", "https://www.rewe.de/angebote/nationale-angebote/")
penny = safe_request("PENNY public store catalog", "https://www.penny.de/.rest/market")
if isinstance(penny, list):
    berlin = next((s for s in penny if isinstance(s,dict) and str(s.get("city","")).lower()=="berlin"), None)
    if berlin:
        tests.append({"provider":"PENNY Berlin market metadata","result":"derived_from_live_json",
                      "fields":{k:berlin.get(k) for k in
                                ("wwIdent","city","zipCode","sellingRegion","nextWeekSellingRegion",
                                 "flippingBookURL","nextWeekFlippingBookURL")}})

nord_html = safe_request("ALDI Nord next-week HTML", "https://www.aldi-nord.de/angebote-vorschau.html")
safe_request("ALDI Sued future structured offers",
             "https://api.aldi-sued.de/v3/product-search?serviceType=walk-in&servicePoint=B384&currency=EUR&limit=12&offset=0&sort=relevance&promotionKey=2026-11-02")
kaufland_html = safe_request("Kaufland next-week HTML", "https://filiale.kaufland.de/angebote/naechste-woche.html")


# Round 2: Verify actual structured product offers and embedded page data.
if isinstance(li, list):
    berlin_stores = [s for s in li if isinstance(s,dict) and
                     "berlin" in str(s.get("locality","")).casefold() and s.get("storeKey")]
    tests.append({"provider":"Lidl Berlin store matching","result":"derived_from_live_json",
                  "matches":len(berlin_stores),
                  "first_store_key":berlin_stores[0].get("storeKey") if berlin_stores else None})
    selected = (berlin_stores[0] if berlin_stores else
                next((s for s in li if isinstance(s,dict) and s.get("storeKey")), None))
    if selected and not any(t.get("provider") == "Lidl offers Berlin store" for t in tests):
        safe_request("Lidl offers Berlin store" if berlin_stores else "Lidl offers sample German store",
                     "https://offers.lidlplus.com/app/api/v4/DE/"+str(selected["storeKey"])+"/offers")

if isinstance(penny, list):
    berlin_store = next((s for s in penny if isinstance(s,dict) and
                         str(s.get("city","")).casefold()=="berlin" and s.get("sellingRegion")), None)
    if berlin_store:
        region=berlin_store.get("nextWeekSellingRegion") or berlin_store["sellingRegion"]
        for week in ("2026-44","2026-45"):
            offers_result = safe_request("PENNY product offers calendar week "+week,
                         "https://www.penny.de/.rest/offers/by-category/"+week+"/top-angebote?"+
                         urlencode({"region":region}))
            if isinstance(offers_result,dict):
                tiles=offers_result.get("offerTiles")
                summary_item={"provider":"PENNY product object fields "+week,
                              "result":"parsed_live_json",
                              "offerTiles_type":type(tiles).__name__}
                if isinstance(tiles,list):
                    summary_item["product_count"]=len(tiles)
                    summary_item["product_keys"]=list(tiles[0])[:50] if tiles and isinstance(tiles[0],dict) else []
                    summary_item["first_product_json_excerpt"]=json.dumps(tiles[:1],ensure_ascii=False,default=str)[:1000]
                tests.append(summary_item)

if isinstance(nord_html,str):
    match=re.search(r'<script[^>]*id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',nord_html,re.S|re.I)
    if match:
        try:
            nd=json.loads(match.group(1))
            candidates=[]
            api_keys=[]
            def walk(node,path="root",depth=0):
                if depth>17 or len(candidates)>8:return
                if isinstance(node,dict):
                    if "OFFER_GET" in node:api_keys.append(path+".OFFER_GET")
                    for k,v in node.items():
                        walk(v,path+"."+str(k),depth+1)
                elif isinstance(node,list) and node and isinstance(node[0],dict):
                    keys=set(node[0])
                    if keys & {"price","priceInfo","productName","title","name","productTitle"}:
                        candidates.append({"path":path,"count":len(node),
                                           "keys":list(node[0])[:24]})
                    for v in node[:5]:walk(v,path+"[]",depth+1)
            walk(nd)
            tests.append({"provider":"ALDI Nord pageProps keys",
                          "result":"embedded_json_parsed",
                          "page_props_keys":list(nd.get("props",{}).get("pageProps",{}))[:50],
                          "page_keys":list(nd.get("props",{}).get("pageProps",{}).get("page",{}))[:30] if isinstance(nd.get("props",{}).get("pageProps",{}).get("page",{}),dict) else []})
            tests.append({"provider":"ALDI Nord embedded JSON structure",
                          "result":"embedded_json_parsed","root_keys":list(nd)[:10],
                          "offer_get_paths":api_keys[:8],"candidate_product_lists":candidates[:8]})
        except Exception as e:
            tests.append({"provider":"ALDI Nord embedded JSON structure",
                          "result":"parse_error","reason":str(e)[:140]})

if isinstance(kaufland_html,str):
    def excerpt_around(needle):
        loc=kaufland_html.find(needle)
        return kaufland_html[max(0,loc-80):loc+320] if loc>=0 else None
    tests.append({"provider":"Kaufland embedded offer excerpts",
                  "result":"observed_html","first_dateFrom_context":excerpt_around('"dateFrom"'),
                  "first_price_context":excerpt_around('"price"')})
    tests.append({"provider":"Kaufland next-week embedded data signals",
                  "result":"html_metadata_examined",
                  "price_field_mentions":len(re.findall(r'["\x27]price["\x27]\s*:',kaufland_html)),
                  "date_from_mentions":kaufland_html.count("dateFrom"),
                  "kloffers_mentions":kaufland_html.count("kloffers"),
                  "sales_from_mentions":kaufland_html.count("salesFrom")})

# One conservative alternate path-format probe; no app-only authentication headers.
safe_request("Lidl sample store key without country prefix",
             "https://offers.lidlplus.com/app/api/v4/DE/7434/offers")


# Verify the nested structured offer payload, not merely HTML marker counts.
if isinstance(kaufland_html, str):
    key_pos = kaufland_html.find('"offerData":')
    if key_pos >= 0:
        obj_start = kaufland_html.find("{", key_pos + len('"offerData":'))
        try:
            offer_data, consumed = json.JSONDecoder().raw_decode(kaufland_html[obj_start:])
            cycles = offer_data.get("cycles", []) if isinstance(offer_data, dict) else []
            per_date = {}
            future_sample = []
            all_count = 0
            for cycle in cycles:
                for category in cycle.get("categories", []) if isinstance(cycle,dict) else []:
                    for offer in category.get("offers", []) if isinstance(category,dict) else []:
                        if not isinstance(offer,dict):continue
                        all_count += 1
                        date_key = str(offer.get("salesFrom") or offer.get("dateFrom") or "unknown")
                        per_date[date_key] = per_date.get(date_key, 0) + 1
                        if date_key >= "2026-11-02" and len(future_sample) < 3:
                            future_sample.append({k:offer.get(k) for k in
                                ("offerId","title","price","unit","dateFrom","dateTo","salesFrom","salesTo")})
            tests.append({"provider":"Kaufland embedded offerData verified",
                          "result":"json_decoded_from_html",
                          "cycles_count":len(cycles),"total_offers_in_embedded_data":all_count,
                          "offer_sales_start_counts":per_date,
                          "sample_future_offers":future_sample})
        except Exception as e:
            tests.append({"provider":"Kaufland embedded offerData verified",
                          "result":"parse_failed","reason":type(e).__name__+": "+str(e)[:140]})

if isinstance(nord_html,str):
    m=re.search(r'<script[^>]*id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',nord_html,re.S|re.I)
    if m:
        nd=json.loads(m.group(1))
        api_data=nd.get("props",{}).get("pageProps",{}).get("apiData")
        tests.append({"provider":"ALDI Nord apiData nested structure",
                      "result":"embedded_json_examined",
                      "type":type(api_data).__name__,
                      "keys":list(api_data)[:45] if isinstance(api_data,dict) else [],
                      "array_count":len(api_data) if isinstance(api_data,list) else None})

summary={"timestamp_utc":datetime.now(timezone.utc).isoformat(),
         "purpose":"read-only snapshot of public retailer offering APIs",
         "limitations":"No authentication, impersonation, CAPTCHA bypass or retries; skip when robots unavailable",
         "tests":tests}
Path("results").mkdir(exist_ok=True)
Path("results/retailer-offers.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False,indent=2,default=str))
