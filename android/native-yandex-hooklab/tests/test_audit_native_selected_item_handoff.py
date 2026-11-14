import unittest
from audit_native_selected_item_handoff import (
    parse_types, written_register, MODEL, DESCRIPTOR_BUILDER,
    PLAYER_OWNERS, PLAYER_METHODS
)

class SelectedItemAuditTests(unittest.TestCase):
    def test_method_descriptor_parser_handles_objects_arrays_and_wide_values(self):
        self.assertEqual(parse_types("(ILjava/lang/String;[B[[JDLru/yandex/music/data/audio/o;)V"),
            ["I", "Ljava/lang/String;", "[B", "[[J", "D", MODEL])

    def test_pinned_input_is_the_exact_2025_owner_asset(self):
        from audit_native_selected_item_handoff import (
            PINNED_XAPK_BYTES, PINNED_XAPK_SHA256, PUBLISHER_VERSION
        )
        self.assertEqual(PINNED_XAPK_BYTES, 45961661)
        self.assertEqual(PINNED_XAPK_SHA256,
            "8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053")
        self.assertEqual(PUBLISHER_VERSION, "2025.10.4 #120.1gpr")

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

    def test_common_destination_registers_are_invalidated(self):
        self.assertEqual(written_register(0x0c, [0x030c]), 3)
        self.assertEqual(written_register(0x22, [0x0500, 0x0010]), 5)
        self.assertEqual(written_register(0x54, [0x0214, 0x0003]), 2)
        self.assertIsNone(written_register(0x1f, [0x021f, 0x0003]))

    def test_malformed_signatures_fail_closed(self):
        for signature in ("V", "(Ljava/lang/String)V", "(Q)V", "([)V"):
            with self.subTest(signature=signature):
                with self.assertRaises(ValueError):
                    parse_types(signature)

if __name__ == "__main__":
    unittest.main()
