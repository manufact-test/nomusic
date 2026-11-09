"""Synthetic-only DEX tests; no proprietary Android package is downloaded/committed."""
import importlib.util
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "inspect_android_host.py"
spec = importlib.util.spec_from_file_location("inspect_android_host", MODULE)
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)


def synthetic_dex(method="createMediaSource", defined=True):
    names = [
        "Landroidx/media3/exoplayer/source/DefaultMediaSourceFactory;",
        "Landroidx/media3/common/MediaItem;",
        "Landroidx/media3/exoplayer/source/MediaSource;",
        method,
    ]
    buf = bytearray(112 + 4 * len(names) + 4 * 3 + 12 + 8 + (32 if defined else 0))
    buf[:8] = b"dex\n039\0"
    str_off = 112
    type_off = str_off + 4 * len(names)
    proto_off = type_off + 12
    method_off = proto_off + 12
    class_off = method_off + 8
    params_off = len(buf)
    struct.pack_into("<II", buf, 56, len(names), str_off)
    struct.pack_into("<II", buf, 64, 3, type_off)
    struct.pack_into("<II", buf, 72, 1, proto_off)
    struct.pack_into("<II", buf, 88, 1, method_off)
    struct.pack_into("<II", buf, 96, int(defined), class_off if defined else 0)
    for i in range(3):
        struct.pack_into("<I", buf, type_off + i * 4, i)
    struct.pack_into("<HHI", buf, method_off, 0, 0, 3)
    if defined:
        struct.pack_into("<I", buf, class_off, 0)
    buf.extend(struct.pack("<IH", 1, 1))
    struct.pack_into("<III", buf, proto_off, 3, 2, params_off)
    for i, name in enumerate(names):
        assert len(name) < 128
        string_pos = len(buf)
        buf.extend(bytes([len(name)]) + name.encode("ascii") + b"\0")
        struct.pack_into("<I", buf, str_off + i * 4, string_pos)
    struct.pack_into("<I", buf, 32, len(buf))
    return bytes(buf)


class InspectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "native-host-test.apk"

    def write(self, dex):
        with zipfile.ZipFile(self.path, "w") as z:
            z.writestr("classes.dex", dex)

    def test_declared_media_factory_detected_but_not_proven(self):
        self.write(synthetic_dex())
        report = inspector.inspect([self.path])
        d = report["apks"][0]["dex"][0]
        self.assertEqual(report["verdict"], "NO_NATIVE_SOURCE_HOOK_PROVEN")
        self.assertEqual(d["defined_media_libraries"], ["media3"])
        self.assertTrue(d["method_references"][0]["defined_in_this_dex"])
        self.assertIn("MediaItem", d["method_references"][0]["signature"])
        self.assertNotIn("OAuth", str(report))

    def test_reference_only_is_not_defined_hook(self):
        self.write(synthetic_dex(defined=False))
        d = inspector.inspect([self.path])["apks"][0]["dex"][0]
        self.assertEqual(d["defined_media_libraries"], [])
        self.assertFalse(d["method_references"][0]["defined_in_this_dex"])

    def test_method_not_in_allowlist_is_silent(self):
        self.write(synthetic_dex(method="getSecret"))
        d = inspector.inspect([self.path])["apks"][0]["dex"][0]
        self.assertEqual(d["method_reference_count"], 0)

    def test_zip_without_dex_fails(self):
        with zipfile.ZipFile(self.path, "w") as z:
            z.writestr("AndroidManifest.xml", "junk")
        with self.assertRaisesRegex(ValueError, "no DEX"):
            inspector.inspect([self.path])

    def test_xapk_bundle_reads_only_code_split(self):
        self.write(synthetic_dex())
        bundle = Path(self.tmp.name) / "host.xapk"
        cfg = Path(self.tmp.name) / "config.apk"
        with zipfile.ZipFile(cfg, "w") as z:
            z.writestr("AndroidManifest.xml", "stub")
        with zipfile.ZipFile(bundle, "w") as z:
            z.writestr("base.apk", self.path.read_bytes())
            z.write(cfg, "config.arm64_v8a.apk")
        report = inspector.inspect([bundle])
        self.assertEqual(report["apk_with_dex_count"], 1)
        self.assertEqual(report["apks"][0]["split_label"], "base.apk")

    def test_malformed_dex_fails(self):
        self.write(b"dex\n039\0" + b"\0" * 110)
        with self.assertRaises(inspector.DexError):
            inspector.inspect([self.path])

    def test_tampered_table_is_rejected(self):
        bad = bytearray(synthetic_dex())
        struct.pack_into("<I", bad, 60, len(bad) - 1)
        self.write(bytes(bad))
        with self.assertRaises(inspector.DexError):
            inspector.inspect([self.path])


if __name__ == "__main__":
    unittest.main()
