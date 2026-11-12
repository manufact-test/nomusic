"""Synthetic AOSP package snapshots: issuer/own grants, strict privacy."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from owner_2025_signature_permission_comparison import compare_issuer_own_signer_package_grants


def fixture(issuer=True):
    focus="true" if issuer else "false"
    return (
        "Packages:\n"
        "  Package [ru.yandex.music] (some-private-system-id):\n"
        "    requested permissions:\n"
        "      android.permission.INTERNET\n"
        "      com.yandex.permission.READ_CREDENTIALS\n"
        "      com.yandex.permission.EXTRA_PRIVATE\n"
        "    install permissions:\n"
        "      android.permission.INTERNET: granted=true\n"
        f"      com.yandex.permission.READ_CREDENTIALS: granted={focus}\n"
        f"      com.yandex.permission.EXTRA_PRIVATE: granted={focus}\n"
        "    User 0:\n"
        "      runtime permissions:\n"
        "        android.permission.POST_NOTIFICATIONS: granted=true\n"
        "  Package [ru.yandex.other.secret] (other):\n"
        "    install permissions:\n"
        "      com.yandex.permission.READ_CREDENTIALS: granted=true\n"
    )


class SamePackageSignerGrantsTests(unittest.TestCase):
    def test_missing_exact_snapshot_inconclusive(self):
        result=compare_issuer_own_signer_package_grants(
            "Package [private.example]","Package [private.example]")
        self.assertEqual(result["result"],"INCONCLUSIVE_PACKAGE_MANAGER_SNAPSHOT")
        self.assertFalse(result["source_dumpsys_exposed"])

    def test_same_manifest_different_grants_fixed_counts_only(self):
        result=compare_issuer_own_signer_package_grants(fixture(True),fixture(False))
        self.assertEqual(result["result"],"SAME_PACKAGE_SIGNER_GRANT_DIFFERENTIAL")
        self.assertTrue(result["requested_permissions_exactly_equal"])
        self.assertEqual(result["issuer_only_grant_count_bounded"],2)
        self.assertEqual(result["issuer_only_grant_families"]["YANDEX"],2)
        self.assertEqual(result["own_only_grant_count_bounded"],0)
        self.assertEqual(result["issuer_focus_credential_install_grant"],"GRANTED")
        self.assertEqual(result["own_focus_credential_install_grant"],"DENIED")
        self.assertNotIn("PRIVATE",str(result))
        self.assertNotIn("some-private",str(result))

    def test_original_and_own_equal_grants_no_false_differences(self):
        result=compare_issuer_own_signer_package_grants(fixture(True),fixture(True))
        self.assertEqual(result["issuer_only_grant_count_bounded"],0)
        self.assertEqual(result["own_only_grant_count_bounded"],0)
        self.assertTrue(result["requested_permissions_exactly_equal"])


if __name__=="__main__":
    unittest.main()
