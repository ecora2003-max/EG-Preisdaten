#!/usr/bin/env python3
"""One bounded anonymous ALDI SÜD catalogue count request. No bulk extraction."""
from __future__ import annotations
import json
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from one_shot_public_price_probe import robots_check, urlopen_small

ORIGIN = "https://api.aldi-sued.de"
PATH = "/v3/product-search"
PARAMS = {"q": "", "servicePoint": "B384", "serviceType": "walk-in",
          "limit": "12", "offset": "0", "sort": "relevance", "currency": "EUR"}


def main():
    uri = ORIGIN + PATH + "?" + urllib.parse.urlencode(PARAMS)
    result = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "source": ORIGIN + PATH,
        "store_id": "B384",
        "scope": "One 12-item page, no pagination or full dataset download",
        "method": "single GET, robots checked, no authentication",
    }
    gate = robots_check(ORIGIN, uri)
    result["robots"] = gate
    if gate["decision"] != "ALLOW":
        result["result"] = "NOT_REQUESTED_ROBOTS"
    else:
        try:
            status, raw, issue = urlopen_small(uri, accept_json=True)
            result["http_status"] = status
            if issue:
                result["result"] = issue
            else:
                obj = json.loads(raw)
                items = obj.get("data")
                meta = obj.get("meta")
                pg = meta.get("pagination") if isinstance(meta, dict) else None
                if isinstance(items, list) and isinstance(pg, dict):
                    result["result"] = "PAGINATED_CATALOGUE_CONFIRMED"
                    result["first_page_count"] = len(items)
                    result["total_count_declared"] = pg.get("totalCount")
                    result["reported_offset"] = pg.get("offset")
                    result["reported_limit"] = pg.get("limit")
                    result["numeric_prices_in_first_page"] = sum(
                        1 for x in items if isinstance(x, dict)
                        and isinstance(x.get("price"), dict)
                        and type(x["price"].get("amountRelevant")) is int
                    )
                    result["price_summary_no_items"] = sorted({
                        x["price"].get("currencyCode")
                        for x in items if isinstance(x, dict)
                        and isinstance(x.get("price"), dict)
                        and isinstance(x["price"].get("currencyCode"), str)
                    })
                else:
                    result["result"] = "UNEXPECTED_SCHEMA"
                    result["response_root_keys"] = sorted(obj)[:15] if isinstance(obj, dict) else []
        except urllib.error.HTTPError as exc:
            result.update({"http_status": exc.code, "result": "HTTP_ERROR"})
        except Exception as exc:
            result.update({"result": "NETWORK_ERROR", "error_type": type(exc).__name__})
    dest = Path("results/aldi_sued_single_catalogue_page.json")
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
