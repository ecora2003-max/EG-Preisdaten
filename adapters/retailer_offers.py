"""Read-only supermarket offer adapters, with explicit applicability confidence.

Only parses supplied, legitimately obtained official responses. No authentication,
scraping proxy, CAPTCHA bypass, or credential use. No guaranteed in-stock claims.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import Enum
from html import unescape
import json
import re
from typing import Any, Iterable, Mapping


class Scope(str, Enum):
    STORE = "STORE_CONFIRMED"
    REGION = "REGION_CONFIRMED"
    CHAIN = "CHAIN_WIDE_REPORTED"
    UNVERIFIED = "UNKNOWN"


@dataclass(frozen=True)
class Offer:
    retailer: str
    product_id: str
    title: str
    price_eur: Decimal | None
    quantity: str | None
    valid_from: str | None
    valid_to: str | None
    scope: Scope
    scope_id: str | None
    price_condition: str | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        v = asdict(self)
        v["price_eur"] = str(self.price_eur) if self.price_eur is not None else None
        v["scope"] = self.scope.value
        return v


def money(value: Any) -> Decimal | None:
    """Parse explicit price amounts; do not turn discount labels into prices."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, dict):
        for key in ("amountRelevant", "value", "amount", "price", "current", "gross"):
            if key in value:
                result = money(value[key])
                if result is not None:
                    return result
        return None
    if isinstance(value, (int, float, Decimal)):
        try:
            n = Decimal(str(value))
            return n if n >= 0 else None
        except InvalidOperation:
            return None
    s = str(value).strip().replace("\u00a0", " ").replace("€", "")
    # Superscript footnotes, qualifiers and "ab" prices are intentionally excluded.
    if not re.fullmatch(r"(?:\d{1,3}(?:\.\d{3})*|\d+)(?:[.,]\d{1,2})?", s):
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        n = Decimal(s)
        return n if n >= 0 else None
    except InvalidOperation:
        return None


def _text(v: Any) -> str | None:
    if v is None:
        return None
    s = unescape(str(v)).strip()
    return s or None


def _iso_date(v: Any) -> str | None:
    if not isinstance(v, str):
        return None
    try:
        return date.fromisoformat(v[:10]).isoformat()
    except (ValueError, TypeError):
        return None


def penny_store(markets: Iterable[Mapping[str, Any]], store_id: str, *, week: str) -> dict[str, str]:
    """Resolve an exact store to its published selling region, never guess by PLZ."""
    if week not in ("current", "next"):
        raise ValueError("PENNY week must be current or next")
    matches = [s for s in markets if str(s.get("wwIdent") or "") == str(store_id)]
    if len(matches) != 1:
        raise ValueError("PENNY market ID missing or ambiguous")
    s = matches[0]
    rg = s.get("nextWeekSellingRegion") if week == "next" else s.get("sellingRegion")
    if not isinstance(rg, str) or not rg.strip():
        raise ValueError("PENNY exact market has no confirmed region for requested week")
    return {"store_id": str(store_id), "region": rg, "week": week}


def penny_offers(payload: Mapping[str, Any], *, region: str, week_start: str) -> list[Offer]:
    if not region or not _iso_date(week_start):
        raise ValueError("PENNY requires validated region and week start")
    tiles = payload.get("offerTiles")
    if not isinstance(tiles, list):
        raise ValueError("PENNY offerTiles missing")
    start = date.fromisoformat(week_start)
    end = date.fromordinal(start.toordinal() + 6).isoformat()
    result = []
    seen = set()
    for i, entry in enumerate(tiles):
        if not isinstance(entry, dict):
            continue
        title = _text(entry.get("title"))
        price = money(entry.get("price"))
        key = _text(entry.get("uuid")) or f"fallback-{i}"
        if not title or price is None or key in seen:
            continue
        seen.add(key)
        conditional = _text(entry.get("benefitPrice"))
        result.append(Offer("PENNY",key,title,price,_text(entry.get("quantity")),
                            start.isoformat(),end,Scope.REGION,region,
                            price_condition=conditional,
                            note=("App-/Vorteilspreis mit Fußnoten separat prüfen" if conditional else None)))
    return result


def _decode_aldi_data(payload: str | Mapping[str, Any]) -> Any:
    if isinstance(payload, str):
        # HTML __NEXT_DATA__, or the apiData JSON string directly
        if "__NEXT_DATA__" in payload:
            m = re.search(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
                          payload, re.S | re.I)
            if not m:
                raise ValueError("ALDI Nord __NEXT_DATA__ script missing")
            payload = m.group(1)
        payload = json.loads(payload)
    if isinstance(payload, dict) and "props" in payload:
        payload = payload.get("props",{}).get("pageProps",{}).get("apiData")
        if isinstance(payload, str):
            payload = json.loads(payload)
    return payload


def aldi_nord_next(payload: str | Mapping[str, Any]) -> list[Offer]:
    calls = _decode_aldi_data(payload)
    if not isinstance(calls,list):
        raise ValueError("ALDI Nord OFFER_GET response missing")
    candidates = [e[1] for e in calls if isinstance(e,list) and len(e)>=2 and e[0]=="OFFER_GET"
                  and isinstance(e[1],dict) and e[1].get("req",{}).get("week")=="next"]
    if len(candidates)!=1:
        raise ValueError("ALDI Nord expected exactly one week=next offer data")
    req=candidates[0]["req"]
    if any(k in req for k in ("storeId","marketId","region","zipCode","store")):
        raise ValueError("ALDI Nord unexpectedly per-store API; reassess scope")
    raw = candidates[0].get("res",{}).get("algoliaDataMap")
    if not isinstance(raw,dict):
        raise ValueError("ALDI Nord algoliaDataMap missing")
    offers=[]
    for key,product in raw.items():
        if not isinstance(product,dict):
            continue
        name=_text(product.get("name"))
        price=money(product.get("currentPrice"))
        if not name or price is None:
            continue
        offers.append(Offer("ALDI Nord",str(product.get("objectID") or key),name,price,
                            _text(product.get("salesUnit")),None,None,Scope.CHAIN,None,
                            note="Bundesweite Vorschau; mögliche Filialausnahmen nicht verifiziert"))
    return offers


def _kaufland_data(page: str | Mapping[str, Any]) -> Mapping[str,Any]:
    if isinstance(page,dict):
        if "props" in page:
            return page["props"]["offerData"]
        return page.get("offerData",page)
    # Embedded \"offerData\" followed by an unescaped JSON object
    at=page.find('"offerData":')
    if at<0:
        raise ValueError("Kaufland offerData JSON missing")
    brace=page.find("{",at+len('"offerData":'))
    if brace<0:
        raise ValueError("Kaufland offerData object start missing")
    obj,_=json.JSONDecoder().raw_decode(page[brace:])
    return obj


def kaufland_offers(page: str | Mapping[str, Any], availability: list[Mapping[str,Any]], *,
                    store_id: str, first_day: str, last_day: str) -> list[Offer]:
    """Intersection with store's official klNr date-window list.

    A cycle offer without exact store klNr and overlapping official dates is excluded.
    """
    if not re.fullmatch(r"DE\d{3,5}",store_id):
        raise ValueError("Kaufland explicit store ID must be DE plus digits")
    first,last=date.fromisoformat(first_day),date.fromisoformat(last_day)
    if first>last:
        raise ValueError("Invalid date interval")
    eligibility=set()
    for e in availability:
        if not isinstance(e,dict):
            continue
        ident=_text(e.get("klNr"))
        s,t=_iso_date(e.get("dateFrom")),_iso_date(e.get("dateTo"))
        if ident and s and t and s <= last_day and t >= first_day:
            eligibility.add(ident)
    data=_kaufland_data(page)
    cycles=data.get("cycles") if isinstance(data,dict) else None
    if not isinstance(cycles,list):
        raise ValueError("Kaufland cycles missing")
    out=[]
    seen=set()
    for cycle in reversed(cycles):  # preserve later cycle XTRA offers on duplicates
        for cat in cycle.get("categories",[]):
            for item in cat.get("offers",[]):
                if not isinstance(item,dict):
                    continue
                kl=_text(item.get("klNr"))
                if not kl or kl not in eligibility or kl in seen:
                    continue
                title=_text(item.get("title"))
                price=money(item.get("price"))
                if not title or price is None:
                    continue
                # Sales dates can differ from pre-publication dateFrom/dateTo;
                # do not treat them as proof when inconsistent with eligibility.
                sales_start=_iso_date(item.get("salesFrom"))
                sales_end=_iso_date(item.get("salesTo"))
                if sales_start and sales_end and (sales_start > last_day or sales_end < first_day):
                    continue
                seen.add(kl)
                out.append(Offer("Kaufland",kl,title,price,_text(item.get("unit")),
                                 first_day,last_day,Scope.STORE,store_id,
                                 note="Offiziell geführte Aktions-Gültigkeit; kein Lagerbestand"))
    return out


def lidl_flyer(payload: Mapping[str,Any], *, expected_start: str,
               confirmed_region_code: str | None = None) -> list[Offer]:
    """Lidl public leaflet JSON is not proof of which individual store participates.

    The product map can mix online/Nonfood with leaflet links. Mark UNKNOWN until
    a verified store->region/flyer mapping is supplied.
    """
    flyer=payload.get("flyer")
    if not isinstance(flyer,dict) or _iso_date(flyer.get("offerStartDate")) != expected_start:
        raise ValueError("Lidl flyer has wrong offer date")
    products=flyer.get("products")
    if not isinstance(products,dict):
        return []
    available_regions={str(r.get("code")) for r in flyer.get("regions",[]) if isinstance(r,dict)}
    confirmed = confirmed_region_code is not None and str(confirmed_region_code) in available_regions
    note="Prospekt-Produktliste kann Onlineshop/Nonfood enthalten; Filialgültigkeit nicht bewiesen"
    records=[]
    for key,p in products.items():
        if not isinstance(p,dict):
            continue
        title=_text(p.get("title"))
        price=money(p.get("price"))
        if not title or price is None:
            continue
        records.append(Offer("Lidl",str(p.get("productId") or key),title,price,None,
                             expected_start,_iso_date(flyer.get("offerEndDate")),
                             Scope.UNVERIFIED,confirmed_region_code if confirmed else None,
                             note=note))
    return records


def edeka_offers(payload: Mapping[str,Any], *, market_id: str) -> list[Offer]:
    """Schema-only adapter: official endpoint unverified from this GitHub runner."""
    docs=payload.get("docs")
    if not market_id or not isinstance(docs,list):
        raise ValueError("EDEKA market ID and docs response required")
    result=[]
    for i,p in enumerate(docs):
        if not isinstance(p,dict):
            continue
        title=_text(p.get("titel"))
        price=money(p.get("preis"))
        if title and price is not None:
            result.append(Offer("EDEKA",str(p.get("id") or i),title,price,
                                _text(p.get("beschreibung")),_iso_date(p.get("gueltig_von")),
                                _iso_date(p.get("gueltig_bis")),
                                Scope.UNVERIFIED,market_id,
                                note="Endpoint unverified live; marketId alone does not prove scope"))
    return result


def netto_status() -> dict[str,str]:
    """Fail closed. No verified structured product interface + market match yet."""
    return {"retailer":"Netto Marken-Discount","status":"NOT_IMPLEMENTATION_READY",
            "reason":"no live-verified market-specific JSON offer endpoint; blocked official access"}
