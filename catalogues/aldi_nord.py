"""ALDI Nord ordinary assortment reference parser. No network access.

Each documented category page contains a full, small server-hydrated
AlgoliaState result under props.pageProps.algoliaState. The product's
currentPrice is a *displayed price*, not verified as historical regular
price or store-specific cash-register price.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from decimal import Decimal,InvalidOperation
from datetime import datetime
from html import unescape
from zoneinfo import ZoneInfo
import json,re

@dataclass(frozen=True)
class CategoryProduct:
    product_id: str
    name: str
    brand: str|None
    pack: str|None
    displayed_price_eur: Decimal
    unit_prices: tuple[tuple[str,Decimal],...]
    price_valid_from: str|None
    price_valid_to: str|None
    category_key: str|None
    market_scope: str="CHAIN_WIDE_REPORTED"
    price_type: str="DISPLAYED_CURRENT_NOT_PROVEN_REGULAR"
    def to_dict(self):
        out=asdict(self)
        out["displayed_price_eur"]=str(self.displayed_price_eur)
        out["unit_prices"]=[{"unit":k,"price_eur":str(v)} for k,v in self.unit_prices]
        return out

def _money(x):
    try:
        if isinstance(x,bool) or x is None: return None
        d=Decimal(str(x).replace(",","."))
        return d if d>=0 and d.is_finite() else None
    except (InvalidOperation,ValueError):return None

def _local_date(x):
    if not isinstance(x,(int,float)) or isinstance(x,bool):return None
    try:
        return datetime.fromtimestamp(x,ZoneInfo("Europe/Berlin")).date().isoformat()
    except (ValueError,OverflowError,OSError):return None

def aldi_nord_catalogue_from_html(html: str) -> tuple[list[CategoryProduct],dict]:
    m=re.search(r'<script[^>]*id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',html,re.I|re.S)
    if not m:raise ValueError("ALDI Nord assortment HTML has no Next data")
    state=json.loads(unescape(m.group(1))).get("props",{}).get("pageProps",{}).get("algoliaState",{}).get("initialResults",{})
    idx=state.get("an_prd_de_de_products2",{})
    results=idx.get("results")
    if not isinstance(results,list) or len(results)!=1:
        raise ValueError("Unknown category search response; refuse partial data")
    result=results[0]
    hits=result.get("hits")
    if not isinstance(hits,list):
        raise ValueError("Category hits absent")
    count=result.get("nbHits")
    if not isinstance(count,int) or count!=len(hits):
        raise ValueError("Page may omit assortment products; refuse to claim complete category")
    if result.get("nbPages")!=1 or result.get("page")!=0:
        raise ValueError("Pagination incomplete")
    parsed=[]
    seen=set()
    for product in hits:
        if not isinstance(product,dict):continue
        pid=str(product.get("objectID") or "")
        name=product.get("name")
        priceinfo=product.get("currentPrice")
        if not isinstance(priceinfo,dict) or not isinstance(name,str) or not pid:
            continue
        price=_money(priceinfo.get("priceValue"))
        if price is None or pid in seen:
            continue
        seen.add(pid)
        units=[]
        for unit in priceinfo.get("basePrice") or []:
            if isinstance(unit,dict):
                amount=_money(unit.get("basePriceValue"))
                scale=unit.get("basePriceScale")
                if amount is not None and isinstance(scale,str):
                    units.append((scale,amount))
        parsed.append(CategoryProduct(product_id=pid,name=name,
            brand=product.get("brandName"),pack=product.get("salesUnit"),
            displayed_price_eur=price,
            unit_prices=tuple(units),
            price_valid_from=_local_date(priceinfo.get("validFrom")),
            price_valid_to=_local_date(priceinfo.get("validUntil")),
            category_key=product.get("mainCategoryID")))
    coverage={"advertised_hits":count,"received_hits":len(hits),"priced_hits":len(parsed),
              "category_complete_response":True,"products_all_priced":len(parsed)==count,
              "price_kind":"displayed_current; not necessarily undiscounted baseline"}
    return parsed,coverage
