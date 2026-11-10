#!/usr/bin/env python3
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab_private_export import ACK, export_private_lab_parts

CERT = "a" * 64

class PrivateLabExportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.repo = self.home / "private-repo"
        self.repo.mkdir()
        self.parts = []
        for i, label in enumerate(["", "config.armeabi_v7a", "config.mdpi",
                                   "config.ru", "config.xxhdpi"]):
            f = self.home / ("mock-input-" + str(i) + ".apk")
            f.write_bytes(b"mock-only-" + str(i).encode())
            self.parts.append((label, f))
    def run_export(self, path, *, confirm=ACK, parts=None):
        return export_private_lab_parts(
            self.parts if parts is None else parts, str(path), confirm,
            repo_root=self.repo, lab_signer=CERT
        )
    def test_requires_opt_in_and_new_outside_repo_directory(self):
        target = self.home / "research-output"
        with self.assertRaisesRegex(ValueError, "CONFIRMATION_REQUIRED"):
            self.run_export(target, confirm=None)
        self.assertFalse(target.exists())
        with self.assertRaisesRegex(ValueError, "NO_RESEARCH_APKS"):
            self.run_export(self.repo / "subfolder")
        with self.assertRaisesRegex(ValueError, "EXACT_FIVE"):
            self.run_export(target, parts=self.parts[:4])
    def test_never_export_from_github_actions(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            with self.assertRaisesRegex(ValueError, "NEVER_EXPORT"):
                self.run_export(self.home / "blocked")
    def test_local_research_output_only(self):
        target = self.home / "private-output"
        result = self.run_export(target)
        self.assertTrue(result["exported"])
        self.assertFalse(result["device_installation_performed"])
        receipt = json.loads((target / "research-receipt.json").read_text())
        self.assertEqual(receipt["host_package"], "ru.yandex.music")
        self.assertEqual(receipt["sigbypass"], 0)
        self.assertEqual(receipt["part_count"], 5)
        self.assertFalse(receipt["consumer_single_apk"])
        self.assertFalse(receipt["native_music_swap_tested"])
        for part in receipt["parts"]:
            self.assertEqual((target / part["name"]).stat().st_size, part["bytes"])
        with self.assertRaisesRegex(ValueError, "MUST_BE_NEW"):
            self.run_export(target)
    def test_no_export_by_default(self):
        result = export_private_lab_parts(
            [], None, None, repo_root=self.repo, lab_signer="not-a-cert")
        self.assertEqual(result, {"exported": False})

if __name__ == "__main__":
    unittest.main()
