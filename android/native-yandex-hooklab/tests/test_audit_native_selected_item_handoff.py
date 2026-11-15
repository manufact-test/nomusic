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

    def test_album_model_is_a_distinct_native_object(self):
        from audit_native_selected_item_handoff import ALBUM_MODEL
        self.assertEqual(ALBUM_MODEL, "Lru/yandex/music/data/audio/Album;")
        self.assertNotEqual(ALBUM_MODEL, MODEL)

    def test_album_constructor_verifier_requires_same_object_stored_on_track(self):
        from unittest.mock import patch
        from audit_native_selected_item_handoff import (
            album_constructor_argument_store, ALBUM_MODEL
        )
        class FakeDex:
            def u16(self, offset):
                return {100:4, 102:2}[offset]
        method=(MODEL,"<init>",f"({ALBUM_MODEL})V")
        direct=[(0,0x5b,[0x235b,0]),(1,0x0e,[0x000e])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=direct), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=(MODEL,"hidden",ALBUM_MODEL)):
            result=album_constructor_argument_store(FakeDex(),method,0,100)
        self.assertEqual(result["album_parameter_index"],0)
        self.assertTrue(result["stores_same_album_argument_on_track"])
        self.assertEqual(result["album_argument_field_write_receiver_alias_count"],1)

        moved=[(0,0x07,[0x0307]),(1,0x5b,[0x205b,0]),(2,0x0e,[0x000e])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=moved), \
             patch("audit_native_selected_item_handoff.move_object_registers",
                   side_effect=lambda op,words:(0,3) if op==0x07 else None), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=(MODEL,"hidden",ALBUM_MODEL)):
            result=album_constructor_argument_store(FakeDex(),method,0,100)
        self.assertTrue(result["stores_same_album_argument_on_track"])

        wrong_receiver=[(0,0x5b,[0x135b,0]),(1,0x0e,[0x000e])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=wrong_receiver), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=(MODEL,"hidden",ALBUM_MODEL)):
            result=album_constructor_argument_store(FakeDex(),method,0,100)
        self.assertFalse(result["stores_same_album_argument_on_track"])

        branched=[(0,0x28,[0x0028]),(1,0x5b,[0x205b,0]),(2,0x0e,[0x000e])]
        with patch("audit_native_selected_item_handoff.instructions",return_value=branched), \
             patch("audit_native_selected_item_handoff.field_id",
                   return_value=(MODEL,"hidden",ALBUM_MODEL)):
            result=album_constructor_argument_store(FakeDex(),method,0,100)
        self.assertFalse(result["stores_same_album_argument_on_track"])

    def test_track_album_copy_method_requires_exact_track_and_album_inputs(self):
        from audit_native_selected_item_handoff import is_native_track_album_copy_method, ALBUM_MODEL
        good=(MODEL,"new",f"({MODEL}J{ALBUM_MODEL}Ljava/util/List;LfCa;I){MODEL}")
        bad=(MODEL,"new",f"({MODEL}JLjava/lang/String;Ljava/util/List;LfCa;I){MODEL}")
        wrong_return=(MODEL,"new",f"({MODEL}J{ALBUM_MODEL}Ljava/util/List;LfCa;I)V")
        self.assertTrue(is_native_track_album_copy_method(good))
        self.assertFalse(is_native_track_album_copy_method(bad))
        self.assertFalse(is_native_track_album_copy_method(wrong_return))

    def test_exact_zero_const4_does_not_confuse_nonzero_or_other_register(self):
        from audit_native_selected_item_handoff import const4_zero_to_register
        self.assertTrue(const4_zero_to_register(0x12, [0x0012], 0))
        self.assertTrue(const4_zero_to_register(0x12, [0x0112], 1))
        self.assertFalse(const4_zero_to_register(0x12, [0xF012], 0))
        self.assertFalse(const4_zero_to_register(0x12, [0x0112], 0))
        self.assertFalse(const4_zero_to_register(0x13, [0x0013,0], 0))

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
