"""Pure synthetic privacy-preserving legacy Push.init regression fixtures."""
import unittest
from a1_private_push_init import inspect_legacy_push_init,_type_family

def group(owner,name):
    return ("PUSH_IMPL_HELPER" if owner.startswith("Lcom/yandex/metrica/push/impl/")
            else "OTHER")

class FakeNoInit:
    method_count=1
    data=bytes(112)
    def method(self,mid):return ("Lexample/NotPush;","a")
    def code_methods(self):return iter(())

class LegacyPushInitTest(unittest.TestCase):
    def test_no_init_returns_empty_evidence_not_success(self):
        r=inspect_legacy_push_init(b"",lambda _:FakeNoInit(),group)
        self.assertEqual(r["overloads"],0)
        self.assertEqual(r["body_count"],0)
        self.assertEqual(r["calls_by_depth"],[[],[],[]])
    def test_only_fixed_categories_leak(self):
        self.assertEqual(_type_family("Lio/appmetrica/analytics/ModulesFacade;","isActivatedForApp",group),
                         "MODERN_ACTIVATED_CHECK")
        self.assertEqual(_type_family("Lcom/yandex/metrica/push/impl/VendorSecret;","doIt",group),
                         "PUSH_IMPL_HELPER")
        self.assertEqual(_type_family("Ljava/lang/String;","contains",group),
                         "JAVA_RUNTIME")
        self.assertNotIn("VendorSecret",str(_type_family(
            "Lcom/yandex/metrica/push/impl/VendorSecret;","doIt",group)))

if __name__=="__main__":unittest.main()
