"""Synthetic ZIP safety validation only. NOT a real Yandex launch."""
import importlib.util
import io
import zipfile
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / "ci" / "chromasync_origin_unwrapped_arm13.py"
spec = importlib.util.spec_from_file_location("chromasync_origin", FILE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def archive(*, dex_count=6, loader=False):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("AndroidManifest.xml", b"synthetic-manifest")
        for index in range(1, dex_count + 1):
            z.writestr("classes.dex" if index == 1 else f"classes{index}.dex", b"dex\n035\x00synthetic")
        z.writestr("lib/arm64-v8a/libplaceholder.so", b"no-code")
        if loader:
            z.writestr("assets/lspatch/config.json", '{"sigBypassLevel":2}')
    return buf.getvalue()


class UnwrappedOriginTests(unittest.TestCase):
    def test_exact_six_dex_host_structure(self):
        result = m.inspect_nested_origin(archive())
        self.assertEqual(result["original_nested_dex_count"], 6)
        self.assertFalse(result["origin_lspatch_loader_embedded"])
        self.assertTrue(result["original_nested_native_libs_present"])

    def test_wrong_dex_count_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "STRUCTURE_MISMATCH"):
            m.inspect_nested_origin(archive(dex_count=5))

    def test_nested_lspatch_loader_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "CONTAINS_OUTER_LOADER"):
            m.inspect_nested_origin(archive(loader=True))

    def test_corrupt_bytes_rejected(self):
        with self.assertRaises(zipfile.BadZipFile):
            m.inspect_nested_origin(b"broken")

    def test_no_launch_on_non_arm_ci(self):
        class NotAllowed:
            serial = "127.0.0.1:5555"
            def shell(self, *_):
                raise AssertionError("Guest touched before ARM guard")
        with self.assertRaisesRegex(RuntimeError, "ONLY_DISPOSABLE"):
            m.run(Path("missing.apk"), NotAllowed())


if __name__ == "__main__":
    unittest.main()
