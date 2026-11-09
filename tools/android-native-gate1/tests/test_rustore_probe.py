"""Pure metadata contract tests: no network, APK, or personal data."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from probe_rustore import normalize

class RustoreMetadataTests(unittest.TestCase):
    def test_exact_version_is_identified(self):
        value=normalize({"body":{"packageName":"ru.yandex.music",
            "versionName":"2026.10.3 #170gpr","versionCode":24026531}})
        self.assertTrue(value["exact_owner_gpr_build"])
        self.assertNotIn("download",str(value).lower())
    def test_other_store_variant_not_marked_exact(self):
        value=normalize({"body":{"packageName":"ru.yandex.music",
            "versionName":"2026.10.3 #170rur","versionCode":24026531}})
        self.assertFalse(value["exact_owner_gpr_build"])
    def test_wrong_package_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"package"):
            normalize({"body":{"packageName":"some.other.app","versionCode":24026531,
                "versionName":"2026.10.3 #170gpr"}})
    def test_missing_version_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"version"):
            normalize({"body":{"packageName":"ru.yandex.music"}})

if __name__=="__main__":unittest.main()
