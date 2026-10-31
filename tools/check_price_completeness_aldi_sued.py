#!/usr/bin/env python3
"""ALDI Süd: exhaustive pagination and price freshness diagnostics.

Read-only, bounded to 75 pages and two additional verification requests.
Does not store individual products; only aggregate quality metrics and
one-way SHA256 fingerprints for detecting changes within a run.
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

ORIGIN = "https://api.aldi-sued.de"
ENDPOINT = "/v3/product-search"
STORE = "B384"
LIMIT = 60
MAX_PAGES = 75
DELAY_SECONDS = 0.65
UA = "ErnaehrungsgedaechnisResearch/1.0 (one-off noncommercial API diagnostic)"
FIELDS = ("Date", "Age", "Cache-Control", "ETag", "Last-Modified", "Expires")


def now():
    return datetime.now(timezone.utc).isoformat()


def get(offset, limit=LIMIT):
    params = {
        "q": "", "servicePoint": STORE, "serviceType": "walk-in",
        "limit": str(limit), "offset": str(offset), "sort": "relevance",
        "currency": "EUR"
    }
    url = ORIGIN + ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "application/json"
    })
    with urllib.request.urlopen(req, timeout=30) as f:
        data = f.read(2_100_000)
        status = f.status
        headers = {k.lower().replace("-", "_"): f.headers.get(k)
                   for k in FIELDS if f.headers.get(k) is not None}
    result = json.loads(data)
    if not isinstance(result, dict) or not isinstance(result.get("data"), list):
        raise ValueError("Unexpected JSON structure")
    pagination = result.get("meta", {}).get("pagination", {})
    if not isinstance(pagination, dict):
        raise ValueError("Missing pagination")
    return {
        "status": status, "headers": headers, "rows": result["data"],
        "pagination": {k: pagination.get(k) for k in
                       ("offset", "limit", "totalCount")}
    }


def item_key(p):
    if not isinstance(p, dict):
        return None
    val = p.get("sku")
    return val if isinstance(val, str) and val else None


def price_measure(p):
    if not isinstance(p, dict):
        return "not_object", None
    raw = p.get("price")
    if not isinstance(raw, dict):
        return "price_missing", None
    cur = raw.get("amountRelevant")
    if type(cur) is not int or cur < 0:
        cur = raw.get("amount")
    if type(cur) is not int or cur < 0:
        return "price_non_numeric", None
    if raw.get("currencyCode") != "EUR":
        return "wrong_or_missing_currency", None
    return "valid", cur


def fingerprint(rows):
    pairs = []
    for item in rows:
        sku = item_key(item)
        kind, amount = price_measure(item)
        if sku:
            pairs.append((sku, kind, amount))
    pairs.sort()
    return hashlib.sha256(json.dumps(
        pairs, separators=(",", ":"), ensure_ascii=False
    ).encode("utf8")).hexdigest()


def run():
    out = {
        "retailer": "ALDI Süd", "store": STORE,
        "started_utc": now(), "status": "RUNNING",
        "test": "All pages requested under stable total; first page repeated",
        "page_size": LIMIT, "max_pages": MAX_PAGES,
        "reports": [], "warnings": [],
    }
    counters = Counter()
    seen = set()
    totals = []
    first = None
    last = None
    page_n = 0
    next_offset = 0
    try:
        for i in range(MAX_PAGES):
            page = get(next_offset)
            if first is None:
                first = page
            last = page
            page_n += 1
            vals = page["pagination"]
            total = vals["totalCount"]
            if type(total) is not int or total < 0:
                raise ValueError("API did not report an integer product count")
            totals.append(total)
            rows = page["rows"]
            counts = Counter()
            for p in rows:
                counts["received"] += 1
                sku = item_key(p)
                if sku is None:
                    counts["missing_product_id"] += 1
                elif sku in seen:
                    counts["duplicate_product_id"] += 1
                else:
                    seen.add(sku)
                kind, price = price_measure(p)
                counts[kind] += 1
                if isinstance(p, dict) and isinstance(p.get("price"), dict):
                    if p["price"].get("wasPriceDisplay"):
                        counts["with_previous_price_display"] += 1
            counters.update(counts)
            out["reports"].append({
                "offset_requested": next_offset,
                "offset_reported": vals["offset"],
                "reported_total": total,
                "returned": len(rows),
                "valid_priced": counts["valid"],
                "duplicate_product_ids": counts["duplicate_product_id"],
            })
            if vals["offset"] != next_offset:
                out["warnings"].append("SERVER_OFFSET_DIFFERS_FROM_REQUEST")
            if len(rows) == 0:
                out["warnings"].append("PREMATURE_EMPTY_PAGE")
                break
            if len(rows) < LIMIT and next_offset + LIMIT < total:
                out["warnings"].append("SHORT_PAGE_AT_OFFSET_" + str(next_offset))
            next_offset += LIMIT
            if next_offset >= total:
                break
            if len(rows) > LIMIT:
                out["warnings"].append("MORE_THAN_REQUESTED")
                break
            time.sleep(DELAY_SECONDS)
        if next_offset < totals[-1]:
            out["warnings"].append("INCOMPLETE_PAGINATION")
        time.sleep(2)
        repeat_first = get(0)
        out["repeat_first"] = {
            "timestamp_utc": now(),
            "declared_total": repeat_first["pagination"]["totalCount"],
            "first_page_price_identity_unchanged":
                fingerprint(first["rows"]) == fingerprint(repeat_first["rows"]),
            "http_cache_headers": repeat_first["headers"],
        }
        out["first_http_cache_headers"] = first["headers"]
        out["last_http_cache_headers"] = last["headers"]
        if first["pagination"]["totalCount"] != repeat_first["pagination"]["totalCount"]:
            out["warnings"].append("TOTAL_CHANGED_DURING_SCAN")
        if min(totals) != max(totals):
            out["warnings"].append("TOTAL_CHANGED_ACROSS_PAGES")
        out["declared_total_first"] = totals[0]
        out["declared_total_last"] = totals[-1]
        out["pages_fetched"] = page_n
        out["rows_received"] = counters["received"]
        out["unique_product_ids"] = len(seen)
        out["coverage_vs_reported_total"] = (
            round(len(seen) / totals[0], 5) if totals[0] else None
        )
        out["price_fields"] = dict(counters)
        out["all_pages_reached_reported_total"] = (
            len(seen) == totals[0]
            and next_offset >= totals[0]
            and min(totals) == max(totals)
            and not out["warnings"]
        )
        out["status"] = "CHECK_COMPLETE"
    except Exception as e:
        out["status"] = "CHECK_ERROR"
        out["error_type"] = type(e).__name__
        out["error_summary"] = str(e)[:200]
    out["finished_utc"] = now()
    return out


if __name__ == "__main__":
    out = run()
    path = Path("results/completeness_freshness/aldi_sued.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf8")
    print(json.dumps({k:v for k,v in out.items() if k!="reports"}, ensure_ascii=False))
    if out["status"] != "CHECK_COMPLETE":
        raise SystemExit(2)
