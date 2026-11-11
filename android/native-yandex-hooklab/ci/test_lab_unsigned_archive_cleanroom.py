#!/usr/bin/env python3
"""Synthetic-only tests for scrub of disposable lab-generated unsigned APKs."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

from lab_signer_signal_gate import probe_apk_zip
from lab_unsigned_archive_cleanroom import (
    is_v1_signing_artifact, remove_stale_v1_from_disposable_unsigned,
)


class CleanroomTest(unittest.TestCase):
    def archive(self, dir: Path, entries: list[tuple[str, bytes]]) -> Path:
        target = dir / "synthetic-unsigned.apk"
        with zipfile.ZipFile(target, "w") as z:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                for name, data in entries:
                    z.writestr(name, data)
        return target

    def basic(self) -> list[tuple[str, bytes]]:
        return [
            ("AndroidManifest.xml", b"fabricated manifest"),
            ("classes.dex", b"fake dex bytes only"),
            ("lib/arm64-v8a/libdummy.so", b"fake ELF bytes only"),
            ("META-INF/ORIGINAL.SF", b"obsolete sig from fabricated example"),
            ("META-INF/ORIGINAL.RSA", b"obsolete sig from fabricated example"),
            ("META-INF/MANIFEST.MF", b"obsolete manifest"),
            ("META-INF/services/registry.txt", b"keep this"),
        ]

    def test_removes_only_old_signing_entries_and_keeps_payload(self):
        with tempfile.TemporaryDirectory(prefix="cleanroom-test-") as d:
            root = Path(d)
            src = self.archive(root, self.basic())
            digest = hashlib.sha256(src.read_bytes()).hexdigest()
            dst = root / "cleaned-unsigned.apk"
            info = remove_stale_v1_from_disposable_unsigned(src, dst)
            self.assertEqual(info["discarded_obsolete_v1_entries"], 3)
            self.assertTrue(info["all_other_entry_bytes_preserved"])
            self.assertTrue(info["issuer_certificate_spoofed"] is False)
            self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(), digest)
            self.assertTrue(probe_apk_zip(dst)["zip_integrity_ok"])
            with zipfile.ZipFile(dst) as zipfile_dst:
                self.assertEqual(zipfile_dst.read("classes.dex"), b"fake dex bytes only")
                self.assertEqual(zipfile_dst.read("lib/arm64-v8a/libdummy.so"), b"fake ELF bytes only")
                self.assertEqual(zipfile_dst.read("META-INF/services/registry.txt"), b"keep this")
                self.assertNotIn("META-INF/ORIGINAL.RSA", zipfile_dst.namelist())
                self.assertNotIn("META-INF/MANIFEST.MF", zipfile_dst.namelist())

    def test_no_signatures_is_idempotent_new_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = self.archive(root, self.basic()[:3])
            dst = root / "cleaned.apk"
            info = remove_stale_v1_from_disposable_unsigned(src, dst)
            self.assertEqual(info["discarded_obsolete_v1_entries"], 0)
            self.assertTrue(info["clean_unsigned_zip_integrity_ok"])

    def test_removal_is_only_direct_meta_inf_child(self):
        self.assertTrue(is_v1_signing_artifact("META-INF/ONE.EC"))
        self.assertTrue(is_v1_signing_artifact("META-INF/ONE.SF"))
        self.assertTrue(is_v1_signing_artifact("META-INF/SIG-UNKNOWN"))
        self.assertTrue(is_v1_signing_artifact("meta-inf/one.rsa"))
        self.assertFalse(is_v1_signing_artifact("META-INF/services/ONE.SF"))
        self.assertFalse(is_v1_signing_artifact("META-INF/services/registry.txt"))
        self.assertFalse(is_v1_signing_artifact("AndroidManifest.xml"))

    def test_refuse_same_source_and_dest(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = self.archive(root, self.basic())
            with self.assertRaisesRegex(ValueError, "SOURCE_DESTINATION_COLLISION"):
                remove_stale_v1_from_disposable_unsigned(src, src)

    def test_refuse_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = self.archive(root, self.basic())
            dest = root / "already-existing.apk"
            dest.write_bytes(b"must never overwrite")
            with self.assertRaisesRegex(ValueError, "INPUT_INVALID"):
                remove_stale_v1_from_disposable_unsigned(src, dest)
            self.assertEqual(dest.read_bytes(), b"must never overwrite")

    def test_refuse_archive_with_duplicate_zip_entry_names(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = self.archive(root, [("AndroidManifest.xml", b"x"),
                                      ("classes.dex", b"x"),
                                      ("classes.dex", b"duplicate")])
            with self.assertRaisesRegex(ValueError, "UNSAFE_ARCHIVE"):
                remove_stale_v1_from_disposable_unsigned(src, root / "out.apk")

    def test_refuse_path_traversal_and_corrupt_zip(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = self.archive(root, [("AndroidManifest.xml", b"x"),("../escape", b"x")])
            with self.assertRaisesRegex(ValueError, "UNSAFE_ARCHIVE"):
                remove_stale_v1_from_disposable_unsigned(src, root / "out.apk")
            bad = root / "bad-input.apk"
            bad.write_bytes(b"corrupt, not APK")
            with self.assertRaisesRegex(ValueError, "UNSAFE_ARCHIVE"):
                remove_stale_v1_from_disposable_unsigned(bad, root / "out.apk")


if __name__ == "__main__":
    unittest.main()
