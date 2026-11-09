import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clone_native_identity_phase2_ephemeral import classify_clone_launch_logcat, summarize_installed_package_code_flags


class SafeCloneCrashClassificationTest(unittest.TestCase):
    def test_security_exception_without_exposing_raw_log(self):
        secret = "https://secret.invalid/never-output?access_token=PRIVATE_VALUE"
        raw = ("FATAL EXCEPTION: main\n"
               "Process: pro.celikom.yandex.nativeclonelab, PID: 1234\n"
               "java.lang.SecurityException: Permission Denial " + secret)
        report = classify_clone_launch_logcat(raw)
        self.assertTrue(report["fatal_exception_seen"])
        self.assertTrue(report["clone_process_named_in_crash"])
        self.assertTrue(report["security_exception_seen"])
        self.assertEqual([], report["bounded_missing_public_class_hints"])
        self.assertTrue(report["permission_denial_seen"])
        self.assertFalse(report["raw_log_included"])
        self.assertNotIn("PRIVATE_VALUE", str(report))
        self.assertNotIn("secret.invalid", str(report))

    def test_abi_and_class_loading_classification(self):
        report = classify_clone_launch_logcat(
            "java.lang.UnsatisfiedLinkError: dlopen failed\n"
            "java.lang.NoClassDefFoundError: Missing\n")
        self.assertTrue(report["native_library_error_seen"])
        self.assertTrue(report["class_loading_exception_seen"])
        self.assertFalse(report["security_exception_seen"])
        self.assertEqual([], report["bounded_missing_public_class_hints"])

    def test_report_only_publisher_class_name_without_raw_stack(self):
        raw = ('FATAL EXCEPTION: main\\n'
               'java.lang.ClassNotFoundException: Didn\'t find class '
               '"com.yandex.music.shared.player.MissingAudioClass" '
               'on path: DexPathList[[zip file "/tmp/private/token.txt"]]\\n'
               'https://private.invalid/?access_token=VERYSECRET\\n')
        report = classify_clone_launch_logcat(raw)
        self.assertEqual(["com.yandex.music.shared.player.MissingAudioClass"],
                         report["bounded_missing_public_class_hints"])
        self.assertNotIn("VERYSECRET", str(report))
        self.assertNotIn("DexPathList", str(report))
        self.assertNotIn("private.invalid", str(report))

    def test_missing_descriptor_without_log_dump(self):
        raw = 'java.lang.NoClassDefFoundError: Failed resolution of: Lru/yandex/music/SomeClass;'
        report = classify_clone_launch_logcat(raw)
        self.assertEqual(["ru.yandex.music.SomeClass"],
                         report["bounded_missing_public_class_hints"])

    def test_package_manager_flags_are_boolean_only(self):
        sample = ("Package [some.public.package] codePath=/data/app/base.apk\\n"
                  "  flags=[ HAS_CODE ALLOW_CLEAR_USER_DATA ]\\n"
                  "  classLoaderName=dalvik.system.PathClassLoader\\n"
                  "  private-tag=NEVER_EXPOSE_THIS\\n")
        report = summarize_installed_package_code_flags(sample)
        self.assertTrue(report["has_code_flag"])
        self.assertTrue(report["has_code_path_record"])
        self.assertTrue(report["has_base_apk_record"])
        self.assertTrue(report["has_classloader_record"])
        self.assertNotIn("NEVER_EXPOSE_THIS", str(report))

    def test_no_crash_produces_zero_flags(self):
        report = classify_clone_launch_logcat("")
        self.assertFalse(any(report.values()))


if __name__ == "__main__":
    unittest.main()
