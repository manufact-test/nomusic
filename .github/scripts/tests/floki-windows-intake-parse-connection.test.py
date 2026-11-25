import base64
import hashlib
import pathlib
import runpy
import unittest
core = runpy.run_path(str(pathlib.Path(__file__).resolve().parents[1] / "floki-windows-intake-parse-connection.py"))
parse = core["parse"]
PIN = "95.133.160.111 ssh-ed25519 " + base64.b64encode(b"\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20"+b"x"*32).decode()
KEY = "-----BEGIN OPENSSH PRIVATE KEY-----\nQUJD\n-----END OPENSSH PRIVATE KEY-----\n"


class EnrollmentTest(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(parse((PIN+"\n"+KEY).encode()), (PIN+"\n", KEY))
    def test_clipboard_whitespace(self):
        self.assertEqual(parse(("\ufeff\n  "+PIN.replace(" ssh-ed25519 ","  ssh-ed25519\t")+"  \r\n\r\n"+KEY.replace("\n","\r\n")+"\r\n").encode()),(PIN+"\n", KEY))
    def test_private_key_only_requires_independently_pinned_host(self):
        blob = base64.b64decode(PIN.split()[2])
        fingerprint = "SHA256:" + base64.b64encode(hashlib.sha256(blob).digest()).decode().rstrip("=")
        trusted = core["validate_trusted_pin"]((PIN+"\n").encode(), fingerprint)
        self.assertEqual(parse(KEY.encode(), trusted),(PIN+"\n",KEY))
        with self.assertRaises(ValueError):
            parse(KEY.encode())
        with self.assertRaisesRegex(ValueError,"HOST_FINGERPRINT_MISMATCH"):
            core["validate_trusted_pin"]((PIN+"\n").encode())
        other = "95.133.160.111 ssh-ed25519 " + base64.b64encode(blob[:-1]+b"z").decode()
        with self.assertRaisesRegex(ValueError,"BUNDLED_PIN_MISMATCH"):
            parse((other+"\n"+KEY).encode(), trusted)
    def test_single_line_envelope(self):
        raw = (PIN+"\n"+KEY).encode()
        envelope = b"CELIKOM-WINDOWS-INTAKE-V1:" + base64.b64encode(raw)
        self.assertEqual(parse(envelope+b"\n"),(PIN+"\n",KEY))
        with self.assertRaisesRegex(ValueError,"ENVELOPE_INVALID"):
            parse(b"CELIKOM-WINDOWS-INTAKE-V1:!!!!")
    def test_wrong_host(self):
        with self.assertRaisesRegex(ValueError,"HOST_PIN_LINE_INVALID"):
            parse((PIN.replace("95.133.160.111","127.0.0.1")+"\n"+KEY).encode())
    def test_missing_or_extra_text(self):
        for raw in (PIN+"\nQUJD\n",PIN+"\n"+KEY+"terminal prompt\n",PIN+"\n-----BEGIN OPENSSH PRIVATE KEY-----\n%bad\n-----END OPENSSH PRIVATE KEY-----\n"):
            with self.assertRaises(ValueError): parse(raw.encode())
    def test_wrong_pin_type(self):
        with self.assertRaisesRegex(ValueError,"HOST_PIN_TYPE_INVALID"):
            parse(("95.133.160.111 ssh-ed25519 QUJD\n"+KEY).encode())


if __name__ == "__main__": unittest.main()
