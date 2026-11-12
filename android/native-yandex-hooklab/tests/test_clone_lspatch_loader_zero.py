"""LSPatch zero-signature-bypass clone gate, without any app/patcher execution."""
import io
import struct
import json
import sys
import unittest
import tempfile
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clone_lspatch_loader_zero import check_zero_loader, mirror_x86_loader_resource_for_arm_bridge, verify_native_loader_elf_offsets

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
    def runcheck(self,level=0,modules=False,changed=False,expected_siglevel=0):
        orig,patched=self.make(level,modules,changed)
        import unittest.mock
        import clone_lspatch_loader_zero as gate
        with unittest.mock.patch.object(gate.source,"apkmeta",return_value={
            "name":"pro.celikom.yandex.nativeclonelab","versionCode":"24026531",
            "split":""}), unittest.mock.patch.object(gate,"fingerprint",return_value="a"*64):
            return check_zero_loader(patched,orig,"a"*64,DummyArsc,
                                     expected_siglevel=expected_siglevel)
    def test_zero_loader_verifies_inner_host_not_stub(self):
        r=self.runcheck()
        self.assertEqual(r["signature_bypass_level"],0)
        self.assertEqual(r["embedded_origin_dex_count"],1)
        self.assertTrue(r["embedded_origin_sha256_payload_parity"])
        self.assertFalse(r["audio_swap_tested"])
    def test_exact_2025_host_version_is_separately_checked(self):
        from unittest.mock import patch
        import clone_lspatch_loader_zero as gate
        original, patched = self.make(level=2)
        expected = {"name": "pro.celikom.yandex.nativeclonelab",
                    "versionCode": "24025542", "split": ""}
        with patch.object(gate.source, "apkmeta", return_value=expected), \
             patch.object(gate, "fingerprint", return_value="a" * 64):
            accepted = check_zero_loader(patched, original, "a" * 64,
                                         DummyArsc, expected_siglevel=2,
                                         expected_version="24025542")
            self.assertTrue(accepted["embedded_origin_sha256_payload_parity"])
            self.assertEqual(accepted["signature_bypass_level"], 2)
            with self.assertRaisesRegex(DummyError, "METALOADER_CLONE_IDENTITY_INVALID"):
                check_zero_loader(patched, original, "a" * 64, DummyArsc,
                                  expected_siglevel=2)
            with self.assertRaisesRegex(DummyError, "METALOADER_UNSUPPORTED_HOST_VERSION"):
                check_zero_loader(patched, original, "a" * 64, DummyArsc,
                                  expected_siglevel=2, expected_version="fake")

    def test_verified_loader_requires_all_four_aligned_abis(self):
        import io
        import struct
        from clone_lspatch_loader_zero import verify_native_loader_elf_offsets
        f=self.root/"loader-layout.apk"
        with zipfile.ZipFile(f,"w") as z:
            for abi,machine,klass in (
                    ("armeabi-v7a",40,1),("arm64-v8a",183,2),
                    ("x86",3,1),("x86_64",62,2)):
                start=z.fp.tell()
                name="assets/lspatch/so/"+abi+"/liblspatch.so"
                pad=(-(start+30+len(name)))%4096
                if 0 < pad < 4:pad+=4096
                info=zipfile.ZipInfo(name)
                info.compress_type=zipfile.ZIP_STORED
                if pad: info.extra=struct.pack("<HH",0xEFA1,pad-4)+bytes(pad-4)
                data=bytearray(20)
                data[:4]=b"\x7fELF"
                data[4]=klass
                data[18:20]=struct.pack("<H",machine)
                z.writestr(info,bytes(data))
        layout=verify_native_loader_elf_offsets(f)
        self.assertEqual(set(layout),{"armeabi-v7a","arm64-v8a","x86","x86_64"})
        self.assertTrue(all(x["page_aligned_4096"] for x in layout.values()))


    def test_emulator_mirror_only_changes_x86_loader_resource(self):
        arm="assets/lspatch/so/armeabi-v7a/liblspatch.so"
        x86="assets/lspatch/so/x86/liblspatch.so"
        contents={
            arm:b"\x7fELF"+bytes([1])+bytes(13)+struct.pack("<H",40)+bytes(12),
            x86:b"\x7fELF"+bytes([1])+bytes(13)+struct.pack("<H",3)+bytes(12),
            "assets/lspatch/so/arm64-v8a/liblspatch.so":
                 b"\x7fELF"+bytes([2])+bytes(13)+struct.pack("<H",183)+bytes(12),
            "assets/lspatch/so/x86_64/liblspatch.so":
                 b"\x7fELF"+bytes([2])+bytes(13)+struct.pack("<H",62)+bytes(12),
            "classes.dex":b"STUB_UNCHANGED",
            "assets/lspatch/origin.apk":b"ORIGIN_UNCHANGED"}
        original=self.root/"mirror-source.apk"
        with zipfile.ZipFile(original,"w") as z:
            for name,body in contents.items():
                info=zipfile.ZipInfo(name)
                info.compress_type=zipfile.ZIP_STORED
                z.writestr(info,body)
        result=self.root/"bridge-mirror.apk"
        report=mirror_x86_loader_resource_for_arm_bridge(original,result)
        self.assertEqual(report["mirrored_x86_resource_machine"],40)
        with zipfile.ZipFile(original) as before, zipfile.ZipFile(result) as after:
            self.assertEqual(set(before.namelist()),set(after.namelist()))
            for name in before.namelist():
                self.assertEqual(after.read(name),
                                 before.read(arm if name==x86 else name))
        layouts=verify_native_loader_elf_offsets(result, expected_x86_machine=40)
        self.assertTrue(all(v["page_aligned_4096"] for v in layouts.values()))
        with self.assertRaises(ValueError):
            verify_native_loader_elf_offsets(result)
        with self.assertRaises(ValueError):
            mirror_x86_loader_resource_for_arm_bridge(original,result)

    def test_never_allow_signature_bypass(self):
        for level in (1,2,3,True,"0"):
            with self.assertRaisesRegex(DummyError,"NONZERO_SIGNATURE_BYPASS"):
                self.runcheck(level=level)
    def test_owner_authorized_signature_level2_structural_only_never_defaults_on(self):
        # Explicit expected level is a TEST assertion, not a CI deployment
        # switch; the executable wrapper checks exact ARM13 branch first.
        report = self.runcheck(level=2, expected_siglevel=2)
        self.assertEqual(report["signature_bypass_level"], 2)
        self.assertTrue(report["embedded_origin_sha256_payload_parity"])
        self.assertFalse(report["audio_swap_tested"])
        for level in [0, 1, 3, True, "2"]:
            with self.assertRaisesRegex(DummyError, "NONZERO_SIGNATURE_BYPASS"):
                self.runcheck(level=level, expected_siglevel=2)

    def test_eval_mode_requires_exact_disposable_branch_and_arm13(self):
        from unittest.mock import patch
        from clone_lspatch_loader_zero import lab_sigcompat_level
        with patch.dict("os.environ", {"CELIKOM_A1_EVAL_SIGBYPASS_LEVEL": "2",
                                     "GITHUB_ACTIONS": "true",
                                     "GITHUB_REPOSITORY": "manufact-test/nomusic",
                                     "GITHUB_REF_NAME": "main"}, clear=True):
            with self.assertRaisesRegex(ValueError,
                                        "SIGCOMPAT2_REQUIRES_ISOLATED_ARM13_EXPERIMENT_ONLY"):
                lab_sigcompat_level()
        with patch.dict("os.environ", {"CELIKOM_A1_EVAL_SIGBYPASS_LEVEL": "1"},
                        clear=True):
            with self.assertRaises(ValueError): lab_sigcompat_level()
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(lab_sigcompat_level(), 0)

    def test_fail_closed_on_unapproved_module(self):
        with self.assertRaisesRegex(DummyError,"EMBEDDED_MODULE"):
            self.runcheck(modules=True)
    def test_fail_closed_on_altered_host_code(self):
        with self.assertRaisesRegex(DummyError,"NATIVE_CODE_DRIFT"):
            self.runcheck(changed=True)

if __name__=="__main__":
    unittest.main()
