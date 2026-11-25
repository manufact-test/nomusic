import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("android_public",
 ROOT/"floki-android-customer-stable-consumer.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class AndroidCustomerApprovalTests(unittest.TestCase):
    def approval(self,approved):
        d={"schema":1,"channel":"customer-stable","approved":approved}
        return type("R",(),{"stdout":json.dumps(d).encode()})
    def test_null_is_not_published(self):
        with patch.object(m.subprocess,"run",return_value=self.approval(None)):
            self.assertIsNone(m.approved())
    def test_requires_exact_owner_acceptance_and_identity(self):
        good={"version_code":95,"version_name":"0.3.94",
              "sha256":"a"*64,"owner_accepted":True}
        with patch.object(m.subprocess,"run",return_value=self.approval(good)):
            self.assertEqual(m.approved(),good)
        for field,bad in (
            ("version_code",94),("version_name","../../etc/passwd"),
            ("sha256","notahash"),("owner_accepted",False)
        ):
            with self.subTest(field=field):
                changed=dict(good);changed[field]=bad
                with patch.object(m.subprocess,"run",return_value=self.approval(changed)):
                    with self.assertRaises(RuntimeError):
                        m.approved()
    def test_owner_only_not_auto_published(self):
        with patch.object(m.os,"geteuid",return_value=0),\
             patch.object(m.Path,"lstat",return_value=type("S",(),{"st_mode":0o040755})()),\
             patch.object(m.Path,"is_symlink",return_value=False),\
             patch.object(m.os,"open",return_value=99),\
             patch.object(m.fcntl,"flock"),\
             patch.object(m.os,"close"),\
             patch.object(m,"approved",return_value=None),\
             patch.object(m,"promote",side_effect=AssertionError("PUBLICATION_FORBIDDEN")):
            m.main()

if __name__=="__main__":
    unittest.main()
