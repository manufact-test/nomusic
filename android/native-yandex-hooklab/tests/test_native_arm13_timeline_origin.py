"""Synthesized timestamped Android event/main interleaving; privacy gates."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from clone_main_crash_buffer import CLONE
from native_arm13_startup_observer import ORIGINAL
from native_arm13_timeline_origin import classify_merged_startup_timeline

SECRET = "ACCESS_TOKEN_SECRET_XX"
EXIT = (
    f"ApplicationExitInfo #0:\n pid=701 process={CLONE} reason=1 status=0\n"
    f"ApplicationExitInfo #1:\n pid=702 process={CLONE} reason=1 status=0\n"
    f"ApplicationExitInfo #2:\n pid=703 process={CLONE}:AppMetrica reason=5 status=9\n"
)


def event(time, name, victim, helper=False):
    if name == "am_proc_start":
        payload = f"[0,{victim},10012,{CLONE + ':helper' if helper else CLONE},service,{CLONE}]"
    else:
        payload = f"[0,{victim},{CLONE + ':helper' if helper else CLONE},0,0]"
    return f"11-11 12:33:{time}  500  500 I {name}: {payload}\n"


def error(time, pid, tag, message="java.lang.IllegalStateException"):
    return f"11-11 12:33:{time}  {pid}  {pid} E {tag}: {message} {SECRET}\n"


class TimelineOriginTests(unittest.TestCase):
    def test_two_separate_pid_errors_before_exit_and_logger_family(self):
        raw = (
            event("01.000", "am_proc_start", 701)
            + error("01.200", 701, "ru.yandex.music.Canonical")
            + event("01.400", "am_proc_died", 701)
            + event("02.000", "am_proc_start", 702)
            + error("02.100", 702, "YandexMusic.Core")
            + event("02.400", "am_proc_died", 702)
            + error("02.500", 703, "System.err")
        )
        result = classify_merged_startup_timeline(raw, CLONE, fresh_main_exit=EXIT)
        self.assertEqual(result["target_exact_main_process_count_bounded"], 2)
        self.assertEqual(result["exact_main_single_start_death_count"], 2)
        self.assertEqual(result["main_with_illegal_state_error_count"], 2)
        self.assertEqual(result["illegal_state_between_start_death_count"], 2)
        self.assertEqual(result["illegal_state_logger_families"], ["MUSIC_LOGGER"])
        self.assertTrue(result["all_main_illegal_state_precedes_death"])
        self.assertFalse(result["raw_logger_or_pid_exposed"])
        self.assertNotIn(SECRET, str(result))
        self.assertNotIn("701", str(result))
        self.assertNotIn("YandexMusic", str(result))

    def test_marker_after_died_is_not_pre_exit(self):
        raw = (
            event("01.000", "am_proc_start", 701)
            + event("01.200", "am_proc_died", 701)
            + error("01.300", 701, "System.err")
            + event("02.000", "am_proc_start", 702)
            + error("02.100", 702, "System.err")
            + event("02.200", "am_proc_died", 702)
        )
        result = classify_merged_startup_timeline(raw, CLONE, fresh_main_exit=EXIT)
        self.assertEqual(result["illegal_state_only_after_death_count"], 1)
        self.assertEqual(result["illegal_state_between_start_death_count"], 1)
        self.assertFalse(result["all_main_illegal_state_precedes_death"])

    def test_helper_with_hosting_package_does_not_count(self):
        raw = (event("01.000", "am_proc_start", 701, helper=True)
               + error("01.020", 703, "System.err")
               + event("01.100", "am_proc_died", 701, helper=True))
        result = classify_merged_startup_timeline(raw, CLONE, fresh_main_exit=EXIT)
        self.assertEqual(result["exact_main_single_start_death_count"], 0)
        self.assertEqual(result["main_with_illegal_state_error_count"], 0)
        self.assertEqual(result["missing_unique_lifecycle_count"], 2)

    def test_unordered_cross_buffer_dump_fails_closed(self):
        raw = (event("02.000", "am_proc_start", 701)
               + error("01.000", 701, "System.err")
               + event("03.000", "am_proc_died", 701))
        result = classify_merged_startup_timeline(raw, CLONE, fresh_main_exit=EXIT)
        self.assertFalse(result["merged_threadtime_non_decreasing"])
        self.assertEqual(result["illegal_state_between_start_death_count"], 0)
        self.assertFalse(result["all_main_illegal_state_precedes_death"])

    def test_original_alive_control_is_not_marked_as_exited(self):
        raw = (
            "11-11 12:33:01.000 500 500 I am_proc_start: [0,801,10012,"
            + ORIGINAL + ",service," + ORIGINAL + "]\n"
            + error("01.100", 801, "System.err", "java.lang.IllegalArgumentException")
        )
        result = classify_merged_startup_timeline(
            raw, ORIGINAL, original_live_pid="801")
        self.assertEqual(result["target_exact_main_process_count_bounded"], 1)
        self.assertEqual(result["main_with_illegal_state_error_count"], 0)
        self.assertFalse(result["all_main_illegal_state_precedes_death"])
        self.assertEqual(result["illegal_state_logger_families"], [])

    def test_unauthorized_original_and_clone_pid_sources_rejected(self):
        with self.assertRaises(ValueError):
            classify_merged_startup_timeline("", "other.private.app")
        with self.assertRaises(ValueError):
            classify_merged_startup_timeline("", CLONE, original_live_pid="801")
        with self.assertRaises(ValueError):
            classify_merged_startup_timeline("", ORIGINAL, fresh_main_exit=EXIT)
        with self.assertRaises(ValueError):
            classify_merged_startup_timeline("", ORIGINAL, original_live_pid=None)

    def test_ambiguous_pid_and_empty_log_cannot_attest(self):
        for candidate in ("801 802", "801; echo BAD", "", "0", "-1"):
            result = classify_merged_startup_timeline(
                error("01.200", 801, "System.err"), ORIGINAL,
                original_live_pid=candidate)
            self.assertEqual(result["target_exact_main_process_count_bounded"], 0)
            self.assertEqual(result["main_with_illegal_state_error_count"], 0)
            self.assertFalse(result["all_main_illegal_state_precedes_death"])
        result = classify_merged_startup_timeline("", CLONE, fresh_main_exit=EXIT)
        self.assertFalse(result["merged_threadtime_non_decreasing"])
        self.assertEqual(result["illegal_state_between_start_death_count"], 0)


if __name__ == "__main__":
    unittest.main()
