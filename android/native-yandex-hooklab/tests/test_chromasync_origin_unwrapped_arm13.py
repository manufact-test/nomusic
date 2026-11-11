"""Synthetic ZIP safety validation only. NOT a real Yandex launch."""
import importlib.util
import io
import zipfile
from pathlib import Path
import unittest
import sys

FILE = Path(__file__).resolve().parents[1] / "ci" / "chromasync_origin_unwrapped_arm13.py"
sys.path.insert(0, str(FILE.parent))
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


    def test_exit_info_scopes_exact_main_not_helper(self):
        raw = ("ApplicationExitInfo #0 processName=app.chromasync.yamclone:helper reason=4 status=1\n"
               "ApplicationExitInfo #1 processName=app.chromasync.yamclone reason=1 status=0\n")
        seen = m.classify_exit_info(raw)
        self.assertTrue(seen["main_exit_info_record_found"])
        self.assertTrue(seen["main_exit_reason_self"])
        self.assertTrue(seen["main_exit_self_status_zero"])
        self.assertFalse(seen["main_exit_reason_crash_java"])
        self.assertFalse(seen["raw_android_exit_history_shared"])

    def test_events_scope_exact_main_only(self):
        text = (
            "am_proc_died app.chromasync.yamclone:aux\n"
            "am_proc_died app.chromasync.yamclone\n"
            "am_crash app.chromasync.yamclone:aux\n"
        )
        seen = m.classify_process_events(text)
        self.assertTrue(seen["am_proc_died_main"])
        self.assertFalse(seen["am_crash_main"])
        self.assertFalse(seen["raw_android_event_log_shared"])


if __name__ == "__main__":
    unittest.main()
