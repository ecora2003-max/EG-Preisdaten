#!/usr/bin/env python3
"""Netto Onlineshop: live one-page price test, offline parser safety checks."""
from __future__ import annotations
import json,sys,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from catalogues.netto_online import prices_from_product_html,validate_one_product

URL="https://www.netto-online.de/koelln-haferflocken-kernig-500-g-10er-pack/p-2162281000"
UA="ErnaehrungsgedaechnisResearch/2.2 (price signal and parsing test)"
OUT=Path("results/netto_online_offer_adapter_live_20261031.json")

def offline():
    s='''<script type="application/ld+json" data-cookieconsent="ignore">
{"@context":"https://schema.org/","@type":"Product","name":"Oat 500 g 10er","sku":"123","brand":{"@type":"Brand","name":"Brand"},"offers":{"@type":"Offer","priceCurrency":"EUR","price":"16.90","availability":"https://schema.org/InStock"}}</script>'''
    item=validate_one_product(s,"https://www.netto-online.de/oats/p-123",required_sku="123")
    assert str(item.price_eur)=="16.90" and item.scope=="NETTO_ONLINE_SHOP"
    assert item.name=="Oat 500 g 10er"
    assert item.brand=="Brand"
    assert not prices_from_product_html(s.replace('"EUR"','"USD"'),"https://www.netto-online.de/oats/p-123")
    assert not prices_from_product_html(s.replace('"16.90"','"NaN"'),"https://www.netto-online.de/oats/p-123")
    try:validate_one_product(s,"https://www.netto-online.de/oats/p-123",required_sku="456")
    except ValueError:pass
    else:raise AssertionError("SKU mismatch unhandled")
    try:prices_from_product_html(s,"https://evil.example/oats/p-123")
    except ValueError:pass
    else:raise AssertionError("Wrong host accepted")
    return "PASS"

def main():
    result={"tested_utc":datetime.now(timezone.utc).isoformat(),
            "scope":"Official Netto Onlineshop, not store POS",
            "url":URL,"offline_contract":offline()}
    try:
        req=urllib.request.Request(URL,headers={"User-Agent":UA,"Accept":"text/html"})
        with urllib.request.urlopen(req,timeout=22) as r:
            body=r.read(1000000)
            result["http_status"]=r.status
        html=body.decode("utf8","replace")
        offers=prices_from_product_html(html,URL)
        result["offer_count"]=len(offers)
        result["offers"]=[a.as_dict() for a in offers[:5]]
        result["price_verified"]=len(offers)==1 and offers[0].currency=="EUR"
        result["result"]="LIVE_PRICE_CONFIRMED" if result["price_verified"] else "NO_UNAMBIGUOUS_PRICE"
    except urllib.error.HTTPError as e:
        result["result"]="HTTP_ERROR";result["status"]=e.code
    except Exception as e:
        result["result"]="ERROR";result["error_type"]=type(e).__name__
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(result,ensure_ascii=False))
    if not result.get("price_verified"):raise SystemExit(2)
if __name__=="__main__":main()
