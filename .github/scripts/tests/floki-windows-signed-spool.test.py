import hashlib
import os
import pathlib
import runpy
import stat
import tempfile
import unittest

core = runpy.run_path(str(pathlib.Path(__file__).resolve().parents[1] / "floki-windows-signed-spool.py"))
publish = core["publish"]

class WindowsSpoolTests(unittest.TestCase):
    def test_atomic_private_stage_and_exact_idempotent_replay(self):
        with tempfile.TemporaryDirectory() as d:
            base = pathlib.Path(d)
            src = base / "signed.zip"
            src.write_bytes(b"PK" + b"x"*8190)
            spool = base / "private-spool"
            dest = publish(src,"0.24.56",3,spool)
            self.assertTrue(dest.is_file())
            self.assertEqual(stat.S_IMODE(dest.lstat().st_mode),0o600)
            self.assertEqual(stat.S_IMODE(spool.lstat().st_mode),0o700)
            self.assertEqual(dest.read_bytes(),src.read_bytes())
            self.assertIn(hashlib.sha256(src.read_bytes()).hexdigest(),dest.name)
            self.assertEqual(publish(src,"0.24.56",3,spool),dest)
            self.assertEqual([p.name for p in spool.iterdir()],[dest.name])

    def test_rejects_unsafe_links_spool_and_identity(self):
        with tempfile.TemporaryDirectory() as d:
            base=pathlib.Path(d)
            src=base/"transfer.zip"
            src.write_bytes(b"PK"+b"y"*100)
            spool=base/"spool"
            for ver,seq in (("../x",3),("0.24.56",0),("0.24.56",2**53)):
                with self.assertRaises(ValueError):publish(src,ver,seq,spool)
            link=base/"link.zip"
            link.symlink_to(src)
            with self.assertRaises(ValueError):publish(link,"0.24.56",3,spool)
            spool.mkdir(mode=0o700)
            spool.chmod(0o755)
            with self.assertRaises(ValueError):publish(src,"0.24.56",3,spool)

    def test_immutable_spool_conflict_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            base=pathlib.Path(d);src=base/"signed.zip"
            src.write_bytes(b"PK"+b"z"*200)
            dest=publish(src,"0.24.56",3,base/"spool")
            dest.chmod(0o644)
            with self.assertRaises(ValueError):publish(src,"0.24.56",3,base/"spool")

if __name__ == "__main__":
    unittest.main()
