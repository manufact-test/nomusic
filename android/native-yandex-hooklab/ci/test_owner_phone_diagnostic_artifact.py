from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from owner_phone_diagnostic_artifact import export_after_native_acceptance, OUTPUT_NAME


class OwnerPhoneDiagnosticArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "clone.apk"
        self.source.write_bytes(b"CELIKOM-DIAGNOSTIC-APK" * 100_000)
        self.runner = self.root / "runner-temp"
        self.runner.mkdir()

    def accepted_report(self):
        return {
            "verdict": "METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO",
            "native_clone_main_75s": True,
            "publisher_stable_75s_before_clone": True,
            "publisher_still_installed_after_clone_start": True,
            "publisher_app_and_clone_can_be_concurrently_installed": True,
            "single_clone_installed_after_original": True,
            "original_splits_installed_before_clone": 16,
            "owner_apk_signer_provenance": "PERSISTENT_OWNER_SIGNER",
            "owner_apk_signer_verified": True,
        }

    def test_exports_only_after_full_original_first_acceptance(self):
        result = export_after_native_acceptance(self.source, self.accepted_report(), self.runner)
        target = self.runner / "celikom-a1-owner-phone-test" / OUTPUT_NAME
        self.assertTrue(target.is_file())
        self.assertEqual(result["sha256"], hashlib.sha256(target.read_bytes()).hexdigest())
        self.assertEqual(result["size_bytes"], target.stat().st_size)
        self.assertTrue(result["exported"])

    def test_rejects_failed_or_partial_native_run(self):
        report = self.accepted_report()
        report["native_clone_main_75s"] = False
        with self.assertRaisesRegex(ValueError, "NATIVE_ACCEPTANCE_REQUIRED"):
            export_after_native_acceptance(self.source, report, self.runner)
        self.assertFalse((self.runner / "celikom-a1-owner-phone-test").exists())

    def test_rejects_missing_original_first_coexistence(self):
        report = self.accepted_report()
        report["publisher_still_installed_after_clone_start"] = False
        with self.assertRaisesRegex(ValueError, "NATIVE_ACCEPTANCE_REQUIRED"):
            export_after_native_acceptance(self.source, report, self.runner)

    def test_rejects_disposable_ci_signer_even_after_native_success(self):
        report = self.accepted_report()
        report["owner_apk_signer_provenance"] = "DISPOSABLE_PER_CI_RUN"
        with self.assertRaisesRegex(ValueError, "STABLE_SIGNER_REQUIRED"):
            export_after_native_acceptance(self.source, report, self.runner)
        self.assertFalse((self.runner / "celikom-a1-owner-phone-test").exists())

    def test_rejects_unverified_release_signer(self):
        report = self.accepted_report()
        report["owner_apk_signer_verified"] = False
        with self.assertRaisesRegex(ValueError, "STABLE_SIGNER_REQUIRED"):
            export_after_native_acceptance(self.source, report, self.runner)

    def test_refuses_existing_destination(self):
        (self.runner / "celikom-a1-owner-phone-test").mkdir()
        with self.assertRaisesRegex(ValueError, "DESTINATION_EXISTS"):
            export_after_native_acceptance(self.source, self.accepted_report(), self.runner)

    def test_refuses_symlink_source(self):
        link = self.root / "clone-link.apk"
        link.symlink_to(self.source)
        with self.assertRaisesRegex(ValueError, "SOURCE_INVALID"):
            export_after_native_acceptance(link, self.accepted_report(), self.runner)


if __name__ == "__main__":
    unittest.main()
