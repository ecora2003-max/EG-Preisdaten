import unittest
from decimal import Decimal
from catalogues.lidl import store_products,merge_store_category_pages,search_products

class LidlPriceTests(unittest.TestCase):
    def row(self,id,price):
        return {"id":id,"brand":"MILBONA","title":"Frische Milch",
                "price":{"price":price,"priceWithoutDeposit":price,
                         "oldPrice":None,"lidlPlusOffer":None}}
    def test_category_price_and_all_pages(self):
        page1={"totalProducts":3,"products":[self.row("1_DE",0.85),self.row("2_DE",1.25)]}
        page2={"totalProducts":3,"products":[self.row("3_DE",1.59)]}
        a=store_products(page1,store_key="DE7434",day="2026-10-31",offset=0,limit=2)
        b=store_products(page2,store_key="DE7434",day="2026-10-31",offset=2,limit=2)
        self.assertEqual(a[0][0].current_price_eur,Decimal("0.85"))
        self.assertFalse(a[1]["complete"])
        self.assertEqual(len(merge_store_category_pages([a,b])),3)
        with self.assertRaises(ValueError):merge_store_category_pages([a])
    def test_search_price_and_app_discount(self):
        rows={"results":[{"id":"X_DE","title":"Milch","brand":"Lidl",
                          "price":0.85,"priceWithoutDeposit":0.85,
                          "oldPrice":1.09,"discount":"Test","lidlPlusOffer":{"price":0.69}}]}
        items=search_products(rows,store_key="DE7434",day="2026-10-31")
        self.assertEqual(len(items),1)
        self.assertEqual(items[0].current_price_eur,Decimal("0.85"))
        self.assertEqual(items[0].previous_display_price_eur,Decimal("1.09"))
        self.assertTrue(items[0].has_discount)
        self.assertTrue(items[0].has_lidl_plus_offer)
        self.assertEqual(items[0].lidl_plus_price_eur, Decimal("0.69"))
    def test_guards(self):
        with self.assertRaises(ValueError):
            store_products({"totalProducts":1,"products":[]},store_key="bad",day="2026-10-31")
        page={"totalProducts":2,"products":[self.row("a",0.85)]}
        a=store_products(page,store_key="DE7434",day="2026-10-31",offset=0)
        b=store_products(page,store_key="DE7434",day="2026-10-31",offset=1)
        with self.assertRaises(ValueError):merge_store_category_pages([a,b])

if __name__=="__main__":unittest.main()
