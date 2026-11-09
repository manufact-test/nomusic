import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clone_native_identity_phase2_ephemeral import classify_clone_launch_logcat, summarize_installed_package_code_flags, classify_activity_start, classify_activity_exit_info, classify_clone_process_events, disposable_foreground_snapshot, full_native_main_ui_pass


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

    def test_activity_result_without_raw_data(self):
        report = classify_activity_start(
            "Status: ok\\nLaunchState: COLD\\nActivity: pro.celikom.lab.Main\\nsecret=NEVER_SHARE")
        self.assertTrue(report["activity_status_ok"])
        self.assertTrue(report["launch_state_cold"])
        self.assertFalse(report["activity_explicit_error"])
        self.assertNotIn("NEVER_SHARE", str(report))

    def test_activity_failure_does_not_dump_raw(self):
        report = classify_activity_start("Error: Activity not started with private=NEVER_SHARE")
        self.assertTrue(report["activity_explicit_error"])
        self.assertNotIn("NEVER_SHARE", str(report))

    def test_exit_reason_classification_no_raw_data(self):
        raw = ("ApplicationExitInfo #0: process=pro.celikom.yandex.nativeclonelab "
               "reason=1 (EXIT SELF) raw_token=NEVER_SHARE")
        report = classify_activity_exit_info(raw)
        self.assertTrue(report["exit_reason_exit_self"])
        self.assertTrue(report["main_exit_record_seen"])
        self.assertFalse(report["exit_reason_crash"])
        self.assertNotIn("NEVER_SHARE", str(report))

    def test_android_11_numeric_crash_reason_main_vs_appmetrica(self):
        raw = ("ApplicationExitInfo #0: process=pro.celikom.yandex.nativeclonelab:AppMetrica "
               "reason=5 (APP CRASH(NATIVE))\\n"
               "ApplicationExitInfo #1:\\n"
               "  process=pro.celikom.yandex.nativeclonelab\\n"
               "  reason=4 (APP CRASH(EXCEPTION))\\n"
               "  trace=NEVER_EXPOSE")
        report = classify_activity_exit_info(raw)
        self.assertTrue(report["exit_reason_crash"])
        self.assertFalse(report["exit_reason_crash_native"])
        self.assertTrue(report["auxiliary_exit_record_seen"])
        self.assertFalse(report["unattributed_exit_record_seen"])
        self.assertNotIn("NEVER_EXPOSE", str(report))

    def test_helper_only_is_not_main_exit(self):
        report = classify_activity_exit_info(
            "ApplicationExitInfo #0: process=pro.celikom.yandex.nativeclonelab:AppMetrica "
            "reason=4 (APP CRASH(EXCEPTION))")
        self.assertFalse(report["exit_reason_crash"])
        self.assertFalse(report["main_exit_record_seen"])
        self.assertTrue(report["auxiliary_exit_record_seen"])

    def test_exit_info_without_process_is_unattributed(self):
        report = classify_activity_exit_info(
            "ApplicationExitInfo #0: reason=4 (APP CRASH(EXCEPTION))")
        self.assertFalse(report["exit_reason_crash"])
        self.assertTrue(report["unattributed_crash_reason_seen"])

    def test_process_events_main_vs_auxiliary_and_no_raw(self):
        raw = ("I/am_proc_start: [0,111,10000,pro.celikom.yandex.nativeclonelab,top]\\n"
               "I/am_proc_died: [0,111,pro.celikom.yandex.nativeclonelab]\\n"
               "I/am_crash: [0,111,pro.celikom.yandex.nativeclonelab]\\n"
               "I/am_proc_start: [0,112,10000,pro.celikom.yandex.nativeclonelab:AppMetrica,service]\\n"
               "PRIVATE_VALUE")
        report = classify_clone_process_events(raw)
        self.assertTrue(report["am_proc_start_main_seen"])
        self.assertTrue(report["am_proc_died_main_seen"])
        self.assertTrue(report["am_crash_main_seen"])
        self.assertTrue(report["auxiliary_process_events_seen"])
        self.assertFalse(report["am_kill_main_seen"])
        self.assertNotIn("PRIVATE_VALUE", str(report))

    def test_only_helper_events_never_claim_main(self):
        report = classify_clone_process_events(
            "I/am_proc_died: [0,123,pro.celikom.yandex.nativeclonelab:AppMetrica]")
        self.assertFalse(report["am_proc_died_main_seen"])
        self.assertTrue(report["auxiliary_process_events_seen"])

    def test_foreground_snapshot_only_reports_package_membership(self):
        pkg = "pro.celikom.yandex.nativeclonelab"
        activities = ("mResumedActivity: ActivityRecord{u0 " + pkg +
                      "/ru.yandex.music.main.MainScreenActivity t4}\\n"
                      "secret=NEVER_SHARE\\n")
        windows = ("mCurrentFocus=Window{u0 " + pkg +
                   "/ru.yandex.music.main.MainScreenActivity}\\n"
                   "token=NEVER_SHARE\\n")
        with patch("clone_native_identity_phase2_ephemeral.arsc.run",
                   side_effect=[activities, windows]):
            result = disposable_foreground_snapshot(pkg)
        self.assertTrue(result["activity_resumed_for_package"])
        self.assertTrue(result["window_focus_for_package"])
        self.assertFalse(result["raw_activity_or_window_output_exposed"])
        self.assertNotIn("NEVER_SHARE", str(result))

    def test_foreground_snapshot_rejects_wrong_package(self):
        with self.assertRaisesRegex(Exception, "UNAPPROVED_FOREGROUND_PACKAGE"):
            disposable_foreground_snapshot("some.other.package")

    def test_auxiliary_appmetrica_never_counts_as_main_player(self):
        samples = [{
            "any_named_process_alive": True,
            "ps_auxiliary_process_alive": True,
            "safe_auxiliary_process_suffixes": ["AppMetrica"],
            "direct_pid_alive": False,
            "ps_main_process_alive": False,
        }]
        self.assertFalse(full_native_main_ui_pass(
            samples, {"activity_status_ok": True, "activity_explicit_error": False},
            {"activity_resumed_for_package": True}))

    def test_main_process_without_resumed_activity_is_not_a_pass(self):
        self.assertFalse(full_native_main_ui_pass(
            [{"direct_pid_alive": True, "ps_main_process_alive": True}],
            {"activity_status_ok": True, "activity_explicit_error": False},
            {"activity_resumed_for_package": False}))

    def test_only_real_main_and_resumed_activity_pass(self):
        self.assertTrue(full_native_main_ui_pass(
            [{"direct_pid_alive": True, "ps_main_process_alive": True}],
            {"activity_status_ok": True, "activity_explicit_error": False},
            {"activity_resumed_for_package": True}))

    def test_no_crash_produces_zero_flags(self):
        report = classify_clone_launch_logcat("")
        self.assertFalse(any(report.values()))


if __name__ == "__main__":
    unittest.main()
