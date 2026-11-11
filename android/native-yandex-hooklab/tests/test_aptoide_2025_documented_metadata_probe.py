#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

target = Path(__file__).resolve().parents[1]/"ci"/"aptoide_2025_documented_metadata_probe.py"
spec = importlib.util.spec_from_file_location("aptoide_meta", target)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def payload(version, code=mod.TARGET_CODE, package=mod.TARGET_PACKAGE):
    return {"info": {"status": "OK"},
            "data": {"package": package, "file": {"vercode": code,
                      "vername": version, "path": "https://UNTRUSTED/candidate.apk"}}}

class TestMetadataOnly(unittest.TestCase):
    def test_rur_claim_is_not_verification(self):
        x=mod.classify(payload(mod.TARGET_RUR))
        self.assertTrue(x["exact_rur_claimed"])
        self.assertFalse(x["publisher_2025_signing_verified"])
        self.assertFalse(x["apk_downloaded"])
        self.assertFalse(x["native_2025_test_permitted"])
        self.assertNotIn("https:",str(x))

    def test_gpr_alternate_separate(self):
        x=mod.classify(payload(mod.TARGET_GPR))
        self.assertTrue(x["alternate_gpr_claimed"])
        self.assertFalse(x["exact_rur_claimed"])

    def test_version_code_mismatch(self):
        self.assertEqual(mod.classify(payload(mod.TARGET_RUR,24026531))["verdict"],
                         "CATALOG_VERSION_CODE_NOT_CONFIRMED")

    def test_package_mismatch(self):
        self.assertEqual(mod.classify(payload(mod.TARGET_RUR,package="fake.modded"))["verdict"],
                         "CATALOG_PACKAGE_IDENTITY_NOT_CONFIRMED")

    def test_wrong_version_name(self):
        self.assertEqual(mod.classify(payload("2025.10.4 #120.1xir"))["verdict"],
                         "CATALOG_VERSION_NAME_NOT_TARGET")

    def test_unexpected_status(self):
        self.assertEqual(mod.classify({"info":{"status":"FAIL"}})["verdict"],
                         "CATALOG_TARGET_NOT_CONFIRMED")

    def test_missing_response(self):
        self.assertEqual(mod.classify({})["verdict"],"CATALOG_TARGET_NOT_CONFIRMED")

    def test_missing_file(self):
        self.assertEqual(mod.classify({"info":{"status":"OK"},"data":{"package":mod.TARGET_PACKAGE}})["verdict"],
                         "CATALOG_VERSION_CODE_NOT_CONFIRMED")

if __name__=="__main__":
    unittest.main()
