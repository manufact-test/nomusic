"""LSPatch zero-signature-bypass clone gate, without any app/patcher execution."""
import io
import json
import sys
import unittest
import tempfile
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clone_lspatch_loader_zero import check_zero_loader

class DummyError(Exception):
    pass
class DummyArsc:
    TrialError=DummyError

def apk(path, data):
    with zipfile.ZipFile(path,"w") as z:
        for name,payload in data.items():z.writestr(name,payload)
    return path

class LoaderZeroTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
    def make(self,level=0,modules=False,changed=False):
        original=self.root/"original.apk"
        apk(original,{"classes.dex":b"host-original","lib/arm/lib.so":b"native"})
        raw=io.BytesIO()
        with zipfile.ZipFile(raw,"w") as z:
            z.writestr("classes.dex", b"host-modified" if changed else b"host-original")
            z.writestr("lib/arm/lib.so",b"native")
        content={"classes.dex":b"stub-loader",
                 "assets/lspatch/origin.apk":raw.getvalue(),
                 "assets/lspatch/loader.dex":b"loader",
                 "assets/lspatch/config.json":json.dumps(
                  {"sigBypassLevel":level,"useManager":False}).encode()}
        if modules: content["assets/lspatch/modules/module.apk"]=b"notallowed"
        out=apk(self.root/"patched.apk",content)
        return original,out
    def runcheck(self,level=0,modules=False,changed=False):
        orig,patched=self.make(level,modules,changed)
        import unittest.mock
        import clone_lspatch_loader_zero as gate
        with unittest.mock.patch.object(gate.source,"apkmeta",return_value={
            "name":"pro.celikom.yandex.nativeclonelab","versionCode":"24026531",
            "split":""}), unittest.mock.patch.object(gate,"fingerprint",return_value="a"*64):
            return check_zero_loader(patched,orig,"a"*64,DummyArsc)
    def test_zero_loader_verifies_inner_host_not_stub(self):
        r=self.runcheck()
        self.assertEqual(r["signature_bypass_level"],0)
        self.assertEqual(r["embedded_origin_dex_count"],1)
        self.assertTrue(r["embedded_origin_sha256_payload_parity"])
        self.assertFalse(r["audio_swap_tested"])
    def test_never_allow_signature_bypass(self):
        for level in (1,2,3,True,"0"):
            with self.assertRaisesRegex(DummyError,"NONZERO_SIGNATURE_BYPASS"):
                self.runcheck(level=level)
    def test_fail_closed_on_unapproved_module(self):
        with self.assertRaisesRegex(DummyError,"EMBEDDED_MODULE"):
            self.runcheck(modules=True)
    def test_fail_closed_on_altered_host_code(self):
        with self.assertRaisesRegex(DummyError,"NATIVE_CODE_DRIFT"):
            self.runcheck(changed=True)

if __name__=="__main__":
    unittest.main()
