"""No connected phone or adb is ever needed for these fail-closed tests."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "probe_arm_device.py"
spec = importlib.util.spec_from_file_location("probe_arm_device", MODULE)
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ArmDeviceGateTest(unittest.TestCase):
    def setUp(self):
        self.good = module.Snapshot(
            api_level="33", abis="arm64-v8a,armeabi-v7a,armeabi",
            emulator="0", boot_emulator="", model="Spare lab device",
            device="generic_spare_arm", yandex_installed=False,
            play_store_installed=True)

    def test_eligible_never_claims_play_protect_pass(self):
        r = module.evaluate(self.good)
        self.assertFalse(r["blocked"])
        self.assertIn("UNVERIFIED", r["play_protect"])
        self.assertFalse(r["installation_performed"])

    def test_64_bit_only_arm_ineligible(self):
        s = module.Snapshot(**{**self.good.__dict__, "abis": "arm64-v8a"})
        self.assertIn("NO_ARMV7_32BIT_APP_SUPPORT", module.evaluate(s)["blockers"])

    def test_existing_yandex_is_hard_blocker(self):
        s = module.Snapshot(**{**self.good.__dict__, "yandex_installed": True})
        self.assertIn("YANDEX_ALREADY_INSTALLED_NO_OVERWRITE", module.evaluate(s)["blockers"])

    def test_owner_honor_50_is_blocked_even_without_yandex(self):
        s = module.Snapshot(**{**self.good.__dict__, "model": "HONOR 50", "device": "NTH-NX9"})
        self.assertIn("OWNER_PRIMARY_MODEL_BLOCKED", module.evaluate(s)["blockers"])

    def test_emulator_or_android_11_is_blocked(self):
        s = module.Snapshot(**{**self.good.__dict__, "emulator": "1", "api_level": "30"})
        r = module.evaluate(s)
        self.assertIn("EMULATOR_NOT_PHYSICAL_DEVICE", r["blockers"])
        self.assertIn("REQUIRES_ANDROID_13_PLUS", r["blockers"])

    def test_play_store_absent_is_blocked(self):
        s = module.Snapshot(**{**self.good.__dict__, "play_store_installed": False})
        self.assertIn("GOOGLE_PLAY_MISSING_PROTECTION_UNVERIFIABLE", module.evaluate(s)["blockers"])

    def test_only_read_only_probes_and_no_private_output(self):
        commands = []
        values = {
            "ro.build.version.sdk": "33", "ro.product.cpu.abilist": "arm64-v8a,armeabi-v7a",
            "ro.kernel.qemu": "0", "ro.boot.qemu": "", "ro.product.model": "Spare",
            "ro.product.device": "spare",
        }
        def fake_adb(*args):
            commands.append(args)
            if args[:2] == ("shell", "getprop"):
                return 0, values[args[2]] + "\n"
            if args == ("shell", "pm", "path", module.TARGET):
                return 0, ""
            if args == ("shell", "pm", "path", module.PLAY_STORE):
                return 0, "package:/some/private/system/path.apk\n"
            raise AssertionError("unexpected adb command")
        r = module.evaluate(module.collect(fake_adb))
        self.assertFalse(r["blocked"])
        self.assertTrue(all(args[0] == "shell" for args in commands))
        self.assertEqual({args[1] for args in commands}, {"getprop", "pm"})

    def test_indeterminate_package_query_fail_closed(self):
        def bad_adb(*args):
            if args[:2] == ("shell", "getprop"):
                return 0, "33\n"
            return 0, "Error: unexpected detail not for logging"
        with self.assertRaisesRegex(RuntimeError, "PACKAGE_QUERY_INDETERMINATE"):
            module.collect(bad_adb)

if __name__ == "__main__":
    unittest.main()
