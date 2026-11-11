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

    def test_known_static_obfuscated_callers_are_bounded_enums(self):
        out = classify_exit_witness(
            EXIT,
            entry(1234, "SYSTEM_EXIT", origin="STATIC_RUN_B", error="NONE")
            + entry(1234, "PROCESS_KILL", origin="STATIC_INVOKER", error="NONE")
            + entry(1234, "SYSTEM_EXIT", origin="STATIC_HANDLER", error="NONE"))
        self.assertEqual(out["caller_groups"],
                         ["STATIC_HANDLER", "STATIC_INVOKER", "STATIC_RUN_B"])
        self.assertEqual(out["observed_events"], ["PROCESS_KILL", "SYSTEM_EXIT"])

    def test_prefix_result_categorized_without_string_values(self):
        raw = (entry(1234, "PREFIX_HOOK", origin="REGISTERED", error="NONE")
               + entry(1234, "PREFIX_CHECK", origin="OWN_AUX", error="MATCH_TRUE")
               + entry(1234, "PREFIX_CHECK", origin="UNCLASSIFIED", error="MATCH_FALSE"))
        x = classify_exit_witness(EXIT, raw)
        self.assertTrue(x["prefix_hook_reported"])
        self.assertTrue(x["prefix_check_observed"])
        self.assertEqual(x["prefix_known_target_groups"], ["OWN_AUX"])
        self.assertEqual(x["prefix_match_result_categories"], ["MATCH_FALSE", "MATCH_TRUE"])
        self.assertNotIn("nativeclonelab", str(x))

    def test_last_prefix_before_first_kill_correlates_same_main_pid_only(self):
        # MIXED PIDs may interleave. Only last MAIN-thread prefix for the
        # exact kill-owning MAIN PID can be associated with first exit call.
        raw = (entry(1234, "PREFIX_CHECK", origin="OWN_MAIN", error="MATCH_FALSE")
               + entry(4321, "PREFIX_CHECK", origin="OWN_AUX", error="MATCH_TRUE")
               + entry(1234, "PREFIX_CHECK", origin="OWN_AUX", error="MATCH_TRUE")
               + entry(1234, "PROCESS_KILL", origin="STATIC_RUN_B", error="NONE")
               + entry(1234, "PREFIX_CHECK", origin="OWN_MAIN", error="MATCH_FALSE")
               + entry(1234, "SYSTEM_EXIT", origin="STATIC_RUN_B", error="NONE"))
        x = classify_exit_witness(EXIT, raw)
        self.assertEqual(x["first_exit_has_preceding_main_prefix_by_pid_bounded"], 1)
        self.assertEqual(x["first_exit_preceding_main_prefix_groups"], ["OWN_AUX"])
        self.assertEqual(x["first_exit_preceding_main_prefix_results"], ["MATCH_TRUE"])
        self.assertNotIn("4321", str(x))
        self.assertTrue(x["first_exit_preceding_prefix_not_causal_proof"])

    def test_background_prefix_not_claimed_for_main_exit(self):
        raw = (entry(1234, "PREFIX_CHECK", origin="OWN_AUX",
                     error="MATCH_TRUE", thread="OTHER")
               + entry(1234, "PROCESS_KILL", origin="STATIC_RUN_B"))
        x = classify_exit_witness(EXIT, raw)
        self.assertEqual(x["first_exit_has_preceding_main_prefix_by_pid_bounded"], 0)
        self.assertEqual(x["first_exit_preceding_main_prefix_results"], [])

    def test_kill_target_pid_is_private_enum_only(self):
        raw = (entry(1234, "PROCESS_KILL", origin="STATIC_RUN_B",
                     error="KILL_TARGET_SELF")
               + entry(1234, "SYSTEM_EXIT", origin="STATIC_RUN_B", error="NONE"))
        x = classify_exit_witness(EXIT, raw)
        self.assertEqual(x["first_kill_target_groups"], ["KILL_TARGET_SELF"])
        self.assertEqual(x["first_kill_target_observed_main_pids_bounded"], 1)
        self.assertTrue(x["kill_target_main_pid_only_no_raw_target_pid"])

    def test_exact_main_runnable_variant_before_own_exit(self):
        raw = (entry(1234, "RUN_HOOK", "REGISTERED", "NONE")
               + entry(1234, "RUN_CTOR", "STATIC_RUN_B", "CASE_2")
               + entry(1234, "RUN_ENTER", "STATIC_RUN_B", "CASE_2")
               + entry(1234, "PREFIX_CHECK", "OWN_AUX", "MATCH_TRUE")
               + entry(1234, "PROCESS_KILL", "STATIC_RUN_B", "KILL_TARGET_OTHER")
               + entry(1234, "RUN_ENTER", "STATIC_RUN_B", "CASE_5"))
        x = classify_exit_witness(EXIT, raw)
        self.assertEqual(x["first_exit_run_mode_groups"], ["CASE_2"])
        self.assertEqual(x["first_exit_run_mode_main_pid_count_bounded"], 1)
        self.assertTrue(x["run_mode_entered"])

    def test_wrong_thread_runnable_not_joined(self):
        raw = (entry(1234, "RUN_ENTER", "STATIC_RUN_B", "CASE_0", "OTHER")
               + entry(1234, "PROCESS_KILL", "STATIC_RUN_B", "KILL_TARGET_OTHER"))
        x = classify_exit_witness(EXIT, raw)
        self.assertEqual(x["first_exit_run_mode_groups"], [])

    def test_exception_category_scoped_without_secret_data(self):
        raw = (entry(1234, "HI2_EXCEPTION", "STATIC_COROUTINE", "EXC_SIGNATURE", "OTHER")
               + entry(9999, "HI2_EXCEPTION", "STATIC_COROUTINE", "EXC_AUTH", "OTHER")
               + "secret_account_token")
        x = classify_exit_witness(EXIT, raw)
        self.assertEqual(x["hi2_exception_categories"], ["EXC_SIGNATURE"])
        self.assertTrue(x["hi2_exception_message_or_token_never_exported"])
        self.assertNotIn("secret_account_token", str(x))

    def test_signature_mode2_prefix_kill_is_same_pid_and_ordered(self):
        raw = (entry(1234, "HI2_EXCEPTION", "STATIC_COROUTINE", "EXC_SIGNATURE", "OTHER")
               + entry(9999, "RUN_ENTER", "STATIC_RUN_B", "CASE_2")
               + entry(1234, "RUN_ENTER", "STATIC_RUN_B", "CASE_2")
               + entry(1234, "PREFIX_CHECK", "OWN_AUX", "MATCH_TRUE")
               + entry(1234, "PROCESS_KILL", "STATIC_RUN_B", "KILL_TARGET_OTHER"))
        x = classify_exit_witness(EXIT, raw)
        self.assertEqual(x["hi2_signature_error_new_main_pids_bounded"], 1)
        self.assertEqual(x["hi2_signature_error_precedes_mode2_in_main_pids_bounded"], 1)
        self.assertEqual(
            x["ordered_signature_mode2_aux_prefix_kill_chain_main_pids_bounded"], 1)
        self.assertTrue(x["ordered_chain_logcat_marker_order_not_proof_of_policy_intent"])

    def test_out_of_order_error_never_counts_as_before_case2(self):
        raw = (entry(1234, "RUN_ENTER", "STATIC_RUN_B", "CASE_2")
               + entry(1234, "HI2_EXCEPTION", "STATIC_COROUTINE", "EXC_SIGNATURE", "OTHER")
               + entry(1234, "PREFIX_CHECK", "OWN_AUX", "MATCH_TRUE")
               + entry(1234, "PROCESS_KILL", "STATIC_RUN_B", "KILL_TARGET_OTHER"))
        x = classify_exit_witness(EXIT, raw)
        self.assertEqual(x["hi2_signature_error_precedes_mode2_in_main_pids_bounded"], 0)
        self.assertEqual(
            x["ordered_signature_mode2_aux_prefix_kill_chain_main_pids_bounded"], 0)

    def test_background_event_not_claimed_main(self):
        out = classify_exit_witness(EXIT, entry(1234, "UNCAUGHT", thread="OTHER"))
        self.assertEqual(out["main_thread_event_count_bounded"], 0)
        self.assertEqual(out["observed_events"], ["UNCAUGHT"])

if __name__ == "__main__":
    unittest.main()
