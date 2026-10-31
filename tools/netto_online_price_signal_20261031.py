#!/usr/bin/env python3
"""Netto online product prices: targeted read-only retrieval, not store-POS prices.

Measures whether Netto's public webshop exposes directly parseable current
prices for products. Two official product-detail pages, one category page.
A status 200 alone is insufficient. Do not persist full HTML.
"""
from __future__ import annotations
import json, re, html
import urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path
from html.parser import HTMLParser

BASE="https://www.netto-online.de"
CASES=[
 {"name":"kornmuehle_haferflocken_zart_10pack","path":"/kornmuehle-haferflocken-zart-500-g-10er-pack/p-2208629000","pack_units":10,"pack_net_g":500},
 {"name":"koelln_haferflocken_kernig_10pack","path":"/koelln-haferflocken-kernig-500-g-10er-pack/p-2162281000","pack_units":10,"pack_net_g":500},
 {"name":"cornflakes_muesli_category","path":"/cornflakes-muesli/c-N011501"},
]
UA="ErnaehrungsgedaechnisResearch/2.2 (public webshop price signal verification)"
DEST=Path("results/netto_online_price_signal_20261031.json")
MAX_BYTES=2_200_000

class Info(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta=[]
        self.jsonld=[]
        self._json=False
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=="meta":
            key=attrs.get("property") or attrs.get("name") or attrs.get("itemprop")
            value=attrs.get("content")
            if isinstance(key,str) and re.search(r"(price|product|description)",key,re.I):
                self.meta.append({"key":key[:55],"value":str(value)[:200] if value else ""})
        if tag=="script" and attrs.get("type","").lower()=="application/ld+json":
            self._json=True
    def handle_data(self,data):
        if self._json and len(data)<250000:
            try:
                obj=json.loads(data)
                self.jsonld.append(obj)
            except json.JSONDecodeError:
                pass
    def handle_endtag(self,tag):
        if tag=="script":self._json=False

def prices_from_jsonld(objects):
    found=[]
    def traverse(value,depth=0):
        if depth>6:return
        if isinstance(value,list):
            for obj in value[:30]:traverse(obj,depth+1)
        if not isinstance(value,dict):return
        typ=value.get("@type")
        if typ in ("Offer","AggregateOffer") and value.get("price") is not None:
            found.append({"price":str(value.get("price"))[:30],"currency":str(value.get("priceCurrency"))[:12]})
        if typ in ("Product","IndividualProduct"):
            traverse(value.get("offers"),depth+1)
        traverse(value.get("@graph"),depth+1)
        traverse(value.get("itemListElement"),depth+1)
    traverse(objects)
    return found[:8]

def one(entry):
    url=BASE+entry["path"]
    out={"case":entry["name"],"url":url,"checked_utc":datetime.now(timezone.utc).isoformat(),"scope":"NETTO_ONLINE_SHOP_NOT_STATIONARY"}
    if "pack_units" in entry:out["units_per_pack"]=entry["pack_units"];out["pack_unit_g"]=entry["pack_net_g"]
    try:
        req=urllib.request.Request(url,headers={
            "User-Agent":UA,"Accept":"text/html,application/xhtml+xml",
            "Accept-Language":"de-DE,de;q=0.9"})
        with urllib.request.urlopen(req,timeout=25) as res:
            body=res.read(MAX_BYTES+1)
            out["status"]=res.status
            out["content_type"]=res.headers.get("Content-Type","")
            out["last_modified"]=res.headers.get("Last-Modified")
        out["bytes"]=len(body)
        if len(body)>MAX_BYTES:
            out["result"]="BODY_LIMIT";return out
        doc=body.decode("utf-8","replace")
        if "<html" not in doc.lower():
            out["result"]="NOT_HTML";return out
        soup=Info();soup.feed(doc)
        out["meta_price_fields"]=[x for x in soup.meta if "price" in x["key"].lower()][:15]
        out["jsonld_price_offers"]=prices_from_jsonld(soup.jsonld)
        # Strictly signal presence; do not interpret arbitrary monetary values.
        out["has_product_card_marker"]=bool(re.search(r"/p-\d{8,12}",doc))
        out["has_likely_shop_price_marker"]=bool(re.search(
            r"(?:itemprop\s*=\s*['\"]price|priceCurrency|product-price|sales-price|price__value|data-price)",doc,re.I))
        out["mentions_out_of_stock"]=bool(re.search(r"aktuell ausverkauft",doc,re.I))
        out["result"]="STRUCTURED_PRICE_FOUND" if out["meta_price_fields"] or out["jsonld_price_offers"] else "HTML_WITHOUT_VERIFIED_PRICE"
    except urllib.error.HTTPError as ex:
        out["status"]=ex.code;out["result"]="HTTP_ERROR"
    except Exception as ex:
        out["result"]="ERROR";out["error_type"]=type(ex).__name__
    return out

def main():
    records=[one(row) for row in CASES]
    result={"retailer":"Netto Marken-Discount", "scope":"OFFICIAL_ONLINE_SHOP",
            "tested_utc":datetime.now(timezone.utc).isoformat(),
            "tests":records,
            "structurally_verified_price_pages":sum(x.get("result")=="STRUCTURED_PRICE_FOUND" for x in records),
            "not_same_as_in_store_prices":True}
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
