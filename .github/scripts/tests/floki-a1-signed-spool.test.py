#!/usr/bin/env python3
"""No-network regression for isolated A1 staging and root verification contracts."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
def load(module_name, filename):
    spec = importlib.util.spec_from_file_location(module_name, HERE / filename)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

STAGE = load("floki_a1_spool", "floki-a1-signed-spool.py")
ROOT = load("floki_a1_consumer", "floki-a1-root-signed-spool-consumer.py")


class A1SpoolContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="a1-spool-test-")
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.name = "CELIKOM-A1-RAMIL-AU-BETA16-HONOR50-20261125.apk"
        self.apk = self.dir / self.name
        self.apk.write_bytes(b"PK\x03\x04" + b"x" * (1024 * 1024))
        self.digest = hashlib.sha256(self.apk.read_bytes()).hexdigest()
        self.meta = {"run":45652314715,"attempt":1,"name":self.name,
                     "size":self.apk.stat().st_size,"sha256":self.digest}
        self.proof = {"schema":1,"distribution_only":True,"distribution_target":"main",
                      "source_repository":"manufact-test/nomusic",
                      "source_branch":STAGE.BRANCH,"source_commit":"1"*40,
                      "workflow_run_id":self.meta["run"],"workflow_run_attempt":1,
                      "apk":self.name,"apk_size":self.meta["size"],
                      "apk_sha256":self.digest,"acoustic_replacement_proven":False}
        self.meta_file = self.dir / "metadata.json"
        self.proof_file = self.dir / "BUILD-PROVENANCE.json"
        self.write()
        self.spool = self.dir / "spool"

    def write(self):
        self.meta_file.write_text(json.dumps(self.meta))
        self.proof_file.write_text(json.dumps(self.proof))

    def call_stage(self):
        return STAGE.stage(self.apk, self.meta_file, self.proof_file, self.spool)

    def test_stages_immutable_and_idempotent(self):
        folder = self.call_stage()
        self.assertEqual(folder, self.call_stage())
        self.assertEqual(folder.stat().st_mode & 0o777, 0o700)
        self.assertEqual((folder / self.name).stat().st_mode & 0o777, 0o600)
        self.assertEqual(hashlib.sha256((folder/self.name).read_bytes()).hexdigest(),
                         self.digest)
        self.assertEqual(len([x for x in self.spool.iterdir() if x.name.startswith("a1-")]),1)

    def test_rejects_wrong_apk_hash(self):
        self.meta["sha256"] = "0"*64
        self.proof["apk_sha256"] = "0"*64
        self.write()
        with self.assertRaisesRegex(ValueError,"APK_SIZE_OR_SHA256"):
            self.call_stage()

    def test_rejects_wrong_provenance(self):
        self.proof["source_branch"] = "main"
        self.write()
        with self.assertRaisesRegex(ValueError,"PROVENANCE_MISMATCH"):
            self.call_stage()

    def test_rejects_symlink_source(self):
        target = self.dir / "another.apk"
        self.apk.rename(target)
        self.apk.symlink_to(target)
        with self.assertRaisesRegex(ValueError,"UNSAFE_SOURCE_FILE"):
            self.call_stage()

    def test_root_metadata_contract(self):
        self.assertEqual(ROOT.validate_provenance(self.meta,self.proof,
                           self.meta["run"],1,self.digest),(self.name,self.meta["size"]))
        wrong = self.proof.copy()
        wrong["acoustic_replacement_proven"] = True
        with self.assertRaisesRegex(RuntimeError,"INVALID_PROVENANCE"):
            ROOT.validate_provenance(self.meta,wrong,self.meta["run"],1,self.digest)
        wrong_meta = self.meta.copy()
        wrong_meta["name"] = "../outside.apk"
        with self.assertRaisesRegex(RuntimeError,"WRONG_APK"):
            ROOT.validate_provenance(wrong_meta,self.proof,self.meta["run"],1,self.digest)

    def test_root_json_no_symlink(self):
        with self.meta_file.open("rb") as _:
            dfd=os.open(self.dir,os.O_RDONLY|os.O_DIRECTORY)
            try:
                self.assertEqual(ROOT.safe_json(dfd,"metadata.json",os.getuid()),self.meta)
                sym=self.dir/"evil.json"
                sym.symlink_to(self.meta_file)
                with self.assertRaises(OSError):
                    ROOT.safe_json(dfd,"evil.json",os.getuid())
            finally:
                os.close(dfd)


if __name__ == "__main__":
    unittest.main()
