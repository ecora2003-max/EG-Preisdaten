"""Lidl physical store product catalogue and displayed price normalizer.

Only parses provided first-party responses; requests must be made with
Accept-Language: de and a verified store key. Store display ≠ guaranteed till
price. Store catalogue price ≠ always undiscounted baseline.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from decimal import Decimal,InvalidOperation
from typing import Any,Mapping
import re

@dataclass(frozen=True)
class StoreItem:
    retailer: str
    store_key: str
    product_id: str
    name: str
    brand: str | None
    current_price_eur: Decimal
    price_without_deposit_eur: Decimal | None
    deposit_eur: Decimal | None
    previous_display_price_eur: Decimal | None
    has_discount: bool
    has_lidl_plus_offer: bool
    price_checked_date: str
    price_kind: str = "DISPLAYED_CURRENT_STORE_PRICE"
    def to_dict(self):
        out=asdict(self)
        for k in ("current_price_eur","price_without_deposit_eur","deposit_eur","previous_display_price_eur"):
            out[k]=str(out[k]) if out[k] is not None else None
        return out

def _number(n):
    if isinstance(n,bool) or n is None:return None
    try:
        v=Decimal(str(n).replace(",","."))
        return v if v.is_finite() and v>=0 else None
    except (InvalidOperation,ValueError):return None

def _value_price(x):
    if isinstance(x,dict):
        return _number(x.get("price"))
    return _number(x)

def _item(row:Mapping[str,Any],store_key:str,day:str)->StoreItem | None:
    product_id=str(row.get("id") or "").strip()
    name=row.get("title")
    if not product_id or not isinstance(name,str) or not name.strip():return None
    # Direct category tiles nest prices under price.price while keyword
    # search results expose price as a number.
    price=row.get("price")
    amount=_value_price(price)
    if amount is None:return None
    p=price if isinstance(price,dict) else row
    deposit=_number(p.get("deposit"))
    price_no_deposit=_number(p.get("priceWithoutDeposit"))
    old=_number(p.get("oldPrice"))
    return StoreItem(
        retailer="Lidl",store_key=store_key,product_id=product_id,
        name=name,brand=row.get("brand") if isinstance(row.get("brand"),str) else None,
        current_price_eur=amount,price_without_deposit_eur=price_no_deposit,
        deposit_eur=deposit,previous_display_price_eur=old,
        has_discount=bool(p.get("discount")) or old is not None,
        has_lidl_plus_offer=bool(p.get("lidlPlusOffer")),
        price_checked_date=day
    )

def store_products(payload:Mapping[str,Any],*,store_key:str,day:str,offset:int=0,limit:int|None=None):
    """Normalize a page from /categories/{id}/products?skip=&limit=&date=.

    Page metadata gives totalProducts but only returned pages can be used.
    Do not infer products from page 1 alone.
    """
    if not re.fullmatch(r"DE\d+",store_key):raise ValueError("Invalid Lidl store key")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",day):raise ValueError("Invalid date")
    if not isinstance(payload,dict) or not isinstance(payload.get("products"),list):
        raise ValueError("Lidl response lacks products")
    rows=payload["products"]
    if limit is not None and (limit<1 or len(rows)>limit):
        raise ValueError("Product page length exceeds requested limit")
    total=payload.get("totalProducts")
    if not isinstance(total,int) or total<0 or offset<0 or offset>total:
        raise ValueError("Lidl page total/offset inconsistent")
    items=[]
    for row in rows:
        if isinstance(row,dict):
            product=_item(row,store_key,day)
            if product:items.append(product)
    keys=[p.product_id for p in items]
    if len(set(keys))!=len(keys):raise ValueError("Duplicate product IDs in one page")
    return items,{"reported_total":total,"received":len(rows),"parsed":len(items),
                  "offset":offset,"complete":offset==0 and len(rows)==total and len(items)==total}

def merge_store_category_pages(pages:list[tuple[list[StoreItem],dict]]):
    """Validate contiguous pages from a single market before claiming complete."""
    if not pages:raise ValueError("No pages")
    total=pages[0][1]["reported_total"]
    expected=0
    merged=[]
    seen=set()
    store=pages[0][0][0].store_key if pages[0][0] else None
    for items,meta in pages:
        if meta["reported_total"]!=total or meta["offset"]!=expected:
            raise ValueError("Market category pagination changed or omitted page")
        if meta["parsed"]!=meta["received"]:
            raise ValueError("Unpriced products in category, cannot claim complete price coverage")
        if store and any(p.store_key!=store for p in items):
            raise ValueError("Mixing Lidl stores in a category")
        for item in items:
            if item.product_id in seen:raise ValueError("Repeated product ID across pages")
            seen.add(item.product_id)
            merged.append(item)
        expected+=meta["received"]
        if not meta["received"] and expected<total:raise ValueError("Premature empty page")
    if expected!=total or len(merged)!=total:
        raise ValueError("Category product catalogue not completely fetched")
    return merged

def search_products(payload:Mapping[str,Any],*,store_key:str,day:str):
    if not re.fullmatch(r"DE\d+",store_key):raise ValueError("Invalid Lidl store key")
    if not isinstance(payload,dict) or not isinstance(payload.get("results"),list):
        raise ValueError("Lidl search results missing")
    return [p for row in payload["results"] if isinstance(row,dict)
            if (p:=_item(row,store_key,day)) is not None]
