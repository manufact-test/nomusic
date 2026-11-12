"""Synthetic-only exact DEX authority test, no private package inputs."""
import unittest
from a1_private_provider_authority import inspect_authority_refs

class FakeDex:
    string_count=1
    def __init__(self,raw):self.value=raw
    def string(self,i):return self.value
    def code_methods(self):return iter(())

class AuthorityTest(unittest.TestCase):
    def test_external_secret_is_never_returned(self):
        x=inspect_authority_refs("secret",lambda _:FakeDex("PRIVATE_TOKEN"),
                                 lambda _: "OTHER")
        self.assertEqual(x,{"literal_found":False,"method_groups":[],
                            "methods_referencing_bounded":0})
        self.assertNotIn("PRIVATE_TOKEN",str(x))
    def test_public_literal_without_callsite_not_assumed_used(self):
        x=inspect_authority_refs(None,lambda _:FakeDex(
            "com.yandex.preinstallsatellite.appmetrica.provider"),lambda _: "OTHER")
        self.assertTrue(x["literal_found"])
        self.assertEqual(x["methods_referencing_bounded"],0)

if __name__=="__main__":unittest.main()
