"""Pure local synthetic UI witness classification. No APK/Android launched."""
import importlib.util
from pathlib import Path
import struct
import unittest

PATH = Path(__file__).resolve().parents[1] / "ci" / "chromasync_native_ui_witness.py"
spec = importlib.util.spec_from_file_location("ui_witness", PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class NativeUiWitnessTest(unittest.TestCase):
    def test_focused_cloned_window(self):
        row = m.classify_focus(
            "mCurrentFocus=Window{12 u0 app.chromasync.yamclone/ru.yandex.music.main.MainScreenActivity}\n"
        )
        self.assertTrue(row["window_focus_record_available"])
        self.assertTrue(row["clone_focused_or_targeted"])

    def test_stock_window_is_not_competitor(self):
        row = m.classify_focus(
            "mCurrentFocus=Window{12 u0 ru.yandex.music/ru.yandex.music.main.MainScreenActivity}"
        )
        self.assertFalse(row["clone_focused_or_targeted"])

    def test_native_hierarchy_with_one_clone_node(self):
        row = m.classify_ui_tree(
            '<hierarchy><node package="android"/><node package="app.chromasync.yamclone"/></hierarchy>'
        )
        self.assertEqual(row["ui_node_count"], 2)
        self.assertEqual(row["ui_clone_node_count"], 1)
        self.assertTrue(row["ui_contains_clone_nodes"])

    def test_foreign_hierarchy_does_not_prove_clone_rendering(self):
        row = m.classify_ui_tree('<hierarchy><node package="com.android.launcher"/></hierarchy>')
        self.assertFalse(row["ui_contains_clone_nodes"])

    def test_png_header_is_only_screen_availability(self):
        good = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 1080, 1920)
        row = m.classify_png_header(good)
        self.assertTrue(row["screenshot_png_valid"])
        self.assertEqual(row["screenshot_width"], 1080)
        self.assertFalse(m.classify_png_header(b"not png")["screenshot_png_valid"])


    def test_general_focus_detects_clone(self):
        dump = "mCurrentFocus=Window{123 u0 app.chromasync.yamclone/ru.yandex.music.main.MainScreenActivity}"
        self.assertTrue(m.classify_general_focus(dump)["global_focus_clone"])
        self.assertTrue(m.classify_general_focus(dump)["clone_window_record_present"])

    def test_general_focus_does_not_invent_focus(self):
        dump = "Window{345 u0 app.chromasync.yamclone/ru.yandex.music.main.MainScreenActivity}"
        self.assertFalse(m.classify_general_focus(dump)["global_focus_present"])

    def test_dump_command_status_is_safe_boolean_categories(self):
        good = m.classify_dump_command(0, "UI hierchary dumped to: /sdcard/x.xml")
        self.assertTrue(good["command_exit_zero"])
        self.assertTrue(good["dump_claims_complete"])
        bad = m.classify_dump_command(0, "ERROR: java.lang.SecurityException")
        self.assertTrue(bad["dump_had_security_error"])
        self.assertTrue(bad["dump_had_command_error"])


if __name__ == "__main__":
    unittest.main()
