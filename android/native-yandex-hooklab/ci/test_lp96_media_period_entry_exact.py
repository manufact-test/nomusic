#!/usr/bin/env python3
import unittest
from lp96_media_period_entry_exact import TARGET,period_target,PERIOD,SOURCE,period_identity_witness


class ExactPeriodEntryTests(unittest.TestCase):
    def test_one_exact_signed_lp96_candidate(self):
        self.assertTrue(period_target((
            "Lp96;","transient","(LSl6$b;LrH2;J)Lo96;")))
        self.assertEqual(PERIOD,"Lo96;")
        self.assertEqual(SOURCE,"LSl6;")

    def test_strict_source_to_period_all_returns(self):
        events=[
            {"kind":"FIELD_READ_TYPED_IDENTITY","field_declaring_owner":"LuIb;",
             "identity_type":"ORIGINAL_MEDIA_SOURCE",
             "receiver_is_this_on_all_paths":True},
            {"kind":"FIELD_STORE_TYPED_IDENTITY","destination_owner":"Lo96;",
             "identity_type":"ORIGINAL_MEDIA_SOURCE",
             "origins":["ORIGINAL_MEDIA_SOURCE_FROM_THIS_FIELD"]},
            {"kind":"RETURN_TYPED_IDENTITY","identity_type":"MEDIA_PERIOD",
             "origins":["MEDIA_PERIOD_NEW_INSTANCE"]},
            {"kind":"RETURN_TYPED_IDENTITY","identity_type":"MEDIA_PERIOD",
             "origins":["MEDIA_PERIOD_NEW_INSTANCE"]},
        ]
        proven=period_identity_witness(events,True,True,2,True)
        self.assertTrue(proven["static_same_source_to_returned_MediaPeriod_proven"])
        self.assertFalse(proven["runtime_active_period_or_decoder_proven"])
        self.assertFalse(period_identity_witness(events,True,True,2,False)
                         ["static_same_source_to_returned_MediaPeriod_proven"])
        self.assertFalse(period_identity_witness(events[:-1],True,True,2,True)
                         ["static_same_source_to_returned_MediaPeriod_proven"])
        self.assertFalse(period_identity_witness(events,False,True,2,True)
                         ["static_same_source_to_returned_MediaPeriod_proven"])

    def test_other_period_or_renderer_not_in_scope(self):
        self.assertFalse(period_target(("LiLb;","transient","(LSl6$b;LrH2;J)Lo96;")))
        self.assertFalse(period_target(("Lp96;","transient","(Ljava/lang/Object;)Lo96;")))
        self.assertFalse(period_target(("LrD0;","createPeriod","(Ljava/lang/Object;)Lo96;")))


if __name__=="__main__":
    unittest.main()
