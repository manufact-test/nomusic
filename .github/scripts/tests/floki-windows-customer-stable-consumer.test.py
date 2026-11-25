import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
import unittest

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT / "floki-windows-customer-stable-consumer.py"
spec=importlib.util.spec_from_file_location("customer_windows",FILE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class CustomerWindowsContract(unittest.TestCase):
    def test_version_sort_and_reject_path(self):
        self.assertGreater(m.version_tuple("0.24.56"),m.version_tuple("0.24.55"))
        self.assertLess(m.version_tuple("0.24.9"),m.version_tuple("0.24.56"))
        for value in ["0.24.056","../0.24.56","0.24.56.exe","0.24.56/other",""]:
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                m.version_tuple(value)

    def test_disabled_feed_no_publish(self):
        with patch.object(m.os,"geteuid",return_value=0), \
             patch.object(m,"secure_directory"), \
             patch.object(m.Path,"is_dir",return_value=True), \
             patch.object(m.Path,"is_symlink",return_value=False), \
             patch.object(m.os,"open",return_value=88), \
             patch.object(m.fcntl,"flock"), \
             patch.object(m.os,"close"), \
             patch.object(m,"approved",return_value=None), \
             patch.object(m,"publish",side_effect=AssertionError("MUST_NOT_PUBLISH")):
            m.main()

    def test_public_version_directories_stay_nginx_readable_under_umask_077(self):
        import os,stat,tempfile
        with tempfile.TemporaryDirectory() as t:
            base=Path(t)/"windows-customer-stable"
            (base/"versions").mkdir(parents=True)
            manifest=json.dumps({"version":"0.24.55","sequence":2,"sha256":"a"*64}).encode()
            sig=b"s"*70
            with patch.object(m,"CUSTOMER",base), \
                 patch.object(m,"verify_signed",return_value={
                    "manifest.json":manifest,"manifest.json.sig":sig}), \
                 patch.object(m,"secure_directory"), \
                 patch.object(m,"atomic_immutable_copy"), \
                 patch.object(m,"atomically_point_accepted_installer"), \
                 patch.object(m.os,"chown"), \
                 patch.object(m,"verify_public"):
                old_umask=os.umask(0o077)
                try:
                    m.publish({"version":"0.24.55","sequence":2,
                               "sha256":"a"*64,"owner_accepted":True})
                finally:
                    os.umask(old_umask)
            version_dir=base/"versions"/"0.24.55"
            self.assertEqual(stat.S_IMODE(version_dir.stat().st_mode),0o755)
            self.assertEqual(json.loads((base/"accepted.json").read_text())["https_verified"],True)

    def test_public_nginx_routes_never_point_at_private_signed_source(self):
        path=ROOT/"floki-windows-customer-stable-install.sh"
        script=path.read_text()
        self.assertIn("auth_basic off;",script)
        self.assertEqual(script.count("allow all;"),4)
        self.assertIn("/srv/celikom-releases/public/windows-customer-stable",script)
        self.assertNotIn("alias /srv/celikom-releases/windows/customer-stable",script)
        self.assertIn("CUSTOMER_WINDOWS_NGINX_PARENT_NOT_TRAVERSABLE",script)

    def test_approval_requires_explicit_owner_flag(self):
        import subprocess
        valid={"schema":1,"channel":"customer-stable","approved":{
            "version":"0.24.57","sequence":4,"sha256":"a"*64,
            "owner_accepted":True}}
        with patch.object(m.subprocess,"run",return_value=type("Result",(),{
            "stdout":json.dumps(valid).encode()})):
            self.assertEqual(m.approved()["version"],"0.24.57")
            invalid=json.loads(json.dumps(valid))
            invalid["approved"]["owner_accepted"]=False
            with patch.object(m.subprocess,"run",return_value=type("Result",(),{
                "stdout":json.dumps(invalid).encode()})):
                with self.assertRaises(RuntimeError):
                    m.approved()


if __name__=="__main__":
    unittest.main()
