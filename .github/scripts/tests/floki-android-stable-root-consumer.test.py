import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("android_stable_owner",
    ROOT/"floki-android-stable-root-consumer.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def proof():
    return {
        "source_run":45589980361,"source_attempt":1,
        "version":"0.3.94","version_code":95,
        "apk_sha256":"d43d2dd12dfa6a4cd79094abccabad67080c6f02542cd25edff55b3d36018469",
        "apk_size":8845385,"apk_name":"CELIKOM-Android-0.3.94-SIGNED.apk",
        "signer_sha256":mod.CERT,"package":mod.PKG
    }

def manifest():
    p=proof()
    return {
        "schemaVersion":1,"enabled":True,"channel":"stable",
        "packageName":mod.PKG,"versionCode":95,"versionName":"0.3.94",
        "signerSha256":mod.CERT,"apkSha256":p["apk_sha256"],
        "sizeBytes":p["apk_size"],"minSdk":28,
        "apkUrl":"https://celikom.com/releases/android/95-"+p["apk_sha256"]+".apk",
        "notesRu":"Переход на новый сервер."
    }

class SignedStableSafety(unittest.TestCase):
    def test_accepted_contract(self):
        p=proof();m=manifest()
        self.assertEqual(mod.validate(m,p,95,p["apk_sha256"]),p["apk_name"])
    def test_reject_alternate_host_signer_and_identity(self):
        p=proof()
        for change in ["apkUrl","signerSha256","versionCode","enabled","packageName"]:
            with self.subTest(change=change),self.assertRaises(RuntimeError):
                m=manifest();m[change]=("https://evil.example/release.apk" if change=="apkUrl"
                        else False if change=="enabled" else 96 if change=="versionCode"
                        else "invalid")
                mod.validate(m,p,95,p["apk_sha256"])
    def test_reject_apk_identity_and_repackaging(self):
        for key,value in [
            ("version","0.3.93"),("apk_name","../payload.apk"),
            ("apk_sha256","0"*64),("package","org.fake"),
            ("signer_sha256","b"*64),("version_code",94)]:
            with self.subTest(key=key),self.assertRaises(RuntimeError):
                p=proof();p[key]=value
                mod.validate(manifest(),p,95,proof()["apk_sha256"])
    def test_reject_duplicate_keys(self):
        with self.assertRaises(RuntimeError):
            mod.json_no_duplicates([("versionCode",95),("versionCode",96)])
if __name__=="__main__":
    unittest.main()
