"""Pure synthetic ZIP fixtures: content equality while signing metadata changes."""
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from own_key_full_payload_identity_gate import verify_independent_signature_preserves_payload


def write_zip(path: Path, files: dict[str,bytes]) -> None:
    with zipfile.ZipFile(path,"w") as data:
        for name, payload in files.items():
            data.writestr(name,payload)


class NonSignaturePayloadEqualityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.original=Path(self.temp.name)/"original.apk"
        self.other=Path(self.temp.name)/"own.apk"
        self.contents={"AndroidManifest.xml":b"ORIGINAL_BINARY_MANIFEST",
                       "classes.dex":b"DEX-SYNTHETIC-VENDOR-DATA-SECRET",
                       "resources.arsc":b"RESOURCE-TEST-SYNTHETIC",
                       "assets/track-license.txt":b"only-fixture"}
        write_zip(self.original,{**self.contents,
                                 "META-INF/MANIFEST.MF":b"OLD_SIGNATURE_MANIFEST",
                                 "META-INF/VENDOR.SF":b"OLD_SIGNATURE",
                                 "META-INF/VENDOR.RSA":b"OLD_CERTIFICATE"})
        write_zip(self.other,{**self.contents,
                              "META-INF/MANIFEST.MF":b"DIFFERENT_SIG_MANIFEST",
                              "META-INF/CELIKOM.SF":b"DIFFERENT_SIGNATURE",
                              "META-INF/CELIKOM.RSA":b"NEW_CERTIFICATE"})

    def test_only_signing_artifacts_differ(self):
        x=verify_independent_signature_preserves_payload(self.original,self.other)
        self.assertTrue(x["non_signature_zip_entry_payloads_identical"])
        self.assertEqual(x["non_signature_zip_entries_checked"],4)
        for secret in ("track-license", "VENDOR", "DEX-SYNTHETIC","RESOURCE-TEST"):
            self.assertNotIn(secret,str(x))

    def test_manifest_content_change_is_rejected(self):
        write_zip(self.other,{**self.contents,
                              "AndroidManifest.xml":b"DIFFERENT_MANIFEST"})
        with self.assertRaisesRegex(ValueError,"PAYLOAD_CHECK_ENTRY_CONTENT_CHANGED"):
            verify_independent_signature_preserves_payload(self.original,self.other)

    def test_zip_entry_set_change_is_rejected(self):
        altered=dict(self.contents)
        del altered["resources.arsc"]
        write_zip(self.other,altered)
        with self.assertRaisesRegex(ValueError,"PAYLOAD_CHECK_ENTRY_SET_CHANGED"):
            verify_independent_signature_preserves_payload(self.original,self.other)

    def test_duplicate_non_signing_entries_are_rejected(self):
        with zipfile.ZipFile(self.other,"w") as data:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore",UserWarning)
                data.writestr("AndroidManifest.xml",b"A")
                data.writestr("AndroidManifest.xml",b"B")
        with self.assertRaisesRegex(ValueError,"PAYLOAD_CHECK_DUPLICATE_ENTRY"):
            verify_independent_signature_preserves_payload(self.original,self.other)

    def test_unexpected_public_sig_looking_asset_is_not_ignored(self):
        altered=dict(self.contents)
        altered["assets/signer_certificate.txt"]=b"DIFFERENT"
        write_zip(self.other,altered)
        with self.assertRaisesRegex(ValueError,"PAYLOAD_CHECK_ENTRY_SET_CHANGED"):
            verify_independent_signature_preserves_payload(self.original,self.other)


if __name__=="__main__":
    unittest.main()
