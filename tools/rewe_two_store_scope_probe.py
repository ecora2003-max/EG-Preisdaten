#!/usr/bin/env python3
"""One-time, two-market REWE stationary API scope check, no scraping.

Two exact unauthenticated HTTP GETs, same term, two public market IDs from
third-party documentation. Respects robots. Captures only intersection stats;
not a complete catalogue, no scheduled monitoring or credential tricks.
"""
import json
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from one_shot_public_price_probe import robots_check, urlopen_small

BASE = "https://www.rewe.de"
PATH = "/api/stationary-product-search/products"
IDS = ("840174", "831002")
TERM = "Haferflocken"


def one(market):
    url = BASE + PATH + "?" + urllib.parse.urlencode(
        {"query": TERM, "wwIdent": market}
    )
    gate = robots_check(BASE, url)
    if gate["decision"] != "ALLOW":
        return {"market_id": market, "result": "NOT_REQUESTED_ROBOTS", "robots": gate}
    try:
        status, raw, failure = urlopen_small(url, accept_json=True)
        if failure:
            return {"market_id": market, "result": failure, "http_status": status}
        obj = json.loads(raw)
        products = obj.get("products")
        if not isinstance(products, list):
            return {"market_id": market, "result": "NO_PRODUCTS_ARRAY",
                    "http_status": status}
        prices = {}
        for row in products:
            if not isinstance(row, dict):
                continue
            product_id = row.get("id")
            pricing = row.get("pricing")
            if (product_id is not None and isinstance(pricing, dict)
                    and type(pricing.get("current")) is int):
                prices[str(product_id)] = {
                    "current": pricing["current"],
                    "regular": pricing.get("regular")
                    if type(pricing.get("regular")) is int else None,
                }
        return {"market_id": market, "result": "OK", "http_status": status,
                "products_in_response": len(products), "prices": prices}
    except urllib.error.HTTPError as exc:
        return {"market_id": market, "result": "HTTP_ERROR",
                "http_status": exc.code}
    except Exception as exc:
        return {"market_id": market, "result": type(exc).__name__}


def main():
    a, b = [one(m) for m in IDS]
    output = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "method": "Two bounded read-only public product searches with same term",
        "market_ids": list(IDS), "query": TERM,
        "markets": [
            {k:v for k,v in r.items() if k != "prices"} for r in (a,b)
        ],
        "comparison": None,
    }
    if a["result"] == b["result"] == "OK":
        pa, pb = a["prices"], b["prices"]
        both = pa.keys() & pb.keys()
        different = [
            (key, pa[key]["current"], pb[key]["current"])
            for key in both if pa[key]["current"] != pb[key]["current"]
        ]
        output["comparison"] = {
            "common_product_ids": len(both),
            "a_only": len(pa.keys() - pb.keys()),
            "b_only": len(pb.keys() - pa.keys()),
            "different_current_prices": len(different),
            "up_to_three_differences": [
                {"market_a_cents": x, "market_b_cents": y}
                for _, x, y in different[:3]
            ],
            "note": "No price differences in search results does not prove "
                    "that the API ignores the market or chainwide uniformity.",
        }
    target = Path("results/rewe_two_store_price_scope.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2)+"\n",
                      encoding="utf8")
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
