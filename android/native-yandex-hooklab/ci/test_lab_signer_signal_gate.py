#!/usr/bin/env python3
"""Synthetic APK ZIP tests. Absolutely no third-party APK, account or signing keys."""
from __future__ import annotations
import contextlib
import io
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

from lab_signer_signal_gate import classify_apksigner_failure, probe_apk_zip, safe_report


class SignalGateTest(unittest.TestCase):
    def archive(self, entries: list[tuple[str, bytes]]) -> tuple[tempfile.TemporaryDirectory, Path]:
        box = tempfile.TemporaryDirectory(prefix="synthetic-apk-signal-")
        target = Path(box.name) / "fictional.apk"
        with zipfile.ZipFile(target, "w") as archive:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                for name, payload in entries:
                    archive.writestr(name, payload)
        return box, target

    def test_clean_synthetic_unsigned_zip(self):
        box, apk = self.archive([("AndroidManifest.xml", b"synthetic"),
                                 ("classes.dex", b"synthetic"),
                                 ("res/values/test.xml", b"synthetic")])
        with box:
            result = probe_apk_zip(apk)
            self.assertTrue(result["zip_integrity_ok"])
            self.assertTrue(result["contains_binary_manifest"])
            self.assertFalse(result["duplicate_entry_names"])
            self.assertEqual(result["v1_signature_marker_count"], 0)
            self.assertEqual(result["unsafe_entry_name_count"], 0)

    def test_stale_v1_metadata_detected_without_names(self):
        box, apk = self.archive([("AndroidManifest.xml", b"fictional"),
                                 ("META-INF/OLD.SF", b"abc"),
                                 ("META-INF/OLD.RSA", b"abc"),
                                 ("META-INF/MANIFEST.MF", b"abc")])
        with box:
            result = probe_apk_zip(apk)
            self.assertEqual(result["v1_signature_marker_count"], 2)
            self.assertEqual(result["v1_manifest_marker_count"], 1)
            self.assertFalse(any("OLD" in str(x) for x in result.values()))

    def test_duplicate_zip_names_flagged(self):
        box, apk = self.archive([("AndroidManifest.xml", b"a"),
                                 ("AndroidManifest.xml", b"b")])
        with box:
            self.assertTrue(probe_apk_zip(apk)["duplicate_entry_names"])

    def test_traversal_zip_names_flagged(self):
        box, apk = self.archive([("../escape", b"x"),
                                 ("/tmp/root", b"x"),
                                 ("a/./wrong", b"x")])
        with box:
            self.assertEqual(probe_apk_zip(apk)["unsafe_entry_name_count"], 3)

    def test_disclose_nothing_on_bad_zip(self):
        with tempfile.TemporaryDirectory(prefix="bad-apk-signal-") as box:
            file = Path(box) / "bad.apk"
            file.write_bytes(b"not a zip")
            result = probe_apk_zip(file)
            self.assertFalse(result["zip_integrity_ok"])
            self.assertFalse(result["zip_opened"])

    def test_verifier_nonzero_never_accepted(self):
        result = classify_apksigner_failure(1, "", "Digest mismatch for /private/vendor/account")
        self.assertFalse(result["apksigner_exit_zero"])
        self.assertIn("entry_digest_problem", result["failure_categories"])
        self.assertNotIn("/private", str(result))

    def test_empty_nonzero_classified(self):
        result = classify_apksigner_failure(7, "", "")
        self.assertEqual(result["failure_categories"], ["unclassified"])

    def test_success_does_not_infer_signature_from_strings(self):
        result = classify_apksigner_failure(0, "certificate\nSIGNER", "digest mismatch")
        self.assertTrue(result["apksigner_exit_zero"])
        self.assertEqual(result["failure_categories"], [])

    def test_scheme_and_sdk_failure_buckets(self):
        result = classify_apksigner_failure(1, "", "V2 signature failed for min SDK 28")
        self.assertFalse(result["apksigner_exit_zero"])
        self.assertIn("v2_scheme_problem", result["failure_categories"])
        self.assertIn("sdk_level_rejection", result["failure_categories"])

    def test_signature_report_contract_is_bounded(self):
        box, apk = self.archive([("AndroidManifest.xml", b"fake")])
        with box:
            first = probe_apk_zip(apk)
            last = probe_apk_zip(apk)
            report = safe_report(first, last, 2, "vendor private", "certificate error", 5)
        self.assertEqual(report["lab_split_index"], 5)
        self.assertFalse(report["signature_verification"]["apksigner_exit_zero"])
        self.assertFalse(report["signed_clone_accepted_without_sdk_verification"])
        self.assertNotIn("vendor private", str(report))


if __name__ == "__main__":
    unittest.main()
