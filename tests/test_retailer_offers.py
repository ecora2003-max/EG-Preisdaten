"""Offline contract tests: no network and no third-party dependencies."""
import json
import unittest
from decimal import Decimal
from adapters.retailer_offers import (
    Scope, Offer, money, penny_store, penny_offers, penny_merge_categories, aldi_nord_next,
    kaufland_offers, lidl_flyer, lidl_store_offers, edeka_offers, netto_store_prospects, netto_status
)


class RetailerContracts(unittest.TestCase):
    def test_money_decimal_and_comma(self):
        self.assertEqual(money("1.69"), Decimal("1.69"))
        self.assertEqual(money("1,49"), Decimal("1.49"))
        self.assertEqual(money({"amount":1.29}), Decimal("1.29"))
        self.assertEqual(money("1.234,56"), Decimal("1234.56"))
        self.assertIsNone(money("1.29²"))
        self.assertIsNone(money("ab 0.99"))
        self.assertIsNone(money("-1.00"))

    def test_penny_resolves_week_region_correctly(self):
        markets=[{"wwIdent":"A1","sellingRegion":"REG-OLD","nextWeekSellingRegion":"REG-NEW"},
                 {"wwIdent":"B2","sellingRegion":"OTHER","nextWeekSellingRegion":""}]
        self.assertEqual(penny_store(markets,"A1",week="current")["region"],"REG-OLD")
        self.assertEqual(penny_store(markets,"A1",week="next")["region"],"REG-NEW")
        with self.assertRaises(ValueError):penny_store(markets,"B2",week="next")
        with self.assertRaises(ValueError):penny_store(markets,"Z",week="next")

    def test_penny_app_price_separate(self):
        offers=penny_offers({"offerTiles":[
            {"uuid":"a","title":"LEERDAMMER Käse","price":"1.49","benefitPrice":"1.29²","quantity":"je 140 g"},
            {"uuid":"a","title":"duplicate","price":"99.99"},
            {"uuid":"bad","title":"Mystery","price":None},
        ]},region="15A-01-56",week_start="2026-11-02")
        self.assertEqual(len(offers),1)
        self.assertEqual(offers[0].price_eur,Decimal("1.49"))
        self.assertEqual(offers[0].price_condition,"1.29²")
        self.assertIsNone(offers[0].valid_to)
        self.assertEqual(offers[0].scope,Scope.REGION)

    def test_penny_multi_category_deduplication(self):
        a={"offerTiles":[{"uuid":"a","title":"Äpfel","price":"1.49"}]}
        b={"offerTiles":[{"uuid":"a","title":"Äpfel","price":"1.49"},
                          {"uuid":"b","title":"Tomaten","price":"1.29"}]}
        offers=penny_merge_categories({"obst-und-gemuese":a,"top-angebote":b},
                                     region="15A-01-56",week_start="2026-11-02")
        self.assertEqual(len(offers),2)
        with self.assertRaises(ValueError):
            penny_merge_categories({"A":a,"B":{"offerTiles":[{"uuid":"a","title":"Äpfel","price":"2.99"}]}},
                                  region="15A-01-56",week_start="2026-11-02")

    def test_aldi_nord_embedded_next_week_and_no_store_guarantee(self):
        p={"props":{"pageProps":{"apiData":json.dumps([["OFFER_GET",{
            "req":{"locale":"de","week":"next"},
            "res":{"algoliaDataMap":{"100":{"objectID":"100","name":"Erdnüsse",
                 "currentPrice":{"priceValue":1.49,"validFromLocalDate":"2026-11-02","validUntilLocalDate":"2026-11-07"},"salesUnit":"200 g"},"200":{"name":"NotPriced"}}}
        }]])}}}
        v=aldi_nord_next(p)
        self.assertEqual(len(v),1)
        self.assertEqual(v[0].title,"Erdnüsse")
        self.assertEqual(v[0].scope,Scope.CHAIN)
        self.assertEqual(v[0].valid_from,"2026-11-02")
        self.assertIsNone(v[0].scope_id)

    def test_aldi_nord_wrong_week_rejected(self):
        with self.assertRaises(ValueError):aldi_nord_next([["OFFER_GET",{"req":{"week":"current"},"res":{}}]])

    def test_kaufland_intersects_actual_store_list(self):
        payload={"cycles":[{"categories":[{"offers":[
            {"klNr":"A","title":"Tofu","price":1.99,"unit":"200 g","salesFrom":"2026-11-02","salesTo":"2026-11-07"},
            {"klNr":"B","title":"Apfel","price":0.99,"salesFrom":"2026-11-02","salesTo":"2026-11-07"},
            {"klNr":"C","title":"Too late","price":4.99,"salesFrom":"2026-11-09","salesTo":"2026-11-14"},
        ]}]}]}
        listing=[{"klNr":"A","dateFrom":"2026-11-02","dateTo":"2026-11-07"},
                 {"klNr":"C","dateFrom":"2026-11-02","dateTo":"2026-11-07"}]
        offers=kaufland_offers(payload,listing,store_id="DE5220",first_day="2026-11-02",last_day="2026-11-08")
        self.assertEqual([o.title for o in offers],["Tofu"])
        self.assertEqual(offers[0].scope,Scope.STORE)
        with self.assertRaises(ValueError):kaufland_offers(payload,listing,store_id="Berlin",first_day="2026-11-02",last_day="2026-11-08")

    def test_kaufland_embedded_html_supported(self):
        raw='<html><script>const foo={"offerData":{"cycles":[{"categories":[{"offers":[{"klNr":"1","title":"Linsen","price":1.29}]}]}]}};</script></html>'
        a=kaufland_offers(raw,[{"klNr":"1","dateFrom":"2026-11-02","dateTo":"2026-11-07"}],
                          store_id="DE4620",first_day="2026-11-02",last_day="2026-11-08")
        self.assertEqual(len(a),1)
        self.assertEqual(a[0].scope_id,"DE4620")

    def test_lidl_flyer_must_not_pretend_product_is_store_verified(self):
        raw={"flyer":{"offerStartDate":"2026-11-02","offerEndDate":"2026-11-07",
                      "regions":[{"code":"0"}],"products":{"P1":{"title":"LUPILU Overall","price":"19.99"}}}}
        a=lidl_flyer(raw,expected_start="2026-11-02",confirmed_region_code="0")
        self.assertEqual(len(a),1)
        self.assertEqual(a[0].scope,Scope.UNVERIFIED)
        with self.assertRaises(ValueError):lidl_flyer(raw,expected_start="2026-11-09")

    def test_lidl_store_specific_shelf_prices_and_excludes_online(self):
        common={"startValidityDate":"2026-10-29T00:00:01+00:00",
                "endValidityDate":"2026-10-31T23:59:59+00:00"}
        p={"totalOffers":3,"offers":[
            dict(common,id="a",title="Mövenpick Eis",category="Store",
                 offerType="StoreSpecialPriceDiscount",packaging="850 ml",
                 priceBox={"largePartNumeric":1.49,"smallPartNumeric":3.99}),
            dict(common,id="b",title="Online-Schrank",category="Online",
                 offerType="OnlineShopSpecialPriceDiscount",priceBox={"largePartNumeric":99.0}),
            dict(common,id="c",title="3 für 2",category="Store",
                 offerType="StoreXforYDiscount",priceBox={"largePartNumeric":2.00})
        ]}
        offers=lidl_store_offers(p,store_key="DE7434")
        self.assertEqual(len(offers),1)
        self.assertEqual(offers[0].price_eur,Decimal("1.49"))
        self.assertEqual(offers[0].scope,Scope.STORE)
        self.assertEqual(offers[0].scope_id,"DE7434")
        with self.assertRaises(ValueError):
            lidl_store_offers(p,store_key="7434")

    def test_edeka_documented_schema_is_not_live_verified(self):
        a=edeka_offers({"docs":[{"titel":"Tofu","preis":"2,29","gueltig_von":"2026-11-02","gueltig_bis":"2026-11-07"}]},market_id="1234")
        self.assertEqual(len(a),1)
        self.assertEqual(a[0].scope,Scope.UNVERIFIED)

    def test_edeka_official_market_scope_millisecond_dates(self):
        payload={"national":False,"gueltig_von":1792972800000,
                 "gueltig_bis":1793404800000,"docs":[
                    {"angebotid":6433527,"titel":"Himbeeren","preis":1.99,
                     "beschreibung":"125 g Packung","gueltig_bis":1793404800000},
                    {"angebotid":6433527,"titel":"Himbeeren","preis":1.99}]}
        offers=edeka_offers(payload,market_id="10003451")
        self.assertEqual(len(offers),1)
        self.assertEqual(offers[0].scope,Scope.STORE)
        self.assertEqual(offers[0].scope_id,"10003451")
        self.assertEqual(offers[0].valid_from,"2026-10-26")
        self.assertEqual(offers[0].valid_to,"2026-10-31")
        self.assertEqual(offers[0].price_eur,Decimal("1.99"))

    def test_edeka_national_fallback_not_store_confirmed(self):
        payload={"national":True,"docs":[
            {"angebotid":1,"titel":"Nationale Butter","preis":1.49}]}
        offers=edeka_offers(payload,market_id="1")
        self.assertEqual(len(offers),1)
        self.assertEqual(offers[0].scope,Scope.CHAIN)
        self.assertIsNone(offers[0].scope_id)

    def test_netto_official_store_specific_prospects(self):
        snippet='''<div class="your-store__info__address">
           Netto Marken-Discount<br/>Wilmersdorfer Str. 46<br/>10627 Berlin
           </div><a id="filialangebote-KW45"
            href="https://wochenprospekt.netto-online.de/hz45_besb/?storeid=7679">Prospekt</a>'''
        got=netto_store_prospects(snippet,store_id="7679")
        self.assertEqual(len(got),1)
        self.assertEqual(got[0]["iso_week"],45)
        self.assertEqual(got[0]["store_id"],"7679")
        self.assertEqual(got[0]["applicability"],"STORE_PROSPECT_CONFIRMED")
        self.assertFalse(got[0]["offers_parsed"])
        with self.assertRaises(ValueError):
            netto_store_prospects(snippet,store_id="8135")
        with self.assertRaises(ValueError):
            netto_store_prospects(snippet.replace("wochenprospekt.netto-online.de","untrusted.example"),store_id="7679")

    def test_netto_fails_closed(self):
        self.assertEqual(netto_status()["status"],"NOT_IMPLEMENTATION_READY")


if __name__=="__main__":
    unittest.main()
