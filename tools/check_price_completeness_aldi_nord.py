#!/usr/bin/env python3
"""ALDI Nord: re-check two previously fully visible regular-price categories.

For each category, validate hits == nbHits, pages == nbPages and numeric prices;
repeat one category once. This is NOT evidence of the full store assortment.
"""
from __future__ import annotations
import json
import re
import hashlib
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://www.aldi-nord.de"
PATHS = [
    "/sortiment/milchprodukte/joghurt-quark-milchdesserts.html",
    "/sortiment/milchprodukte/milch-milchgetraenke.html"
]
UA = "ErnaehrungsgedaechnisResearch/1.1 (price freshness quality comparison)"


def get(route):
    req = urllib.request.Request(BASE + route, headers={
        "User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=22) as r:
        html = r.read(1_700_000).decode("utf8", "replace")
        headers = {k.lower().replace("-", "_"): r.headers.get(k)
                   for k in ("Date", "Age", "Cache-Control", "ETag", "Last-Modified")
                   if r.headers.get(k) is not None}
    match = re.search(r'<script[^>]*id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',
                      html, re.S | re.I)
    if not match:
        raise ValueError("NEXT_DATA absent")
    data = json.loads(match.group(1))
    results = data.get("props", {}).get("pageProps", {}).get(
        "algoliaState", {}).get("initialResults", {}).get(
        "an_prd_de_de_products2", {}).get("results", [])
    if not isinstance(results, list) or not results:
        raise ValueError("Missing Algolia index")
    first = results[0]
    hits = first.get("hits", [])
    rows = []
    for p in hits:
        if not isinstance(p, dict):
            continue
        current = p.get("currentPrice") or {}
        val = current.get("priceValue") if isinstance(current, dict) else None
        rows.append((str(p.get("objectID")), val if isinstance(val, (float, int)) and not isinstance(val, bool) else None))
    page_hash = hashlib.sha256(json.dumps(sorted(rows)).encode()).hexdigest()
    return {
        "reported_total": first.get("nbHits"),
        "reported_pages": first.get("nbPages"),
        "page": first.get("page"),
        "page_size": first.get("hitsPerPage"),
        "received": len(hits),
        "with_numeric_price": sum(v is not None for _,v in rows),
        "distinct_ids": len({id for id,_ in rows}),
        "fingerprint": page_hash, "http_cache_headers": headers
    }


def main():
    result = {"retailer": "ALDI Nord", "start_utc":
              datetime.now(timezone.utc).isoformat(), "categories": [],
              "status": "RUNNING"}
    try:
        for path in PATHS:
            row = get(path)
            row["path"] = path
            row["fully_visible_single_page"] = (
                type(row["reported_total"]) is int and
                row["reported_total"] == row["received"] and
                row["reported_pages"] == 1 and
                row["with_numeric_price"] == row["received"] and
                row["distinct_ids"] == row["received"])
            result["categories"].append(row)
            time.sleep(1.2)
        second = get(PATHS[0])
        result["repeat_first_category"] = {
            "same_ids_and_prices": second["fingerprint"] ==
                result["categories"][0]["fingerprint"],
            "same_reported_total": second["reported_total"] ==
                result["categories"][0]["reported_total"],
            "http_cache_headers": second["http_cache_headers"],
        }
        result["status"] = "CHECK_COMPLETE"
    except Exception as ex:
        result["status"] = "CHECK_ERROR"
        result["error_type"] = type(ex).__name__
        result["error_summary"] = str(ex)[:180]
    result["finish_utc"] = datetime.now(timezone.utc).isoformat()
    dest = Path("results/completeness_freshness/aldi_nord.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",
                    encoding="utf8")
    print(json.dumps(result, ensure_ascii=False))
    if result["status"] != "CHECK_COMPLETE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
