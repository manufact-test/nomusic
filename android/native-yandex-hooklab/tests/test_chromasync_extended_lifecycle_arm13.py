"""Deterministic observer tests; cannot prove actual Yandex Music runtime."""
import importlib.util
from pathlib import Path
import sys
import unittest

SRC = Path(__file__).resolve().parents[1] / "ci" / "chromasync_extended_lifecycle_arm13.py"
sys.path.insert(0, str(SRC.parent))
spec = importlib.util.spec_from_file_location("extended", SRC)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Fake:
    def __init__(self, pids, resumed=True, focused=True):
        self.pids = pids
        self.i = 0
        self.resumed = resumed
        self.focused = focused
    def command(self, *args, **kwargs):
        class Result:
            returncode = 0
        value = Result()
        cur = self.pids[self.i]
        self.i += 1
        value.stdout = (str(cur) + "\n") if cur is not None else ""
        value.returncode = 0 if cur is not None else 1
        return value
    def shell(self, *args):
        if args[0] != "dumpsys":
            raise AssertionError("NO OTHER GUEST CALLS ALLOWED")
        if args[1] == "window":
            return ("mCurrentFocus=Window{abc u0 app.chromasync.yamclone/.Main}\n"
                    if self.focused else "mCurrentFocus=Window{abc u0 com.android.launcher/.Main}\n")
        return (
            "mResumedActivity: ActivityRecord{app.chromasync.yamclone/.Main}\n"
            if self.resumed else
            "mResumedActivity: ActivityRecord{com.android.launcher/.Main}\n"
        )


class ExtendedProbeTests(unittest.TestCase):
    def test_stable_pid_and_actual_activity(self):
        result = m.sample_guest(Fake([100,100,100,100,100]), seconds=15,
                                interval=3, sleep=lambda _: None)
        self.assertTrue(result["same_main_pid_all_samples"])
        self.assertEqual(result["main_activity_resumed_samples"],5)
        self.assertEqual(result["clone_focus_first_last_count"],2)
        self.assertEqual(result["sample_count"],5)

    def test_crash_restart_cannot_pass_as_stable(self):
        result = m.sample_guest(Fake([100,100,None,101,101]), seconds=15,
                                interval=3, sleep=lambda _: None)
        self.assertFalse(result["same_main_pid_all_samples"])
        self.assertTrue(result["main_pid_changed_or_missing"])
        self.assertEqual(result["main_pid_present_samples"],4)

    def test_same_pid_but_background_activity_not_passed(self):
        result = m.sample_guest(Fake([100]*5, resumed=False), seconds=15,
                                interval=3, sleep=lambda _: None)
        self.assertTrue(result["same_main_pid_all_samples"])
        self.assertEqual(result["main_activity_resumed_samples"],0)

    def test_different_focused_window_is_not_passed(self):
        result = m.sample_guest(Fake([100]*5, focused=False), seconds=15,
                                interval=3, sleep=lambda _: None)
        self.assertEqual(result["clone_focus_first_last_count"],0)

    def test_invalid_observation_window(self):
        with self.assertRaisesRegex(RuntimeError, "INVALID_BOUNDED"):
            m.sample_guest(Fake([100]), seconds=14, interval=3, sleep=lambda _: None)

    def test_main_cannot_run_on_owner_phone_or_nonarm(self):
        class UserDevice:
            serial = "192.168.0.3:5555"
            def shell(self, *_):
                raise AssertionError("NO DEVICE SHOULD BE TOUCHED")
        with self.assertRaisesRegex(RuntimeError, "ONLY_CLEAN_NATIVE_ARM13_CI_ALLOWED"):
            m.run(UserDevice(), Path("/nonexistent"), "full", 75)


if __name__ == "__main__":
    unittest.main()
