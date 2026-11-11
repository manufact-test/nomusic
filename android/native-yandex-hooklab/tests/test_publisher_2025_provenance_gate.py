#!/usr/bin/env python3
"""Synthetic safety tests only. NEVER uses or executes publisher APK."""
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch

TARGET = Path(__file__).resolve().parents[1] / "ci" / "publisher_2025_provenance_gate.py"
spec = importlib.util.spec_from_file_location("publisher_2025_provenance_gate", TARGET)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

AAPT = "package: name='ru.yandex.music' versionCode='24025542' versionName='2025.10.4 #120.1rur'"
SIGNER = (
    "Verifies\n"
    "Verified using v1 scheme (JAR signing): false\n"
    "Verified using v2 scheme (APK Signature Scheme v2): true\n"
    "Verified using v3 scheme (APK Signature Scheme v3): true\n"
    "Signer #1 certificate SHA-256 digest: " + mod.KNOWN_ISSUER_CERT + "\n"
)


class PublisherGateTest(unittest.TestCase):
    def test_correct_signed_version_passes(self):
        result = mod.verify_metadata(AAPT, SIGNER)
        self.assertTrue(result["publisher_cert_matches_verified_rustore_2026_reference"])

    def test_altered_package_rejected(self):
        with self.assertRaisesRegex(mod.GateError, "WRONG_PACKAGE_OR_VERSION"):
            mod.verify_metadata(AAPT.replace("ru.yandex.music", "app.chromasync.yamclone"), SIGNER)

    def test_wrong_version_code_rejected(self):
        with self.assertRaisesRegex(mod.GateError, "WRONG_PACKAGE_OR_VERSION"):
            mod.verify_metadata(AAPT.replace("24025542", "24026531"), SIGNER)

    def test_wrong_version_name_rejected(self):
        with self.assertRaisesRegex(mod.GateError, "WRONG_PACKAGE_OR_VERSION"):
            mod.verify_metadata(AAPT.replace("#120.1rur", "#120.1gpr"), SIGNER)

    def test_missing_manifest_rejected(self):
        with self.assertRaisesRegex(mod.GateError, "BAD_MANIFEST_METADATA"):
            mod.verify_metadata("not a package", SIGNER)

    def test_wrong_cert_rejected(self):
        with self.assertRaisesRegex(mod.GateError, "PUBLISHER_CERTIFICATE_MISMATCH"):
            mod.verify_metadata(AAPT, SIGNER.replace(mod.KNOWN_ISSUER_CERT, "0" * 64))

    def test_two_signers_rejected(self):
        with self.assertRaisesRegex(mod.GateError, "SIGNER_SET_NOT_SINGLE_ISSUER"):
            mod.verify_metadata(AAPT, SIGNER + "Signer #2 certificate SHA-256 digest: " + mod.KNOWN_ISSUER_CERT)

    def test_no_v2_v3_rejected(self):
        with self.assertRaisesRegex(mod.GateError, "VALID_V2_V3_SIGNING_NOT_CONFIRMED"):
            mod.verify_metadata(AAPT, SIGNER.replace("): true", "): false"))

    def test_missing_signer_rejected(self):
        with self.assertRaisesRegex(mod.GateError, "SIGNER_SET_NOT_SINGLE_ISSUER"):
            mod.verify_metadata(AAPT, "Verified using v2 scheme (APK Signature Scheme v2): true")

    def test_no_apk_is_non_go(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(mod.main([]), 0)
        self.assertIn("PUBLISHER_SIGNED_2025_SAMPLE_NOT_YET_OBTAINED", output.getvalue())
        self.assertIn('"native_2025_test_permitted": false', output.getvalue())

    def test_missing_file_rejected_without_tools(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(mod.main(["--apk", "/this-file-does-not-exist.apk"]), 2)
        self.assertIn("CANDIDATE_MISSING_OR_NOT_REGULAR", output.getvalue())

    def test_inspect_requires_both_sdk_checks_and_apk_hash(self):
        with patch.object(mod, "file_hashes", return_value=(59498960, "a" * 64, mod.HISTORICAL_MD5)), \
             patch.object(mod, "private_command", side_effect=[SIGNER, AAPT]) as command:
            result = mod.inspect(Path("/fake-unread.apk"))
        self.assertEqual(command.call_count, 2)
        self.assertTrue(result["historical_4pda_bytes_and_md5_match"])
        self.assertFalse(result["installed_or_executed"])
        self.assertEqual(result["android_stage_a"], "NO_GO")

    def test_historical_md5_not_a_substitute_for_signature(self):
        with patch.object(mod, "file_hashes", return_value=(59498960, "a" * 64, mod.HISTORICAL_MD5)), \
             patch.object(mod, "private_command", side_effect=[SIGNER.replace(mod.KNOWN_ISSUER_CERT, "a" * 64), AAPT]):
            with self.assertRaisesRegex(mod.GateError, "PUBLISHER_CERTIFICATE_MISMATCH"):
                mod.inspect(Path("/fake-unread.apk"))

    def test_size_drift_not_silently_historical_match(self):
        with patch.object(mod, "file_hashes", return_value=(12, "b" * 64, mod.HISTORICAL_MD5)), \
             patch.object(mod, "private_command", side_effect=[SIGNER, AAPT]):
            self.assertFalse(mod.inspect(Path("/fake-unread.apk"))["historical_4pda_bytes_and_md5_match"])


if __name__ == "__main__":
    unittest.main()
