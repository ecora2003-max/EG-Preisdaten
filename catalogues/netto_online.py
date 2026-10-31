"""Read-only Netto Onlineshop product-price parsing.

Only a Product JSON-LD Offer in the official retailer's product page is
accepted as a numeric price. The result is explicitly an ONLINE_SHOP price,
not a claim about a Netto brick-and-mortar checkout price.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from decimal import Decimal,InvalidOperation
from html import unescape
import json,re
from urllib.parse import urlparse

_SCRIPT = re.compile(r'<script\b(?=[^>]*\btype\s*=\s*["\x27]application/ld\+json["\x27])[^>]*>(.*?)</script\s*>',re.S|re.I)
_ALLOWED_HOSTS = {"www.netto-online.de","netto-online.de"}

@dataclass(frozen=True)
class NettoOnlineOffer:
    source_url: str
    name: str
    price_eur: Decimal
    currency: str
    sku: str | None
    gtin: str | None
    brand: str | None
    availability: str | None
    price_valid_until: str | None
    scope: str = "NETTO_ONLINE_SHOP"
    price_kind: str = "DISPLAYED_CURRENT"
    store_id: None = None

    def as_dict(self):
        d=asdict(self)
        d["price_eur"]=str(self.price_eur)
        return d

def _walk(obj):
    if isinstance(obj,list):
        for item in obj:
            yield from _walk(item)
    elif isinstance(obj,dict):
        yield obj
        for k in ("@graph","mainEntity","itemListElement"):
            if k in obj:yield from _walk(obj[k])

def _is_type(obj,expected):
    t=obj.get("@type")
    return expected in t if isinstance(t,list) else isinstance(t,str) and t.split("/")[-1]==expected

def _money(value):
    if isinstance(value,bool) or value is None:return None
    try:
        v=Decimal(str(value).replace(",","."))
        if v.is_finite() and v >= 0:return v
    except (ValueError,InvalidOperation):pass
    return None

def _text(value):
    if isinstance(value,str):
        s=value.strip()
        return s or None
    return None

def prices_from_product_html(page_html: str, page_url: str)->list[NettoOnlineOffer]:
    host=urlparse(page_url).netloc.lower()
    if host not in _ALLOWED_HOSTS or urlparse(page_url).scheme!="https":
        raise ValueError("Only official HTTPS Netto Onlineshop pages are supported")
    found=[]
    seen=set()
    for script in _SCRIPT.finditer(page_html):
        try:document=json.loads(unescape(script.group(1)),strict=False)
        except (json.JSONDecodeError,TypeError):continue
        for obj in _walk(document):
            if not isinstance(obj,dict) or not _is_type(obj,"Product"):continue
            name=_text(obj.get("name"))
            if not name:continue
            brands=obj.get("brand")
            if isinstance(brands,dict):brand=_text(brands.get("name"))
            elif isinstance(brands,str):brand=_text(brands)
            else:brand=None
            offers=obj.get("offers")
            if isinstance(offers,dict): offers=[offers]
            if not isinstance(offers,list):continue
            for off in offers:
                if not isinstance(off,dict) or not _is_type(off,"Offer"):continue
                amount=_money(off.get("price"))
                curr=_text(off.get("priceCurrency"))
                if amount is None or curr!="EUR":continue
                key=(name,amount,_text(obj.get("sku")),_text(obj.get("gtin13")))
                if key in seen:continue
                seen.add(key)
                found.append(NettoOnlineOffer(
                    source_url=page_url,name=name,price_eur=amount,
                    currency=curr,sku=_text(obj.get("sku")),
                    gtin=_text(obj.get("gtin13") or obj.get("gtin")),
                    brand=brand,
                    availability=_text(off.get("availability")),
                    price_valid_until=_text(off.get("priceValidUntil"))))
    return found

def validate_one_product(page_html: str, page_url: str, required_sku: str | None = None):
    """No price guessing: return an actual offer only for the requested SKU."""
    offers=prices_from_product_html(page_html,page_url)
    if required_sku is not None:
        offers=[x for x in offers if x.sku==required_sku]
    if len(offers)!=1:
        raise ValueError(f"Expected exactly one on-page EUR Offer; observed {len(offers)}")
    return offers[0]
