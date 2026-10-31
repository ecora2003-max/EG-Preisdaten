"""ADR-016 offline security and scope matrix; no HTTP or user data."""
import copy
import unittest

from price_module import PriceService, provider_registry
from price_module.service import DataError

DAY = "2026-10-31"
NOW = "2026-10-31T12:00:00+01:00"
HOSTS = {
    "ALDI_NORD": "www.aldi-nord.de",
    "ALDI_SUED": "www.aldi-sued.de",
    "LIDL": "www.lidl.de",
    "REWE": "www.rewe.de",
    "PENNY": "www.penny.de",
    "KAUFLAND": "www.kaufland.de",
    "EDEKA": "www.edeka.de",
    "NETTO_MD": "www.netto-online.de",
}


def request(retailer, **changes):
    return {"retailerIds": [retailer], "shoppingDate": DAY, "maxResults": 20, **changes}


def row(article_id="X1", **changes):
    return {"id": article_id, "label": "Haferflocken", "price": "1.29",
            "pack": "500 g", "fromDate": DAY, "untilDate": "2026-11-06",
            **changes}


def synthetic(retailer, channel="SALE", rows=None, **changes):
    return {"retailerId": retailer, "channel": channel, "fixture": True,
            "format": "synthetic-fixture", "origin": "synthetic-fixture",
            "observedAt": NOW, "body": [row()] if rows is None else rows,
            **changes}


def official(retailer, channel="SALE", **changes):
    return {"retailerId": retailer, "channel": channel,
            "origin": "official-retailer", "observedAt": NOW,
            "sourceUrl": "https://" + HOSTS[retailer] + "/offers",
            "contentType": "application/json", "httpStatus": 200,
            "body": {}, **changes}


class RightsAndStorePolicyMatrix(unittest.TestCase):
    def setUp(self):
        self.service = PriceService()

    def test_all_eight_official_app_snapshots_fail_closed_even_with_claimed_permission(self):
        for retailer in HOSTS:
            with self.subTest(retailer=retailer):
                snapshot = official(retailer, rightsStatus="PERMITTED",
                                    licenseRef="invented-blanket-license",
                                    usageScope="APP_DISPLAY")
                saved = copy.deepcopy(snapshot)
                result = self.service.search_offers(
                    request(retailer, usageMode="APP_DISPLAY"), [snapshot])
                self.assertEqual(result["observations"], [])
                self.assertEqual([e["code"] for e in result["errors"]],
                                 ["RIGHTS_NOT_CLEARED"])
                self.assertEqual(result["coverage"][0]["status"], "ERROR")
                self.assertNotEqual(provider_registry()[retailer]["rights"], "PERMITTED")
                self.assertEqual(snapshot, saved)

    def test_mixed_app_usage_keeps_synthetic_fixture_but_not_official_snapshot(self):
        fixture = synthetic("LIDL", rows=[row("DEMO")])
        external = official("LIDL", rightsStatus="PERMITTED")
        result = self.service.search_offers(
            request("LIDL", usageMode="APP_DISPLAY"), [fixture, external])
        self.assertEqual(len(result["observations"]), 1)
        self.assertEqual(result["observations"][0]["payload"]["article"]["retailerArticleId"], "DEMO")
        self.assertEqual(result["observations"][0]["payload"]["source"]["origin"], "synthetic-fixture")
        self.assertEqual([e["code"] for e in result["errors"]], ["RIGHTS_NOT_CLEARED"])
        self.assertEqual([c["status"] for c in result["coverage"]],
                         ["PARSED_PARTIAL", "ERROR"])

    def test_private_user_history_is_not_a_retailer_source_mode(self):
        with self.assertRaises(DataError) as caught:
            self.service.search_offers(
                request("LIDL", usageMode="PRIVATE_USER_HISTORY"),
                [synthetic("LIDL")])
        self.assertEqual(caught.exception.code, "INVALID_REQUEST")

    def test_four_offer_only_retailers_cannot_smuggle_regular_kind_through_sale(self):
        for retailer in ("PENNY", "KAUFLAND", "EDEKA", "NETTO_MD"):
            with self.subTest(retailer=retailer):
                snapshot = synthetic(retailer, rows=[
                    row("A", sourcePriceKind="CURRENT_DISPLAYED")])
                result = self.service.search_offers(request(retailer), [snapshot])
                self.assertEqual(result["observations"], [])
                self.assertEqual([e["code"] for e in result["errors"]],
                                 ["INVALID_PRICE_KIND"])
                self.assertEqual(result["coverage"][0]["status"], "ERROR")

    def test_store_scope_requires_exact_proof_and_never_crosses_two_markets(self):
        for retailer in HOSTS:
            with self.subTest(retailer=retailer):
                snapshot = synthetic(
                    retailer, rows=[row("S1", scope="STORE_CONFIRMED", scopeId="S1"),
                                    row("S2", scope="STORE_CONFIRMED", scopeId="S2")],
                    storeId="S1", scopeProof={"storeId": "S1", "sourceRef": "synthetic-store-proof"})
                selection = request(retailer, storeSelections={retailer: {"storeId": "S1"}})
                result = self.service.search_offers(selection, [snapshot])
                self.assertEqual(len(result["observations"]), 1)
                self.assertEqual(result["observations"][0]["payload"]["scope"]["storeId"], "S1")
                self.assertEqual(result["observations"][0]["payload"]["article"]["retailerArticleId"], "S1")
                unknown = copy.deepcopy(snapshot)
                unknown["scopeProof"] = {"storeId": "S2", "sourceRef": "wrong-store"}
                result = self.service.search_offers(selection, [unknown])
                self.assertEqual(result["observations"][0]["payload"]["scope"]["scopeType"], "UNKNOWN")
                other = self.service.search_offers(
                    request(retailer, storeSelections={retailer: {"storeId": "S2"}}), [snapshot])
                self.assertEqual(other["observations"], [])
                self.assertEqual([c["status"] for c in other["coverage"]],
                                 ["OUT_OF_SCOPE", "NO_MATCHING_SCOPE"])

    def test_invalid_second_offer_rolls_back_even_if_search_would_filter_it(self):
        for retailer in HOSTS:
            with self.subTest(retailer=retailer):
                snapshot = synthetic(retailer, rows=[
                    row("OK"), row("BAD", label="Different item", price="-1.00")])
                result = self.service.search_offers(
                    request(retailer, query="Haferflocken"), [snapshot])
                self.assertEqual(result["observations"], [])
                self.assertEqual(result["matchedCount"], 0)
                self.assertEqual([e["code"] for e in result["errors"]], ["INVALID_PRICE"])
                self.assertEqual(result["coverage"][0]["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()
