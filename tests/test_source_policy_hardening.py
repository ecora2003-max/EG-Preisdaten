"""Offline source/retailer policy tests; no HTTP and no private data."""
import copy
import unittest
from price_module import PriceService, provider_registry

DAY = "2026-10-31"
NOW = "2026-10-31T12:00:00+01:00"
HOSTS = {"ALDI_NORD": "www.aldi-nord.de", "ALDI_SUED": "www.aldi-sued.de",
         "REWE": "www.rewe.de", "LIDL": "www.lidl.de",
         "PENNY": "www.penny.de", "KAUFLAND": "www.kaufland.de",
         "EDEKA": "www.edeka.de", "NETTO_MD": "www.netto-online.de"}
TARGETED = ("ALDI_NORD", "ALDI_SUED", "REWE", "LIDL")
OFFERS_ONLY = ("PENNY", "KAUFLAND", "EDEKA", "NETTO_MD")


def req(retailer, **extra):
    return {"shoppingDate": DAY, "retailerIds": [retailer], "maxResults": 5, **extra}


def row(**extra):
    return {"id": "TEST", "label": "Haferflocken", "price": "1.29",
            "pack": "500 g", "fromDate": DAY, "untilDate": "2026-11-06", **extra}


def fixture(retailer, channel="SALE", **extra):
    return {"retailerId": retailer, "channel": channel, "fixture": True,
            "format": "synthetic-fixture", "origin": "synthetic-fixture",
            "observedAt": NOW, "body": [row()], **extra}


def official(retailer, channel="SALE", **extra):
    return {"retailerId": retailer, "channel": channel, "origin": "official-retailer",
            "observedAt": NOW, "sourceUrl": "https://" + HOSTS[retailer] + "/offers",
            "contentType": "application/json", "httpStatus": 200, "body": {}, **extra}


class SourcePolicyHardening(unittest.TestCase):
    def setUp(self):
        self.service = PriceService()

    def test_all_eight_reject_foreign_hosts_userinfo_http_and_nonstandard_ports(self):
        for retailer in HOSTS:
            other = next(host for name, host in HOSTS.items() if name != retailer)
            urls = ("https://" + other + "/offers",
                    "https://user:secret@" + HOSTS[retailer] + "/offers",
                    "https://" + HOSTS[retailer] + ":8443/offers",
                    "http://" + HOSTS[retailer] + "/offers")
            for url in urls:
                with self.subTest(retailer=retailer, url=url):
                    result = self.service.search_offers(
                        req(retailer), [official(retailer, sourceUrl=url)])
                    self.assertEqual(result["observations"], [])
                    self.assertEqual([e["code"] for e in result["errors"]], ["INVALID_SOURCE"])

    def test_four_regular_retailers_reject_credential_aliases_and_url_fragments(self):
        for retailer in TARGETED:
            urls = ("https://" + HOSTS[retailer] + "/search?authToken=synthetic",
                    "https://" + HOSTS[retailer] + "/search?session_id=synthetic",
                    "https://" + HOSTS[retailer] + "/search?x-api-key=synthetic",
                    "https://" + HOSTS[retailer] + "/search#access_token=synthetic",
                    " https://" + HOSTS[retailer] + "/search",
                    "https://" + HOSTS[retailer] + "/search\n")
            for url in urls:
                with self.subTest(retailer=retailer, url=url):
                    snapshot = official(retailer, channel="REGULAR", sourceUrl=url)
                    saved = copy.deepcopy(snapshot)
                    result = self.service.search_product_prices(
                        req(retailer, query="Haferflocken"), [snapshot])
                    self.assertEqual(result["observations"], [])
                    self.assertEqual([e["code"] for e in result["errors"]], ["INVALID_SOURCE"])
                    self.assertEqual(result["coverage"][0]["status"], "ERROR")
                    self.assertEqual(snapshot, saved)

    def test_targeted_four_positive_offer_only_four_negative_and_offers_positive(self):
        for retailer in TARGETED:
            with self.subTest(retailer=retailer):
                ds = fixture(retailer, channel="REGULAR",
                             body=[row(sourcePriceKind="LISTED_REGULAR")])
                result = self.service.search_product_prices(
                    req(retailer, query="Haferflocken"), [ds])
                self.assertEqual(result["errors"], [])
                self.assertEqual(len(result["observations"]), 1)
                self.assertEqual(result["observations"][0]["payload"]["priceKind"],
                                 "LISTED_REGULAR")
                self.assertNotEqual(provider_registry()[retailer]["rights"], "PERMITTED")
        for retailer in OFFERS_ONLY:
            with self.subTest(retailer=retailer):
                ds = fixture(retailer, channel="REGULAR",
                             body=[row(sourcePriceKind="LISTED_REGULAR")])
                result = self.service.search_product_prices(
                    req(retailer, query="Haferflocken"), [ds])
                self.assertEqual(result["observations"], [])
                self.assertEqual([e["code"] for e in result["errors"]],
                                 ["CAPABILITY_NOT_ALLOWED"])
                self.assertEqual(result["coverage"][0]["status"], "POLICY_DENIED")
                offers = self.service.search_offers(req(retailer), [fixture(retailer)])
                self.assertEqual(len(offers["observations"]), 1)
                self.assertEqual(offers["observations"][0]["payload"]["priceKind"], "SALE")

    def test_regular_store_scope_needs_matching_explicit_provenance(self):
        for retailer in TARGETED:
            with self.subTest(retailer=retailer):
                ds = fixture(retailer, channel="REGULAR", storeId="S1",
                             body=[row(sourcePriceKind="LISTED_REGULAR",
                                       scope="STORE_CONFIRMED", scopeId="S1")])
                selection = req(retailer, query="Haferflocken",
                                storeSelections={retailer: {"storeId": "S1"}})
                unproven = self.service.search_product_prices(selection, [ds])
                self.assertEqual(unproven["observations"][0]["payload"]["scope"]["scopeType"],
                                 "UNKNOWN")
                proven = copy.deepcopy(ds)
                proven["scopeProof"] = {"storeId": "S1", "sourceRef": "synthetic-proof"}
                accepted = self.service.search_product_prices(selection, [proven])
                self.assertEqual(accepted["observations"][0]["payload"]["scope"]["scopeType"],
                                 "STORE_CONFIRMED")
                other = self.service.search_product_prices(
                    req(retailer, query="Haferflocken",
                        storeSelections={retailer: {"storeId": "S2"}}), [proven])
                self.assertEqual(other["observations"], [])
                self.assertEqual([c["status"] for c in other["coverage"]],
                                 ["OUT_OF_SCOPE", "NO_MATCHING_SCOPE"])

    def test_all_eight_app_display_remains_rights_fail_closed(self):
        for retailer in HOSTS:
            with self.subTest(retailer=retailer):
                result = self.service.search_offers(
                    req(retailer, usageMode="APP_DISPLAY"),
                    [official(retailer, rightsStatus="PERMITTED",
                              licenseRef="unverified-synthetic-claim")])
                self.assertEqual(result["observations"], [])
                self.assertEqual([e["code"] for e in result["errors"]],
                                 ["RIGHTS_NOT_CLEARED"])


if __name__ == "__main__":
    unittest.main()
