import importlib.util
import json
import stat
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("release_receipt",ROOT/"floki-release-public-receipt.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class SanitizedReleaseStatus(unittest.TestCase):
    def test_sha_only_no_private_url_or_identity(self):
        win={"version":"0.24.56","sha256":"a"*64,
             "packageUrl":"https://celikom.com/downloads/windows/private-owner.exe"}
        items=[
            {"sha256":"b"*64},
            {"sha256":"c"*64,"https_verified":True,
             "url":"https://celikom.com/downloads/android/private-token"},
            {"apkSha256":"d"*64},
            {"sha256":"e"*64,"https_verified":True,"source_commit":"f"*40},
        ]
        with patch.object(mod.Path,"lstat",return_value=SimpleNamespace(
                st_mode=stat.S_IFLNK|0o777,st_uid=0)), \
             patch.object(mod.os,"readlink",return_value="versions/0.24.56"), \
             patch.object(mod,"read",return_value=json.dumps(win).encode()), \
             patch.object(mod,"optional_json",side_effect=items):
            result=mod.snapshot()
        self.assertEqual(result,{
            "windows_owner_sha256":"a"*64,
            "windows_customer_sha256":"b"*64,
            "android_owner_sha256":"c"*64,
            "android_customer_sha256":"d"*64,
            "extension_owner_sha256":"e"*64
        })
        published=json.dumps(result)
        for secret in ("url","source_commit","private-token","run_id","user"):
            self.assertNotIn(secret,published)
    def test_private_capability_symlink_refused(self):
        with patch.object(mod.Path,"lstat",return_value=SimpleNamespace(
                st_mode=stat.S_IFLNK|0o777,st_uid=0)), \
             patch.object(mod.os,"readlink",return_value="../../private/token"):
            with self.assertRaises(RuntimeError):
                mod.snapshot()
    def test_unverified_state_not_reported(self):
        win={"version":"0.24.55","sha256":"a"*64}
        values=[None,{"sha256":"c"*64,"https_verified":False},
                None,{"sha256":"e"*64,"https_verified":False}]
        with patch.object(mod.Path,"lstat",return_value=SimpleNamespace(
                st_mode=stat.S_IFLNK|0o777,st_uid=0)), \
             patch.object(mod.os,"readlink",return_value="versions/0.24.55"), \
             patch.object(mod,"read",return_value=json.dumps(win).encode()), \
             patch.object(mod,"optional_json",side_effect=values):
            d=mod.snapshot()
        self.assertEqual(d["windows_owner_sha256"],"a"*64)
        for v in (d["windows_customer_sha256"],d["android_owner_sha256"],
                  d["android_customer_sha256"],d["extension_owner_sha256"]):
            self.assertIsNone(v)

if __name__=="__main__":unittest.main()
