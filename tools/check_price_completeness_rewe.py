#!/usr/bin/env python3
"""REWE stationary: search coverage, per-hit prices, paging behavior and freshness.

Read-only; nine bounded GETs, two stores, three terms, pagination probe
and first-query repeat. Not a complete in-store assortment enumeration.
"""
from __future__ import annotations
import hashlib
import json
import time
import urllib.parse
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ORIGIN = "https://www.rewe.de"
ROUTE = "/api/stationary-product-search/products"
UA = "ErnaehrungsgedaechtnisResearch/1.1 (price coverage and freshness diagnostics)"
STORES = ("840174", "831002")
TERMS = ("Haferflocken", "Milch", "Reis")


def now():
    return datetime.now(timezone.utc).isoformat()


def get(store, term, extra=None):
    query = {"query": term, "wwIdent": store}
    if extra:
        query.update(extra)
    url = ORIGIN + ROUTE + "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "application/json"
    })
    with urllib.request.urlopen(req, timeout=28) as response:
        body = response.read(1_500_000)
        meta = {k.lower().replace("-", "_"): response.headers.get(k)
                for k in ("Date", "Age", "Last-Modified", "ETag",
                          "Cache-Control", "Expires")
                if response.headers.get(k) is not None}
        status = response.status
    payload = json.loads(body)
    if not isinstance(payload, dict) or not isinstance(payload.get("products"), list):
        raise ValueError("No products list")
    return {"http": status, "rows": payload["products"],
            "headers": meta, "root_keys": sorted(payload),
            "state_type": type(payload.get("state")).__name__}


def measure(resp):
    c = Counter()
    seen = set()
    price_ids = {}
    entries = []
    for p in resp["rows"]:
        c["rows"] += 1
        if not isinstance(p, dict):
            c["non_object"] += 1
            continue
        pid = str(p.get("id")) if p.get("id") is not None else None
        if pid is None:
            c["no_id"] += 1
        elif pid in seen:
            c["duplicate_id"] += 1
        else:
            seen.add(pid)
        pr = p.get("pricing")
        if not isinstance(pr, dict):
            c["missing_pricing"] += 1
            continue
        cur = pr.get("current")
        regular = pr.get("regular")
        if type(cur) is int and cur >= 0:
            c["valid_current_cents"] += 1
            if pid is not None:
                price_ids[pid] = cur
                entries.append((pid, cur))
        else:
            c["invalid_current_cents"] += 1
        if type(regular) is int and regular >= 0:
            c["valid_regular_cents"] += 1
        else:
            c["missing_regular_cents"] += 1
        if type(pr.get("refund")) is int:
            c["refund_numeric"] += 1
    encoded = json.dumps(sorted(entries), separators=(",", ":"))
    return {"stats": dict(c), "unique_product_ids": len(seen),
            "price_hash": hashlib.sha256(encoded.encode()).hexdigest(),
            "price_ids": price_ids}


def report():
    result = {"retailer": "REWE", "started_utc": now(),
              "stores": list(STORES), "terms": list(TERMS),
              "status": "RUNNING", "samples": [], "warnings": [],
              "note": "Search-returned products only; no official all-store total."}
    first = None
    raw = {}
    try:
        for store in STORES:
            for term in TERMS:
                resp = get(store, term)
                met = measure(resp)
                raw[(store, term)] = met
                result["samples"].append({
                    "store": store, "query": term, "http": resp["http"],
                    "root_keys": resp["root_keys"],
                    "state_type": resp["state_type"],
                    "counts": met["stats"],
                    "unique_products": met["unique_product_ids"],
                    "http_cache_headers": resp["headers"],
                })
                if store == STORES[0] and term == TERMS[0]:
                    first = resp
                time.sleep(0.65)
        # Determine whether API honors page arguments; not infer entire inventory.
        for args in ({"limit": "50"}, {"limit": "12", "offset": "12"}):
            r = get(STORES[0], TERMS[0], args)
            result.setdefault("pagination_probe", []).append({
                "requested": args,
                "returned_products": len(r["rows"]),
                "unique_products": measure(r)["unique_product_ids"],
                "equal_to_original_first_page":
                    measure(r)["price_hash"] == measure(first)["price_hash"],
            })
            time.sleep(0.65)
        again = get(STORES[0], TERMS[0])
        result["repeat_first"] = {
            "at_utc": now(),
            "unchanged_ids_and_prices":
                measure(again)["price_hash"] == measure(first)["price_hash"],
            "http_cache_headers": again["headers"]
        }
        comparisons = []
        for term in TERMS:
            a = raw[(STORES[0], term)]["price_ids"]
            b = raw[(STORES[1], term)]["price_ids"]
            common = a.keys() & b.keys()
            comparisons.append({
                "query": term, "common_ids": len(common),
                "only_a": len(a.keys()-b.keys()),
                "only_b": len(b.keys()-a.keys()),
                "shared_ids_with_different_prices":
                    sum(a[pid] != b[pid] for pid in common),
            })
        result["market_comparisons"] = comparisons
        result["status"] = "CHECK_COMPLETE"
    except Exception as ex:
        result["status"] = "CHECK_ERROR"
        result["error_type"] = type(ex).__name__
        result["error_summary"] = str(ex)[:200]
    result["finished_utc"] = now()
    return result


if __name__ == "__main__":
    data = report()
    p = Path("results/completeness_freshness/rewe.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    print(json.dumps(data, ensure_ascii=False))
    if data["status"] != "CHECK_COMPLETE":
        raise SystemExit(2)
