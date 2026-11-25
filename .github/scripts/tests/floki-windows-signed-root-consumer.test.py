import hashlib
import re
import os
import pathlib
import runpy
import stat
import tempfile
import unittest

core=runpy.run_path(str(pathlib.Path(__file__).resolve().parents[1]/
                       "floki-windows-signed-root-consumer.py"))

class RootConsumerContractTests(unittest.TestCase):
    def test_only_exact_immutable_release_archive_names_accepted(self):
        good="windows-0.24.56-3-"+"a"*64+".zip"
        self.assertEqual(core["NAME"].fullmatch(good).groups(),("0.24.56","3","a"*64))
        for name in ("../windows-0.24.56-3-"+ "a"*64+".zip",
                     "windows-0.24.56-03-"+"a"*64+".zip",
                     "windows-0.24.56-0-"+"a"*64+".zip",
                     "windows-0.24.56-3-"+"Z"*64+".zip",
                     "windows-0.24.56-3-"+"a"*64+".zip/evil"):
            self.assertIsNone(core["NAME"].fullmatch(name))

    def test_runner_spool_untrusted_bytes_are_copied_and_sha_checked(self):
        if os.getuid()==0:
            self.skipTest("The isolated runner must not execute tests as root")
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);spool=root/"spool";spool.mkdir(mode=0o700)
            raw=b"PK"+b"valid-data-only-bytes"*20
            sha=hashlib.sha256(raw).hexdigest()
            name=f"windows-0.24.56-3-{sha}.zip"
            path=spool/name;path.write_bytes(raw);path.chmod(0o600)
            old=core["SPOOL"];core["SPOOL"]=spool
            try:
                pending=core["list_pending"]()
                self.assertEqual(len(pending),1)
                _,ver,expected,p,ino,dev,size=pending[0]
                self.assertEqual((ver,expected,p,size),("0.24.56",sha,path,len(raw)))
                dest=core["snapshot_into_root"](p,ino,dev,size,expected,root)
                self.assertEqual(dest.read_bytes(),raw)
                dest.unlink()
                with self.assertRaises(RuntimeError):
                    core["snapshot_into_root"](p,ino,dev,size,"0"*64,root)
                path.chmod(0o644)
                with self.assertRaises(RuntimeError):core["list_pending"]()
            finally:
                core["SPOOL"]=old

    def test_unknown_members_or_world_access_are_rejected(self):
        if os.getuid()==0:
            self.skipTest("The isolated runner must not execute tests as root")
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);spool=root/"spool";spool.mkdir(mode=0o700)
            old=core["SPOOL"];core["SPOOL"]=spool
            try:
                (spool/"unexpected").write_text("x")
                with self.assertRaises(RuntimeError):core["list_pending"]()
                (spool/"unexpected").unlink()
                spool.chmod(0o755)
                with self.assertRaises(RuntimeError):core["list_pending"]()
            finally:
                core["SPOOL"]=old


    def test_nginx_bootstrap_pythons_and_installer_hash_pins_match(self):
        directory=pathlib.Path(__file__).resolve().parents[1]
        nginx=(directory/"floki-windows-owner-download-bootstrap.sh").read_text()
        snippets=re.findall(r"<<'PY'\\n(.*?)\\nPY",nginx,re.S)
        self.assertGreaterEqual(len(snippets),2)
        for i,src in enumerate(snippets):
            compile(src,"nginx-bootstrap-"+str(i),"exec")
        self.assertIn("CELIKOM-Windows-latest.exe",nginx)
        self.assertIn("auth_basic",nginx)
        installer=(directory/"floki-windows-root-consumer-install.sh").read_text()
        for file in ("floki-windows-signed-root-consumer.py",
                     "floki-windows-owner-download-bootstrap.sh"):
            data=(directory/file).read_bytes()
            sha=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\\0"+data).hexdigest()
            self.assertIn(sha,installer,"installer must pin reviewed root source "+file)

if __name__=="__main__":
    unittest.main()
