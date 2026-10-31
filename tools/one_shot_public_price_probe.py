#!/usr/bin/env python3
"""Two bounded, unauthenticated, read-only retailer price endpoint checks.

Exactly one product search per retailer and no pagination. The probe first
respects robots.txt, never uses login/certificates/API keys, never evades
blocks, and saves only a small sanitized diagnostic summary.
Not a scraper, pricing feed, or authorisation for continued extraction.
"""
from __future__ import annotations
import json
import sys
import urllib.parse
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.robotparser import RobotFileParser

UA = "ErnaehrungsgedaechtnisResearch/1.0 (one-off noncommercial API diagnostic)"
HOSTS = {
    "rewe_stationary": {
        "origin": "https://www.rewe.de",
        "path": "/api/stationary-product-search/products",
        "query": {"query": "Haferflocken", "wwIdent": "840174"},
        "expected_price": "pricing.current",
        "price_unit": "cents",
    },
    "aldi_sued": {
        "origin": "https://api.aldi-sued.de",
        "path": "/v3/product-search",
        "query": {"q": "Haferflocken", "servicePoint": "B384",
                  "serviceType": "walk-in", "limit": "12", "offset": "0"},
        "expected_price": "price.amountRelevant",
        "price_unit": "cents",
    },
}
MAX_BYTES = 450_000


def urlopen_small(url, *, accept_json=False):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json" if accept_json else "text/plain",
    })
    with urllib.request.urlopen(req, timeout=16) as res:
        data = res.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            return res.status, None, "TOO_LARGE"
        return res.status, data, None


def robots_check(origin, url):
    try:
        status, raw, issue = urlopen_small(origin + "/robots.txt")
        if issue or not raw:
            return {"decision": "SKIP_UNKNOWN", "reason": issue or "EMPTY"}
        if status != 200:
            return {"decision": "SKIP_UNKNOWN", "reason": "NON_200"}
        parser = RobotFileParser()
        parser.parse(raw.decode("utf8", "replace").splitlines())
        return {"decision": "ALLOW" if parser.can_fetch(UA, url) else "DISALLOW"}
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return {"decision": "ALLOW", "reason": "ROBOTS_404"}
        return {"decision": "SKIP_UNKNOWN", "reason": "ROBOTS_HTTP_" + str(err.code)}
    except Exception as err:
        return {"decision": "SKIP_UNKNOWN", "reason": type(err).__name__}


def inspect_prices(app, payload):
    if not isinstance(payload, dict):
        return {"result": "NOT_A_JSON_OBJECT"}
    results = payload.get("products") if app == "rewe_stationary" else payload.get("data")
    if not isinstance(results, list):
        return {"result": "NO_PRODUCT_ARRAY", "root_keys": sorted(payload)[:20]}
    out = {"result": "JSON_PRODUCTS_FOUND", "returned_products": len(results),
           "root_keys": sorted(payload)[:15], "price_examples": []}
    for row in results[:5]:
        if not isinstance(row, dict):
            continue
        rawprice = row.get("pricing") if app == "rewe_stationary" else row.get("price")
        if not isinstance(rawprice, dict):
            continue
        if app == "rewe_stationary":
            fields = {"current": rawprice.get("current"),
                      "regular": rawprice.get("regular"),
                      "refund": rawprice.get("refund")}
        else:
            fields = {"amount": rawprice.get("amount"),
                      "amountRelevant": rawprice.get("amountRelevant"),
                      "wasPriceDisplay": rawprice.get("wasPriceDisplay"),
                      "currencyCode": rawprice.get("currencyCode")}
        # Numbers only, no customer data, free text, or confidential tokens.
        fields = {k: v for k, v in fields.items()
                  if isinstance(v, (int, float))
                  or (isinstance(v, str) and len(v) < 32)}
        if fields:
            out["price_examples"].append(fields)
    return out


def study(name, cfg):
    url = cfg["origin"] + cfg["path"] + "?" + urllib.parse.urlencode(cfg["query"])
    result = {
        "app": name, "origin": cfg["origin"], "path": cfg["path"],
        "query_keys": sorted(cfg["query"]),
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "method": "Single unauthenticated GET only if robots permits",
        "expected_price_field": cfg["expected_price"],
        "expected_price_unit": cfg["price_unit"],
    }
    guard = robots_check(cfg["origin"], url)
    result["robots"] = guard
    if guard["decision"] != "ALLOW":
        result["result"] = "NOT_REQUESTED_ROBOTS"
        return result
    try:
        status, body, issue = urlopen_small(url, accept_json=True)
        result["http_status"] = status
        if issue:
            result["result"] = issue
        else:
            try:
                obj = json.loads(body)
                result.update(inspect_prices(name, obj))
            except json.JSONDecodeError:
                result["result"] = "NON_JSON_RESPONSE"
    except urllib.error.HTTPError as err:
        result.update({"http_status": err.code, "result": "HTTP_BLOCK_OR_ERROR"})
    except Exception as err:
        result.update({"result": "NETWORK_ERROR", "failure_type": type(err).__name__})
    return result


def main():
    report = {"purpose": "One-off feasibility test, NOT licence to use a price catalogue",
              "results": [study(name, cfg) for name, cfg in HOSTS.items()]}
    target = Path("results/one_shot_retailer_prices.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
