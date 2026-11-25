import importlib.util
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("root_windows",
       ROOT/"floki-windows-signed-root-consumer.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class WindowsOwnerHTTPSReceipt(unittest.TestCase):
    def test_receipt_is_written_only_after_matching_manifest_sequence(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            dest=root/"versions"/"0.24.56"
            dest.mkdir(parents=True)
            (dest/"manifest.json").write_text(json.dumps({
                "version":"0.24.56","sequence":3,"sha256":"a"*64
            }))
            with patch.object(mod,"ROOT",root),patch.object(mod.os,"chown"):
                mod.record_verified_owner("0.24.56",3)
                record=json.loads((root/"owner-verified.json").read_text())
                self.assertEqual(record,{
                    "version":"0.24.56","sequence":3,"sha256":"a"*64,
                    "https_verified":True
                })
                with self.assertRaises(RuntimeError):
                    mod.record_verified_owner("0.24.56",4)
                self.assertEqual(json.loads((root/"owner-verified.json").read_text()),record)

if __name__=="__main__":unittest.main()
