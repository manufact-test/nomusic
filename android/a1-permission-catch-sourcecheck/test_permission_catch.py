"""Synthetic only: the signature permission link must not be inferred from API name alone."""
import importlib.util
import pathlib
import unittest
import sys

SUBJECT=pathlib.Path(__file__).with_name("permission_catch.py")
spec=importlib.util.spec_from_file_location("a1_permission_only",SUBJECT)
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class Dex:
    method_count=4
    string_count=1
    def __init__(self,owner,name,marker="unrelated"):
        self.owner,self.name,self.marker=owner,name,marker
    def method(self,mid):
        return self.owner,self.name
    def string(self,idx):
        return self.marker

class PermissionCheckTests(unittest.TestCase):
    def test_direct_permission_api_requires_exact_framework_owner(self):
        invoke=bytes((0x6e,0,0,0,0,0,0x0e,0))
        good=Dex("Landroid/content/pm/PackageManager;","checkPermission")
        bad=Dex("Lcom/unknown/Library;","checkPermission")
        self.assertTrue(p._direct_auth(invoke,good))
        self.assertFalse(p._direct_auth(invoke,bad))
    def test_literal_never_confused_with_another_string(self):
        const=bytes((0x1a,0,0,0,0x0e,0))
        self.assertTrue(p._direct_literal(const,Dex("Lnone;","x",p.PERMISSION_MARKER)))
        self.assertFalse(p._direct_literal(const,Dex("Lnone;","x","not the permission")))
    def test_direct_iae_throw_requires_matching_register_and_type(self):
        class Types:
            type_count=1
            def type(self,idx):return "Ljava/lang/IllegalArgumentException;"
        # new-instance v1, type#0; throw v1
        direct=bytes((0x22,1,0,0,0x27,1,0x0e,0))
        just_new=bytes((0x22,1,0,0,0x27,2,0x0e,0))
        self.assertEqual(p._explicit_iae_throw(direct,Types()),"IAE_DIRECT_THROW")
        self.assertEqual(p._explicit_iae_throw(just_new,Types()),"IAE_CONSTRUCT_ONLY")

    def test_ise_candidate_only_direct_same_register_throw(self):
        class Types:
            type_count=1
            def type(self,idx):return "Ljava/lang/IllegalStateException;"
        self.assertTrue(p._explicit_sdk_illegal_state(bytes((
            0x22,2,0,0,0x27,2,0x0e,0)),Types()))
        self.assertFalse(p._explicit_sdk_illegal_state(bytes((
            0x22,2,0,0,0x27,1,0x0e,0)),Types()))

    def test_runtime_causality_default_not_claimed(self):
        self.assertNotIn("runtime_throw_site_proven\":True",SUBJECT.read_text())
if __name__=="__main__":
    unittest.main()
