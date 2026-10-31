"""Offline unit tests: synthetic examples, not claimed live checkout evidence."""
import unittest
from adapters.stationary_price_catalogues import integer_cents, rewe_stationary, aldi_sued


class PriceCatalogueTest(unittest.TestCase):
    def test_cents_validation(self):
        self.assertEqual(integer_cents(0), 0)
        self.assertIsNone(integer_cents(True))
        self.assertIsNone(integer_cents(0.99))
        self.assertIsNone(integer_cents(-50))
        self.assertIsNone(integer_cents("99"))

    def test_rewe_discount_and_deposit(self):
        raw = {"products": [
            {"id": 123, "title": "Testprodukt", "pricing":
             {"current": 129, "regular": 189, "refund": 25}},
            {"id": 124, "pricing": {"current": 200}},
            {"id": 125, "pricing": {"current": "3.49"}}
        ]}
        res = rewe_stationary(raw, "840174")
        self.assertEqual(res["listed_count"], 2)
        self.assertIsNone(res["catalogue_complete"])
        self.assertEqual(res["listings"][0]["price_cents"], 129)
        self.assertEqual(res["listings"][0]["regular_cents"], 189)
        self.assertEqual(res["listings"][0]["deposit_cents"], 25)
        self.assertTrue(res["listings"][0]["discount_is_observed"])
        self.assertIsNone(res["listings"][1]["discount_is_observed"])
        self.assertIsNone(res["listings"][1]["deposit_cents"])

    def test_aldi_known_price_in_cents_and_total(self):
        raw = {"meta": {"pagination": {"totalCount": 3}}, "data": [
            {"sku": "A", "name": "Probe", "price": {
                "amount": 149, "amountRelevant": 159,
                "bottleDeposit": 25, "currencyCode": "EUR",
                "wasPriceDisplay": "1,99 €"}}
        ]}
        res = aldi_sued(raw, "B384")
        self.assertFalse(res["catalogue_complete"])
        p = res["listings"][0]
        self.assertEqual(p["price_cents"], 159)
        self.assertIsNone(p["regular_cents"])
        self.assertEqual(p["previous_price_display"], "1,99 €")
        self.assertTrue(p["discount_is_observed"])

    def test_aldi_complete_one_page(self):
        raw = {"meta": {"pagination": {"totalCount": 1}}, "data": [
            {"sku": "B", "price": {"amount": 99}}
        ]}
        self.assertTrue(aldi_sued(raw, "B384")["catalogue_complete"])

    def test_aldi_inconsistent_page_totals_do_not_claim_full_coverage(self):
        def item(sku, price):
            return {"sku":sku,"name":"Synthetic","price":{"amount":price}}
        cases=[
            ([item("A",99),item("B",199)],1),
            ([item("A",99),item("B",199)],3),
            ([item("A",99),item("A",199)],2),
            ([item(None,99),item("B",199)],2),
            ([item("A",99),item("B",None)],2),
        ]
        for products,total in cases:
            with self.subTest(total=total,products=products):
                out=aldi_sued({"meta":{"pagination":{"totalCount":total}},
                               "data":products},"B384")
                self.assertIs(out["catalogue_complete"],False)
        good=aldi_sued({"meta":{"pagination":{"totalCount":2}},
                        "data":[item("A",99),item("B",199)]},"B384")
        self.assertIs(good["catalogue_complete"],True)

    def test_not_list_is_error(self):
        with self.assertRaises(ValueError):
            rewe_stationary({"errors": []}, "840174")
        with self.assertRaises(ValueError):
            aldi_sued({}, "B384")


if __name__ == "__main__":
    unittest.main()
