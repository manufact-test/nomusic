import struct
import unittest

from a1_private_onboarding_contract import (
    classify_calls,
    inspect_exact_onboarding_writer,
)


class FakeDex:
    def __init__(self):
        self.strings = {1: "Yandex_Music", 2: "onboarding", 3: "other"}
        self.methods = {
            1: ("Landroid/content/Context;", "getSharedPreferences"),
            2: ("Landroid/content/SharedPreferences;", "edit"),
            3: ("Landroid/content/SharedPreferences$Editor;", "putBoolean"),
            4: ("Landroid/content/SharedPreferences$Editor;", "apply"),
            5: ("Landroid/content/SharedPreferences$Editor;", "commit"),
            6: ("Landroid/content/SharedPreferences;", "getBoolean"),
            7: ("Lsome/VendorWrapper;", "setValue"),
        }

    def string(self, index):
        return self.strings[index]

    def method(self, index):
        return self.methods[index]


def const_string(register, string_index):
    return bytes((0x1a, register)) + struct.pack("<H", string_index)


def const4(register, value):
    return bytes((0x12, ((value & 0x0f) << 4) | (register & 0x0f)))


def invoke35c(opcode, method_index, registers):
    count = len(registers)
    padded = registers + [0] * (5 - count)
    first = bytes((opcode, (count << 4) | padded[4]))
    args = bytes(((padded[0] & 0x0f) | ((padded[1] & 0x0f) << 4),
                  (padded[2] & 0x0f) | ((padded[3] & 0x0f) << 4)))
    return first + struct.pack("<H", method_index) + args


def direct_writer_code(key_index=2, preference_index=1, persist=True):
    code = b"".join((
        const_string(0, preference_index),
        const4(1, 1),
        invoke35c(0x6e, 1, [4, 0, 1]),  # Context.getSharedPreferences
        bytes((0x0c, 4)),               # move-result-object preference
        invoke35c(0x72, 2, [4]),        # SharedPreferences.edit
        bytes((0x0c, 4)),               # move-result-object editor
        const_string(0, key_index),
        invoke35c(0x72, 3, [4, 0, 1]),  # Editor.putBoolean
        bytes((0x0c, 4)),               # returned editor alias
        invoke35c(0x72, 4 if persist else 6, [4]),
        bytes((0x0e, 0)),
    ))
    return code


class OnboardingCallClassificationTests(unittest.TestCase):
    def test_boolean_writer_is_classified(self):
        result = classify_calls({
            ("Landroid/content/SharedPreferences$Editor;", "putBoolean"),
            ("Landroid/content/SharedPreferences$Editor;", "apply"),
        })
        self.assertEqual(result["write_candidates"], ["putBoolean"])
        self.assertEqual(result["preference_calls"], ["apply", "putBoolean"])

    def test_original_reader_is_not_a_writer(self):
        result = classify_calls({
            ("Landroid/content/SharedPreferences;", "getBoolean"),
        })
        self.assertEqual(result["read_calls"], ["getBoolean"])
        self.assertEqual(result["write_candidates"], [])

    def test_vendor_preference_wrapper_is_only_a_cooccurrence_candidate(self):
        result = classify_calls({("LY7a;", "setValue"), ("LY7a;", "getValue")})
        self.assertEqual(result["write_candidates"], ["setValue"])
        self.assertEqual(result["read_calls"], [])

    def test_exact_yandex_music_onboarding_putboolean_and_apply(self):
        self.assertEqual(
            inspect_exact_onboarding_writer(FakeDex(), direct_writer_code()),
            (True, True),
        )

    def test_wrong_preference_file_is_not_a_confirmed_writer(self):
        self.assertEqual(
            inspect_exact_onboarding_writer(
                FakeDex(), direct_writer_code(preference_index=3)
            ),
            (False, False),
        )

    def test_wrong_boolean_key_is_not_a_confirmed_writer(self):
        self.assertEqual(
            inspect_exact_onboarding_writer(
                FakeDex(), direct_writer_code(key_index=3)
            ),
            (False, False),
        )

    def test_putboolean_without_apply_is_direct_writer_not_persisted_writer(self):
        self.assertEqual(
            inspect_exact_onboarding_writer(
                FakeDex(), direct_writer_code(persist=False)
            ),
            (True, False),
        )


if __name__ == "__main__":
    unittest.main()
