import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clone_native_identity_phase2_ephemeral import classify_clone_launch_logcat, summarize_installed_package_code_flags, classify_activity_start, classify_activity_exit_info, classify_clone_process_events, classify_main_pid_scoped_system_logs, disposable_foreground_snapshot, full_native_main_ui_pass, classify_nonblocking_activity_start


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

    def test_nonblocking_start_only_confirms_dispatch_not_foreground(self):
        report = classify_nonblocking_activity_start(
            "Starting: Intent { act=android.intent.action.MAIN cmp=secret.private }")
        self.assertTrue(report["activity_status_ok"])
        self.assertTrue(report["nonblocking_dispatch_only"])
        self.assertFalse(report["raw_activity_output_exposed"])
        self.assertNotIn("secret.private", str(report))
        self.assertFalse(full_native_main_ui_pass(
            [{"ps_main_process_alive": False}], report,
            {"activity_resumed_for_package": False, "window_focus_for_package": False}))
        failed = classify_nonblocking_activity_start("Error: Activity not started")
        self.assertFalse(failed["activity_status_ok"])
        self.assertTrue(failed["activity_explicit_error"])

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
               "reason=5 (APP CRASH(NATIVE))\n"
               "ApplicationExitInfo #1:\n"
               "  process=pro.celikom.yandex.nativeclonelab\n"
               "  reason=4 (APP CRASH(EXCEPTION))\n"
               "  trace=NEVER_EXPOSE")
        report = classify_activity_exit_info(raw)
        self.assertTrue(report["exit_reason_crash"])
        self.assertFalse(report["exit_reason_crash_native"])
        self.assertTrue(report["auxiliary_exit_record_seen"])
        self.assertFalse(report["unattributed_exit_record_seen"])
        self.assertNotIn("NEVER_EXPOSE", str(report))

    def test_actual_aosp_android11_status_and_subreason_are_sanitized(self):
        sample = ("ApplicationExitInfo #0:\n"
                  "  timestamp=ANY pid=100 realUid=1234\n"
                  "  process=pro.celikom.yandex.nativeclonelab reason=1 (EXIT_SELF) "
                  "subreason=0 (UNKNOWN) status=0\n"
                  "  description=secret.invalid?token=DO_NOT_PRINT\n"
                  "ApplicationExitInfo #1:\n"
                  "  process=pro.celikom.yandex.nativeclonelab:AppMetrica "
                  "reason=4 (APP CRASH(EXCEPTION)) subreason=0 status=3\n")
        observed = classify_activity_exit_info(sample)
        self.assertTrue(observed["exit_reason_exit_self"])
        self.assertTrue(observed["main_exit_status_available"])
        self.assertEqual(observed["main_exit_status"], 0)
        self.assertTrue(observed["main_exit_self_status_zero"])
        self.assertFalse(observed["main_exit_self_status_nonzero"])
        self.assertEqual(observed["main_exit_subreason"], 0)
        self.assertFalse(observed["exit_reason_crash"])
        self.assertNotIn("DO_NOT_PRINT", str(observed))

    def test_nonzero_main_exit_status_not_confused_with_helper(self):
        raw = ("ApplicationExitInfo #0:\n  process=pro.celikom.yandex.nativeclonelab:AppMetrica "
               "reason=1 status=0\n"
               "ApplicationExitInfo #1:\n  process=pro.celikom.yandex.nativeclonelab "
               "reason=1 (EXIT_SELF) subreason=4 status=137\n")
        observed = classify_activity_exit_info(raw)
        self.assertEqual(observed["main_exit_status"], 137)
        self.assertTrue(observed["main_exit_self_status_nonzero"])
        self.assertFalse(observed["main_exit_self_status_zero"])
        self.assertEqual(observed["main_exit_subreason"], 4)

    def test_stage_timeline_reports_events_only_not_raw_lines(self):
        pkg = "pro.celikom.yandex.nativeclonelab"
        raw = (f"I/am_proc_start: [0,9,10010,{pkg},top]\n"
               f"I/am_create_activity: [0,8,24,{pkg}/ru.yandex.music.main.MainScreenActivity]\n"
               f"I/am_resume_activity: [0,8,24,{pkg}/ru.yandex.music.main.MainScreenActivity]\n"
               f"I/am_proc_died: [0,9,{pkg}] PRIVATE_TOKEN")
        out = classify_clone_process_events(raw)
        self.assertEqual(out["main_lifecycle_stages"],
                         ["am_proc_start", "am_create_activity", "am_resume_activity", "am_proc_died"])
        self.assertTrue(out["main_activity_lifecycle_observed"])
        self.assertNotIn("PRIVATE_TOKEN", str(out))

    def test_main_pid_only_logging_never_leaks_credentials(self):
        exit_info = (
            "ApplicationExitInfo #0:\n"
            "  timestamp=X pid=404 realUid=10234\n"
            "  process=pro.celikom.yandex.nativeclonelab reason=1 status=0\n"
            "ApplicationExitInfo #1:\n"
            "  timestamp=X pid=405 realUid=10234\n"
            "  process=pro.celikom.yandex.nativeclonelab:AppMetrica reason=1 status=0\n")
        logs = (
            "11-09 21:59:00.011  402  402 E System.err: java.lang.SecurityException: ORIGINAL_PRIVATE\n"
            "11-09 21:59:00.012  405  405 E System.err: java.lang.RuntimeException: AUX_PRIVATE\n"
            "11-09 21:59:00.013  404  404 E System.err: java.lang.IllegalStateException: token=MAIN_PRIVATE\n"
            "11-09 21:59:00.014  404  404 W Other: unrelated marker\n")
        report = classify_main_pid_scoped_system_logs(exit_info, logs)
        self.assertTrue(report["main_exit_pid_records_available"])
        self.assertTrue(report["main_pid_scoped_system_err_seen"])
        self.assertTrue(report["main_pid_java_exception_marker_seen"])
        self.assertTrue(report["main_pid_scoped_error_severity_seen"])
        self.assertFalse(report["main_pid_security_exception_marker_seen"])
        for secret in ("ORIGINAL_PRIVATE", "AUX_PRIVATE", "MAIN_PRIVATE", "token="):
            self.assertNotIn(secret, str(report))

    def test_pid_scoped_runtime_throwable_types_and_stage(self):
        exit_info = (
            "ApplicationExitInfo #0:\n  timestamp=X pid=611\n"
            "  process=pro.celikom.yandex.nativeclonelab reason=1 status=0\n"
            "ApplicationExitInfo #1:\n  timestamp=X pid=612\n"
            "  process=pro.celikom.yandex.nativeclonelab:AppMetrica reason=1 status=0\n")
        logs = (
            "11-09 21:59:00.010  612  612 E AndroidRuntime: FATAL EXCEPTION: BAD_HELPER\n"
            "11-09 21:59:00.011  612  612 E AndroidRuntime: java.lang.SecurityException: SECRETHELPER\n"
            "11-09 21:59:00.012  611  611 E AndroidRuntime: FATAL EXCEPTION: main\n"
            "11-09 21:59:00.013  611  611 E AndroidRuntime: java.lang.RuntimeException: "
            "Unable to instantiate provider PRIVATE_PATH token=NEVER_LOG\n"
            "11-09 21:59:00.014  611  611 E AndroidRuntime: Caused by: "
            "android.content.res.Resources$NotFoundException: SECRET\n")
        result = classify_main_pid_scoped_system_logs(exit_info, logs)
        self.assertTrue(result["main_pid_android_runtime_fatal_seen"])
        self.assertEqual(result["main_pid_android_runtime_initialization_stage"],
                         "PROVIDER_INSTANTIATE")
        self.assertIn("java.lang.RuntimeException",
                      result["main_pid_bounded_runtime_throwable_types"])
        self.assertIn("android.content.res.Resources$NotFoundException",
                      result["main_pid_bounded_caused_by_throwable_types"])
        self.assertFalse(result["main_pid_security_exception_marker_seen"])
        for word in ("SECRETHELPER", "NEVER_LOG", "PRIVATE_PATH", "SECRET", "BAD_HELPER"):
            self.assertNotIn(word, str(result))

    def test_nonruntime_vendor_exception_is_only_a_class_not_private_log(self):
        exit_info = ("ApplicationExitInfo #0:\n pid=818\n "
                     "process=pro.celikom.yandex.nativeclonelab reason=1 status=0\n"
                     "ApplicationExitInfo #1:\n pid=819\n "
                     "process=pro.celikom.yandex.nativeclonelab:AppMetrica reason=1\n")
        logs = (
            "11-09 21:59:00.011  818  818 E VendorCrash: java.lang.IllegalStateException: "
            "token=SECRET_MAIN https://secret.invalid/a\n"
            "11-09 21:59:00.012  818  818 E SystemStuff: "
            "android.content.res.Resources$NotFoundException: SECRET_RESOURCE\n"
            "11-09 21:59:00.013  819  819 E VendorCrash: java.lang.SecurityException: "
            "SECRET_HELPER\n"
            "11-09 21:59:00.014  817  817 E VendorCrash: "
            "java.lang.RuntimeException: SECRET_OTHER\n")
        result = classify_main_pid_scoped_system_logs(exit_info, logs)
        self.assertTrue(result["main_pid_nonruntime_error_lines_observed"])
        self.assertEqual(
            result["main_pid_bounded_nonruntime_error_throwable_types"],
            ["java.lang.IllegalStateException",
             "android.content.res.Resources$NotFoundException"])
        for secret in ("SECRET_MAIN", "SECRET_RESOURCE", "SECRET_HELPER",
                       "SECRET_OTHER", "secret.invalid", "token="):
            self.assertNotIn(secret, str(result))


    def test_main_pid_nonruntime_error_frame_subsystems_are_labels_only(self):
        exit_info = ("ApplicationExitInfo #0:\n pid=987\n "
                     "process=pro.celikom.yandex.nativeclonelab reason=1 status=0\n"
                     "ApplicationExitInfo #1:\n pid=988\n "
                     "process=pro.celikom.yandex.nativeclonelab:AppMetrica reason=1\n")
        logs = (
            "11-09 21:59:00.010  987  987 E Vendor: java.lang.IllegalStateException: TOKEN_PRIVATE\n"
            "11-09 21:59:00.011  987  987 E Vendor:     at com.yandex.passport.internal.Auth.init(Auth.java:34)\n"
            "11-09 21:59:00.012  987  987 E Vendor:     at ru.yandex.music.YMApplication.onCreate(YMApplication.java:4)\n"
            "11-09 21:59:00.013  988  988 E Vendor:     at com.google.android.gms.Secret.method(Secret.java:1)\n")
        result = classify_main_pid_scoped_system_logs(exit_info, logs)
        self.assertEqual(result["main_pid_nonruntime_exception_frame_subsystems"],
                         ["YANDEX_PASSPORT", "YANDEX_MUSIC"])
        self.assertNotIn("Auth.init", str(result))
        self.assertNotIn("TOKEN_PRIVATE", str(result))
        self.assertNotIn("Secret", str(result))


    def test_main_pid_log_fails_closed_if_no_process_pid(self):
        raw = "ApplicationExitInfo #0: process=pro.celikom.yandex.nativeclonelab reason=1"
        log = "11-09 21:59:00.013  404  404 E System.err: java.lang.SecurityException: SECRET"
        result = classify_main_pid_scoped_system_logs(raw, log)
        self.assertFalse(result["main_exit_pid_records_available"])
        self.assertFalse(result["main_pid_security_exception_marker_seen"])
        self.assertNotIn("SECRET", str(result))

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
        raw = ("I/am_proc_start: [0,111,10000,pro.celikom.yandex.nativeclonelab,top]\n"
               "I/am_proc_died: [0,111,pro.celikom.yandex.nativeclonelab]\n"
               "I/am_crash: [0,111,pro.celikom.yandex.nativeclonelab]\n"
               "I/am_proc_start: [0,112,10000,pro.celikom.yandex.nativeclonelab:AppMetrica,service]\n"
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

    def test_main_and_resumed_but_not_window_focused_is_not_pass(self):
        self.assertFalse(full_native_main_ui_pass(
            [{"direct_pid_alive": True, "ps_main_process_alive": True}],
            {"activity_status_ok": True, "activity_explicit_error": False},
            {"activity_resumed_for_package": True, "window_focus_for_package": False}))

    def test_only_real_main_and_resumed_activity_pass(self):
        self.assertTrue(full_native_main_ui_pass(
            [{"direct_pid_alive": True, "ps_main_process_alive": True}],
            {"activity_status_ok": True, "activity_explicit_error": False},
            {"activity_resumed_for_package": True, "window_focus_for_package": True}))

    def test_no_crash_produces_zero_flags(self):
        report = classify_clone_launch_logcat("")
        self.assertFalse(any(report.values()))


if __name__ == "__main__":
    unittest.main()
