"""Synthetic-only, fail-closed verdict tests for native issuer-vs-own signer A/B."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from owner_2025_paired_issuer_vs_own_signer_arm13 import (
    strict_75s_stable, verdict_for_pair,
)

PASS={"launch_intent_accepted":True,"main_alive_25_of_25":True,
      "same_exact_main_pid_25_of_25":True,"resumed_25_of_25":True}
FAIL={"launch_intent_accepted":True,"main_alive_25_of_25":False,
      "same_exact_main_pid_25_of_25":False,"resumed_25_of_25":False,
      "exit_status":{"latest_main_exit_reason":"JAVA_CRASH"},
      "main_crash_category":{"java_fatal_thread_enum":"MAIN_UI",
          "java_top_exception_enum":"ILLEGAL_STATE",
          "java_top_stack_family":"YANDEX_APP",
          "java_exception_security_markers":["SIGNATURE"]}}


class PairedCausalVerdictTests(unittest.TestCase):
    def test_original_75s_stability_is_required(self):
        self.assertFalse(strict_75s_stable({}))
        self.assertFalse(strict_75s_stable({**PASS,"resumed_25_of_25":False}))
        self.assertTrue(strict_75s_stable(PASS))
        self.assertEqual(verdict_for_pair(True,FAIL,True,FAIL),
                         "CONTROL_ORIGINAL_75S_NO_GO")
        self.assertEqual(verdict_for_pair(False,PASS,True,FAIL),
                         "CONTROL_ORIGINAL_75S_NO_GO")

    def test_only_proven_main_signature_throw_gets_specific_label(self):
        self.assertEqual(verdict_for_pair(True,PASS,True,FAIL),
            "PAIRED_ORIGINAL_STABLE_OWN_KEY_MAIN_SIGNATURE_JAVA_CRASH")
        self.assertEqual(verdict_for_pair(True,PASS,True,
            {**FAIL,"main_crash_category":{"java_exception_security_markers":["SIGNATURE"]}}),
            "PAIRED_ORIGINAL_STABLE_OWN_KEY_MAIN_OTHER_NO_GO")

    def test_other_failures_not_signature_causality(self):
        self.assertEqual(verdict_for_pair(True,PASS,False,FAIL),
                         "CONTROL_OWN_KEY_INSTALL_NO_GO")
        x={**FAIL,"main_crash_category":{**FAIL["main_crash_category"],
                                         "java_top_stack_family":"ANDROID_FRAMEWORK"}}
        self.assertEqual(verdict_for_pair(True,PASS,True,x),
                         "PAIRED_ORIGINAL_STABLE_OWN_KEY_MAIN_OTHER_NO_GO")
        x={**FAIL,"exit_status":{"latest_main_exit_reason":"EXIT_SELF"}}
        self.assertEqual(verdict_for_pair(True,PASS,True,x),
                         "PAIRED_ORIGINAL_STABLE_OWN_KEY_MAIN_OTHER_NO_GO")

    def test_both_native_startups_pass_are_not_audio_acceptance(self):
        self.assertEqual(verdict_for_pair(True,PASS,True,PASS),
                         "PAIRED_BOTH_NATIVE_MAIN_75S_STABLE")


if __name__=="__main__":
    unittest.main()
