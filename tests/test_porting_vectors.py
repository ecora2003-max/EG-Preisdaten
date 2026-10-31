"""Portable synthetic price contract parity vectors for Kotlin/JVM integration.

This suite asserts independent, manually curated expected projections. No network,
real retailer snapshots, purchases, inventory, Room or Sheets side effects.
"""
import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from price_module import PriceService

ROOT = Path(__file__).resolve().parent
VECTORS = ROOT / "fixtures" / "porting_vectors.json"
SCHEMA = ROOT / "fixtures" / "architecture-contract.schema.json"


def assert_subset(test, expected, actual, path="payload"):
    if isinstance(expected, dict):
        test.assertIsInstance(actual, dict, path)
        for key, value in expected.items():
            test.assertIn(key, actual, path)
            assert_subset(test, value, actual[key], path + "." + key)
    elif isinstance(expected, list):
        test.assertIsInstance(actual, list, path)
        test.assertEqual(len(actual), len(expected), path)
        for index, (wanted, got) in enumerate(zip(expected, actual)):
            assert_subset(test, wanted, got, path + "[" + str(index) + "]")
    else:
        test.assertEqual(actual, expected, path)


class KotlinPortingParityTests(unittest.TestCase):
    def test_all_offline_parity_vectors(self):
        doc = json.loads(VECTORS.read_text(encoding="utf-8"))
        self.assertEqual(doc["contractVersion"], "1.0.0-draft")
        self.assertEqual(doc["retailerCapabilityPolicyVersion"], "1.0.1")
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        names = [case["name"] for case in doc["cases"]]
        self.assertEqual(len(names), len(set(names)))
        self.assertGreaterEqual(len(names), 12)
        for case in doc["cases"]:
            with self.subTest(vector=case["name"]):
                request = copy.deepcopy(case["request"])
                datasets = copy.deepcopy(case["datasets"])
                original = copy.deepcopy((request, datasets))
                result = PriceService().search(request, datasets)
                self.assertEqual((request, datasets), original, "input mutation")
                expected = case["expect"]
                self.assertEqual(result["contractVersion"], doc["contractVersion"])
                self.assertEqual(result["capabilityPolicyVersion"], doc["retailerCapabilityPolicyVersion"])
                self.assertEqual(result["matchedCount"], expected["matchedCount"])
                self.assertEqual([e["code"] for e in result["errors"]], expected["errorCodes"])
                self.assertEqual(len(result["observations"]), len(expected["observations"]))
                self.assertEqual(result["outputTruncated"], expected.get("outputTruncated", False))
                if "coverageStatuses" in expected:
                    self.assertEqual([c["status"] for c in result["coverage"]],
                                     expected["coverageStatuses"])
                if expected.get("uniqueObservationIds"):
                    ids = [x["payload"]["observationId"] for x in result["observations"]]
                    self.assertEqual(len(ids), len(set(ids)))
                for actual, wanted in zip(result["observations"], expected["observations"]):
                    self.assertEqual(actual["messageType"], "price.observation")
                    self.assertFalse(list(validator.iter_errors(actual)),
                                     "invalid architecture contract envelope")
                    assert_subset(self, wanted, actual["payload"])


if __name__ == "__main__":
    unittest.main()
