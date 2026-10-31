import json
import unittest
from decimal import Decimal
from catalogues.aldi_nord import aldi_nord_catalogue_from_html

def fixture(total=1,nbPages=1):
    products=[{"objectID":"791","name":"Bio-Quark","brandName":"BIO",
               "salesUnit":"250-g-Packung","mainCategoryID":"joghurt-quark-milchdesserts",
               "currentPrice":{"priceValue":0.99,
                   "basePrice":[{"basePriceScale":"kg","basePriceValue":3.96}],
                   "validFrom":1767826800,"validUntil":1893452399}}]
    obj={"props":{"pageProps":{"algoliaState":{"initialResults":{
         "an_prd_de_de_products2":{"results":[{"nbHits":total,"page":0,
                        "nbPages":nbPages,"hits":products}]}}}}}}
    return '<html><script id="__NEXT_DATA__" type="application/json">'+json.dumps(obj)+'</script></html>'

class CatalogueTests(unittest.TestCase):
    def test_complete_category_and_price(self):
        products,stats=aldi_nord_catalogue_from_html(fixture())
        self.assertEqual(len(products),1)
        self.assertTrue(stats["products_all_priced"])
        self.assertEqual(products[0].displayed_price_eur,Decimal("0.99"))
        self.assertEqual(products[0].unit_prices[0],("kg",Decimal("3.96")))
        self.assertEqual(products[0].market_scope,"CHAIN_WIDE_REPORTED")
        self.assertEqual(products[0].price_type,"DISPLAYED_CURRENT_NOT_PROVEN_REGULAR")

    def test_reject_truncated_and_multi_page(self):
        with self.assertRaises(ValueError):aldi_nord_catalogue_from_html(fixture(total=100))
        with self.assertRaises(ValueError):aldi_nord_catalogue_from_html(fixture(nbPages=2))
    def test_reject_no_json(self):
        with self.assertRaises(ValueError):aldi_nord_catalogue_from_html("<html></html>")

if __name__=="__main__":unittest.main()
