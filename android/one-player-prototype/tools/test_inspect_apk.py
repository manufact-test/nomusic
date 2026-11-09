import importlib.util
import pathlib
import tempfile
import unittest
import zipfile

SPEC = importlib.util.spec_from_file_location("inspect_apk", pathlib.Path(__file__).with_name("inspect_apk.py"))
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class InspectorTest(unittest.TestCase):
    def test_valid_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            apk = pathlib.Path(d) / "test.apk"
            with zipfile.ZipFile(apk, "w") as z:
                z.writestr("classes.dex", b"dex\nandroidx/media3\0DataSource$Factory")
                z.writestr("lib/arm64-v8a/libexample.so", b"fake")
                z.writestr("AndroidManifest.xml", b"not a real manifest")
            data = mod.inspect(apk)
            self.assertEqual(data["zip_integrity"], "ok")
            self.assertEqual(data["dex_entries"], ["classes.dex"])
            self.assertEqual(data["native_library_abis"], ["arm64-v8a"])
            self.assertTrue(data["player_marker_hits"]["androidx_media3"])
            self.assertTrue(data["player_marker_hits"]["data_source_factory"])
            self.assertFalse(data["player_marker_hits"]["legacy_exoplayer"])
            self.assertEqual(len(data["apk_sha256"]), 64)

    def test_bad_archive(self):
        with tempfile.TemporaryDirectory() as d:
            apk = pathlib.Path(d) / "not.zip"
            apk.write_bytes(b"not an apk")
            with self.assertRaises(zipfile.BadZipFile):
                mod.inspect(apk)


if __name__ == "__main__":
    unittest.main()
