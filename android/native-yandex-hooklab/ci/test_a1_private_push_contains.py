"""Pure synthetic String.contains operand classification privacy test."""
import unittest
from a1_private_push_contains import _literal_family,inspect_push_contains

class SyntheticContainsTest(unittest.TestCase):
    def test_only_fixed_argument_families_emitted(self):
        self.assertEqual(_literal_family(":"),"PROCESS_SEPARATOR")
        self.assertEqual(_literal_family("ru.yandex.music"),"STOCK_PACKAGE_LITERAL")
        self.assertEqual(_literal_family("ru.yandex.music:push"),"STOCK_PROCESS_SUFFIX")
        self.assertEqual(_literal_family("PRIVATE_ACCESS_TOKEN_X"),"OTHER_LITERAL")
        self.assertEqual(_literal_family(""),"EMPTY")
    def test_no_private_push_error_empty(self):
        class Fake:
            method_count=0
            def possible_error_strings(self):return set()
        self.assertEqual(inspect_push_contains(b"",lambda _:Fake(),
                         lambda _: "OTHER",lambda a,b:"OTHER",
                         lambda a,b,c,d:None),[])

if __name__=="__main__":unittest.main()
