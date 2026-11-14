import unittest
from audit_native_selected_item_handoff import (
    parse_types, MODEL, DESCRIPTOR_BUILDER, PLAYER_OWNERS, PLAYER_METHODS
)

class SelectedItemAuditTests(unittest.TestCase):
    def test_method_descriptor_parser_handles_objects_arrays_and_wide_values(self):
        self.assertEqual(parse_types("(ILjava/lang/String;[B[[JDLru/yandex/music/data/audio/o;)V"),
            ["I", "Ljava/lang/String;", "[B", "[[J", "D", MODEL])

    def test_descriptor_builder_is_exact(self):
        self.assertEqual(DESCRIPTOR_BUILDER,
            ("Lcom/yandex/music/shared/player/download2/o;", "while"))
        self.assertNotEqual(DESCRIPTOR_BUILDER,
            ("Lcom/yandex/music/shared/player/download2/o;", "if"))

    def test_only_public_player_owner_methods_are_player_selection_calls(self):
        self.assertIn("Landroidx/media3/common/Player;", PLAYER_OWNERS)
        self.assertIn("setMediaItem", PLAYER_METHODS)
        self.assertIn("getCurrentMediaItem", PLAYER_METHODS)
        self.assertNotIn("getTitle", PLAYER_METHODS)

    def test_malformed_signatures_fail_closed(self):
        for signature in ("V", "(Ljava/lang/String)V", "(Q)V", "([)V"):
            with self.subTest(signature=signature):
                with self.assertRaises(ValueError):
                    parse_types(signature)

if __name__ == "__main__":
    unittest.main()
