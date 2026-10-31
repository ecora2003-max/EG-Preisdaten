"""Schema-safe normalization for REWE stationary and ALDI Süd catalogue results.

Pure data transformation; *never* contacts retailers or updates inventory.
All prices are integer cents, store scope explicit, missing values remain None.
No site bypass/auth, bulk harvesting or license assumption.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Listing:
    retailer: str
    store_id: str
    product_id: str | None
    title: str | None
    brand: str | None
    price_cents: int | None
    regular_cents: int | None
    deposit_cents: int | None
    currency: str | None
    discount_is_observed: bool | None
    price_source: str
    price_type: str
    previous_price_display: str | None = None


def integer_cents(value: Any) -> int | None:
    # bool is a subclass of int: never parse true as 1 cent
    if type(value) is int and 0 <= value <= 100_000_000:
        return value
    return None


def safe_string(value: Any) -> str | None:
    return value[:200] if isinstance(value, str) and value.strip() else None


def rewe_stationary(payload: Any, store_id: str) -> dict:
    """REWE web stationary-price search; not the pickup/delivery API."""
    if not isinstance(payload, dict) or not isinstance(payload.get("products"), list):
        raise ValueError("Missing products array")
    listings = []
    for product in payload["products"]:
        if not isinstance(product, dict):
            continue
        price = product.get("pricing")
        if not isinstance(price, dict):
            continue
        current = integer_cents(price.get("current"))
        regular = integer_cents(price.get("regular"))
        if current is None:
            continue
        deposit = integer_cents(price.get("refund"))
        discounted = current < regular if regular is not None else None
        listings.append(asdict(Listing(
            retailer="REWE", store_id=str(store_id),
            product_id=safe_string(str(product["id"])) if product.get("id") is not None else None,
            title=safe_string(product.get("title")),
            brand=safe_string(product.get("brand")),
            price_cents=current, regular_cents=regular,
            deposit_cents=deposit, currency="EUR",
            discount_is_observed=discounted,
            price_source="rewe.de/api/stationary-product-search/products",
            price_type="stationary_advertised_price",
        )))
    return {
        "retailer": "REWE", "store_id": str(store_id),
        "listed_count": len(listings), "source_count": len(payload["products"]),
        "total_count": None, "catalogue_complete": None,
        "listings": listings,
    }


def aldi_sued(payload: Any, store_id: str) -> dict:
    """ALDI Süd public web product search (walk-in servicePoint)."""
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError("Missing data array")
    listings = []
    for product in payload["data"]:
        if not isinstance(product, dict):
            continue
        price = product.get("price")
        if not isinstance(price, dict):
            continue
        current = integer_cents(price.get("amountRelevant"))
        if current is None:
            current = integer_cents(price.get("amount"))
        if current is None:
            continue
        deposit = integer_cents(price.get("bottleDeposit"))
        previous = safe_string(price.get("wasPriceDisplay"))
        # Former price exists only as a display string; do not infer a cents value.
        listings.append(asdict(Listing(
            retailer="ALDI Süd", store_id=str(store_id),
            product_id=safe_string(product.get("sku")),
            title=safe_string(product.get("name")),
            brand=safe_string(product.get("brandName")),
            price_cents=current, regular_cents=None,
            deposit_cents=deposit,
            currency=safe_string(price.get("currencyCode")) or None,
            discount_is_observed=True if previous is not None else None,
            price_source="api.aldi-sued.de/v3/product-search",
            price_type="walk_in_catalogue_price",
            previous_price_display=previous,
        )))
    page = payload.get("meta") or {}
    pagination = page.get("pagination") if isinstance(page, dict) else {}
    total = pagination.get("totalCount") if isinstance(pagination, dict) else None
    total = total if type(total) is int and total >= 0 else None
    return {
        "retailer": "ALDI Süd", "store_id": str(store_id),
        "listed_count": len(listings), "source_count": len(payload["data"]),
        "total_count": total,
        "catalogue_complete": (len(payload["data"]) >= total) if total is not None else None,
        "listings": listings,
    }
