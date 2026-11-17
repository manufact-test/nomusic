#!/usr/bin/env python3
"""Fail-closed: same class type is not enough; one exact allocation is needed."""
import unittest
from lca9_exact_source_player_identity import (
    MEDIA_SOURCE_CONSTRUCTOR,PLAYER_SOURCE_SETTER,WRAPPER_SOURCE,evaluate_identity
)


def event(callee, label, origin, common=True):
    return {
        "kind":"CALL_WITH_TYPED_IDENTITY",
        "callee":{"owner":callee[0],"method":callee[1],"signature":callee[2]},
        "identity_is_common_to_all_incoming_paths":common,
        "identity_arguments":[{"identity_type":label,"origins":[origin]}],
    }


class Lca9IdentityTests(unittest.TestCase):
    def test_unique_source_proven_and_wrapper_if_direct(self):
        events=[
            event(MEDIA_SOURCE_CONSTRUCTOR,"MEDIA_SOURCE_HOLDER","MEDIA_SOURCE_HOLDER_NEW_INSTANCE"),
            event(PLAYER_SOURCE_SETTER,"MEDIA_SOURCE_HOLDER","MEDIA_SOURCE_HOLDER_NEW_INSTANCE"),
            event(WRAPPER_SOURCE,"TRACK_WRAPPER","TRACK_WRAPPER_PARAMETER"),
        ]
        verdict=evaluate_identity(events,True)
        self.assertTrue(verdict["same_LiLb_instance_constructor_to_player_setter_proven"])
        self.assertTrue(verdict["caller_TrackWrapper_to_descriptor_same_object_proven"])
        self.assertFalse(verdict["audible_decoder_source_proven"])

    def test_multiple_allocations_fail_closed(self):
        events=[
            event(MEDIA_SOURCE_CONSTRUCTOR,"MEDIA_SOURCE_HOLDER","MEDIA_SOURCE_HOLDER_NEW_INSTANCE"),
            event(PLAYER_SOURCE_SETTER,"MEDIA_SOURCE_HOLDER","MEDIA_SOURCE_HOLDER_NEW_INSTANCE"),
        ]
        self.assertFalse(evaluate_identity(events,False)["same_LiLb_instance_constructor_to_player_setter_proven"])

    def test_unknown_or_ambiguous_path_fails(self):
        events=[
            event(MEDIA_SOURCE_CONSTRUCTOR,"MEDIA_SOURCE_HOLDER","MEDIA_SOURCE_HOLDER_NEW_INSTANCE"),
            event(PLAYER_SOURCE_SETTER,"MEDIA_SOURCE_HOLDER","MEDIA_SOURCE_HOLDER_NEW_INSTANCE",False),
        ]
        self.assertFalse(evaluate_identity(events,True)["same_LiLb_instance_constructor_to_player_setter_proven"])

    def test_disconnected_source_fails(self):
        events=[
            event(MEDIA_SOURCE_CONSTRUCTOR,"MEDIA_SOURCE_HOLDER","MEDIA_SOURCE_HOLDER_NEW_INSTANCE"),
            event(PLAYER_SOURCE_SETTER,"MEDIA_SOURCE_INTERFACE","MEDIA_SOURCE_INTERFACE_PARAMETER"),
        ]
        self.assertFalse(evaluate_identity(events,True)["same_LiLb_instance_constructor_to_player_setter_proven"])


if __name__=="__main__":
    unittest.main()
