import unittest
from a1_private_onboarding_contract import classify_calls

class OnboardingCallClassificationTests(unittest.TestCase):
    def test_boolean_writer_is_classified(self):
        result=classify_calls({
            ("Landroid/content/SharedPreferences$Editor;","putBoolean"),
            ("Landroid/content/SharedPreferences$Editor;","apply"),
        })
        self.assertEqual(result["write_candidates"],["putBoolean"])
        self.assertEqual(result["preference_calls"],["apply","putBoolean"])

    def test_original_reader_is_not_a_writer(self):
        result=classify_calls({
            ("Landroid/content/SharedPreferences;","getBoolean"),
        })
        self.assertEqual(result["read_calls"],["getBoolean"])
        self.assertEqual(result["write_candidates"],[])

    def test_vendor_preference_wrapper_is_candidate(self):
        result=classify_calls({("LY7a;","setValue"),("LY7a;","getValue")})
        self.assertEqual(result["write_candidates"],["setValue"])
        self.assertEqual(result["read_calls"],[])

if __name__=="__main__":
    unittest.main()
