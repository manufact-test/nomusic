import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from probe_arm_device import Snapshot
import probe_parallel_honor as phone

def make(**kwargs):
    o=dict(api_level="33",abis="arm64-v8a,armeabi-v7a",
           emulator="0",boot_emulator="0",model="HONOR 50",
           device="NTH-NX9",yandex_installed=True,play_store_installed=True)
    o.update(kwargs)
    return Snapshot(**o)

class TestHonorReadonly(unittest.TestCase):
    def test_current_owner_device_is_allowed_for_READ_ONLY_checks(self):
        report=phone.evaluate(make(),False)
        self.assertTrue(report["ready_for_FUTURE_manual_package_review"])
        self.assertTrue(report["official_yandex_still_installed"])
        self.assertFalse(report["native_audio_replacement_tested"])
        self.assertFalse(report["device_mutation"])
        self.assertEqual(report["play_protect"],"MUST_BE_CHECKED_MANUALLY_ON_DEVICE")
    def test_official_yandex_absent_is_hard_stop(self):
        self.assertFalse(phone.evaluate(make(yandex_installed=False),False)["ready_for_FUTURE_manual_package_review"])
    def test_no_automatic_overwrite_existing_parallel_copy(self):
        self.assertIn("PARALLEL_TEST_PACKAGE_ALREADY_PRESENT_NO_AUTOMATIC_OVERWRITE",
                      phone.evaluate(make(),True)["blockers"])
    def test_api_abi_emulator_and_wrong_device_fail(self):
        for changes in (
            {"api_level":"32"},{"abis":"arm64-v8a"},
            {"emulator":"1"},{"model":"Pixel","device":"pixel"},
        ):
            self.assertFalse(phone.evaluate(make(**changes),False)["ready_for_FUTURE_manual_package_review"])
    def test_no_reveal_of_pm_values(self):
        def fake(*args):
            return 0, "package:/data/app/secret-base.apk"
        self.assertTrue(phone._pm_present(fake,"pro.celikom.yandex.nativeclonelab"))
        self.assertNotIn("secret-base",str(phone.evaluate(make(),False)))
        with self.assertRaisesRegex(RuntimeError,"UNEXPECTED_PACKAGE"):
            phone._pm_present(lambda *args:(0,"auth_token=secret"),"x")
if __name__=="__main__":
    unittest.main()
