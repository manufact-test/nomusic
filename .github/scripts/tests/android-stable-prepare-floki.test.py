import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

path = pathlib.Path(__file__).resolve().parents[1] / "android-stable-prepare-floki.py"
spec = importlib.util.spec_from_file_location("android_prepare", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class AndroidStableTest(unittest.TestCase):
    def fixture(self, code=94, origin=m.ORIGIN):
        h = hashlib.sha256(b"a" * 100000).hexdigest()
        return dict(schemaVersion=1, enabled=True, channel="stable", packageName=m.PACKAGE,
                    versionCode=code, versionName="0.3.93", signerSha256=m.SIGNER,
                    apkSha256=h, sizeBytes=100000, minSdk=28,
                    apkUrl=f"{origin}/releases/android/{code}-{h}.apk", notesRu="Test")

    def evidence(self, code=94):
        return (
            "Verified using v2 scheme (APK Signature Scheme v2): true\n"
            "Verified using v3 scheme (APK Signature Scheme v3): true\n"
            f"Signer #1 certificate SHA-256 digest: {m.SIGNER}\n",
            f"package: name='{m.PACKAGE}' versionCode='{code}' versionName='0.3.93' platformBuildVersionName=''\n"
            "sdkVersion:'28'\n"
        )

    def test_manifest_fails_closed(self):
        base = self.fixture()
        self.assertEqual(m.validate_manifest(base), base)
        for change in ({"signerSha256":"0"*64}, {"packageName":"other"}, {"versionCode":True},
                       {"apkUrl":base["apkUrl"].replace(m.ORIGIN,m.OLD_ORIGIN)},
                       {"apkUrl":base["apkUrl"]+"?x=1"}, {"sizeBytes":99999}, {"notesRu":"<bad>"},
                       {"minSdk":29}, {"versionName":"1.0.0"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                m.validate_manifest(base | change)

    def test_signature_and_package_contract(self):
        sig,badging = self.evidence()
        m.verify_tool_output(sig,badging,self.fixture())
        m.verify_tool_output(sig.replace("v2): true","v2): false"),badging,self.fixture())
        m.verify_tool_output(sig.replace("v3): true","v3): false"),badging,self.fixture())
        for s,b in ((sig.replace(m.SIGNER,"0"*64),badging),
                    (sig+"Signer #2 certificate SHA-256 digest: "+"1"*64+"\n",badging),
                    (sig.replace("v2): true","v2): false").replace("v3): true","v3): false"),badging),
                    (sig,badging.replace("versionCode='94'","versionCode='93'")),
                    (sig,badging.replace(m.PACKAGE,"other")),
                    (sig,badging.replace("sdkVersion:'28'","sdkVersion:'29'"))):
            with self.assertRaises(ValueError):
                m.verify_tool_output(s,b,self.fixture())

    def test_private_candidate_is_immutable_and_monotonic(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            current=root/"current.json"
            current.write_text(json.dumps(self.fixture(93,m.OLD_ORIGIN)))
            apk=root/"candidate.apk"
            apk.write_bytes(b"a"*100000)
            target=root/"candidate"
            signature,badging=self.evidence()
            with patch.object(m,"run_tool",side_effect=[signature,badging]):
                new=m.prepare(current,apk,target,"0.3.93",94,"Test","apksigner","aapt")
            self.assertEqual(m.load_manifest(target/"stable.json"),new)
            self.assertEqual((target/pathlib.Path(new["apkUrl"]).name).read_bytes(),apk.read_bytes())
            self.assertEqual(target.stat().st_mode & 0o777,0o700)
            for code,out in [(93,root/"downgrade"),(94,target)]:
                with self.assertRaises(ValueError):
                    m.prepare(current,apk,out,"0.3.93",code,"Test","apksigner","aapt")
            self.assertFalse((root/"downgrade").exists())
            apk.write_bytes(b"b"*100000)
            with self.assertRaises(ValueError):
                m.verify_apk(apk,new,"apksigner","aapt")

    def test_bad_signature_never_leaves_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            current=root/"current.json"; current.write_text(json.dumps(self.fixture(93)))
            apk=root/"candidate.apk"; apk.write_bytes(b"a"*100000)
            out=root/"candidate"
            with patch.object(m,"run_tool",side_effect=["invalid", self.evidence()[1]]):
                with self.assertRaises(ValueError):
                    m.prepare(current,apk,out,"0.3.93",94,"Test","apksigner","aapt")
            self.assertFalse(out.exists())
            self.assertEqual(sorted(x.name for x in root.iterdir()),["candidate.apk","current.json"])


if __name__ == "__main__":
    unittest.main()
