from __future__ import annotations
import base64
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from a1_persistent_owner_signer import DEST_ALIAS, DEST_STORE_PASSWORD, prepare_persistent_owner_keystore

@unittest.skipUnless(shutil.which("keytool"), "JDK keytool is required")
class PersistentOwnerSignerTests(unittest.TestCase):
    def create_source_keystore(self, root: Path):
        source = root / "source.p12"
        password = "test-owner-pass-2026"
        result = subprocess.run([
            "keytool", "-genkeypair", "-noprompt", "-storetype", "PKCS12",
            "-keystore", str(source), "-storepass", password, "-keypass", password,
            "-alias", "celikom-a1-owner", "-keyalg", "RSA", "-keysize", "2048",
            "-validity", "3650", "-dname", "CN=CELIKOM A1 Test,O=MANUFACT,C=BY",
        ], capture_output=True, text=True, timeout=90, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        listing = subprocess.run([
            "keytool", "-list", "-v", "-keystore", str(source), "-storetype", "PKCS12",
            "-storepass", password, "-alias", "celikom-a1-owner",
        ], capture_output=True, text=True, timeout=90, check=False)
        self.assertEqual(listing.returncode, 0, listing.stderr)
        match = re.search(r"(?im)^\s*SHA256:\s*([0-9a-f:]{64,95})\s*$", listing.stdout)
        self.assertIsNotNone(match, listing.stdout)
        fingerprint = re.sub(r"[^0-9a-f]", "", match.group(1).lower())
        env = {
            "CELIKOM_A1_OWNER_KEYSTORE_BASE64": base64.b64encode(source.read_bytes()).decode("ascii"),
            "CELIKOM_A1_OWNER_KEYSTORE_PASSWORD": password,
            "CELIKOM_A1_OWNER_KEY_ALIAS": "celikom-a1-owner",
            "CELIKOM_A1_OWNER_KEY_PASSWORD": password,
            "CELIKOM_A1_OWNER_CERT_SHA256": fingerprint,
        }
        source.unlink()
        return source, env, fingerprint

    def test_imports_pkcs12_and_verifies_pinned_certificate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, env, expected = self.create_source_keystore(root)
            result = prepare_persistent_owner_keystore(root, env)
            destination = Path(result["keystore_path"])
            self.assertTrue(destination.is_file())
            self.assertEqual(destination.stat().st_mode & 0o777, 0o600)
            self.assertFalse(source.exists())
            self.assertEqual(result["certificate_sha256"], expected)
            self.assertEqual(result["alias"], DEST_ALIAS)
            check = subprocess.run([
                "keytool", "-list", "-v", "-keystore", str(destination),
                "-storetype", "JKS", "-storepass", DEST_STORE_PASSWORD, "-alias", DEST_ALIAS,
            ], capture_output=True, text=True, timeout=90, check=False)
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertIn("PrivateKeyEntry", check.stdout)

    def test_accepts_text_file_trailing_newlines_in_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, env, expected = self.create_source_keystore(root)
            copied_text_values = {name: value + "\\r\\n" for name, value in env.items()}
            result = prepare_persistent_owner_keystore(root, copied_text_values)
            self.assertEqual(result["certificate_sha256"], expected)
            self.assertFalse(source.exists())

    def test_rejects_incomplete_secret_set(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "SECRETS_INCOMPLETE"):
                prepare_persistent_owner_keystore(directory, {})

    def test_rejects_invalid_base64(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {
                "CELIKOM_A1_OWNER_KEYSTORE_BASE64": "not-base64!",
                "CELIKOM_A1_OWNER_KEYSTORE_PASSWORD": "password",
                "CELIKOM_A1_OWNER_KEY_ALIAS": "celikom-a1-owner",
                "CELIKOM_A1_OWNER_KEY_PASSWORD": "password",
                "CELIKOM_A1_OWNER_CERT_SHA256": "a" * 64,
            }
            with self.assertRaisesRegex(ValueError, "BASE64_INVALID"):
                prepare_persistent_owner_keystore(directory, env)

    def test_rejects_certificate_fingerprint_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, env, _ = self.create_source_keystore(root)
            env["CELIKOM_A1_OWNER_CERT_SHA256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "FINGERPRINT_MISMATCH"):
                prepare_persistent_owner_keystore(root, env)
            self.assertFalse((root / "unique-own-key.jks").exists())
            self.assertFalse(source.exists())

    def test_rejects_wrong_source_password_without_disclosing_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, env, _ = self.create_source_keystore(root)
            env["CELIKOM_A1_OWNER_KEYSTORE_PASSWORD"] = "wrong-password"
            with self.assertRaisesRegex(ValueError, "KEYSTORE_IMPORT_FAILED"):
                prepare_persistent_owner_keystore(root, env)
            self.assertFalse(source.exists())

if __name__ == "__main__":
    unittest.main()
