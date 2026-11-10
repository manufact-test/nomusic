import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_native_exit_calls_static import exit_target, safe_method_meta, immediate_int_before_exit, TARGETS


class ExplicitExitTargetTest(unittest.TestCase):
    def test_only_exact_platform_termination_calls(self):
        for method, label in TARGETS.items():
            self.assertEqual(label, exit_target(method))

    def test_bounded_callsite_metadata_rejects_invalid_tokens(self):
        self.assertIsNone(safe_method_meta(
            ("Lprivate/path/contains-hyphen;", "foo", "()V")))
        self.assertIsNone(safe_method_meta(
            ("Lexample/Bad;", "https://private.invalid?token=SECRET", "()V")))
        self.assertEqual(
            {"owner": "Lru/yandex/music/YMApplication;", "method": "onCreate",
             "prototype": "()V"},
            safe_method_meta(("Lru/yandex/music/YMApplication;", "onCreate", "()V")))

    def test_exit_constant_zero_immediately_precedes_invoke(self):
        class Fake:
            def __init__(self, words):
                self.raw = bytes(12) + struct.pack("<I", len(words)) + struct.pack(
                    "<" + "H" * len(words), *words)
            def u16(self, offset):
                return struct.unpack_from("<H", self.raw, offset)[0]
            def u32(self, offset):
                return struct.unpack_from("<I", self.raw, offset)[0]
        cases = [
            ([0x0012, 0x1071, 0, 0], 1, 0x71, "IMMEDIATE_CONST_ZERO"),
            ([0x1012, 0x1071, 0, 0], 1, 0x71, "IMMEDIATE_CONST_NONZERO"),
            ([0x0012, 0x0177, 0, 0], 1, 0x77, "IMMEDIATE_CONST_ZERO"),
            ([0x0013, 0, 0x1071, 0, 0], 2, 0x71, "IMMEDIATE_CONST_ZERO"),
            ([0x0014, 0, 0, 0x1071, 0, 0], 3, 0x71, "IMMEDIATE_CONST_ZERO"),
        ]
        for words, pc, op, expected in cases:
            with self.subTest(words=words):
                self.assertEqual(
                    immediate_int_before_exit(Fake(words), 0, pc, op), expected)

    def test_process_observation_and_activity_finish_not_misclassified(self):
        self.assertIsNone(exit_target(("Landroid/app/Activity;", "finish", "()V")))
        self.assertIsNone(exit_target(("Landroid/os/Process;", "myPid", "()I")))
        self.assertIsNone(exit_target(("Ljava/lang/System;", "gc", "()V")))
        self.assertIsNone(exit_target(("Lcom/yandex/SomeClass;", "exit", "(I)V")))


if __name__ == "__main__":
    unittest.main()
