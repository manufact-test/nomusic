#!/usr/bin/env python3
"""A1 host observation gates; no adb/device required in these unit tests."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import witness_installed_arm_host as witness
from probe_arm_device import Snapshot

def snapshot(**changes):
    baseline = dict(
        api_level="33", abis="armeabi-v7a,arm64-v8a", emulator="0",
        boot_emulator="0", model="Disposable Test ARM", device="test_arm",
        yandex_installed=True, play_store_installed=True,
    )
    baseline.update(changes)
    return Snapshot(**baseline)

def adb_fake(*args):
    if args == ("devices",):
        return 0, "List of devices attached\nSERIAL\tdevice\n"
    if args == ("shell", "dumpsys", "package", witness.HOST):
        return 0, "Packages:\nPackage [ru.yandex.music]:\n versionCode=24026531\n"
    raise AssertionError(args)

class WitnessTest(unittest.TestCase):
    def test_exact_postinstall_gate(self):
        self.assertEqual(witness.eligible_post_install(snapshot()), [])
        self.assertIn("OWNER_PRIMARY_MODEL_BLOCKED",
                      witness.eligible_post_install(snapshot(model="HONOR 50", device="NTH-NX9")))
        self.assertIn("RESEARCH_HOST_NOT_INSTALLED",
                      witness.eligible_post_install(snapshot(yandex_installed=False)))
        self.assertIn("NO_ARMV7_32BIT_APP_SUPPORT",
                      witness.eligible_post_install(snapshot(abis="arm64-v8a")))
        self.assertIn("EMULATOR_NOT_PHYSICAL_DEVICE",
                      witness.eligible_post_install(snapshot(emulator="1")))
        self.assertIn("REQUIRES_ANDROID_13_PLUS",
                      witness.eligible_post_install(snapshot(api_level="32")))
    def test_private_log_never_appears_in_summary(self):
        log = "\n".join([
            "I/CELIKOM-NativeLab( 123): observer: module loaded URL=https://private.invalid/secret",
            "I/CELIKOM-NativeLab( 123): observer: native file-info converter hooks armed; read-only",
            "I/CELIKOM-NativeLab( 123): observer: reader executions=9 token=PRIVATE",
            "I/Other( 123): observer: module loaded",
            "anything without a real tag observer: package ready",
        ])
        flags = witness.classify(log)
        self.assertEqual(flags["module_loaded"], 1)
        self.assertEqual(flags["fileinfo_armed"], 1)
        self.assertEqual(flags["reader_execution_event"], 1)
        self.assertEqual(flags["package_ready"], 0)
        self.assertNotIn("PRIVATE", str(flags))
        self.assertNotIn("https", str(flags))
    def test_refuses_without_manual_confirmations(self):
        result = witness.report(adb_fake, seconds=10,
                                confirmed_spare=False, confirmed_protect=True)
        self.assertTrue(result["blocked"])
        self.assertFalse(result["native_audio_swap_verified"])
    def test_observation_is_not_sound(self):
        original_collect = witness.collect
        try:
            witness.collect = lambda adb: snapshot()
            result = witness.report(
                adb_fake, seconds=10, confirmed_spare=True,
                confirmed_protect=True,
                observer=lambda seconds: ({"module_loaded": 1,
                                          "source_lifecycle_event": 3},
                                         "OBSERVATION_WINDOW_COMPLETE"))
            self.assertFalse(result["blocked"])
            self.assertTrue(result["module_runtime_observed"])
            self.assertTrue(result["source_pipeline_activity_observed"])
            self.assertFalse(result["native_active_decoder_verified"])
            self.assertFalse(result["native_audio_swap_verified"])
            self.assertFalse(result["play_protect_automatic_attestation"])
        finally:
            witness.collect = original_collect
    def test_wrong_host_version(self):
        self.assertTrue(witness.installed_version(adb_fake))
        self.assertFalse(witness.installed_version(
            lambda *args: (0, "versionCode=24026530")))
        self.assertFalse(witness.installed_version(
            lambda *args: (1, "")))

if __name__ == "__main__":
    unittest.main()
