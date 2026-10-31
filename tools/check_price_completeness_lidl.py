#!/usr/bin/env python3
"""Lidl DE7434: category-tree completeness, price presence and date sensitivity.

Recursively visits leaf categories and paginates within strict request budget.
No persistence of raw catalogue; only counts and one-way hashes.
"""
from __future__ import annotations
import hashlib
import json
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HOST = "https://product-catalog.lidlplus.com"
ROOT = "/api/app/v1/DE/store/DE7434"
STORE = "DE7434"
MAX_REQUESTS = 160
PAGE_LIMIT = 100
PAUSE = 0.35
UA = "ErnaehrungsgedaechnisResearch/1.1 (catalogue completeness quality check)"
TODAY = datetime.now(ZoneInfo("Europe/Berlin")).date()
HEADERS = {"User-Agent": UA, "Accept": "application/json",
           "Accept-Language": "de"}


class LimitReached(Exception):
    pass


def stamp():
    return datetime.now(timezone.utc).isoformat()


class Fetcher:
    def __init__(self):
        self.count = 0
        self.headers = None
        self.last_headers = None

    def get(self, path, params=None):
        if self.count >= MAX_REQUESTS:
            raise LimitReached("Bounded request cap")
        if self.count:
            time.sleep(PAUSE)
        url = HOST + ROOT + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=28) as r:
            self.count += 1
            headers = {k.lower().replace("-", "_"): r.headers.get(k)
                       for k in ("Date", "Age", "ETag", "Cache-Control", "Last-Modified")
                       if r.headers.get(k) is not None}
            if self.headers is None:
                self.headers = headers
            self.last_headers = headers
            data = r.read(2_200_000)
        return json.loads(data)


def item_price(p):
    if not isinstance(p, dict):
        return None
    v = p.get("price")
    if isinstance(v, dict):
        v = v.get("price")
    if type(v) in (int, float) and 0 <= v < 100000:
        return str(v)
    return None


def hash_page(items):
    vals = sorted((str(p.get("id")), item_price(p))
                  for p in items if isinstance(p, dict) and p.get("id"))
    return hashlib.sha256(json.dumps(vals).encode()).hexdigest()


def run():
    f = Fetcher()
    today = TODAY.isoformat()
    yesterday = (TODAY-timedelta(days=1)).isoformat()
    out = {"retailer": "Lidl", "store": STORE, "started_utc": stamp(),
           "date_requested": today, "max_requests": MAX_REQUESTS,
           "leaf_category_results": [], "category_counts": Counter(),
           "status": "RUNNING", "issues": []}
    seed = None

    def walk(path, depth):
        nonlocal seed
        if depth > 5:
            out["issues"].append("TREE_DEPTH_EXCEEDED")
            return
        data = f.get(path)
        cat = data.get("categories") if isinstance(data, dict) else None
        if not isinstance(cat, list):
            out["issues"].append("MALFORMED_CATEGORY_RESPONSE:" + path)
            return
        out["category_counts"]["navigation_nodes"] += len(cat)
        for node in cat:
            if not isinstance(node, dict) or node.get("id") is None:
                out["issues"].append("CATEGORY_MISSING_ID")
                continue
            name = str(node.get("id"))
            prefix = path.rsplit("/categories", 1)[0] + "/categories/" + urllib.parse.quote(name, safe="")
            if node.get("hasSubcategories"):
                out["category_counts"]["branches"] += 1
                walk(prefix + "/categories", depth+1)
            else:
                out["category_counts"]["leaves"] += 1
                offset = 0
                declared = None
                counts = Counter()
                sku_seen = set()
                page = None
                price_hashes = []
                pages = 0
                while True:
                    page = f.get(prefix + "/products", {"skip": str(offset),
                                  "limit": str(PAGE_LIMIT), "date": today})
                    if not isinstance(page, dict) or not isinstance(page.get("products"), list):
                        out["issues"].append("MALFORMED_PRODUCTS:" + prefix)
                        break
                    n = page.get("totalProducts")
                    if type(n) is not int or n < 0:
                        out["issues"].append("MISSING_TOTAL:" + prefix)
                        break
                    if declared is None:
                        declared = n
                    if n != declared:
                        out["issues"].append("CHANGING_TOTAL:" + prefix)
                    rows = page["products"]
                    pages += 1
                    if seed is None and rows:
                        seed = {"path": prefix + "/products", "date": today,
                                "hash": hash_page(rows),
                                "product_ids": sorted(str(p.get("id"))
                                                      for p in rows if isinstance(p, dict))}
                    for item in rows:
                        counts["returned"] += 1
                        if not isinstance(item, dict):
                            counts["non_object"] += 1
                            continue
                        pid = str(item.get("id")) if item.get("id") is not None else None
                        if pid:
                            if pid in sku_seen:
                                counts["duplicate_product_id"] += 1
                            sku_seen.add(pid)
                        else:
                            counts["missing_product_id"] += 1
                        if item_price(item) is not None:
                            counts["priced"] += 1
                        else:
                            counts["unpriced"] += 1
                    offset += len(rows)
                    if offset >= n:
                        break
                    if not rows:
                        out["issues"].append("EMPTY_BEFORE_TOTAL:" + prefix)
                        break
                out["leaf_category_results"].append({
                    "id": name, "reported_total": declared,
                    "returned": counts["returned"], "priced": counts["priced"],
                    "unpriced": counts["unpriced"], "duplicate_ids":
                    counts["duplicate_product_id"],
                    "pages": pages, "reached_reported_total":
                    (declared is not None and offset == declared),
                })
    try:
        walk("/categories", 0)
        out["requests"] = f.count
        if seed:
            # Validate same date stability and check whether date parameter
            # changes price responses. Unchanged prices over adjacent dates
            # do not imply a stale catalogue.
            repeat = f.get(seed["path"], {"skip": "0", "limit":
                            str(PAGE_LIMIT), "date": today})
            earlier = f.get(seed["path"], {"skip": "0", "limit":
                             str(PAGE_LIMIT), "date": yesterday})
            out["date_sensitive_probe"] = {
                "same_day_first_page_unchanged":
                    hash_page(repeat.get("products", [])) == seed["hash"],
                "previous_date_requested": yesterday,
                "previous_date_first_page_equal":
                    hash_page(earlier.get("products", [])) == seed["hash"],
                "same_day_count": repeat.get("totalProducts"),
                "previous_day_count": earlier.get("totalProducts"),
            }
        out["requests"] = f.count
        out["first_http_cache_headers"] = f.headers
        out["last_http_cache_headers"] = f.last_headers
        out["category_counts"] = dict(out["category_counts"])
        out["reported_products_sum_across_leaves"] = sum(
            v["reported_total"] or 0 for v in out["leaf_category_results"])
        out["returned_products_sum_across_leaves"] = sum(
            v["returned"] for v in out["leaf_category_results"])
        out["priced_product_entries"] = sum(
            v["priced"] for v in out["leaf_category_results"])
        out["unpriced_product_entries"] = sum(
            v["unpriced"] for v in out["leaf_category_results"])
        out["leaves_fully_paginated"] = sum(
            bool(v["reached_reported_total"]) for v in out["leaf_category_results"])
        out["tree_fully_traversed"] = (
            out["leaves_fully_paginated"] ==
            out["category_counts"].get("leaves") and not out["issues"])
        out["status"] = "CHECK_COMPLETE"
    except Exception as e:
        out["status"] = "CHECK_PARTIAL"
        out["error_type"] = type(e).__name__
        out["error_summary"] = str(e)[:200]
        out["requests"] = f.count
        out["category_counts"] = dict(out["category_counts"])
    out["finished_utc"] = stamp()
    return out


if __name__ == "__main__":
    result = run()
    dest = Path("results/completeness_freshness/lidl.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",encoding="utf8")
    print(json.dumps({k:v for k,v in result.items() if k!="leaf_category_results"}, ensure_ascii=False))
    if result["status"] != "CHECK_COMPLETE":
        raise SystemExit(2)
