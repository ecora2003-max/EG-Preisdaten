"""Offline contract, provider, negative and bridge tests. No network or user data."""
import copy
import json
from pathlib import Path
import unittest
from price_module import PriceService, provider_registry, parse_quantity, cents, resolve_stores
from price_module.service import DataError
try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    Draft202012Validator = None

DAY="2026-10-31"
TIME="2026-10-31T12:00:00+01:00"
REQUEST={"shoppingDate":DAY,"retailerIds":["LIDL"],"maxResults":100}
SYNTHETIC={"retailerId":"LIDL","channel":"SALE","fixture":True,
           "format":"synthetic-fixture","origin":"synthetic-fixture",
           "observedAt":TIME,"body":[]}

def fixture(rows,retailer="LIDL",channel="SALE",**kwargs):
    d={**SYNTHETIC,"retailerId":retailer,"channel":channel,"body":rows}
    d.update(kwargs)
    return d

def r(label="Milch",price="1.25",**changes):
    return {"id":"s1","label":label,"price":price,"pack":"2 x 500 g",
            "fromDate":DAY,"untilDate":"2026-11-05",**changes}

def source(retailer,channel,body,url,**kwargs):
    d={"retailerId":retailer,"channel":channel,"body":body,"sourceUrl":url,
       "origin":"official-retailer","observedAt":TIME,"contentType":"application/json"}
    d.update(kwargs)
    return d

class ModuleTests(unittest.TestCase):
    def setUp(self):
        self.service=PriceService()

    def test_eight_providers_distinct_and_rights_not_granted(self):
        reg=provider_registry()
        self.assertEqual(len(reg),8)
        self.assertEqual(reg["NETTO_MD"]["rights"],"UNVERIFIED")
        self.assertEqual(reg["EDEKA"]["rights"],"RESTRICTED")
        self.assertFalse(any(x["dataMayBeRedistributed"] for x in reg.values()))

    def test_all_eight_synthetic_current_future_expired(self):
        for chain in provider_registry():
            req={**REQUEST,"retailerIds":[chain],"windowEnd":"2026-11-10"}
            ds=fixture([r(id="current",fromDate=DAY,untilDate=DAY),
                        r(id="future",fromDate="2026-11-03",untilDate="2026-11-07"),
                        r(id="expired",fromDate="2026-10-01",untilDate="2026-10-02")],retailer=chain)
            output=self.service.search_offers(req,[ds])
            self.assertEqual(len(output["observations"]),2,chain)
            self.assertEqual(output["errors"],[])
            self.assertFalse(output["coverage"][0]["complete"])

    def test_contract_schema_valid_unknown_and_zero_and_invalid_source(self):
        self.assertIsNotNone(Draft202012Validator,"CI requires jsonschema dependency")
        schema=json.loads(Path("tests/fixtures/architecture-contract.schema.json").read_text())
        v=Draft202012Validator(schema,format_checker=FormatChecker())
        result=self.service.search(REQUEST,[fixture([r(price=None),r(id="s2",price="0.00")])],"SALE")
        messages=result["observations"]
        self.assertEqual([x["payload"]["priceCents"] for x in messages],[None,0])
        for doc in messages:
            self.assertFalse(list(v.iter_errors(doc)))
        invalid=copy.deepcopy(messages[0])
        invalid["payload"]["priceCents"]=-1
        self.assertTrue(list(v.iter_errors(invalid)))
        invalid=copy.deepcopy(messages[0])
        invalid["payload"]["scope"]={"retailerId":"LIDL","scopeType":"STORE_CONFIRMED"}
        self.assertTrue(list(v.iter_errors(invalid)))
        invalid=copy.deepcopy(messages[0])
        invalid["payload"]["source"]["rightsStatus"]="ALLOWED_BY_HTTP_200"
        self.assertTrue(list(v.iter_errors(invalid)))
        for message in json.loads(Path("tests/fixtures/architecture-examples.json").read_text()):
            self.assertFalse(list(v.iter_errors(message)))

    def test_decimal_money_and_quantity_no_guess(self):
        self.assertEqual(cents("1,99"),199)
        self.assertEqual(cents("0"),0)
        self.assertIsNone(cents(None))
        for p in (True,1.123,-1,"NaN",1.2):
            with self.assertRaises(DataError):cents(p)
        self.assertEqual(parse_quantity("500-g-Packung")["amount"],500)
        self.assertEqual(parse_quantity("2×500 g")["amount"],1000)
        self.assertEqual(parse_quantity("2×500 g")["quantityPerPackage"],500)
        self.assertEqual(parse_quantity("0,75 l")["amount"],750)
        self.assertEqual(parse_quantity("4 Stück")["unit"],"piece")
        self.assertIsNone(parse_quantity("2 x 1 Stück"))
        self.assertIsNone(parse_quantity("eine Packung"))
        self.assertIsNone(parse_quantity("3,1234 kg"))

    def test_scope_requires_verifiable_exact_binding(self):
        raw=fixture([r(scope="STORE_CONFIRMED",scopeId="DE1")],storeId="DE1")
        unknown=self.service.search(REQUEST,[raw])["observations"][0]["payload"]["scope"]
        self.assertEqual(unknown["scopeType"],"UNKNOWN")
        raw["scopeProof"]={"storeId":"DE1","sourceRef":"official-store-selection"}
        confirmed=self.service.search(REQUEST,[raw])["observations"][0]["payload"]["scope"]
        self.assertEqual(confirmed["storeId"],"DE1")
        raw["storeId"]="DE2"
        switched=self.service.search(REQUEST,[raw])["observations"][0]["payload"]["scope"]
        self.assertEqual(switched["scopeType"],"UNKNOWN")
        a=resolve_stores("LIDL",[{"retailerId":"LIDL","storeId":"DE1",
                                   "sourceRef":"official"}],"DE1")
        self.assertEqual(a[0]["storeId"],"DE1")
        self.assertEqual(resolve_stores("REWE",[{"retailerId":"LIDL","storeId":"DE1",
                                                 "sourceRef":"official"}],"DE1"),[])

    def test_source_restrictions_and_http_errors(self):
        bad=source("LIDL","REGULAR",{"products":[]},"https://attacker.example/prices",mode="category")
        result=self.service.search(REQUEST,[bad])
        self.assertEqual(result["errors"][0]["code"],"INVALID_SOURCE")
        for status,expected in ((403,"SOURCE_BLOCKED"),(429,"RATE_LIMITED"),
                                (204,"NO_CONTENT"),(502,"UPSTREAM_ERROR")):
            d=fixture([r()],httpStatus=status)
            self.assertEqual(self.service.search(REQUEST,[d])["errors"][0]["code"],expected)
        ds=fixture([r()],contentType="text/html")
        self.assertEqual(self.service.search(REQUEST,[ds])["errors"][0]["code"],"INVALID_CONTENT_TYPE")
        ds=fixture([r()],observedAt="2026-10-31T12:00:00")
        self.assertEqual(self.service.search(REQUEST,[ds])["errors"][0]["code"],"INVALID_TIMESTAMP")
        ds=fixture([r()],origin="")
        self.assertEqual(self.service.search(REQUEST,[ds])["errors"][0]["code"],"INVALID_SOURCE")

    def test_unknown_fields_and_invalid_conditions(self):
        d=fixture([r(conditions=["only with app"],deposit="0.25")])
        result=self.service.search(REQUEST,[d])["observations"][0]["payload"]
        self.assertEqual(result["depositCents"],25)
        self.assertEqual(result["conditional"],["only with app"])
        bad=fixture([r(conditions=[123])])
        self.assertEqual(self.service.search(REQUEST,[bad])["errors"][0]["code"],"INVALID_CONDITION")
        bad=fixture([r(fromDate="2026-11-10",untilDate="2026-10-10")])
        self.assertEqual(self.service.search(REQUEST,[bad])["errors"][0]["code"],"INVALID_DATE")
        bad=fixture([r(price="1.001")])
        self.assertEqual(self.service.search(REQUEST,[bad])["errors"][0]["code"],"INVALID_PRICE")

    def test_no_side_effect_on_snapshots(self):
        before=fixture([r()])
        saved=copy.deepcopy(before)
        self.service.search_offers(REQUEST,[before])
        self.service.search_catalog_prices(REQUEST,[before])
        self.service.lookup_price(REQUEST,[before],"s1")
        self.service.get_coverage(REQUEST,[before])
        self.assertEqual(before,saved)

    def test_rewe_stationary_two_stores_and_reference_price(self):
        body={"products":[{"id":"001","title":"Milch","brand":"Demo",
                           "pricing":{"current":115,"regular":129,"refund":25}}]}
        one=source("REWE","REGULAR",body,
                   "https://www.rewe.de/api/stationary-product-search/products",
                   storeId="840174",scopeProof={"storeId":"840174","sourceRef":"official-market-search"})
        two=copy.deepcopy(one)
        two["storeId"]="831002"
        two["scopeProof"]={"storeId":"831002","sourceRef":"official-market-search"}
        two["body"]["products"][0]["pricing"]["current"]=125
        req={**REQUEST,"retailerIds":["REWE"]}
        result=self.service.search_catalog_prices(req,[one,two])
        prices=[v["payload"]["priceCents"] for v in result["observations"] if v["payload"]["priceKind"]=="CURRENT_DISPLAYED"]
        self.assertEqual(prices,[115,125])
        self.assertEqual(len(result["observations"]),4)
        self.assertTrue(all(x["payload"]["scope"]["scopeType"]=="STORE_CONFIRMED" for x in result["observations"]))

    def test_lidl_price_catalogue_and_incomplete_category(self):
        body={"totalProducts":3,"products":[{"id":"1_DE","title":"Milch","brand":"Demo",
               "price":{"price":0.85,"oldPrice":1.09}}]}
        ds=source("LIDL","REGULAR",body,
                  "https://product-catalog.lidlplus.com/api/app/v1/DE/store/DE7434/categories/milk/products",
                  storeId="DE7434",scopeProof={"storeId":"DE7434","sourceRef":"official-stores"},
                  mode="category",snapshotDate=DAY,limit=2,offset=0)
        result=self.service.search_catalog_prices(REQUEST,[ds])
        self.assertEqual(result["observations"][0]["payload"]["priceCents"],85)
        self.assertFalse(result["coverage"][0]["complete"])

    def test_aldi_sued_refuses_claim_of_entire_catalogue(self):
        body={"data":[{"sku":"1","name":"Demo","price":{"amountRelevant":199,"currencyCode":"EUR"}}],
              "meta":{"pagination":{"totalCount":3538}}}
        ds=source("ALDI_SUED","REGULAR",body,"https://api.aldi-sued.de/v3/product-search",
                  storeId="B384",scopeProof={"storeId":"B384","sourceRef":"servicepoint-selected"})
        res=self.service.search_catalog_prices({**REQUEST,"retailerIds":["ALDI_SUED"]},[ds])
        self.assertEqual(res["observations"][0]["payload"]["priceCents"],199)
        self.assertFalse(res["coverage"][0]["complete"])
        self.assertEqual(res["coverage"][0]["reportedTotal"],3538)

    def test_reject_html_as_api_json_and_missing_schema(self):
        ds=source("REWE","REGULAR","<html>oops</html>",
                  "https://www.rewe.de/api/stationary-product-search/products",
                  storeId="840174")
        res=self.service.search_catalog_prices({**REQUEST,"retailerIds":["REWE"]},[ds])
        self.assertEqual(res["errors"][0]["code"],"SCHEMA_CHANGED")
        self.assertEqual(res["coverage"][0]["status"],"ERROR")


    def test_all_offer_bridges_with_realistic_offline_shapes(self):
        req={**REQUEST,"windowEnd":"2026-11-07"}
        cases=[
          (source("PENNY","SALE",{"offerTiles":[{"uuid":"x","title":"Käse","price":"1.49",
                        "benefitPrice":"1.29²","quantity":"140 g"}]},
                    "https://www.penny.de/angebote",
                    regionId="R1",weekStart="2026-11-02",
                    scopeProof={"regionId":"R1","sourceRef":"published-selling-region"}),
           "PENNY",149,"REGION_CONFIRMED"),
          (source("KAUFLAND","SALE",{"page":{"cycles":[{"categories":[{"offers":[{
                    "klNr":"A","title":"Tofu","price":1.99,"unit":"200 g",
                    "salesFrom":"2026-11-02","salesTo":"2026-11-07"}]}]}]},
                    "availability":[{"klNr":"A","dateFrom":"2026-11-02","dateTo":"2026-11-07"}]},
                    "https://www.kaufland.de/angebote",storeId="DE5220",
                    firstDay="2026-11-02",lastDay="2026-11-07",
                    scopeProof={"storeId":"DE5220","sourceRef":"official-klNr-market"}),
           "KAUFLAND",199,"STORE_CONFIRMED"),
          (source("ALDI_NORD","SALE",{"props":{"pageProps":{"apiData":json.dumps([
                    ["OFFER_GET",{"req":{"locale":"de","week":"next"},
                    "res":{"algoliaDataMap":{"a":{"objectID":"a","name":"Nüsse",
                    "currentPrice":{"priceValue":1.49,"validFromLocalDate":"2026-11-02",
                    "validUntilLocalDate":"2026-11-07"}}}}}]])}}},
                    "https://www.aldi-nord.de/angebote"),
           "ALDI_NORD",149,"CHAIN_WIDE_REPORTED"),
          (source("LIDL","SALE",{"offers":[{"id":"1","title":"Eis","category":"Store",
                    "offerType":"StoreSpecialPriceDiscount",
                    "priceBox":{"largePartNumeric":1.49},
                    "startValidityDate":"2026-11-02","endValidityDate":"2026-11-07"}],
                    "totalOffers":1},
                    "https://offers.lidlplus.com/app/api/v4/DE/DE7434/offers",
                    storeId="DE7434",scopeProof={"storeId":"DE7434","sourceRef":"official-lidl-store"}),
           "LIDL",149,"STORE_CONFIRMED"),
          (source("EDEKA","SALE",{"national":False,"docs":[{"angebotid":1,"titel":"Tofu",
                    "preis":"2,29","gueltig_von":"2026-11-02","gueltig_bis":"2026-11-07"}]},
                    "https://www.edeka.de/api/angebote",storeId="1234",
                    scopeProof={"storeId":"1234","sourceRef":"market-id"}),
           "EDEKA",229,"STORE_CONFIRMED")
        ]
        for ds,retailer,expected_price,scope in cases:
            result=self.service.search_offers({**req,"retailerIds":[retailer]},[ds])
            self.assertFalse(result["errors"],(retailer,result["errors"]))
            self.assertEqual(len(result["observations"]),1,retailer)
            p=result["observations"][0]["payload"]
            self.assertEqual(p["priceCents"],expected_price,retailer)
            self.assertEqual(p["scope"]["scopeType"],scope,retailer)
            if retailer=="EDEKA":
                self.assertEqual(p["source"]["rightsStatus"],"RESTRICTED")

    def test_parser_rolls_back_all_rows_on_one_invalid_row(self):
        ds=fixture([r(id="good"),r(id="bad",price="1.123")])
        result=self.service.search_offers(REQUEST,[ds])
        self.assertEqual(result["errors"][0]["code"],"INVALID_PRICE")
        self.assertEqual(result["observations"],[])

    def test_query_filter_applies_before_output_limit(self):
        ds=fixture([r(id="a",label="Tomaten"),r(id="b",label="Milch"),
                    r(id="c",label="Milch")])
        req={**REQUEST,"query":"Milch","maxResults":1}
        result=self.service.search_offers(req,[ds])
        self.assertEqual(len(result["observations"]),1)
        self.assertEqual(result["observations"][0]["payload"]["article"]["label"],"Milch")

    def test_no_foreign_currency_claimed_as_eur(self):
        body={"data":[{"sku":"X","name":"M","price":{"amountRelevant":199,
             "currencyCode":"USD"}}]}
        ds=source("ALDI_SUED","REGULAR",body,
                  "https://api.aldi-sued.de/v3/product-search",storeId="B384")
        out=self.service.search_catalog_prices({**REQUEST,"retailerIds":["ALDI_SUED"]},[ds])
        self.assertEqual(out["errors"][0]["code"],"INVALID_CURRENCY")
        self.assertEqual(out["observations"],[])

    def test_official_chain_current_category_and_netto_online(self):
        product={"objectID":"A","name":"Bio-Quark","brandName":"BIO","salesUnit":"250 g",
                 "currentPrice":{"priceValue":0.99}}
        aldi_payload={"props":{"pageProps":{"algoliaState":{"initialResults":{
                "an_prd_de_de_products2":{"results":[{"nbHits":1,"nbPages":1,"page":0,
                                                       "hits":[product]}]}}}}}}
        html='<script id="__NEXT_DATA__" type="application/json">'+json.dumps(aldi_payload)+'</script>'
        aldi=source("ALDI_NORD","REGULAR",html,
                    "https://www.aldi-nord.de/sortiment/produkte",contentType="text/html")
        result=self.service.search_catalog_prices({**REQUEST,"retailerIds":["ALDI_NORD"]},[aldi])
        self.assertEqual(result["observations"][0]["payload"]["scope"]["scopeType"],"CHAIN_WIDE_REPORTED")
        self.assertEqual(result["observations"][0]["payload"]["priceCents"],99)
        self.assertTrue(result["coverage"][0]["complete"]) # one API category only, not whole chain
        netto_html="""<script type="application/ld+json">{"@type":"Product","name":"Haferflocken",
                    "sku":"D1","offers":{"@type":"Offer","price":"1.89",
                    "priceCurrency":"EUR"}}</script>"""
        netto=source("NETTO_MD","REGULAR",netto_html,
                     "https://www.netto-online.de/produkt/haferflocken",
                     contentType="text/html")
        result=self.service.search_catalog_prices({**REQUEST,"retailerIds":["NETTO_MD"]},[netto])
        self.assertEqual(result["observations"][0]["payload"]["priceKind"],"ONLINE_LISTED")
        self.assertEqual(result["observations"][0]["payload"]["scope"]["scopeType"],"ONLINE")
        self.assertEqual(result["observations"][0]["payload"]["priceCents"],189)


    def test_lidl_two_pages_complete_only_when_contiguous(self):
        def item(i):
            return {"id":str(i)+"_DE","title":"Demo"+str(i),
                    "price":{"price":1.29}}
        p1={"payload":{"totalProducts":3,"products":[item(1),item(2)]},
            "offset":0,"limit":2}
        p2={"payload":{"totalProducts":3,"products":[item(3)]},
            "offset":2,"limit":2}
        ds=source("LIDL","REGULAR",[p1,p2],
                  "https://product-catalog.lidlplus.com/api/app/v1/DE/store/DE7434/categories/x/products",
                  storeId="DE7434",mode="category-pages",snapshotDate=DAY)
        out=self.service.search_catalog_prices(REQUEST,[ds])
        self.assertTrue(out["coverage"][0]["complete"])
        self.assertEqual(len(out["observations"]),3)
        ds["body"]=[p2,p1]
        out=self.service.search_catalog_prices(REQUEST,[ds])
        self.assertFalse(out["coverage"][0]["complete"])
        self.assertEqual(out["errors"][0]["code"],"SCHEMA_CHANGED")
        self.assertEqual(out["observations"],[])

    def test_unproven_future_price_is_never_reported_as_valid_forecast(self):
        ds=fixture([{"id":"n","label":"Nudeln","priceCents":90}],channel="REGULAR")
        out=self.service.search_catalog_prices(
            {**REQUEST,"shoppingDate":"2026-11-05"},[ds])
        self.assertEqual(out["observations"][0]["payload"]["eg-preisdaten:targetDateStatus"],
                         "OBSERVED_ONLY_NO_VALIDITY_PROOF")
        ds=fixture([r(id="offer",fromDate="2026-11-02",untilDate="2026-11-07")])
        out=self.service.search_offers(
            {**REQUEST,"shoppingDate":"2026-11-05"},[ds])
        self.assertEqual(out["observations"][0]["payload"]["eg-preisdaten:targetDateStatus"],
                         "PUBLISHED_WINDOW")


    def test_restricted_source_fails_closed_in_app_usage(self):
        edeka=source("EDEKA","SALE",{"national":False,"docs":[
                {"angebotid":1,"titel":"Tofu","preis":"1.99"}]},
                "https://www.edeka.de/api/angebote",storeId="1234")
        req={**REQUEST,"retailerIds":["EDEKA"],"usageMode":"APP_DISPLAY"}
        out=self.service.search_offers(req,[edeka])
        self.assertEqual(out["observations"],[])
        self.assertEqual(out["errors"][0]["code"],"RIGHTS_NOT_CLEARED")
        preview=self.service.search_offers({**req,"usageMode":"RESEARCH_ONLY"},[edeka])
        self.assertEqual(len(preview["observations"]),1)
        self.assertEqual(preview["observations"][0]["payload"]["source"]["rightsStatus"],"RESTRICTED")
        synthetic=fixture([r()])
        out=self.service.search_offers({**REQUEST,"usageMode":"APP_DISPLAY"},[synthetic])
        self.assertEqual(len(out["observations"]),1)

    def test_netto_branch_price_must_match_visible_and_embedded_value(self):
        from urllib.parse import urlencode
        url="https://www.netto-online.de/angebote/c-N07"
        def page(price):
            query=urlencode({"SKU":"A1","Price":price,"ValidTo":"2026-10-31 23:59:59",
                             "Name":"Hafer","BasePrice":"1 kg=3.98 EUR"})
            return ('<section><h2>Filial-Angebote</h2>'
                    '<div class="store-offers__header__date">26.10.2026 - 31.10.2026</div>'
                    '<div class="tc-store-product-tile" data-ff-id="A1">'
                    '<span class="tc-product-name">Hafer</span>'
                    '<a href="https://www.netto-online.de/ViewMMPWishlist-AddStoreArticle?'+query+'">Test</a>'
                    '<div class="grid-top-price"><span class="product__current-price tc-product-price">1,99</span></div>'
                    '</div></section>')
        ds=source("NETTO_MD","SALE",page("1.99"),url,contentType="text/html")
        out=self.service.search_offers(REQUEST | {"retailerIds":["NETTO_MD"]},[ds])
        self.assertEqual(len(out["observations"]),1,out["errors"])
        self.assertEqual(out["observations"][0]["payload"]["priceCents"],199)
        self.assertEqual(out["observations"][0]["payload"]["scope"]["scopeType"],"UNKNOWN")
        ds["body"]=page("2.49")
        out=self.service.search_offers(REQUEST | {"retailerIds":["NETTO_MD"]},[ds])
        self.assertEqual(out["observations"],[])
        self.assertEqual(out["coverage"][0]["status"],"PARSED_PARTIAL")


    def test_conditional_penny_benefit_is_not_unconditional_price(self):
        ds=source("PENNY","SALE",{"offerTiles":[{"uuid":"b","title":"Käse 140 g",
                 "price":"1.49","benefitPrice":"1.29²","quantity":"140 g"}]},
                 "https://www.penny.de/angebote",regionId="R1",weekStart=DAY)
        out=self.service.search_offers({**REQUEST,"retailerIds":["PENNY"]},[ds])
        p=out["observations"][0]["payload"]
        self.assertEqual(p["priceCents"],149)
        self.assertEqual(p["conditional"],["SEPARATE_BENEFIT_PRICE_TERMS_UNVERIFIED"])
        self.assertEqual(p["eg-preisdaten:advertisedBenefitText"],"1.29²")
        self.assertEqual(p["eg-preisdaten:conditionalPrices"],[])

    def test_lidl_plus_secondary_price_is_not_base_price(self):
        ds=source("LIDL","REGULAR",{"results":[
            {"id":"x","title":"Milch 1 l","brand":"Example","price":1.29,
             "lidlPlusOffer":{"price":0.89},"priceWithoutDeposit":1.29,
             "oldPrice":1.49}]},
             "https://product-catalog.lidlplus.com/api/app/v1/DE/store/DE7434/search",
             storeId="DE7434",mode="search",snapshotDate=DAY)
        out=self.service.search_catalog_prices(REQUEST,[ds])
        self.assertEqual(out["errors"],[])
        p=out["observations"][0]["payload"]
        self.assertEqual(p["priceCents"],129)
        self.assertEqual(p["priceKind"],"CURRENT_DISPLAYED")
        self.assertEqual(p["eg-preisdaten:conditionalPrices"],[
            {"priceCents":89,"access":"LIDL_PLUS","evidence":"lidlPlusOffer.price",
             "termsVerified":False}])
        self.assertEqual(p["eg-preisdaten:priceWithoutDepositCents"],129)
        self.assertIs(p["eg-preisdaten:hasDiscount"],True)

    def test_ambiguous_netto_base_price_is_not_product_weight(self):
        from urllib.parse import urlencode
        q=urlencode({"SKU":"A1","Price":"1.99","ValidTo":"2026-10-31 23:59:59",
                    "Name":"Hafer","BasePrice":"1 kg = 3,98 EUR"})
        html=('<section><h2>Filial-Angebote</h2><div class="store-offers__header__date">'
              '26.10.2026 - 31.10.2026</div>'
              '<div class="tc-store-product-tile" data-ff-id="A1">'
              '<span class="tc-product-name">Hafer</span>'
              '<a href="https://www.netto-online.de/ViewMMPWishlist-AddStoreArticle?'+q+'">Test</a>'
              '<div class="grid-top-price"><span class="product__current-price tc-product-price">1,99</span></div>'
              '<div class="grid-app-price"><span class="product__current-price tc-product-price">1,49</span></div>'
              '</div></section>')
        ds=source("NETTO_MD","SALE",html,"https://www.netto-online.de/angebote/c-N07",
                  contentType="text/html")
        p=self.service.search_offers({**REQUEST,"retailerIds":["NETTO_MD"]},[ds])["observations"][0]["payload"]
        self.assertIsNone(p["article"]["quantity"])
        self.assertEqual(p["eg-preisdaten:advertisedUnitPrice"],"1 kg = 3,98 EUR")
        self.assertEqual(p["eg-preisdaten:conditionalPrices"][0]["priceCents"],149)
        self.assertEqual(p["priceCents"],199)


    def test_request_date_not_window_start_determines_validity(self):
        ds=fixture([r(fromDate="2026-11-03",untilDate="2026-11-07")])
        out=self.service.search_offers(
            {**REQUEST,"shoppingDate":"2026-11-05","windowStart":"2026-11-01",
             "windowEnd":"2026-11-06"},[ds])
        self.assertEqual(out["observations"][0]["payload"]["eg-preisdaten:targetDateStatus"],
                         "PUBLISHED_WINDOW")

    def test_store_selection_rejects_other_market_but_preserves_proper_scope(self):
        req={**REQUEST,"storeSelections":{"LIDL":{"storeId":"DE1"}}}
        one=fixture([r(id="a",scope="STORE_CONFIRMED",scopeId="DE1")],
                    storeId="DE1",scopeProof={"storeId":"DE1","sourceRef":"published-store"})
        two=fixture([r(id="b",scope="STORE_CONFIRMED",scopeId="DE2")],
                    storeId="DE2",scopeProof={"storeId":"DE2","sourceRef":"published-store"})
        out=self.service.search_offers(req,[one,two])
        self.assertEqual(len(out["observations"]),1)
        self.assertEqual(out["observations"][0]["payload"]["scope"]["storeId"],"DE1")
        self.assertIn("OUT_OF_SCOPE",[r["status"] for r in out["coverage"]])
        with self.assertRaises(DataError):
            self.service.search_offers({**REQUEST,"storeSelections":{"LIDL":{"storeId":""}}},[one])

    def test_lookup_price_matches_before_result_cap(self):
        ds=fixture([r(id=str(i)) for i in range(20)])
        req={**REQUEST,"maxResults":1}
        out=self.service.lookup_price(req,[ds],"19")
        self.assertEqual(len(out["observations"]),1)
        self.assertEqual(out["observations"][0]["payload"]["article"]["retailerArticleId"],"19")
        self.assertEqual(out["matchedCount"],1)
        self.assertFalse(out["outputTruncated"])

    def test_output_truncation_is_global_and_reported_without_faking_incomplete_source(self):
        ds=fixture([r(id=str(i)) for i in range(8)])
        out=self.service.search_offers({**REQUEST,"maxResults":2},[ds])
        self.assertEqual(out["matchedCount"],8)
        self.assertEqual(len(out["observations"]),2)
        self.assertTrue(out["outputTruncated"])
        self.assertEqual(out["coverage"][0]["status"],"PARSED_PARTIAL")

    def test_multi_quantity_text_is_not_silently_reduced_to_first_amount(self):
        self.assertIsNone(parse_quantity("500 g + 200 g gratis"))
        self.assertIsNone(parse_quantity("1 kg = 3,98 €"))
        self.assertIsNone(parse_quantity("200 g / 100 g"))
        self.assertEqual(parse_quantity("3 x 200 g")["amount"],600)

    def test_identical_price_different_observation_instant_retained(self):
        one=fixture([r()],observedAt="2026-10-31T09:00:00+01:00")
        two=fixture([r()],observedAt="2026-10-31T18:00:00+01:00")
        out=self.service.search_offers(REQUEST,[one,two])
        self.assertEqual(len(out["observations"]),2)
        self.assertNotEqual(out["observations"][0]["payload"]["observationId"],
                            out["observations"][1]["payload"]["observationId"])


    def test_netto_skipped_bad_tile_count_is_visible_in_coverage(self):
        from urllib.parse import urlencode
        good=urlencode({"SKU":"A1","Price":"1.99","ValidTo":"2026-10-31 23:59:59","Name":"Hafer"})
        broken=urlencode({"SKU":"A2","Price":"2.99","ValidTo":"2026-10-31 23:59:59","Name":"Hafer2"})
        def tile(pid,slug,display):
            return (f'<div class="tc-store-product-tile" data-ff-id="{pid}">'
                    f'<span class="tc-product-name">{slug}</span>'
                    f'<a href="https://www.netto-online.de/ViewMMPWishlist-AddStoreArticle?{good if pid=="A1" else broken}">Test</a>'
                    f'<div class="grid-top-price"><span class="product__current-price tc-product-price">{display}</span></div></div>')
        html='<section><h2>Filial-Angebote</h2>'+tile("A1","Hafer","1,99")+tile("A2","Hafer2","1,99")+'</section>'
        ds=source("NETTO_MD","SALE",html,"https://www.netto-online.de/angebote/c-N07",
                  contentType="text/html")
        out=self.service.search_offers({**REQUEST,"retailerIds":["NETTO_MD"]},[ds])
        self.assertEqual(len(out["observations"]),1)
        self.assertEqual(out["coverage"][0]["received"],2)
        self.assertEqual(out["coverage"][0]["parsed"],1)
        self.assertIn("PRICE_NAME_OR_SKU_MISMATCH",out["coverage"][0]["sourceWarnings"])

    def test_lidl_offer_unsupported_discount_type_reported_as_skipped(self):
        ds=source("LIDL","SALE",{"totalOffers":2,"offers":[
            {"id":"x","title":"Eis","category":"Store","offerType":"StoreSpecialPriceDiscount",
             "priceBox":{"largePartNumeric":1.49},
             "startValidityDate":"2026-10-31","endValidityDate":"2026-11-07"},
            {"id":"y","title":"3 für 2","category":"Store","offerType":"StoreXforYDiscount",
             "priceBox":{"largePartNumeric":2.49},
             "startValidityDate":"2026-10-31","endValidityDate":"2026-11-07"}]},
             "https://offers.lidlplus.com/app/api/v4/DE/DE7434/offers",storeId="DE7434")
        out=self.service.search_offers(REQUEST,[ds])
        self.assertEqual(len(out["observations"]),1)
        self.assertEqual(out["coverage"][0]["received"],2)
        self.assertEqual(out["coverage"][0]["parsed"],1)
        self.assertFalse(out["coverage"][0]["complete"])

    def test_transport_timeouts_and_cancellation_have_specific_codes(self):
        for err,expected in [("TIMEOUT","TIMEOUT"),("NETWORK","NETWORK_ERROR"),
                             ("TLS","TLS_ERROR"),("CANCELLED","CANCELLED")]:
            ds=fixture([r()],transportError=err)
            result=self.service.search_offers(REQUEST,[ds])
            self.assertEqual(result["observations"],[])
            self.assertEqual(result["errors"][0]["code"],expected)
        ds=fixture([r()],transportError="UPSTREAM_MAGIC")
        self.assertEqual(self.service.search_offers(REQUEST,[ds])["errors"][0]["code"],
                         "INVALID_TRANSPORT_ERROR")


    def test_reference_price_not_as_a_paid_past_or_regular_price(self):
        ds=source("LIDL","REGULAR",{"results":[
            {"id":"x","title":"Milch","price":0.85,"oldPrice":1.19}]},
            "https://product-catalog.lidlplus.com/api/app/v1/DE/store/DE7434/search",
            mode="search",storeId="DE7434",snapshotDate=DAY)
        p=self.service.search_catalog_prices(REQUEST,[ds])["observations"][0]["payload"]
        self.assertEqual(p["priceKind"],"CURRENT_DISPLAYED")
        self.assertEqual(p["priceCents"],85)
        self.assertEqual(p["eg-preisdaten:referenceOldPriceCents"],119)
        self.assertIs(p["eg-preisdaten:hasDiscount"],True)

    def test_aldi_sued_strikethrough_price_only_text(self):
        ds=source("ALDI_SUED","REGULAR",{"data":[{"sku":"X","name":"Haferflocken",
             "price":{"amountRelevant":99,"currencyCode":"EUR","wasPriceDisplay":"1,29 €"}}]},
             "https://api.aldi-sued.de/v3/product-search",storeId="B384")
        p=self.service.search_catalog_prices({**REQUEST,"retailerIds":["ALDI_SUED"]},[ds])["observations"][0]["payload"]
        self.assertEqual(p["priceKind"],"CURRENT_DISPLAYED")
        self.assertEqual(p["eg-preisdaten:referenceOldText"],"1,29 €")
        self.assertIsNone(p["eg-preisdaten:referenceOldPriceCents"])

    def test_verified_barcode_requires_valid_check_digit_and_never_guesses(self):
        valid=fixture([r(id="v",gtin="4000540200300"),r(id="i",gtin="4000540200301")])
        values=[x["payload"]["article"]["gtin"] for x in self.service.search_offers(REQUEST,[valid])["observations"]]
        self.assertEqual(values,["4000540200300",None])


    def test_aldi_nord_base_price_retains_exact_unit_without_synthetic_conversion(self):
        p={"objectID":"A","name":"Hafer","currentPrice":{"priceValue":0.99,
           "basePrice":[{"basePriceScale":"kg","basePriceValue":1.98}]}}
        body={"props":{"pageProps":{"algoliaState":{"initialResults":{
              "an_prd_de_de_products2":{"results":[{"nbHits":1,"nbPages":1,"page":0,"hits":[p]}]}}}}}}
        ds=source("ALDI_NORD","REGULAR",'<script id="__NEXT_DATA__">'+json.dumps(body)+'</script>',
            "https://www.aldi-nord.de/sortiment/kategorie",contentType="text/html")
        out=self.service.search_catalog_prices({**REQUEST,"retailerIds":["ALDI_NORD"]},[ds])
        self.assertFalse(out["errors"])
        self.assertEqual(out["observations"][0]["payload"]["eg-preisdaten:reportedBaseUnitPrices"],
                         [{"basis":"kg","priceEur":"1.98"}])

    def test_source_urls_with_credential_fields_rejected_without_logging_them(self):
        ds=source("REWE","REGULAR",{"products":[]},
                  "https://www.rewe.de/api/stationary-product-search/products?token=DO_NOT_LOG",
                  storeId="840174")
        out=self.service.search_catalog_prices({**REQUEST,"retailerIds":["REWE"]},[ds])
        self.assertEqual(out["errors"][0]["code"],"INVALID_SOURCE")
        self.assertNotIn("DO_NOT_LOG",json.dumps(out))
        ds["sourceUrl"]="https://www.rewe.de:bad/api/stationary-product-search/products"
        out=self.service.search_catalog_prices({**REQUEST,"retailerIds":["REWE"]},[ds])
        self.assertEqual(out["errors"][0]["code"],"INVALID_SOURCE")

    def test_rewe_discount_not_unproven_sale(self):
        ds=source("REWE","REGULAR",{"products":[{"id":"X","title":"Hafer",
            "pricing":{"current":119,"regular":139,"refund":0}}]},
            "https://www.rewe.de/api/stationary-product-search/products",
            storeId="840174")
        out=self.service.search_catalog_prices({**REQUEST,"retailerIds":["REWE"]},[ds])
        self.assertEqual(len(out["observations"]),2)
        by_type={x["payload"]["priceKind"]:x["payload"] for x in out["observations"]}
        self.assertEqual(by_type["CURRENT_DISPLAYED"]["priceCents"],119)
        self.assertIs(by_type["CURRENT_DISPLAYED"]["eg-preisdaten:hasDiscount"],True)
        self.assertEqual(by_type["LISTED_REGULAR"]["priceCents"],139)
        self.assertNotIn("SALE",by_type)


    def test_region_only_dataset_must_not_leak_into_unmapped_store_selection(self):
        ds=fixture([r(id="p",scope="REGION_CONFIRMED",scopeId="R2")],
                   retailer="PENNY",regionId="R2",
                   scopeProof={"regionId":"R2","sourceRef":"official-selling-region"})
        req={**REQUEST,"retailerIds":["PENNY"],
             "storeSelections":{"PENNY":{"storeId":"DE1"}}}
        out=self.service.search_offers(req,[ds])
        self.assertEqual(out["observations"],[])
        self.assertIn("OUT_OF_SCOPE",[c["status"] for c in out["coverage"]])
        req["storeSelections"]["PENNY"]["regionId"]="R2"
        out=self.service.search_offers(req,[ds])
        self.assertEqual(len(out["observations"]),1)

    def test_mixed_store_rows_dont_cross_selected_market_even_when_source_claims_store(self):
        ds=fixture([r(id="A",scope="STORE_CONFIRMED",scopeId="DE1"),
                    r(id="B",scope="STORE_CONFIRMED",scopeId="DE2")],
                   storeId="DE1",scopeProof={"storeId":"DE1","sourceRef":"official-store"})
        req={**REQUEST,"storeSelections":{"LIDL":{"storeId":"DE1"}}}
        out=self.service.search_offers(req,[ds])
        self.assertEqual([x["payload"]["article"]["retailerArticleId"] for x in out["observations"]],["A"])


    def test_exact_gtin_filter_only_matches_valid_verified_barcode(self):
        ds=fixture([r(id="v",gtin="4000540200300"),r(id="i",gtin="4000540200301"),
                    r(id="none",gtin=None)])
        out=self.service.search_offers({**REQUEST,"gtin":"4000540200300"},[ds])
        self.assertEqual([x["payload"]["article"]["retailerArticleId"] for x in out["observations"]],["v"])
        with self.assertRaises(DataError) as c:
            self.service.search_offers({**REQUEST,"gtin":"4000540200301"},[ds])
        self.assertEqual(c.exception.code,"INVALID_GTIN")

    def test_exact_foodtype_filter_without_invented_category_assignment(self):
        ds=fixture([r(id="a",foodTypeId="oats-fine"),r(id="b",foodTypeId="rice"),
                    r(id="c",foodTypeId=None)])
        out=self.service.search_offers({**REQUEST,"foodTypeId":"oats-fine"},[ds])
        self.assertEqual([x["payload"]["article"]["retailerArticleId"] for x in out["observations"]],["a"])
        self.assertEqual(out["observations"][0]["payload"]["article"]["foodTypeId"],"oats-fine")
        ds=fixture([r(foodTypeId=42)])
        out=self.service.search_offers(REQUEST,[ds])
        self.assertEqual(out["errors"][0]["code"],"INVALID_ID")
        self.assertEqual(out["observations"],[])


    def test_base_price_crosscheck_exact_arithmetic_and_rounding(self):
        def item(id,price,pack,basis,value,deposit=None):
            return r(id=id,price=price,pack=pack,deposit=deposit,
                     reportedBaseUnitPrices=[{"basis":basis,"priceEur":value}])
        rows=[
            item("correct","0.99","500 g","kg","1.98"),
            item("different","1.99","500 g","kg","1.98"),
            item("volume","1.20","0,75 l","l","1.60"),
            item("piece","1.00","1 Stück","kg","1.00"),
            item("deposit","1.20","0,75 l","l","1.60","0.25"),
            item("unknown",None,"500 g","kg","1.98")
        ]
        out=self.service.search_offers(REQUEST,[fixture(rows)])
        by_id={p["payload"]["article"]["retailerArticleId"]:
               p["payload"]["eg-preisdaten:basePriceCheck"] for p in out["observations"]}
        self.assertEqual(by_id,{"correct":"CONSISTENT_WITH_DISPLAYED_QUANTITY",
                                "different":"MISMATCH","volume":"CONSISTENT_WITH_DISPLAYED_QUANTITY",
                                "piece":"NOT_COMPARABLE","deposit":"DEPOSIT_UNCERTAIN",
                                "unknown":"PRICE_UNKNOWN"})

    def test_bad_reported_base_price_rejects_source_dataset_atomically(self):
        ds=fixture([r(id="good"),r(id="bad",reportedBaseUnitPrices=[
            {"basis":"kg","priceEur":"NaN"}])])
        out=self.service.search_offers(REQUEST,[ds])
        self.assertEqual(out["observations"],[])
        self.assertEqual(out["errors"][0]["code"],"INVALID_QUANTITY")


    def test_malformed_metadata_rejects_entire_snapshot_before_schema_violation(self):
        samples=[r(id="first"),r(id="second",brand=123)]
        out=self.service.search_offers(REQUEST,[fixture(samples)])
        self.assertEqual(out["errors"][0]["code"],"INVALID_FIELD")
        self.assertEqual(out["observations"],[])
        samples=[r(id="first"),r(id=["bad"])]
        out=self.service.search_offers(REQUEST,[fixture(samples)])
        self.assertEqual(out["errors"][0]["code"],"INVALID_ID")
        self.assertEqual(out["observations"],[])
        ds=fixture([r()],scopeProof="not-an-object")
        out=self.service.search_offers(REQUEST,[ds])
        self.assertEqual(out["errors"][0]["code"],"INVALID_SCOPE")

    def test_malformed_request_and_origin_fail_without_uncaught_exceptions(self):
        for request in (None,{},{"shoppingDate":DAY,"retailerIds":[{"bad":1}]}):
            with self.assertRaises(DataError):
                self.service.search_offers(request,[])
        with self.assertRaises(DataError):
            self.service.search_offers(REQUEST,{"bad":"dataset"})
        ds=fixture([r()],origin=99)
        self.assertEqual(self.service.search_offers(REQUEST,[ds])["errors"][0]["code"],
                         "INVALID_SOURCE")

    def test_extreme_pack_text_is_unknown_not_resource_intensive_or_guessed(self):
        self.assertIsNone(parse_quantity("9"*260+" kg"))
        self.assertIsNone(parse_quantity("1001 x 200 g"))
        self.assertIsNone(parse_quantity("999999999 kg"))


    def test_same_article_and_price_with_different_pack_and_deposit_stays_distinct(self):
        source_rows=[
            r(id="SKU1",pack="250 g",deposit=None,conditions=["normal"]),
            r(id="SKU1",pack="500 g",deposit=None,conditions=["normal"]),
            r(id="SKU1",pack="250 g",deposit="0.25",conditions=["normal"]),
            r(id="SKU1",pack="250 g",deposit=None,conditions=["requires card"]),
        ]
        out=self.service.search_offers(REQUEST,[fixture(source_rows)])
        self.assertEqual(out["errors"],[])
        self.assertEqual(len(out["observations"]),4)
        ids=[x["payload"]["observationId"] for x in out["observations"]]
        self.assertEqual(len(ids),len(set(ids)))
        dupe=self.service.search_offers(REQUEST,[fixture([source_rows[0],source_rows[0]])])
        self.assertEqual(len(dupe["observations"]),1)

    def test_different_app_price_same_public_price_does_not_collapse(self):
        rows=[r(id="SKU1",conditionalPrices=[
             {"priceCents":79,"access":"LIDL_PLUS","evidence":"lidlPlusOffer.price",
              "termsVerified":False}]),
              r(id="SKU1",conditionalPrices=[
             {"priceCents":89,"access":"LIDL_PLUS","evidence":"lidlPlusOffer.price",
              "termsVerified":False}])]
        out=self.service.search_offers(REQUEST,[fixture(rows)])
        self.assertEqual(len(out["observations"]),2)
        self.assertEqual({x["payload"]["priceCents"] for x in out["observations"]},{125})

    def test_aldi_nord_catalogue_dates_not_discarded(self):
        import datetime
        start=int(datetime.datetime(2026,11,2,12,tzinfo=datetime.timezone.utc).timestamp())
        end=int(datetime.datetime(2026,11,8,12,tzinfo=datetime.timezone.utc).timestamp())
        product={"objectID":"A","name":"Hafer","currentPrice":{
                 "priceValue":0.99,"validFrom":start,"validUntil":end}}
        data={"props":{"pageProps":{"algoliaState":{"initialResults":{
              "an_prd_de_de_products2":{"results":[{"nbHits":1,"nbPages":1,
                  "page":0,"hits":[product]}]}}}}}}
        ds=source("ALDI_NORD","REGULAR",'<script id="__NEXT_DATA__" type="application/json">'+json.dumps(data)+'</script>',
                  "https://www.aldi-nord.de/sortiment/hafer",contentType="text/html")
        out=self.service.search_catalog_prices(
             {**REQUEST,"retailerIds":["ALDI_NORD"],"shoppingDate":"2026-11-05",
              "windowStart":"2026-11-02","windowEnd":"2026-11-09"},[ds])
        self.assertEqual(out["errors"],[])
        p=out["observations"][0]["payload"]
        self.assertEqual((p["validFrom"],p["validUntil"]),("2026-11-02","2026-11-08"))
        self.assertEqual(p["eg-preisdaten:targetDateStatus"],"PUBLISHED_WINDOW")

    def test_conflicting_price_kind_and_out_of_range_cents_fail_closed(self):
        for bad_kind,channel in [("REFERENCE_OLD","SALE"),("ONLINE_LISTED","SALE"),
                                 ("SALE","REGULAR"),("HISTORICAL_PAID","REGULAR")]:
            ds=fixture([r(sourcePriceKind=bad_kind)],channel=channel)
            out=self.service.search({**REQUEST},[ds])
            self.assertEqual(out["observations"],[])
            self.assertEqual(out["errors"][0]["code"],"INVALID_PRICE_KIND")
        for field in ("priceCents","depositCents"):
            ds=fixture([r(**{field:100_000_001})])
            out=self.service.search_offers(REQUEST,[ds])
            self.assertEqual(out["errors"][0]["code"],"INVALID_PRICE")
            self.assertEqual(out["observations"],[])

    def test_malformed_source_discount_flags_rejected(self):
        ds=fixture([r(id="safe"),r(id="bad",hasDiscount="false")])
        out=self.service.search_offers(REQUEST,[ds])
        self.assertEqual(out["errors"][0]["code"],"INVALID_FIELD")
        self.assertEqual(out["observations"],[])

if __name__=="__main__":
    unittest.main()
