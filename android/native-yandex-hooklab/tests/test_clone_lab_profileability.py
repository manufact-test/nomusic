"""Safety tests for standard Android profiler on non-publisher clone only."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import xml.etree.ElementTree as ET
from clone_lab_profileability import (
    enable_private_lab_shell_profiling, classify_compiled_shell_profiler,
)

NS = "{http://schemas.android.com/apk/res/android}"
BASE = ('<manifest xmlns:android="http://schemas.android.com/apk/res/android"'
        ' package="pro.celikom.yandex.nativeclonelab">'
        '<application android:name="ru.yandex.music.YMApplication">'
        '<profileable android:shell="false"/></application></manifest>')

class TestLabProfileable(unittest.TestCase):
    def test_only_shell_attribute_changes(self):
        before = ET.fromstring(BASE)
        after = ET.fromstring(enable_private_lab_shell_profiling(BASE.encode()))
        self.assertEqual(before.find("application").attrib, after.find("application").attrib)
        self.assertEqual(after.find("application").find("profileable").get(NS + "shell"), "true")
        self.assertEqual(before.find("application").find("profileable").get(NS + "shell"), "false")
        self.assertEqual(after.get("package"), "pro.celikom.yandex.nativeclonelab")
    def test_missing_profileable_added(self):
        out = ET.fromstring(enable_private_lab_shell_profiling(
            BASE.replace('<profileable android:shell="false"/>', "").encode()))
        self.assertEqual(out.find("application").find("profileable").get(NS + "shell"), "true")
    def test_compiled_profileable_element_is_actually_enabled(self):
        sample = (
            "    E: application (line=1)\n"
            "      E: profileable (line=2)\n"
            "        A: android:shell(0x01010510)=(type 0x12)0xffffffff\n"
            "        A: android:enabled(0x0101000e)=(type 0x12)0xffffffff\n"
            "      E: activity (line=3)\n"
        )
        result = classify_compiled_shell_profiler(sample)
        self.assertTrue(result["compiled_shell_profiler_true"])
        self.assertTrue(result["compiled_profileable_declaration_seen"])
        self.assertFalse(result["raw_manifest_exposed"])
        self.assertFalse(classify_compiled_shell_profiler(
            sample.replace("0xffffffff", "0x0"))["compiled_shell_profiler_true"])
        self.assertFalse(classify_compiled_shell_profiler(
            "    E: application (line=1)")["compiled_profileable_declaration_seen"])

    def test_compiled_profileable_rejects_other_element_shell_attribute(self):
        fake = (
            "E: application\n"
            "  A: android:shell(0x01010510)=(type 0x12)0xffffffff\n"
            "E: profileable\n"
            "  A: android:shell(0x01010510)=(type 0x12)0x0\n"
        )
        self.assertFalse(classify_compiled_shell_profiler(
            fake)["compiled_shell_profiler_true"])

    def test_no_original_package(self):
        for pkg in ("ru.yandex.music", "other.app"):
            with self.assertRaisesRegex(ValueError, "NOT_THE_ISOLATED"):
                enable_private_lab_shell_profiling(BASE.replace("pro.celikom.yandex.nativeclonelab",pkg).encode())
    def test_no_debuggable_or_shared_uid(self):
        values = [
            (BASE.replace('android:name="ru.yandex.music.YMApplication"', 'android:name="Other.App"'), "UNEXPECTED"),
            (BASE.replace('<application ', '<application android:debuggable="true" '), "DEBUGGABLE"),
            (BASE.replace('<manifest ', '<manifest android:sharedUserId="ru.yandex.music" '), "SHARED_USER")
        ]
        for raw,msg in values:
            with self.assertRaisesRegex(ValueError, msg):
                enable_private_lab_shell_profiling(raw.encode())

if __name__ == "__main__":
    unittest.main()
