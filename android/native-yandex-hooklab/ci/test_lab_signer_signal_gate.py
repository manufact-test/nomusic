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
        result = classify_apksigner_failure(1, "", "ERROR: Digest mismatch for /private/vendor/account")
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
        result = classify_apksigner_failure(1, "", "ERROR: V2 signature failed for min SDK 28")
        self.assertFalse(result["apksigner_exit_zero"])
        self.assertIn("v2_scheme_problem", result["failure_categories"])
        self.assertIn("sdk_level_rejection", result["failure_categories"])

    def test_info_lines_are_not_diagnosed_as_signing_errors(self):
        # Prior CI conflated these normal --verbose/--print-certs info lines
        # with a signature or certificate root cause.
        info = ("DOES NOT VERIFY\n"
                "Verified using v1 scheme (JAR signing): false\n"
                "Signer #1 certificate SHA-256 digest: 0123456789abcdef")
        result = classify_apksigner_failure(1, info, "")
        self.assertEqual(result["failure_categories"], ["unclassified"])
        self.assertEqual(result["reported_scheme_verification"], {"v1": False})
        self.assertEqual(result["diagnostic_error_count"], 0)
        self.assertTrue(result["generic_does_not_verify_banner"])

    def test_error_only_not_warning_or_certificate_info(self):
        result = classify_apksigner_failure(
            1, "Signer #1 certificate SHA-256 digest: aabb\n"
               "Verified using v2 scheme (APK Signature Scheme v2): true",
            "WARNING: JAR signature output may vary\n"
            "ERROR: ZIP central directory malformed")
        self.assertIn("zip_or_central_directory", result["failure_categories"])
        self.assertNotIn("certificate_or_signer", result["failure_categories"])
        self.assertNotIn("v1_jar_problem", result["failure_categories"])
        self.assertEqual(result["diagnostic_warning_count"], 1)

    def test_error_diagnostics_do_not_leak_private_paths(self):
        result = classify_apksigner_failure(
            1, "", "ERROR: certificate digest mismatch at /secret/account/private.apk")
        self.assertIn("entry_digest_problem", result["failure_categories"])
        self.assertNotIn("/secret", str(result))
        self.assertNotIn("private.apk", str(result))

    def test_v1_signature_stripping_error_is_distinct_from_certificate_info(self):
        result = classify_apksigner_failure(
            1, "",
            "DOES NOT VERIFY\nERROR: JAR signer SAMPLE.RSA: JAR signature "
            "META-INF/SAMPLE.SF indicates the APK is signed using APK Signature "
            "Scheme v2 but no such signature was found. Signature stripped?")
        self.assertEqual(result["specific_error_reasons"],
                         ["v1_signature_stripping_v2"])
        self.assertNotIn("SAMPLE", str(result))

    def test_v1_crypto_unsupported_old_api_is_distinct(self):
        result = classify_apksigner_failure(
            1, "", "ERROR: JAR signer TEST: JAR signature uses digest algorithm "
                   "SHA-256 which is not supported on API Level(s) 1-20")
        self.assertIn("v1_crypto_not_supported_for_lower_api",
                      result["specific_error_reasons"])
        self.assertIn("v1_digest_not_supported_for_lower_api",
                      result["specific_error_reasons"])

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
