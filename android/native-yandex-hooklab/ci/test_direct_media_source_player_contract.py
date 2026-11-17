#!/usr/bin/env python3
"""Fail-closed tests: exact MediaSource type, not general List/MediaItem."""
import unittest

from direct_media_source_player_contract import (
    SOURCE, PLAYER_OWNERS, direct_contract,
)


class DirectMediaSourcePlayerContractTests(unittest.TestCase):
    def test_only_known_player_owner_with_exact_source_parameter(self):
        self.assertTrue(direct_contract(("LfH7;", "x", "(" + SOURCE + ")V")))
        self.assertTrue(direct_contract(("LrD0;", "x", "(I" + SOURCE + "Z)V")))
        self.assertFalse(direct_contract(("Lunknown;", "x", "(" + SOURCE + ")V")))

    def test_no_mediaitem_or_list_inferred(self):
        self.assertFalse(direct_contract(("LfH7;", "set", "(LOf6;)V")))
        self.assertFalse(direct_contract(
            ("LfH7;", "set", "(Ljava/util/List;)V")
        ))
        self.assertFalse(direct_contract(
            ("LfH7;", "sourceReturn", "()" + SOURCE)
        ))

    def test_source_is_an_exact_type_not_name_guess(self):
        self.assertIn("LfH7;", PLAYER_OWNERS)
        self.assertFalse(direct_contract(
            ("LfH7;", "setMediaSource", "(Ljava/lang/Object;)V")
        ))


if __name__ == "__main__":
    unittest.main()
