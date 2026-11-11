import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from exit_callsite_witness_log import classify_exit_witness

SECRET = "private-auth-token-stay-hidden"
EXIT = (
    "ApplicationExitInfo #0\n"
    "  process=pro.celikom.yandex.nativeclonelab\n"
    "  pid=1234\n"
    "  reason=1 (EXIT_SELF)\n"
    "  status=0\n"
)
def entry(pid, event, origin="VENDOR_UNCAUGHT_HANDLER", error="ILLEGAL_STATE",
          thread="MAIN", tag="CELIKOM_A1_EXIT_WITNESS"):
    return (f"11-11 12:00:01.123 {pid:5d}  9000 I {tag}: "
            f"event={event};origin={origin};error={error};thread={thread}\n")

class WitnessClassifierTests(unittest.TestCase):
    def test_real_main_pid_only_valid_issuer_not_counted(self):
        raw = (entry(4567, "SYSTEM_EXIT") + entry(1234, "ARMED", "REGISTERED", "NONE")
               + entry(1234, "UNCAUGHT")
               + entry(1234, "SYSTEM_EXIT") + SECRET)
        out = classify_exit_witness(EXIT, raw)
        self.assertTrue(out["module_armed_on_main"])
        self.assertEqual(out["observed_events"], ["ARMED", "SYSTEM_EXIT", "UNCAUGHT"])
        self.assertEqual(out["caller_groups"],
                         ["REGISTERED", "VENDOR_UNCAUGHT_HANDLER"])
        self.assertEqual(out["exception_categories"], ["ILLEGAL_STATE", "NONE"])
        self.assertEqual(out["main_thread_event_count_bounded"], 3)
        self.assertNotIn(SECRET, str(out))
        self.assertNotIn("1234", str(out))

    def test_fake_tag_and_untrusted_payload_ignored(self):
        raw = (entry(1234, "SYSTEM_EXIT", tag="ANDROID_RUNTIME")
               + entry(1234, "WRONG")
               + entry(1234, "ARMED", origin=SECRET)
               + entry(1234, "PROCESS_KILL", error=SECRET))
        out = classify_exit_witness(EXIT, raw)
        self.assertEqual(out["observed_events"], [])
        self.assertEqual(out["ignored_untrusted_lines_bounded"], 3)
        self.assertFalse(out["module_armed_on_main"])

    def test_no_main_witness_is_not_proof_of_no_exit(self):
        out = classify_exit_witness("", entry(1234, "SYSTEM_EXIT"))
        self.assertFalse(out["scoped_fresh_main_pid_available"])
        self.assertEqual(out["observed_events"], [])
        self.assertTrue(out["runtime_cause_not_assumed"])

    def test_background_event_not_claimed_main(self):
        out = classify_exit_witness(EXIT, entry(1234, "UNCAUGHT", thread="OTHER"))
        self.assertEqual(out["main_thread_event_count_bounded"], 0)
        self.assertEqual(out["observed_events"], ["UNCAUGHT"])

if __name__ == "__main__":
    unittest.main()
