"""Unit tests for finite read-only true-ARM startup observation.

Synthetic fixtures only: no Yandex APK, Android guest, account or network.
"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from clone_main_crash_buffer import CLONE, classify_main_exit_status
from native_arm13_startup_observer import (
    classify_startup_events,
    only_new_main_exit_info,
    classify_new_main_log_signals,
    classify_live_main_log_signals,
    ORIGINAL,
)

SECRET = "PRIVATE_TOKEN_QWERTY"
BEFORE = (
    "ApplicationExitInfo #0:\n"
    f"pid=101 process={CLONE} reason=4 status=88 private={SECRET}\n"
)
AFTER = (
    f"ApplicationExitInfo #0:\n pid=102 process={CLONE} reason=1 status=0 secret={SECRET}\n"
    f"ApplicationExitInfo #1:\n pid=101 process={CLONE} reason=4 status=88 secret={SECRET}\n"
    f"ApplicationExitInfo #2:\n pid=103 process={CLONE}:AppMetrica reason=5 status=11\n"
    "ApplicationExitInfo #3:\n pid=104 process=ru.yandex.music reason=4 status=88\n"
)


def event(tag, value):
    return f"11-11 12:33:00.000 I {tag}: [0, 102, {value}, {SECRET}]\n"


def log(pid, severity, tag, message):
    return f"11-11 12:33:00.123   {pid}   {pid} {severity} {tag}: {message}\n"


class ArmStartupObserverTests(unittest.TestCase):
    def test_main_events_are_ordered_and_helper_not_main(self):
        raw = (
            event("am_proc_start", CLONE + ":AppMetrica")
            + event("am_proc_start", CLONE)
            + event("am_resume_activity", CLONE + "/ru.yandex.music.main.MainScreenActivity")
            + event("am_finish_activity", CLONE + "/ru.yandex.music.main.MainScreenActivity")
            + event("am_proc_died", CLONE)
            + event("am_crash", ORIGINAL)
        )
        out = classify_startup_events(raw, CLONE)
        self.assertEqual(out["main_event_order"], [
            "am_proc_start", "am_resume_activity",
            "am_finish_activity", "am_proc_died",
        ])
        self.assertTrue(out["process_start_seen"])
        self.assertTrue(out["activity_resumed_seen"])
        self.assertTrue(out["finish_event_before_death"])
        self.assertTrue(out["auxiliary_process_events_seen"])
        self.assertFalse(out["system_crash_or_anr_event_seen"])
        self.assertFalse(out["raw_event_log_exposed"])
        self.assertNotIn(SECRET, str(out))
        self.assertNotIn("102", str(out))

    def test_original_exact_scoping_and_no_vendor_inference(self):
        raw = (
            event("am_proc_start", ORIGINAL + ":helper")
            + event("am_proc_start", ORIGINAL)
            + event("am_resume_activity", ORIGINAL + "/ru.yandex.music.main.MainScreenActivity")
            + event("am_proc_died", CLONE)
        )
        out = classify_startup_events(raw, ORIGINAL)
        self.assertEqual(out["main_event_order"],
                         ["am_proc_start", "am_resume_activity"])
        self.assertFalse(out["process_died_seen"])
        self.assertTrue(out["causality_not_proven"])
        self.assertNotIn(SECRET, str(out))

    def test_event_log_without_exact_main_fails_closed(self):
        raw = event("am_proc_died", CLONE + ":helper")
        out = classify_startup_events(raw, CLONE)
        self.assertEqual(out["main_event_order"], [])
        self.assertFalse(out["process_died_seen"])
        self.assertTrue(out["auxiliary_process_events_seen"])

    def test_reject_unknown_package(self):
        with self.assertRaises(ValueError):
            classify_startup_events("anything", "com.private.invalid")

    def test_discard_stale_main_exit_records_but_not_new_zero(self):
        new, summary = only_new_main_exit_info(BEFORE, AFTER)
        self.assertTrue(summary["new_main_exit_record_seen"])
        self.assertEqual(summary["historical_main_exit_records_ignored"], 1)
        result = classify_main_exit_status(new)
        self.assertEqual(result["latest_main_exit_reason"], "EXIT_SELF")
        self.assertEqual(result["latest_main_exit_status"], "ZERO")
        self.assertEqual(result["main_exit_record_count_bounded"], 1)
        self.assertNotIn(SECRET, str(summary))

    def test_old_exit_only_must_not_turn_into_new_cause(self):
        new, summary = only_new_main_exit_info(BEFORE, BEFORE)
        self.assertEqual(new, "")
        self.assertFalse(summary["new_main_exit_record_seen"])
        result = classify_main_exit_status(new)
        self.assertEqual(result["latest_main_exit_reason"], "NOT_OBSERVED")

    def test_recent_pid_scoped_main_log_reveals_only_fixed_classes(self):
        filtered, _ = only_new_main_exit_info(BEFORE, AFTER)
        raw = (
            log(101, "F", "AndroidRuntime", "FATAL EXCEPTION: main " + SECRET)
            + log(103, "E", "System.err", "java.lang.SecurityException " + SECRET)
            + log(102, "E", "System.err", "java.lang.IllegalStateException " + SECRET)
            + log(102, "E", "System.err", "uncaughtException " + SECRET)
            + log(102, "W", "System.err", "java.lang.UnsatisfiedLinkError " + SECRET)
        )
        out = classify_new_main_log_signals(filtered, raw)
        self.assertTrue(out["new_main_exit_pid_available"])
        self.assertTrue(out["main_scoped_warning_or_error_seen"])
        self.assertTrue(out["main_scoped_error_severity_seen"])
        self.assertTrue(out["uncaught_handler_marker_seen"])
        self.assertFalse(out["android_runtime_fatal_seen"])
        self.assertEqual(out["throwable_groups"], ["ILLEGAL_STATE", "NATIVE_LINK"])
        self.assertFalse(out["raw_main_log_exposed"])
        self.assertNotIn(SECRET, str(out))
        self.assertNotIn("java.", str(out))
        self.assertNotIn("102", str(out))

    def test_only_bounded_subsystem_groups_from_current_error_stack(self):
        filtered, _ = only_new_main_exit_info(BEFORE, AFTER)
        private = "/data/user/0/private/account/DO_NOT_LEAK"
        raw = (
            log(101, "E", "System.err", "java.lang.SecurityException " + SECRET)
            + log(101, "E", "System.err", "    at com.yandex.passport.Private.read(" + private + ")")
            + log(102, "E", "System.err", "java.lang.IllegalArgumentException " + SECRET)
            + log(102, "E", "System.err", "    at ru.yandex.music.Private.run(" + private + ")")
            + log(102, "E", "System.err", "    at com.yandex.passport.Private.lookup(" + private + ")")
            + log(102, "W", "System.err", "    at java.lang.Thread.run(Thread.java:10)")
            + log(102, "E", "System.err", "    at com.vendor.unknown.Helper.go(" + private + ")")
        )
        out = classify_new_main_log_signals(filtered, raw)
        self.assertIn("ILLEGAL_ARGUMENT", out["throwable_groups"])
        self.assertNotIn("SECURITY", out["throwable_groups"])
        self.assertEqual(out["exception_stack_subsystems"], [
            "YANDEX_MUSIC", "YANDEX_PASSPORT",
            "ANDROID_RUNTIME", "OTHER_OR_UNKNOWN",
        ])
        self.assertEqual(out["exception_stack_frames_seen_bounded"], 4)
        self.assertTrue(out["system_err_tag_seen"])
        self.assertFalse(out["android_runtime_tag_seen"])
        for secret in ("PRIVATE", "DO_NOT_LEAK", "token", "/data/user", "102"):
            self.assertNotIn(secret, str(out))

    def test_real_logcat_brief_event_tag_format_with_process_pid(self):
        # Real adb logcat -b events -v brief uses I/am_proc_start( 1234):,
        # not "I am_proc_start:". The previous parser silently missed it.
        raw = (
            "I/am_proc_start( 1234): [0,231," + CLONE + ",private=NOPE]\n"
            "I/am_resume_activity( 1234): [0,private," + CLONE + "/Main]\n"
            "I/am_proc_start( 1234): [0,231," + CLONE + ":helper]\n"
            "I/am_finish_activity( 1234): [0,private," + CLONE + "/Main]\n"
            "I/am_proc_died( 1234): [0,231," + CLONE + "]\n"
        )
        out = classify_startup_events(raw, CLONE)
        self.assertEqual(out["main_event_order"], [
            "am_proc_start", "am_resume_activity",
            "am_finish_activity", "am_proc_died",
        ])
        self.assertTrue(out["known_event_tag_seen_any_package"])
        self.assertTrue(out["activity_resumed_seen"])
        self.assertTrue(out["finish_event_before_death"])
        self.assertTrue(out["auxiliary_process_events_seen"])
        self.assertNotIn("1234", str(out))
        self.assertNotIn("NOPE", str(out))

    def test_differential_event_buffer_coverage_is_not_lifecycle_proof(self):
        out = classify_startup_events(
            event("am_proc_start", "unrelated.example.package"), CLONE)
        self.assertTrue(out["known_event_tag_seen_any_package"])
        self.assertFalse(out["exact_main_package_token_seen"])
        self.assertGreater(out["buffer_entry_count_bounded"], 0)
        self.assertFalse(out["process_start_seen"])

    def test_unattributed_or_stale_pid_never_leaks(self):
        out = classify_new_main_log_signals(
            "", log(101, "E", "AndroidRuntime",
                    "java.lang.SecurityException " + SECRET))
        self.assertEqual(out["throwable_groups"], [])
        self.assertFalse(out["main_scoped_warning_or_error_seen"])
        self.assertFalse(out["new_main_exit_pid_available"])
        self.assertNotIn(SECRET, str(out))

    def test_live_signed_original_can_have_same_exception_marker(self):
        original_log = (
            log(612, "E", "System.err", "java.lang.IllegalStateException " + SECRET)
            + log(612, "E", "System.err", "java.lang.IllegalArgumentException " + SECRET)
            + log(613, "F", "AndroidRuntime", "FATAL EXCEPTION: main " + SECRET)
        )
        witness = classify_live_main_log_signals("612", original_log)
        self.assertTrue(witness["new_main_exit_pid_available"])
        self.assertEqual(witness["throwable_groups"],
                         ["ILLEGAL_STATE", "ILLEGAL_ARGUMENT"])
        self.assertTrue(witness["illegal_state_error_severity_seen"])
        self.assertFalse(witness["illegal_state_warning_severity_seen"])
        self.assertFalse(witness["android_runtime_fatal_seen"])
        self.assertNotIn(SECRET, str(witness))
        self.assertNotIn("612", str(witness))

    def test_live_original_scope_rejects_multi_pid_injection_or_no_pid(self):
        raw = (log(612, "E", "AndroidRuntime", "java.lang.IllegalStateException ")
               + log(613, "W", "System.err", "java.lang.IllegalStateException "))
        for candidate in ("", "612 613", "612;echo SECRET", "-1", "0", "612\n613",
                          "999999999", "1.5", "612 garbage"):
            with self.subTest(candidate=candidate):
                result = classify_live_main_log_signals(candidate, raw)
                self.assertFalse(result["new_main_exit_pid_available"])
                self.assertFalse(result["main_scoped_error_severity_seen"])
                self.assertEqual(result["throwable_groups"], [])
        with self.assertRaises(ValueError):
            classify_live_main_log_signals(None, raw)

    def test_warning_vs_error_illegal_state_not_conflated(self):
        raw = log(615, "W", "System.err", "java.lang.IllegalStateException " + SECRET)
        result = classify_live_main_log_signals("615", raw)
        self.assertTrue(result["illegal_state_warning_severity_seen"])
        self.assertFalse(result["illegal_state_error_severity_seen"])
        self.assertFalse(result["main_scoped_error_severity_seen"])
        self.assertTrue(result["main_scoped_warning_or_error_seen"])
        self.assertNotIn(SECRET, str(result))

    def test_no_event_does_not_imply_healthy_app(self):
        out = classify_startup_events("", CLONE)
        self.assertFalse(out["process_start_seen"])
        self.assertFalse(out["process_died_seen"])
        self.assertTrue(out["causality_not_proven"])


if __name__ == "__main__":
    unittest.main()
