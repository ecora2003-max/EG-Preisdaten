"""Netto: precise read-only parser for publicly embedded branch-offer tiles.

Official category pages contain 'Filial-Angebote' cards in server-rendered
HTML. Each card embeds a direct wishlist-link with product metadata and
Price/ValidTo, but this module DOES NOT invoke that state-changing link.

Only advertised sale offers from published cards. No claim of normal prices
or a full store assortment. Default pricing cannot use app-only price.
"""
from __future__ import annotations

from dataclasses import dataclass,asdict
from datetime import datetime
from decimal import Decimal,InvalidOperation
import re
from urllib.parse import urlparse,parse_qs
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class NettoBranchOffer:
    offer_id: str
    product_name: str
    sale_price_eur: Decimal
    advertised_unit_price: str | None
    valid_from_date: str | None
    valid_to_local: str
    advertised_app_price_eur: Decimal | None
    source_url: str
    scope: str = "NETTO_BRANCH_WEEKLY_PROMOTIONS_NOT_NORMAL_PRICES"

    def to_dict(self):
        out=asdict(self)
        for key in ("sale_price_eur","advertised_app_price_eur"):
            if out[key] is not None:out[key]=str(out[key])
        return out


def _money(v):
    try:
        if v is None or isinstance(v,bool):return None
        amount=Decimal(str(v).replace(",","."))
        if amount.is_finite() and amount>=0 and amount.as_tuple().exponent>=-2:
            return amount
    except (ValueError,InvalidOperation):pass
    return None


def _visible_euros(tag):
    """Read only one displayed product price, no surrounding struck-through price."""
    if tag is None:return None
    s=tag.get_text("",strip=True)
    s=s.replace("*","").replace("\xa0","").replace(" ","")
    if not re.fullmatch(r"\d{1,4}[.,]\d\d",s):return None
    return _money(s)


def _offer_section(soup):
    heading=soup.find("h2",string=lambda s:isinstance(s,str) and s.strip()=="Filial-Angebote")
    if heading is None:return None,None
    # Header alone has 'store-offers__header'; choose the nearest parent
    # actually containing product cards, not merely the heading wrapper.
    root=next((node for node in heading.parents if node.select_one(".tc-store-product-tile")),None)
    if root is None:return None,None
    date_el=root.select_one(".store-offers__header__date")
    return root,(date_el.get_text(" ",strip=True) if date_el else None)


def _begin_date(label):
    # Only date reference from retailer, not a guessed update timestamp.
    if not label:return None
    m=re.search(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b",label)
    if not m:return None
    d,mn,y=map(int,m.groups())
    if y<100:y+=2000
    try:return datetime(y,mn,d).date().isoformat()
    except ValueError:return None


def parse_branch_offers(page_html:str, source_url:str)->tuple[list[NettoBranchOffer],dict]:
    u=urlparse(source_url)
    if u.scheme!="https" or u.hostname!="www.netto-online.de":
        raise ValueError("Source must be an official HTTPS Netto product/category page")
    soup=BeautifulSoup(page_html,"html.parser")
    root,header=_offer_section(soup)
    if root is None:
        return [],{"status":"NO_STORE_OFFER_SECTION","source_url":source_url}
    candidate_tiles=root.select(".tc-store-product-tile")
    records=[]
    warnings=[]
    mismatch_details=[]
    seen=set()
    for tile in candidate_tiles:
        ffid=tile.get("data-ff-id")
        name_tag=tile.select_one(".tc-product-name")
        link=tile.select_one('a[href*="ViewMMPWishlist-AddStoreArticle"]')
        visible=tile.select_one(".grid-top-price .product__current-price.tc-product-price")
        if name_tag is None or link is None or visible is None or not ffid:
            warnings.append("MISSING_REQUIRED_FIELD")
            continue
        product_name=name_tag.get_text(" ",strip=True)
        href=link.get("href","")
        parsed=urlparse(href)
        if parsed.scheme!="https" or parsed.hostname!="www.netto-online.de" or not parsed.path.endswith("/ViewMMPWishlist-AddStoreArticle"):
            warnings.append("UNEXPECTED_LINK_HOST_OR_PATH")
            continue
        query=parse_qs(parsed.query)
        def only(k):
            vals=query.get(k,[])
            return vals[0] if len(vals)==1 else None
        sku=only("SKU")
        price=_money(only("Price"))
        shown=_visible_euros(visible)
        valid_to=only("ValidTo")
        linked_name=only("Name")
        if not (sku==ffid and price is not None and shown==price and valid_to and linked_name==product_name):
            warnings.append("PRICE_NAME_OR_SKU_MISMATCH")
            mismatch_details.append({"ff_id":ffid, "name":product_name[:80],
              "sku_equal":sku==ffid, "price_from_link":str(price) if price is not None else None,
              "price_visible":str(shown) if shown is not None else None,
              "name_from_link":linked_name[:80] if linked_name else None,
              "has_valid_to":bool(valid_to)})
            continue
        try:datetime.strptime(valid_to,"%Y-%m-%d %H:%M:%S")
        except ValueError:
            warnings.append("INVALID_VALID_TO")
            continue
        if ffid in seen:
            warnings.append("DUPLICATE_ID")
            continue
        seen.add(ffid)
        app_price_node=tile.select_one(".grid-app-price .product__current-price.tc-product-price")
        app_price=_visible_euros(app_price_node)
        if app_price is not None and app_price>price:
            warnings.append("APP_PRICE_ABOVE_SALE_PRICE")
        records.append(NettoBranchOffer(
            offer_id=ffid,
            product_name=product_name,
            sale_price_eur=price,
            advertised_unit_price=only("BasePrice"),
            valid_from_date=_begin_date(header),
            valid_to_local=valid_to,
            advertised_app_price_eur=app_price,
            source_url=source_url))
    return records,{
        "status":"PARSED_WITH_WARNINGS" if warnings else "PARSED",
        "source_url":source_url,"published_offer_date_label":header,
        "candidate_tiles":len(candidate_tiles),
        "verified_sale_price_tiles":len(records),
        "warnings":warnings,
        "mismatch_details":mismatch_details,
        "all_offer_prices_have_local_valid_to":bool(records) and all(x.valid_to_local for x in records),
        "limitations":"Only published branch-offer tiles; region/store applicability and regular shelf price unknown; app price conditional."}
