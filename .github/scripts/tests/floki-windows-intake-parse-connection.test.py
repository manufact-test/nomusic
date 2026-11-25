import base64
import pathlib
import runpy
import unittest
parse = runpy.run_path(str(pathlib.Path(__file__).resolve().parents[1] / "floki-windows-intake-parse-connection.py"))["parse"]
PIN = "95.133.160.111 ssh-ed25519 " + base64.b64encode(b"\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20"+b"x"*32).decode()
KEY = "-----BEGIN OPENSSH PRIVATE KEY-----\nQUJD\n-----END OPENSSH PRIVATE KEY-----\n"


class EnrollmentTest(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(parse((PIN+"\n"+KEY).encode()), (PIN+"\n", KEY))
    def test_clipboard_whitespace(self):
        self.assertEqual(parse(("\ufeff\n  "+PIN.replace(" ssh-ed25519 ","  ssh-ed25519\t")+"  \r\n\r\n"+KEY.replace("\n","\r\n")+"\r\n").encode()),(PIN+"\n", KEY))
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
