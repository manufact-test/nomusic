"""Own witness fixed marker parser, never device or private data."""
import importlib.util
from pathlib import Path
import unittest

here=Path(__file__).resolve().parents[1]/"own_lspatch_x86_witness_runtime.py"
spec=importlib.util.spec_from_file_location("own_x86_witness",here)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class OwnX86WitnessTests(unittest.TestCase):
    def test_pass(self):
        x=module.classify_witness_log("I/CelikomOwnHookWitness: "+module.RESULT)
        self.assertEqual(x["witness_result"],"PASS")
        self.assertTrue(x["module_activity_intercepted"])
        self.assertFalse(x["raw_log_exported"])
    def test_fail(self):
        x=module.classify_witness_log("RESULT=FAIL CODE=OWN_MODULE_ACTIVITY_INTERCEPTED")
        self.assertEqual(x["witness_result"],"FAIL")
        self.assertFalse(x["module_activity_intercepted"])
    def test_unrelated_log(self):
        x=module.classify_witness_log("another application's personal details")
        self.assertEqual(x["witness_result"],"NOT_OBSERVED")
        self.assertFalse(x["raw_log_exported"])
    def test_scope_only_own(self):
        scope=(Path(__file__).resolve().parents[1]/
               "armv7-witness-module/app/src/main/resources/META-INF/xposed/scope.list")
        self.assertEqual(set(scope.read_text().splitlines()),{
            "pro.celikom.armv7loaderhost.witness",
            "pro.celikom.armv7loaderhost.audio",
            "pro.celikom.armv7loaderhost.x86control"
        })

if __name__=="__main__":
    unittest.main()
