import unittest

from lft2_class_inspection import flag_names, CLASS_FLAGS, METHOD_FLAGS, OBJECT_TO_OBJECT

class LfT2ClassInspectionTests(unittest.TestCase):
    def test_class_flags_are_decoded(self):
        self.assertEqual(
            flag_names(0x0001 | 0x0010 | 0x0400, CLASS_FLAGS),
            ["PUBLIC", "FINAL", "ABSTRACT"],
        )

    def test_method_flags_keep_native_abstract_bridge_distinct(self):
        self.assertEqual(
            flag_names(0x0001 | 0x0100 | 0x0400, METHOD_FLAGS),
            ["PUBLIC", "NATIVE", "ABSTRACT"],
        )

    def test_exact_continuation_signature_is_not_inferred_from_name(self):
        self.assertEqual(OBJECT_TO_OBJECT, "(Ljava/lang/Object;)Ljava/lang/Object;")
        self.assertNotEqual(
            OBJECT_TO_OBJECT,
            "(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;",
        )

if __name__ == "__main__":
    unittest.main()
