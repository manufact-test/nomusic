"""Synthetic-only exact-flow DEX checks, no publisher data."""
import unittest
from a1_private_dex_flow import decode_instructions,exact_error_guard_report,FlowDecodeError

class FakeDex:
    method_count=10
    def method(self,mid):
        return ("Lcom/yandex/metrica/push/impl/TEST;","k")

def fixed_category(owner,name):
    return "PUSH_IMPL_HELPER"

class ExactDexFlowUnitTests(unittest.TestCase):
    def test_exact_invoke_result_guard_skips_failure(self):
        # invoke-static @1; move-result v0; if-nez v0 +9;
        # new-instance; const-string @5; invoke-direct @2; throw v1; return
        code=bytes((0x71,0,1,0,0,0,
                    0x0a,0,
                    0x39,0,9,0,
                    0x22,1,3,0,
                    0x1a,2,5,0,
                    0x70,0,2,0,0,0,
                    0x27,1,
                    0x0e,0))
        # Relative IF offset is measured in 16-bit units: IF at byte 8, RETURN at byte 28.
        code=code[:10]+bytes((10,0))+code[12:]
        report=exact_error_guard_report(code,{5},FakeDex(),fixed_category)
        self.assertEqual(report["target_strings"],1)
        self.assertEqual(report["guards_skipping_throw"],1)
        self.assertEqual(report["verified_guard_sources"],["PUSH_IMPL_HELPER"])
        self.assertFalse(report["causal_branch_proven"])


    def test_direct_string_guard_register_origin_only_enum(self):
        from a1_private_dex_flow import private_guard_input_sources,private_direct_guard_branch_roles
        code=bytes((
            0x1a,0,5,0,
            0x71,0x10,1,0,0,0,
            0x0a,1,
            0x39,1,10,0,
            0x22,3,3,0,
            0x1a,2,9,0,
            0x70,0,2,0,0,0,
            0x27,3,
            0x0e,0))
        class Fake:
            method_count=10
            def method(self,idx):
                return ("Lcom/yandex/metrica/push/common/Dummy;","check") if idx==1 else ("Ljava/lang/IllegalStateException;","init")
        def categorize(owner,name):
            return "PUSH_COMMON" if "push/common" in owner else "JAVA_RUNTIME"
        self.assertEqual(private_guard_input_sources(code,{9},Fake(),categorize),{"STRING_LITERAL"})
        self.assertEqual(private_direct_guard_branch_roles(
            code,{9},Fake(),categorize),{"BRANCH_SKIPS_THROW_ON_TRUE"})


    def test_synthetic_string_length_rule_positive_only(self):
        from a1_private_dex_predicate import rule_from_synthetic_lengths
        code=bytes((0x12,0x00,0x6e,0x10,1,0,2,0,
                    0x0a,1,0x39,1,3,0,0x0f,0,0x12,0x10,0x0f,0))
        class Fake:
            method_count=2
            def method(self,mid):
                return ("Ljava/lang/String;","length")
        self.assertEqual(rule_from_synthetic_lengths(code,3,1,True,Fake()),
                         "TRUE_FOR_POSITIVE_LENGTH")
        swapped=code[:10]+bytes((0x38,))+code[11:]
        self.assertEqual(rule_from_synthetic_lengths(swapped,3,1,True,Fake()),
                         "TRUE_FOR_ZERO_ONLY")

    def test_synthetic_string_predicate_unsupported_call_fails_closed(self):
        from a1_private_dex_predicate import rule_from_synthetic_lengths
        code=bytes((0x6e,0x10,1,0,2,0,0x0a,1,0x0f,1))
        class Fake:
            method_count=2
            def method(self,mid):
                return ("Lcom/example/Unknown;","getSecret")
        self.assertEqual(rule_from_synthetic_lengths(code,3,1,True,Fake()),
                         "INCONCLUSIVE")


    def test_exact_cfg_only_reports_discriminating_guard(self):
        from a1_private_dex_fatal_cfg import exact_fatal_cfg
        # Direct helper result controls a branch that skips the concrete throw.
        # No APK symbols, exception text or production data in this fixture.
        code=bytes((
            0x1a,1,4,0,
            0x71,0x10,1,0,0,0,
            0x0a,0,
            0x39,0,10,0,
            0x22,2,3,0,
            0x1a,3,5,0,
            0x70,0,2,0,0,0,
            0x27,2,
            0x0e,0))
        class Fake:
            method_count=3
            def method(self,mid):
                return ("Lcom/yandex/metrica/push/impl/Fake;","a")
        def category(owner,name):return "PUSH_IMPL_HELPER"
        v=exact_fatal_cfg(code,{5},Fake(),category)
        self.assertTrue(v["decoded"])
        self.assertEqual(v["exclusive_fatal_guards"],1)
        self.assertEqual(v["guard_source_categories"],["PUSH_IMPL_HELPER"])
        self.assertEqual(v["fatal_guard_polarities"],["FALLTHROUGH_FATAL"])
        self.assertFalse(v["runtime_causality_proven"])
        self.assertNotIn("Fake",str(v))

    def test_absent_throw_fails_closed(self):
        code=bytes((0x1a,0,5,0,0x0e,0))
        report=exact_error_guard_report(code,{5},FakeDex(),fixed_category)
        self.assertTrue(report["decoded"])
        self.assertEqual(report["guards_skipping_throw"],0)

    def test_operand_byte_is_never_fake_const_or_invoke(self):
        code=bytes((0x14,0,0x1a,0x27,0x71,0,0x0e,0))
        report=exact_error_guard_report(code,{5},FakeDex(),fixed_category)
        self.assertEqual(report["target_strings"],0)

    def test_dex_switch_payload_is_single_instruction(self):
        payload=bytes((0,1,1,0,0,0,0,0,0,0,0,0))
        self.assertEqual([v[2] for v in decode_instructions(payload)],[6])

    def test_unsupported_opcode_does_not_claim_guard(self):
        code=bytes((0x79,0,0x1a,0,5,0,0x27,0))
        report=exact_error_guard_report(code,{5},FakeDex(),fixed_category)
        self.assertFalse(report["decoded"])
        self.assertEqual(report["guards_skipping_throw"],0)

    def test_truncated_payload_rejected(self):
        with self.assertRaises(FlowDecodeError):
            decode_instructions(bytes((0,1,1,0)))

if __name__=="__main__": unittest.main()
