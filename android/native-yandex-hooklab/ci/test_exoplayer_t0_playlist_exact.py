#!/usr/bin/env python3
import unittest
from exoplayer_t0_playlist_exact import (
    OWNER,SETTERS,COMMIT,SINGLETON,identity_witness,exact_targets_only
)


def event(target, label, origin, common=True):
    return {
        "kind":"CALL_WITH_TYPED_IDENTITY",
        "callee":{"owner":target[0],"method":target[1],"signature":target[2]},
        "identity_is_common_to_all_incoming_paths":common,
        "identity_arguments":[{"identity_type":label,"origins":[origin]}],
    }


class ExactPlaylistT0Tests(unittest.TestCase):
    def test_only_exoplayer_d_source_setters_and_exact_T0(self):
        self.assertEqual(OWNER,"Landroidx/media3/exoplayer/d;")
        self.assertTrue(exact_targets_only(COMMIT))
        self.assertIn((OWNER,"e","(LSl6;J)V"),SETTERS)
        self.assertFalse(exact_targets_only(("LrD0;","T0","(Ljava/util/List;IJZ)V")))

    def test_one_singleton_source_list_passes(self):
        events=[
            event(SINGLETON,"NATIVE_SOURCE","NATIVE_SOURCE_PARAMETER"),
            event(COMMIT,"EXACT_SOURCE_LIST","EXACT_SOURCE_LIST_RETURNED_FROM_METHOD"),
        ]
        result=identity_witness(events,SINGLETON,COMMIT)
        self.assertTrue(result["one_source_to_T0_list_contract"])
        self.assertFalse(result["runtime_active_source_confirmed"])

    def test_ambiguous_branch_fails(self):
        events=[
            event(SINGLETON,"NATIVE_SOURCE","NATIVE_SOURCE_PARAMETER"),
            event(COMMIT,"EXACT_SOURCE_LIST","EXACT_SOURCE_LIST_RETURNED_FROM_METHOD",False),
        ]
        self.assertFalse(identity_witness(events,SINGLETON,COMMIT)["one_source_to_T0_list_contract"])

    def test_unrelated_list_fails(self):
        events=[
            event(SINGLETON,"NATIVE_SOURCE","NATIVE_SOURCE_PARAMETER"),
            event(COMMIT,"EXACT_SOURCE_LIST","EXACT_SOURCE_LIST_PARAMETER"),
        ]
        self.assertFalse(identity_witness(events,SINGLETON,COMMIT)["one_source_to_T0_list_contract"])

    def test_double_singleton_must_not_claim_same_list(self):
        events=[
            event(SINGLETON,"NATIVE_SOURCE","NATIVE_SOURCE_PARAMETER"),
            event(SINGLETON,"NATIVE_SOURCE","NATIVE_SOURCE_PARAMETER"),
            event(COMMIT,"EXACT_SOURCE_LIST","EXACT_SOURCE_LIST_RETURNED_FROM_METHOD"),
        ]
        self.assertFalse(identity_witness(events,SINGLETON,COMMIT)["one_source_to_T0_list_contract"])


if __name__=="__main__":
    unittest.main()
