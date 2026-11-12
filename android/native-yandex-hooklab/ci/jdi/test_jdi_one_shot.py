"""Synthetic-only protections for exact JDI catch witness. No Android input."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

path=Path(__file__).with_name("one_shot.py")
spec=importlib.util.spec_from_file_location("jdi_trial_subject",path)
subject=importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)

class JdiTrialTests(unittest.TestCase):
    def test_one_exact_private_target_never_logged(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"PrivatePushTargets.java"
            p.write_text(
                'public static String[][] getFatalExactObjectTargets() { '
                'return new String[][] { {"com.vendor.internal.Secret",'
                '"a","java.lang.Object"} }; }'
            )
            before=subject.TARGET
            try:
                subject.TARGET=p
                self.assertEqual(subject.exact_target(),
                    ["com.vendor.internal.Secret","a","java.lang.Object"])
            finally:
                subject.TARGET=before

    def test_mapping_distinguishes_code_units_and_ambiguity(self):
        self.assertEqual(subject.safe_map("16|JAVA|OTHER\n",[32]),
                         [{"callsite":"CASE_00","throw_family":"JAVA",
                           "exception_family":"OTHER"}])
        self.assertEqual(subject.safe_map("16|JAVA|ANDROID\n",[16,32])[0]["callsite"],
                         "UNMAPPED")

    def test_malformed_exception_event_rejected(self):
        self.assertEqual(subject.safe_map("99|VENDOR_INTERNAL_RAW|JAVA\n",[]),[])
        self.assertEqual(subject.safe_map("secret Exception hello\n",[]),[])
        self.assertEqual(subject.safe_map("-1|OTHER|OTHER\n",[])[0]["callsite"],
                         "UNMAPPED")

if __name__=="__main__":
    unittest.main()
