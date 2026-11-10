import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_ga4_primary_source import scan_signed, TARGETS


class SignedGa4TwoSlotTests(unittest.TestCase):
    def test_two_distinct_reader_fields_not_conflated(self):
        first=("Lga4;","Le48;","hidden1")
        second=("Lga4;","Le48;","hidden2")
        def selection(apks,reader_method="c"):
            return first if reader_method=="d" else second
        with patch("audit_native_ga4_primary_source.discover_read_slot",side_effect=selection), \
             patch("audit_native_ga4_primary_source.writer_evidence_for_slot",return_value={"writers":[]}), \
             patch("audit_native_ga4_primary_source.exact_method_outlines",return_value={}):
            info=scan_signed([])
        self.assertTrue(info["Le48_primary_different_from_secondary"])
        self.assertFalse(info["native_audio_replacement_proven"])

    def test_identical_slot_must_fail(self):
        key=("Lga4;","Le48;","same_key")
        with patch("audit_native_ga4_primary_source.discover_read_slot",return_value={key}):
            with self.assertRaisesRegex(ValueError,"MIXED"):
                scan_signed([])

    def test_b_c_secondary_disagreement_must_fail(self):
        a={("Lga4;","Le48;","a")}
        b={("Lga4;","Le48;","b")}
        def selection(apks,reader_method="c"):
            return b if reader_method=="b" else a
        with patch("audit_native_ga4_primary_source.discover_read_slot",side_effect=selection):
            with self.assertRaisesRegex(ValueError,"MISMATCH"):
                scan_signed([])

    def test_exact_real_source_factory_names_pinned(self):
        self.assertIn(("Lcq7;","A"),TARGETS)
        self.assertIn(("Leyc;","d"),TARGETS)
        self.assertIn(("Lga4;","d"),TARGETS)
        self.assertIn(("Lya4;","a"),TARGETS)


if __name__=="__main__":
    unittest.main()
