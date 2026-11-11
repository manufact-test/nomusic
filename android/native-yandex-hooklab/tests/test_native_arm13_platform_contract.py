"""Synthetic read-only native A1 PackageManager/system-denial tests."""
import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from native_arm13_platform_contract import (
    CLONE, ORIGINAL, FOCUS, classify_installed_permission_state,
    compare_installed_permission_states, classify_public_system_denials,
)
SECRET = "PRIVATE_TOKEN_DB_PASS_PATH"
INTERNET = "android.permission.INTERNET"
NOTIFY = "android.permission.POST_NOTIFICATIONS"

def pkg(name, *, focus=True, grant=False, runtime=False, extra=False):
    req = f"      {FOCUS}\n" if focus else ""
    state = f"      {FOCUS}: granted={str(grant).lower()}\n" if focus else ""
    add = "  Package [unrelated.private] (ff):\n" if extra else ""
    return (
        f"Packages:\n  Package [{name}] (abc):\n"
        f"    codePath=/data/private/{SECRET}\n"
        f"    requested permissions:\n      {INTERNET}\n{req}"
        f"      {NOTIFY}\n"
        f"    install permissions:\n      {INTERNET}: granted=true\n{state}"
        f"    User 0:\n      runtime permissions:\n"
        f"        {NOTIFY}: granted={str(runtime).lower()}, flags=[USER_SET]\n"
        f"    User 10:\n      runtime permissions:\n"
        f"        {NOTIFY}: granted=true, flags=[USER_SET]\n" + add
    )

def line(tag, msg, severity="W"):
    return f"11-11 12:33:00.123   999   888 {severity} {tag}: {msg}\n"

class PublicOSPermissionWitness(unittest.TestCase):
    def test_snapshot_requested_vs_granted_and_only_user_zero(self):
        result = classify_installed_permission_state(pkg(CLONE, extra=True), CLONE)
        self.assertEqual(result["snapshot"], "AVAILABLE")
        self.assertEqual(result["requested_count_bounded"], 3)
        self.assertEqual(result["requested_groups"]["YANDEX"], 1)
        self.assertEqual(result["install_granted_groups"]["ANDROID"], 1)
        self.assertEqual(result["install_denied_groups"]["YANDEX"], 1)
        self.assertEqual(result["runtime_denied_groups"]["ANDROID"], 1)
        self.assertEqual(result["runtime_granted_groups"]["ANDROID"], 0)
        self.assertEqual(result["focus_credential_install_grant"], "DENIED")
        self.assertNotIn(FOCUS, str(result))
        self.assertNotIn(SECRET, str(result))

    def test_missing_metadata_does_not_forge_grant(self):
        for raw in ("", "Package [not.clone] (abc):", "wrong", None):
            x = classify_installed_permission_state(raw, CLONE)
            self.assertEqual(x["snapshot"], "UNAVAILABLE")
        without_focus = classify_installed_permission_state(
            pkg(CLONE, focus=False), CLONE)
        self.assertEqual(without_focus["focus_credential_install_grant"],
                         "NOT_LISTED")
        with self.assertRaises(ValueError):
            classify_installed_permission_state(pkg(CLONE), "unknown.package")

    def test_differential_explicit_denial_no_security_override(self):
        x = compare_installed_permission_states(
            pkg(CLONE, grant=False), pkg(ORIGINAL, grant=True))
        self.assertEqual(x["comparison"], "AVAILABLE")
        self.assertEqual(x["shared_requested_count_bounded"], 3)
        self.assertEqual(
            x["original_granted_clone_not_granted_shared_count_bounded"], 1)
        self.assertEqual(x["clone_explicitly_denied_shared_count_bounded"], 1)
        self.assertTrue(x["missing_focus_credential_permission"])
        self.assertTrue(x["no_permission_grant_or_security_override"])
        self.assertNotIn(SECRET, str(x))
        self.assertNotIn(FOCUS, str(x))

    def test_grant_not_listed_differs_from_explicit_deny(self):
        raw = pkg(CLONE).replace(f"      {FOCUS}: granted=false\n", "")
        x = compare_installed_permission_states(raw, pkg(ORIGINAL, grant=True))
        self.assertEqual(x["clone_explicitly_denied_shared_count_bounded"], 0)
        self.assertEqual(x["clone_grant_not_listed_shared_count_bounded"], 1)
        self.assertEqual(
            compare_installed_permission_states(raw, "")["comparison"], "INCONCLUSIVE")

    def test_system_server_reporter_not_main_pid(self):
        raw = (
            line("ActivityManager", f"Permission Denial to {CLONE} {SECRET}")
            + line("ActivityTaskManager", f"component not exported to {CLONE}", "E")
            + line("AppOps", f"AppOp request denied for {CLONE}", "E")
            + line("PackageManager", f"SecurityException for {CLONE}", "E")
        )
        x = classify_public_system_denials(raw, CLONE)
        self.assertEqual(set(x["exact_package_denial_categories"]), {
            "PERMISSION_DENIAL", "COMPONENT_DENIAL",
            "APP_OP_DENIAL", "SECURITY_EXCEPTION",
        })
        self.assertFalse(x["raw_logs_or_package_data_exposed"])
        self.assertNotIn(SECRET, str(x))
        self.assertNotIn(CLONE, str(x))

    def test_scope_excludes_helper_subpackage_other_and_ambiguous(self):
        raw = (
            line("ActivityManager", "Permission Denial to " + CLONE + ":worker")
            + line("ActivityManager", "Permission Denial to " + CLONE + ".other")
            + line("ActivityManager", "Permission Denial to " + ORIGINAL)
            + line("ActivityManager", "Permission Denial to " + CLONE + " and " + ORIGINAL)
            + line("VendorTag", "Permission Denial to " + CLONE)
        )
        x = classify_public_system_denials(raw, CLONE)
        self.assertEqual(x["exact_package_denial_categories"], [])
        self.assertEqual(x["ambiguous_two_package_lines_ignored_bounded"], 1)

    def test_original_class_name_not_exact_package(self):
        raw = (
            line("ActivityManager",
                 "Permission Denial ru.yandex.music.main.MainScreenActivity")
            + line("PackageManager", "Permission Denial " + ORIGINAL)
        )
        x = classify_public_system_denials(raw, ORIGINAL)
        self.assertEqual(x["exact_package_denial_categories"], ["PERMISSION_DENIAL"])

    def test_bad_stream_and_unknown_identity_fail_closed(self):
        for raw in ("", None, 9, "Permission Denial " + CLONE):
            self.assertEqual(
                classify_public_system_denials(raw, CLONE)["exact_package_denial_categories"], [])
        with self.assertRaises(ValueError):
            classify_public_system_denials("", "unknown")
if __name__ == "__main__":
    unittest.main()
