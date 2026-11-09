"""Synthetic apksigner output contract tests (no binaries or network)."""
import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import audit_rustore_host_once as host

CERT=host.RUSTORE_SHA256_CERT
class SignerFormatTests(unittest.TestCase):
    def run_signer(self,text):
        with patch.object(host.subprocess,"run") as fake:
            fake.return_value.returncode=0
            fake.return_value.stdout=text
            fake.return_value.stderr=""
            return host.signer_digest(Path("/offline/synthetic.apk"),"/mock/apksigner")
    def test_v3_0_certificate_matches_pinned(self):
        text="Verified using v2 scheme (APK Signature Scheme v2): true\n"+\
            "V3.0 Signer: certificate SHA-256 digest: "+CERT+"\n"
        self.assertEqual(self.run_signer(text),CERT)
    def test_v2_and_v3_same_cert(self):
        text="Verified using v3 scheme (APK Signature Scheme v3): true\n"+\
            "V3.0 Signer: certificate SHA-256 digest: "+CERT+"\n"+\
            "Signer #1 certificate SHA-256 digest: "+CERT+"\n"
        self.assertEqual(self.run_signer(text),CERT)
    def test_wrong_certificate_rejected(self):
        text="Verified using v2 scheme (APK Signature Scheme v2): true\n"+\
            "V3.0 Signer: certificate SHA-256 digest: "+("0"*64)+"\n"
        with self.assertRaisesRegex(ValueError,"certificate"):
            self.run_signer(text)
    def test_legacy_only_not_accepted(self):
        text="Verified using v2 scheme (APK Signature Scheme v2): false\n"+\
            "Verified using v3 scheme (APK Signature Scheme v3): false\n"+\
            "V3.0 Signer: certificate SHA-256 digest: "+CERT+"\n"
        with self.assertRaisesRegex(ValueError,"v2/v3"):
            self.run_signer(text)

if __name__=="__main__":unittest.main()
