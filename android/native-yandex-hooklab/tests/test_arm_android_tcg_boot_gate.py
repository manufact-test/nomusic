"""Pure tests of native ARM Android emulator ABI gate, no adb connection."""
import importlib.util
import pathlib
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / "arm_android_tcg_boot_gate.py"
spec = importlib.util.spec_from_file_location("arm_android_tcg_boot_gate", PATH)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class BootGateTests(unittest.TestCase):
    def sample(self, **kw):
        params = dict(host_machine="arm64", boot="1", is_emulator="1",
                      isa="aarch64", abis="arm64-v8a,armeabi-v7a,armeabi",
                      abis32="armeabi-v7a,armeabi", sdk="30")
        params.update(kw)
        return gate.classify(**params)
    def test_real_arm_32bit_guest(self):
        obj = self.sample()
        self.assertTrue(obj["ready_for_armv7_owned_loader"])
        self.assertFalse(obj["apk_installed"])
        self.assertFalse(obj["vendor_code_accessed"])
    def test_64bit_only_guest_is_honestly_not_ready(self):
        self.assertFalse(self.sample(abis32="")["ready_for_armv7_owned_loader"])
    def test_reject_x86_translated_guest(self):
        with self.assertRaises(gate.GateError):
            self.sample(isa="x86")
        with self.assertRaises(gate.GateError):
            self.sample(abis="x86,armeabi-v7a")
    def test_reject_physical_device_even_if_arm(self):
        with self.assertRaises(gate.GateError):
            self.sample(is_emulator="0")
    def test_reject_non_arm_runner(self):
        with self.assertRaises(gate.GateError):
            self.sample(host_machine="x86_64")
    def test_reject_incomplete_boot_and_wrong_version(self):
        with self.assertRaises(gate.GateError):
            self.sample(boot="0")
        with self.assertRaises(gate.GateError):
            self.sample(sdk="33")

if __name__ == "__main__":
    unittest.main()
