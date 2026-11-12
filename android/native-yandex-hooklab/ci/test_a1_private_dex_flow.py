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
        payload=bytes((0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0))
        self.assertEqual([v[2] for v in decode_instructions(payload)],[8])

    def test_unsupported_opcode_does_not_claim_guard(self):
        code=bytes((0x79,0,0x1a,0,5,0,0x27,0))
        report=exact_error_guard_report(code,{5},FakeDex(),fixed_category)
        self.assertFalse(report["decoded"])
        self.assertEqual(report["guards_skipping_throw"],0)

    def test_truncated_payload_rejected(self):
        with self.assertRaises(FlowDecodeError):
            decode_instructions(bytes((0,1,1,0)))

if __name__=="__main__": unittest.main()
