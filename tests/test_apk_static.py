"""Security and parsing contract for APK binary research (synthetic bytes only)."""
import unittest
from collections import Counter
from tools.real_apk_static_analysis import clean_host,clean_path,inspect_bytes

class APKAnalysisContracts(unittest.TestCase):
    def test_hostname_only_no_secret_query(self):
        url=b"https://api.examplecommerce.de/api/v1/mpos/1234/itemInfo?itemEAN=4000000000123&auth=not-a-secret"
        self.assertEqual(clean_host(url),"api.examplecommerce.de")
        self.assertEqual(clean_path(b"/api/v1/mpos/1234/itemInfo?auth=not-a-secret"),"/api/v1/mpos/1234/itemInfo")
    def test_suppress_private_auth_endpoints(self):
        self.assertIsNone(clean_path(b"/api/v3/auth/session"))
        self.assertIsNone(clean_path(b"/api/v3/checkout/payment"))
    def test_extract_prices_from_binary_without_token_values(self):
        stats={"hosts":Counter(),"paths":Counter(),"signal_hits":Counter(),
               "scanned_bytes":0,"scanned_files":0}
        data=(b"\x00/api/v1/mpos/{storeId}/itemInfo\x00"
              b"https://shelf.examplecommerce.de/api/v3/product-search?query=Tofu&apikey=secret"
              b"\x00itemEAN\x00product-search\x00")
        inspect_bytes(data,stats,"classes.dex")
        self.assertGreater(stats["hosts"]["shelf.examplecommerce.de"],0)
        self.assertIn("/api/v1/mpos/{storeId}/itemInfo",stats["paths"])
        self.assertTrue(all("secret" not in x for x in stats["paths"]))
        self.assertGreater(stats["signal_hits"]["itemEAN"],0)
if __name__=="__main__":unittest.main()
