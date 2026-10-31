"""Eight-retailer price snapshot facade. No HTTP, user DB, OCR or purchase writes.

The caller supplies lawful snapshots; this library NEVER obtains one. Live evidence
and data-redistribution rights are deliberately independent. Python stdlib for core.
"""
from __future__ import annotations
import hashlib
import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit, parse_qsl
from typing import Any

VERSION = "0.1.0"
CONTRACT_VERSION = "1.0.0-draft"
_IDS = ("ALDI_NORD", "ALDI_SUED", "LIDL", "REWE", "EDEKA", "NETTO_MD", "PENNY", "KAUFLAND")
# Reports are dated observations, NOT a newly verified licence or a live uptime guarantee.
_REGISTRY = {
    "ALDI_NORD": ("LIVE_VERIFIED", "LIVE_VERIFIED", "CHAIN_WIDE_REPORTED", "UNVERIFIED", ("aldi-nord.de",)),
    "ALDI_SUED": ("EXPERIMENTAL", "LIVE_VERIFIED", "UNKNOWN", "UNVERIFIED", ("aldi-sued.de",)),
    "LIDL": ("LIVE_VERIFIED", "LIVE_VERIFIED", "STORE_CONFIRMED", "UNVERIFIED", ("lidlplus.com", "lidl.de")),
    "REWE": ("NOT_TESTED", "LIVE_VERIFIED", "STORE_CONFIRMED", "UNVERIFIED", ("rewe.de",)),
    "EDEKA": ("LIVE_VERIFIED", "NOT_TESTED", "STORE_CONFIRMED", "RESTRICTED", ("edeka.de",)),
    "NETTO_MD": ("LIVE_VERIFIED", "EXPERIMENTAL", "UNKNOWN", "UNVERIFIED", ("netto-online.de",)),
    "PENNY": ("LIVE_VERIFIED", "NOT_TESTED", "REGION_CONFIRMED", "UNVERIFIED", ("penny.de",)),
    "KAUFLAND": ("LIVE_VERIFIED", "NOT_TESTED", "STORE_CONFIRMED", "UNVERIFIED", ("kaufland.de",)),
}
class DataError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code

def provider_registry() -> dict[str, dict[str, Any]]:
    return {k: dict(offers=v[0], catalogue=v[1], bestKnownScope=v[2],
                    rights=v[3], lastResearchTest="2026-10-31",
                    dataMayBeRedistributed=(v[3]=="PERMITTED"))
            for k,v in _REGISTRY.items()}

def cents(value: Any) -> int | None:
    """Strict EUR decimal conversion, refusing floats, subcents and negative values."""
    if value is None: return None
    if isinstance(value, bool) or isinstance(value, float):
        raise DataError("INVALID_PRICE", "Float or boolean is not an auditable price")
    try:
        d=Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError):
        raise DataError("INVALID_PRICE", "Price is not numeric")
    if not d.is_finite() or d<0 or d.as_tuple().exponent < -2:
        raise DataError("INVALID_PRICE", "Price has negative value or more than two decimals")
    result=d*100
    if result>100_000_000 or result!=result.to_integral_value():
        raise DataError("INVALID_PRICE", "Price out of bounds")
    return int(result)

def parse_quantity(text: Any) -> dict[str, Any] | None:
    """Only explicit, unambiguous net mass/volume or piece counts; no weight guesses."""
    if not isinstance(text,str) or not text.strip() or len(text)>256:return None
    s=text.lower().replace("\u00a0"," ").replace("×","x").replace("‐","-")
    pattern=r"(?<![\d.,])\b(?:(\d+)\s*x\s*)?(\d+(?:[.,]\d{1,3})?)\s*-?\s*(kg|g|ml|l|stück|stueck|stk)(?!\w)"
    matches=list(re.finditer(pattern,s))
    if len(matches)!=1:return None
    m=matches[0]
    if s[m.end():].lstrip().startswith(("=","/")):return None
    n=int(m.group(1) or 1)
    unit=m.group(3)
    try: value=Decimal(m.group(2).replace(",", "."))
    except InvalidOperation:return None
    if unit in ("kg","l"):value*=1000
    total=value*n
    if n<=0 or n>1000 or total<=0 or total>1_000_000_000 or total!=total.to_integral_value():return None
    normalized="g" if unit in ("kg","g") else "ml" if unit in ("l","ml") else "piece"
    if normalized=="piece" and n>1: return None # ambiguous '2x3 Stück' pack format
    out={"amount":int(total),"unit":normalized,"basis":"PIECE" if normalized=="piece" else "NET",
         "confirmed":False,"notes":"Parsed from supplier display text; not independently verified"}
    if n>1:out.update(packageCount=n,quantityPerPackage=int(value))
    return out

def _date(v: Any) -> str | None:
    if v is None:return None
    if not isinstance(v,str):raise DataError("INVALID_DATE","Expected ISO calendar date")
    try:return date.fromisoformat(v).isoformat()
    except ValueError:raise DataError("INVALID_DATE","Invalid calendar date")

def _time(v: Any) -> str:
    if not isinstance(v,str):raise DataError("INVALID_TIMESTAMP","Timestamp is missing")
    try:
        d=datetime.fromisoformat(v.replace("Z","+00:00"))
        if d.tzinfo is None or d.utcoffset() is None:raise ValueError()
    except ValueError:raise DataError("INVALID_TIMESTAMP","Timestamp needs timezone")
    return d.isoformat()

def _host_authorized(url: Any, retailer: str, fixture: bool) -> str | None:
    if url is None and fixture:return None
    if not isinstance(url,str):raise DataError("INVALID_SOURCE","Source URL is required")
    if len(url)>4096:raise DataError("INVALID_SOURCE","Source URL too long")
    try:
        u=urlsplit(url)
        port=u.port
    except ValueError:raise DataError("INVALID_SOURCE","Malformed source URL")
    if u.scheme!="https" or not u.hostname or u.username or u.password or port not in (None,443):
        raise DataError("INVALID_SOURCE","Only anonymous official HTTPS URLs accepted")
    sensitive={"token","access_token","auth","authorization","session","apikey",
               "api_key","password","cookie","secret","signature","bearer"}
    if any(k.casefold() in sensitive for k,_ in parse_qsl(u.query,keep_blank_values=True)):
        raise DataError("INVALID_SOURCE","Source URL contains credential-like query keys")
    if not any(u.hostname==host or u.hostname.endswith("."+host) for host in _REGISTRY[retailer][4]):
        raise DataError("INVALID_SOURCE","Source does not belong to selected retailer")
    return url

def _gtin(v: Any) -> str | None:
    if not isinstance(v,str) or len(v) not in (8,12,13,14) or not v.isascii() or not v.isdigit():return None
    digits=[int(x) for x in v]
    check=(10-sum(d*(3 if i%2==0 else 1) for i,d in enumerate(reversed(digits[:-1])))%10)%10
    return v if check==digits[-1] else None

def _records(ds: dict[str,Any], typ: str) -> tuple[list[dict[str,Any]], dict[str,Any]]:
    """Bridge historical Try parsers. An unexpected schema fails closed."""
    r=ds["retailerId"]
    body=ds.get("body")
    store=ds.get("storeId")
    if ds.get("format")=="synthetic-fixture":
        if ds.get("fixture") is not True or not isinstance(body,list):
            raise DataError("INVALID_FIXTURE","Fixture source not explicitly synthetic")
        return body, {"received":len(body),"parsed":len(body),"complete":False}
    if typ=="SALE":
        from adapters import retailer_offers as a
        if r=="PENNY":
            offers=a.penny_offers(body,region=ds["regionId"],week_start=ds["weekStart"])
        elif r=="KAUFLAND":
            offers=a.kaufland_offers(body["page"],body["availability"],store_id=store,
                                     first_day=ds["firstDay"],last_day=ds["lastDay"])
        elif r=="ALDI_NORD":
            offers=a.aldi_nord_next(body)
        elif r=="LIDL":
            offers=a.lidl_store_offers(body,store_key=store)
        elif r=="EDEKA":
            offers=a.edeka_offers(body,market_id=store)
        elif r=="NETTO_MD":
            from catalogues.netto_branch_offers import parse_branch_offers
            items,cov=parse_branch_offers(body,ds["sourceUrl"])
            return [dict(id=x.offer_id,label=x.product_name,price=x.sale_price_eur,
                         advertisedUnitPrice=x.advertised_unit_price,fromDate=x.valid_from_date,
                         untilDate=x.valid_to_local[:10],scope="UNKNOWN",
                         scopeId=None,conditions=[],sourcePriceKind="SALE",
                         conditionalPrices=([{"priceCents":cents(x.advertised_app_price_eur),
                           "access":"NETTO_APP","evidence":"visible_app_price",
                           "termsVerified":False}] if x.advertised_app_price_eur is not None else [])) for x in items],{
                               "received":cov.get("candidate_tiles",len(items)),
                               "parsed":cov.get("verified_sale_price_tiles",len(items)),
                               "complete":False,"sourceWarnings":cov.get("warnings",[]),
                               "sourceStatus":cov.get("status","UNKNOWN")}
        else:
            raise DataError("UNSUPPORTED_SOURCE","No proven sales adapter for this chain")
        raw_count=len(offers)
        if r=="PENNY":raw_count=len(body["offerTiles"])
        elif r=="LIDL":raw_count=len(body["offers"])
        elif r=="EDEKA":raw_count=len(body["docs"])
        return [dict(id=x.product_id,label=x.title,price=x.price_eur,pack=x.quantity,
                     fromDate=x.valid_from,untilDate=x.valid_to,
                     scope=x.scope.value,scopeId=x.scope_id,
                     conditions=(["SEPARATE_BENEFIT_PRICE_TERMS_UNVERIFIED"] if r=="PENNY" and x.price_condition else []),
                     advertisedBenefitText=(x.price_condition if r=="PENNY" else None),
                     sourcePriceKind="SALE") for x in offers], {"received":raw_count,"parsed":len(offers),
                         "complete":False,"skipped":raw_count-len(offers)}
    if r=="REWE":
        from adapters.stationary_price_catalogues import rewe_stationary
        data=rewe_stationary(body,store)
        rows=[dict(id=x["product_id"],label=x["title"],brand=x["brand"],
                   priceCents=x["price_cents"],regularCents=x["regular_cents"],
                   depositCents=x["deposit_cents"],scope="STORE_CONFIRMED",scopeId=store,
                   hasDiscount=x["discount_is_observed"],
                   sourcePriceKind="CURRENT_DISPLAYED") for x in data["listings"]]
        return rows,{"received":data["source_count"],"parsed":len(rows),"complete":False}
    if r=="ALDI_SUED":
        from adapters.stationary_price_catalogues import aldi_sued
        data=aldi_sued(body,store)
        if any(x["currency"] != "EUR" for x in data["listings"]):
            raise DataError("INVALID_CURRENCY", "Non-EUR catalogue values cannot become EUR cents")
        rows=[dict(id=x["product_id"],label=x["title"],brand=x["brand"],
                   priceCents=x["price_cents"],depositCents=x["deposit_cents"],
                   scope="STORE_CONFIRMED",scopeId=store,
                   hasDiscount=x["discount_is_observed"],
                   referenceOldText=x["previous_price_display"],
                   sourcePriceKind="CURRENT_DISPLAYED") for x in data["listings"]]
        return rows,{"received":data["source_count"],"parsed":len(rows),
                     "reportedTotal":data["total_count"],"complete":data["catalogue_complete"] is True}
    if r=="LIDL":
        from catalogues.lidl import store_products,search_products
        if ds.get("mode")=="category-pages":
            from catalogues.lidl import merge_store_category_pages
            if not isinstance(body,list) or not body:
                raise DataError("INVALID_PAGINATION","Nonempty page list required")
            parsed_pages=[]
            for page in body:
                if not isinstance(page,dict) or not isinstance(page.get("payload"),dict):
                    raise DataError("INVALID_PAGINATION","Page payload and offset required")
                parsed_pages.append(store_products(page["payload"],store_key=store,
                    day=ds["snapshotDate"],offset=page["offset"],limit=page.get("limit")))
            items=merge_store_category_pages(parsed_pages)
            cov={"received":len(items),"parsed":len(items),"complete":True,
                 "reportedTotal":len(items),"pages":len(parsed_pages)}
        elif ds.get("mode")=="category":
            items,meta=store_products(body,store_key=store,day=ds["snapshotDate"],
                                      offset=ds.get("offset",0),limit=ds.get("limit"))
            cov={"received":meta["received"],"parsed":meta["parsed"],"complete":meta["complete"],
                 "reportedTotal":meta["reported_total"]}
        elif ds.get("mode")=="search":
            items=search_products(body,store_key=store,day=ds["snapshotDate"])
            cov={"received":len(body["results"]),"parsed":len(items),"complete":False}
        else:raise DataError("INVALID_REQUEST","Lidl catalogue needs mode=category/category-pages/search")
        return [dict(id=x.product_id,label=x.name,brand=x.brand,price=x.current_price_eur,
                     deposit=x.deposit_eur,scope="STORE_CONFIRMED",scopeId=store,
                     sourcePriceKind="CURRENT_DISPLAYED",
                     hasDiscount=x.has_discount,hasConditionalOffer=x.has_lidl_plus_offer,
                     priceWithoutDeposit=x.price_without_deposit_eur,
                     advertisedUnitPrice=x.advertised_unit_price_text,
                     referenceOldPrice=x.previous_display_price_eur,
                     conditionalPrices=([{"priceCents":cents(x.lidl_plus_price_eur),
                       "access":"LIDL_PLUS","evidence":"lidlPlusOffer.price",
                       "termsVerified":False}] if x.lidl_plus_price_eur is not None else [])) for x in items],cov
    if r=="ALDI_NORD":
        from catalogues.aldi_nord import aldi_nord_catalogue_from_html
        items,meta=aldi_nord_catalogue_from_html(body)
        return [dict(id=x.product_id,label=x.name,brand=x.brand,pack=x.pack,
                     price=x.displayed_price_eur,scope="CHAIN_WIDE_REPORTED",
                     fromDate=x.price_valid_from,untilDate=x.price_valid_to,
                     reportedBaseUnitPrices=[{"basis":unit,"priceEur":str(value)}
                                             for unit,value in x.unit_prices if unit in ("kg","l")],
                     sourcePriceKind="CURRENT_DISPLAYED") for x in items],{
                         "received":meta["received_hits"],"parsed":meta["priced_hits"],
                         "reportedTotal":meta["advertised_hits"],
                         "complete":meta["category_complete_response"] and meta["products_all_priced"]}
    if r=="NETTO_MD":
        from catalogues.netto_online import prices_from_product_html
        items=prices_from_product_html(body,ds["sourceUrl"])
        return [dict(id=x.sku,label=x.name,gtin=x.gtin,brand=x.brand,
                     price=x.price_eur,untilDate=x.price_valid_until,
                     scope="ONLINE",sourcePriceKind="ONLINE_LISTED") for x in items],{
                         "received":len(items),"parsed":len(items),"complete":False}
    raise DataError("UNSUPPORTED_SOURCE","No verified catalogue parser for this retailer")

def resolve_stores(retailer_id: str, records: list[dict[str,Any]], store_id: str) -> list[dict[str,Any]]:
    """Only exact retailer-bound, source-supplied store references; never infer via ZIP."""
    if retailer_id not in _REGISTRY: raise DataError("INVALID_RETAILER","Unknown retailer")
    if not store_id or not isinstance(store_id,str):raise DataError("INVALID_STORE","Exact storeId required")
    result=[]
    for row in records:
        if isinstance(row,dict) and row.get("retailerId")==retailer_id and row.get("storeId")==store_id and row.get("sourceRef"):
            result.append({"retailerId":retailer_id,"storeId":store_id,"sourceRef":row["sourceRef"],
                           "regionId":row.get("regionId")})
    if len(result)>1:raise DataError("AMBIGUOUS_STORE","Multiple exact store references")
    return result

def _payload(row: dict[str,Any], ds:dict[str,Any], kind:str, time:str, idx:int,
             requested_start:str,requested_end:str, regular:bool=False, shopping_date:str|None=None) -> dict[str,Any] | None:
    start=_date(row.get("fromDate"))
    end=_date(row.get("untilDate"))
    if start and end and start>end:raise DataError("INVALID_DATE","Offer validity reversed")
    if start and start>requested_end or end and end<requested_start:return None
    if not isinstance(row.get("label"),str) or not row["label"].strip():
        raise DataError("MISSING_FIELD","Product label is required")
    if row.get("foodTypeId") is not None and (
        not isinstance(row["foodTypeId"],str) or not row["foodTypeId"].strip()
    ):
        raise DataError("INVALID_ID","FoodType ID must remain source-verified")
    retailer=ds["retailerId"]
    for key in ("brand","advertisedUnitPrice","referenceOldText","advertisedBenefitText"):
        if row.get(key) is not None and not isinstance(row[key],str):
            raise DataError("INVALID_FIELD",f"{key} must be a string or null")
    raw_id=row.get("id")
    if raw_id is not None and (type(raw_id) not in (str,int) or isinstance(raw_id,bool)):
        raise DataError("INVALID_ID","Retailer article identifier is malformed")
    source_scope=row.get("scope") or "UNKNOWN"
    if source_scope not in ("STORE_CONFIRMED","REGION_CONFIRMED","CHAIN_WIDE_REPORTED","ONLINE","UNKNOWN"):
        raise DataError("INVALID_SCOPE","Unexpected scope")
    scope={"retailerId":retailer,"scopeType":source_scope}
    sid=row.get("scopeId")
    if sid is not None and (not isinstance(sid,str) or not sid.strip()):
        raise DataError("INVALID_SCOPE","Scope identifier must be nonempty text")
    proof=ds.get("scopeProof") or {}
    if not isinstance(proof,dict):
        raise DataError("INVALID_SCOPE","Scope provenance is not an object")
    # A caller-provided market ID alone is not evidence of scope; require explicit
    # provenance binding, checked against exact market/region in parsed response.
    if source_scope=="STORE_CONFIRMED":
        if not sid or sid!=ds.get("storeId") or proof.get("storeId")!=sid or not proof.get("sourceRef"):
            scope["scopeType"]="UNKNOWN"
        else:scope["storeId"]=sid
    elif source_scope=="REGION_CONFIRMED":
        if not sid or sid!=ds.get("regionId") or proof.get("regionId")!=sid or not proof.get("sourceRef"):
            scope["scopeType"]="UNKNOWN"
        else:scope["region"]=sid
    elif source_scope=="ONLINE":scope["storeId"]=None
    elif source_scope=="CHAIN_WIDE_REPORTED":scope["storeId"]=None
    raw_amount=row.get("regularCents") if regular else row.get("priceCents")
    if regular or "priceCents" in row:
        if raw_amount is not None and (type(raw_amount) is not int or not 0<=raw_amount<=100_000_000):raise DataError("INVALID_PRICE","Integer cents out of bounds")
        value=raw_amount
    else:value=cents(row.get("price"))
    if regular and value is None:return None
    if "depositCents" in row:
        dep=row["depositCents"]
        if dep is not None and (type(dep) is not int or not 0<=dep<=100_000_000):raise DataError("INVALID_PRICE","Invalid deposit cents")
    else:dep=cents(row.get("deposit"))
    # Explicit unknowns remain null; do not convert missing deposit to zero.
    name=row["label"].strip()
    condition=row.get("conditions") or []
    if not isinstance(condition,list) or any(not isinstance(v,str) for v in condition):
        raise DataError("INVALID_CONDITION","Conditions must be strings")
    kind_out="LISTED_REGULAR" if regular else row.get("sourcePriceKind") or ("SALE" if kind=="SALE" else "CURRENT_DISPLAYED")
    if kind_out not in ("SALE","CURRENT_DISPLAYED","LISTED_REGULAR","ONLINE_LISTED","UNKNOWN"):
        raise DataError("INVALID_PRICE_KIND","Unexpected price kind")
    if (kind=="SALE" and kind_out!="SALE") or (kind=="REGULAR" and kind_out=="SALE"):
        raise DataError("INVALID_PRICE_KIND","Retailer price kind contradicts source channel")
    for flag in ("hasDiscount","hasConditionalOffer"):
        if row.get(flag) is not None and type(row[flag]) is not bool:
            raise DataError("INVALID_FIELD",f"{flag} must be a boolean or null")
    qty=parse_quantity(row.get("pack"))
    reference_old=cents(row.get("referenceOldPrice"))
    if row.get("referenceOldPriceCents") is not None:
        x=row["referenceOldPriceCents"]
        if type(x) is not int or x<0 or x>100_000_000:
            raise DataError("INVALID_PRICE","Reference price must be integer nonnegative cents")
        reference_old=x
    reported_base=row.get("reportedBaseUnitPrices",[])
    if not isinstance(reported_base,list):
        raise DataError("INVALID_QUANTITY","Reported base prices need list form")
    for base in reported_base:
        if not isinstance(base,dict) or base.get("basis") not in ("kg","l") or not isinstance(base.get("priceEur"),str):
            raise DataError("INVALID_QUANTITY","Unexpected base price shape")
        try:n=Decimal(base["priceEur"])
        except InvalidOperation:raise DataError("INVALID_QUANTITY","Invalid base price")
        if not n.is_finite() or n<0:raise DataError("INVALID_QUANTITY","Invalid base price")
    conditional_prices=row.get("conditionalPrices",[])
    if not isinstance(conditional_prices,list):raise DataError("INVALID_CONDITION","Conditional prices list required")
    normalized_conditions=[]
    for x in conditional_prices:
        if not isinstance(x,dict) or type(x.get("priceCents")) is not int or x["priceCents"]<0 or x["priceCents"]>100_000_000 or x.get("access") not in ("NETTO_APP","LIDL_PLUS") or x.get("termsVerified") is not False:
            raise DataError("INVALID_CONDITION","Unsupported or unverified conditional price")
        normalized_conditions.append(dict(x))
    # Source-supplied base prices are comparison evidence, never inferred
    # pack weights or proof of a till price. Check only physically compatible
    # units and *displayed* net quantity, with a one-cent rounding allowance.
    base_price_check="NO_REPORTED_BASE_PRICE"
    if reported_base:
        if value is None:
            base_price_check="PRICE_UNKNOWN"
        elif dep is not None and dep>0:
            base_price_check="DEPOSIT_UNCERTAIN"
        elif qty is None or qty["amount"] is None or qty["basis"]!="NET":
            base_price_check="NOT_COMPARABLE"
        else:
            usable=[b for b in reported_base if (b["basis"]=="kg" and qty["unit"]=="g")
                   or (b["basis"]=="l" and qty["unit"]=="ml")]
            if not usable:
                base_price_check="NOT_COMPARABLE"
            else:
                computed=(Decimal(value)*1000)/Decimal(qty["amount"])
                checks=[abs(computed-(Decimal(b["priceEur"])*100))<=Decimal("1")
                        for b in usable]
                base_price_check="CONSISTENT_WITH_DISPLAYED_QUANTITY" if all(checks) else "MISMATCH"
    # Fingerprint the *normalized observation*, not just article ID and base
    # amount. Otherwise two offers with different packs, deposit or app terms
    # in one snapshot silently collapse into one observation.
    identity=json.dumps({
        "retailer":retailer,"scope":scope,"sourceScope":source_scope,
        "sourceScopeId":sid,"storeId":ds.get("storeId"),"regionId":ds.get("regionId"),
        "retailerArticleId":str(raw_id) if raw_id is not None else None,
        "label":name,"foodTypeId":row.get("foodTypeId"),"brand":row.get("brand"),
        "gtin":_gtin(row.get("gtin")),"quantity":qty,"kind":kind_out,
        "priceCents":value,"depositCents":dep,"validFrom":start,"validUntil":end,
        "conditions":condition,"conditionalPrices":normalized_conditions,
        "reportedBaseUnitPrices":reported_base,"referenceOldPriceCents":reference_old,
        "referenceOldText":row.get("referenceOldText"),
        "advertisedBenefitText":row.get("advertisedBenefitText"),
        "advertisedUnitPrice":row.get("advertisedUnitPrice"),
        "priceWithoutDeposit":row.get("priceWithoutDeposit"),
        "hasDiscount":row.get("hasDiscount"),"hasConditionalOffer":row.get("hasConditionalOffer"),
        "observedAt":time,"sourceUrl":ds.get("sourceUrl")
    },ensure_ascii=False,sort_keys=True,default=str)
    obs_id="PRICE-"+hashlib.sha256(identity.encode()).hexdigest()[:24]
    # A snapshot observed today is not proof of a future checkout price.
    if start is not None and end is not None:
        temporal="PUBLISHED_WINDOW" if start<=(shopping_date or requested_start)<=end else "OUTSIDE_TARGET_DATE"
    elif start is not None or end is not None:
        temporal="PARTIAL_VALIDITY_UNKNOWN"
    else:
        temporal="OBSERVED_ONLY_NO_VALIDITY_PROOF"
    return {"contractVersion":CONTRACT_VERSION,"messageType":"price.observation",
            "meta":{"producer":"EG-Preisdaten/"+VERSION,"createdAt":time,"traceId":obs_id,
                    "coverageNote":"Snapshot only; store rights and completeness require independent checks"},
            "payload":{"observationId":obs_id,
                       "article":{"label":name,"retailerArticleId":str(raw_id) if raw_id is not None else None,
                                  "foodTypeId":row.get("foodTypeId"),
                                  "gtin":_gtin(row.get("gtin")),"brandName":row.get("brand"),
                                  "brandKind":"UNKNOWN","organic":None,"quantity":qty},
                       "scope":scope,"priceCents":value,"currency":"EUR",
                       "priceKind":kind_out,"validFrom":start,"validUntil":end,
                       "depositCents":dep,"conditional":condition,
                       "source":{"origin":ds.get("origin","retailer-snapshot"),
                                 "url":ds.get("sourceUrl"),"observedAt":time,
                                 "evidenceKind":"UNKNOWN" if ds.get("fixture") else "OFFICIAL_WEB",
                                 "rightsStatus":_REGISTRY[retailer][3],"dataQuality":"UNKNOWN" if ds.get("fixture") else "SOURCED",
                                 "parserVersion":VERSION},
                       "availability":"UNKNOWN","eg-preisdaten:targetDateStatus":temporal,
                       "eg-preisdaten:conditionalPrices":normalized_conditions,
                       "eg-preisdaten:hasConditionalOffer":row.get("hasConditionalOffer"),
                       "eg-preisdaten:hasDiscount":row.get("hasDiscount"),
                       "eg-preisdaten:referenceOldPriceCents":reference_old,
                       "eg-preisdaten:referenceOldText":row.get("referenceOldText"),
                       "eg-preisdaten:advertisedBenefitText":row.get("advertisedBenefitText"),
                       "eg-preisdaten:advertisedUnitPrice":row.get("advertisedUnitPrice"),
                       "eg-preisdaten:reportedBaseUnitPrices":reported_base,
                       "eg-preisdaten:basePriceCheck":base_price_check,
                       "eg-preisdaten:priceWithoutDepositCents":cents(row.get("priceWithoutDeposit"))}}

class PriceService:
    """All functions are synchronous pure snapshot transforms. No network requests."""
    def search(self, request:dict[str,Any], datasets:list[dict[str,Any]], kind:str="BOTH")->dict[str,Any]:
        if not isinstance(request,dict) or not isinstance(datasets,list):
            raise DataError("INVALID_REQUEST","Request object and dataset list required")
        if kind not in ("SALE","REGULAR","BOTH"):raise DataError("INVALID_REQUEST","Invalid price selection")
        day=_date(request.get("shoppingDate"))
        if not day:raise DataError("INVALID_DATE","shoppingDate required")
        begin=_date(request.get("windowStart")) or day
        end=_date(request.get("windowEnd")) or day
        if begin>end:raise DataError("INVALID_DATE","Invalid request window")
        retailers=request.get("retailerIds")
        if not isinstance(retailers,list) or not retailers or any(
            not isinstance(x,str) or x not in _REGISTRY for x in retailers
        ):
            raise DataError("INVALID_RETAILER","Select at least one known retailer")
        limit=request.get("maxResults",100)
        if type(limit) is not int or not 1<=limit<=1000:raise DataError("INVALID_REQUEST","maxResults must be 1..1000")
        term=request.get("query")
        if term is not None and not isinstance(term,str):
            raise DataError("INVALID_REQUEST","query must be string")
        mode=request.get("usageMode","RESEARCH_ONLY")
        if mode not in ("RESEARCH_ONLY","APP_DISPLAY"):
            raise DataError("INVALID_REQUEST","usageMode must be RESEARCH_ONLY or APP_DISPLAY")
        selections=request.get("storeSelections",{})
        if not isinstance(selections,dict) or any(r not in _REGISTRY for r in selections):
            raise DataError("INVALID_REQUEST","Invalid store selection keys")
        for selection in selections.values():
            if not isinstance(selection,dict) or not selection:
                raise DataError("INVALID_REQUEST","Expected storeId and/or regionId")
            if any(k not in ("storeId","regionId") for k in selection) or any(
                not isinstance(v,str) or not v.strip() for v in selection.values()
            ):
                raise DataError("INVALID_REQUEST","Invalid store or region selection")
        article_filter=request.get("retailerArticleId")
        if article_filter is not None and (not isinstance(article_filter,str) or not article_filter.strip()):
            raise DataError("INVALID_REQUEST","Invalid retailer article ID filter")
        gtin_filter=request.get("gtin")
        if gtin_filter is not None and _gtin(gtin_filter)!=gtin_filter:
            raise DataError("INVALID_GTIN","Barcode must have valid digits, length and check digit")
        food_type_filter=request.get("foodTypeId")
        if food_type_filter is not None and (not isinstance(food_type_filter,str) or not food_type_filter.strip()):
            raise DataError("INVALID_REQUEST","FoodType ID must be a nonempty identifier")
        found=[]; errors=[]; coverage=[]; seen=set()
        for retailer in dict.fromkeys(retailers):
            store_selection=selections.get(retailer,{})
            raw_selected=[d for d in datasets if isinstance(d,dict) and d.get("retailerId")==retailer]
            selected=[]
            for dataset in raw_selected:
                mismatch=any(k in dataset and dataset[k] is not None and dataset[k]!=v
                             for k,v in store_selection.items())
                # A region-bound feed without a proven store->region binding is not
                # applicable merely because the request named a physical store.
                if store_selection.get("storeId") and dataset.get("regionId") and not store_selection.get("regionId"):
                    mismatch=True
                # The inverse is also unknown: a physical store without a region
                # reference cannot be silently included in a region-only query.
                if store_selection.get("regionId") and dataset.get("storeId") and not dataset.get("regionId"):
                    mismatch=True
                if mismatch:
                    coverage.append(dict(retailerId=retailer,channel=dataset.get("channel"),
                                         received=0,parsed=0,complete=False,status="OUT_OF_SCOPE",
                                         rights=_REGISTRY[retailer][3]))
                else:
                    selected.append(dataset)
            if not selected:
                coverage.append(dict(retailerId=retailer,received=0,parsed=0,complete=False,
                                     status="NO_MATCHING_SCOPE" if raw_selected else "NO_DATA",rights=_REGISTRY[retailer][3]))
            for ds in selected:
                channel=ds.get("channel")
                if channel not in ("SALE","REGULAR") or kind!="BOTH" and kind!=channel:continue
                received=0;parsed=0;complete=False
                prior_len=len(found); seen_before=seen.copy()
                try:
                    transport=ds.get("transportError")
                    if transport is not None:
                        codes={"TIMEOUT":"TIMEOUT","NETWORK":"NETWORK_ERROR",
                               "CANCELLED":"CANCELLED","TLS":"TLS_ERROR"}
                        if transport not in codes:
                            raise DataError("INVALID_TRANSPORT_ERROR","Unsupported transport error")
                        raise DataError(codes[transport],"Source transport failed before a usable response")
                    status=ds.get("httpStatus",200)
                    if status==403:raise DataError("SOURCE_BLOCKED","403 source denied")
                    if status==429:raise DataError("RATE_LIMITED","429 source throttled")
                    if status==204:raise DataError("NO_CONTENT","204 without price payload")
                    if type(status) is not int or status!=200:raise DataError("UPSTREAM_ERROR","Unexpected HTTP status")
                    if mode=="APP_DISPLAY" and ds.get("fixture") is not True and _REGISTRY[retailer][3]!="PERMITTED":
                        raise DataError("RIGHTS_NOT_CLEARED","External retailer data lack verified reuse permission")
                    if ds.get("fixture") is not True:
                        _host_authorized(ds.get("sourceUrl"),retailer,False)
                    elif ds.get("format")!="synthetic-fixture":
                        raise DataError("INVALID_FIXTURE","Fixture bypass requires synthetic-fixture format")
                    when=_time(ds.get("observedAt"))
                    if not isinstance(ds.get("origin"),str) or not ds["origin"].strip():
                        raise DataError("INVALID_SOURCE","Nonempty source origin is required")
                    if ds.get("contentType") not in (None,"application/json","text/html"):
                        raise DataError("INVALID_CONTENT_TYPE","Unexpected content type")
                    if ds.get("contentType")=="text/html" and not (retailer=="ALDI_NORD" and channel=="REGULAR" or retailer=="NETTO_MD"):
                        raise DataError("INVALID_CONTENT_TYPE","HTML instead of API JSON")
                    rows,summary=_records(ds,channel)
                    received=summary.get("received",len(rows)); parsed=summary.get("parsed",len(rows))
                    complete=summary.get("complete") is True
                    # Fail-closed: catalogues with invalid/missing IDs or prices must
                    # remain flagged partial even if upstream pagination is complete.
                    for idx,row in enumerate(rows):
                        if not isinstance(row,dict):raise DataError("SCHEMA_CHANGED","Row is not an object")
                        row_scope=row.get("scope")
                        scope_id=row.get("scopeId")
                        if (row_scope=="STORE_CONFIRMED" and store_selection.get("storeId")
                                and scope_id and scope_id!=store_selection["storeId"]):
                            continue
                        if (row_scope=="REGION_CONFIRMED" and store_selection.get("regionId")
                                and scope_id and scope_id!=store_selection["regionId"]):
                            continue
                        if (row_scope=="REGION_CONFIRMED" and store_selection.get("storeId")
                                and not store_selection.get("regionId")):
                            continue
                        for regular in ((False,True) if channel=="REGULAR" and retailer=="REWE" else (False,)):
                            payload=_payload(row,ds,channel,when,idx,begin,end,regular,day)
                            if payload is None:continue
                            article=payload["payload"]["article"]
                            if term is not None and term.casefold() not in article["label"].casefold():continue
                            if article_filter is not None and article["retailerArticleId"]!=article_filter:continue
                            if gtin_filter is not None and article["gtin"]!=gtin_filter:continue
                            if food_type_filter is not None and article["foodTypeId"]!=food_type_filter:continue
                            oid=payload["payload"]["observationId"]
                            if oid not in seen:
                                found.append(payload);seen.add(oid)
                    if received!=parsed:complete=False
                    coverage.append(dict(retailerId=retailer,channel=channel,received=received,parsed=parsed,
                                         complete=complete,status="PARSED_PARTIAL" if not complete else "PARSED_PAGE",
                                         rights=_REGISTRY[retailer][3],reportedTotal=summary.get("reportedTotal"),
                                         checkedAt=when,sourceUrl=ds.get("sourceUrl"),
                                         sourceWarnings=summary.get("sourceWarnings",[]),
                                         sourceStatus=summary.get("sourceStatus")))
                except (DataError, ValueError, TypeError, KeyError, AttributeError,
                        OverflowError, ImportError, json.JSONDecodeError) as exc:
                    # Atomic dataset import: never leak half-parsed output after schema failure.
                    found=found[:prior_len];seen=seen_before
                    code=exc.code if isinstance(exc,DataError) else "SCHEMA_CHANGED"
                    errors.append(dict(retailerId=retailer,channel=channel,code=code,message=str(exc)[:250]))
                    coverage.append(dict(retailerId=retailer,channel=channel,received=received,parsed=parsed,
                                         complete=False,status="ERROR",rights=_REGISTRY[retailer][3]))
        truncated=len(found)>limit
        warnings=["Source retrieval and redistribution rights are not granted by parser success",
                  "Observations do not create purchases, receipts or inventory events"]
        if truncated:warnings.append("OUTPUT_TRUNCATED: matching observations exceed maxResults")
        return {"contractVersion":CONTRACT_VERSION,"observations":found[:limit],
                "matchedCount":len(found),"outputTruncated":truncated,
                "coverage":coverage,"errors":errors,"warnings":warnings}
    def search_offers(self, request, datasets):
        return self.search(request,datasets,"SALE")
    def search_catalog_prices(self,request,datasets):
        return self.search(request,datasets,"REGULAR")
    def lookup_price(self,request,datasets,retailer_article_id):
        return self.search({**request,"retailerArticleId":retailer_article_id},datasets,"BOTH")
    def get_coverage(self,request,datasets):
        return self.search(request,datasets,"BOTH")["coverage"]
