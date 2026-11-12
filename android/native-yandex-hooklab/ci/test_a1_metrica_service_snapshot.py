"""Synthetic privacy regression for guest process/service comparisons."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from a1_metrica_service_snapshot import classify_metrica_service_snapshot,CLONE,ORIGINAL

class GuestServiceSnapshotTest(unittest.TestCase):
    def test_scope_to_requested_package_without_pid_or_vendor_symbol(self):
        ps=(
            "u0_a11 431 other app "+CLONE+"\n"
            "u0_a11 432 other app "+CLONE+":Metrica\n"
            "u0_a13 833 other app "+ORIGINAL+":Metrica\n"
            "u0_a15 555 other app com.third.party.secret\n")
        svc="ServiceRecord x "+CLONE+"/com.yandex.metrica.AppMetricaService account_token=SECRET"
        got=classify_metrica_service_snapshot(ps,svc,CLONE,ps_ok=True,services_ok=True)
        self.assertEqual(got["metrica_aux_process_count_bounded"],1)
        self.assertEqual(got["own_process_count_bounded"],2)
        self.assertTrue(got["metrica_service_record_line_candidate"])
        for private in ("431","432","833","555","account_token","SECRET","com.third.party"):
            self.assertNotIn(private,str(got))

    def test_unavailable_snapshot_is_unknown_not_false(self):
        got=classify_metrica_service_snapshot("","",CLONE,ps_ok=False,services_ok=False)
        self.assertIsNone(got["metrica_aux_process_count_bounded"])
        self.assertIsNone(got["metrica_service_record_line_candidate"])

    def test_forbid_unscoped_external_package(self):
        with self.assertRaises(ValueError):
            classify_metrica_service_snapshot("","", "com.random.user",ps_ok=True,services_ok=True)

if __name__=="__main__":
    unittest.main()
