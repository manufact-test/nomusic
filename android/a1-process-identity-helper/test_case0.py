"""B-only synthetic regression suite; no original binaries or secrets."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location("case0",Path(__file__).with_name("case0.py"))
case=importlib.util.module_from_spec(spec);spec.loader.exec_module(case)

class FakeDex:
    method_count=1
    string_count=0
    def method(self,idx):
        assert idx==0
        return "Landroid/app/ActivityThread;","currentProcessName"

class Case0Tests(unittest.TestCase):
    def test_process_role_is_package_scoped(self):
        ps="""USER PID PPID CMD
u0_a1 101 1 ru.yandex.music
u0_a1 102 1 ru.yandex.music:metrica
u0_a2 202 1 pro.celikom.yandex.nativeclonelab
u0_a2 203 1 pro.celikom.yandex.nativeclonelab:metrica"""
        stock=case.parse_ps(ps,case.ORIGINAL)
        clone=case.parse_ps(ps,case.CLONE)
        self.assertTrue(stock["main"])
        self.assertTrue(clone["main"])
        self.assertTrue(clone["metrica_aux"])
        self.assertNotIn("202",repr(stock))
    def test_android_event_process_differentiation(self):
        events="""
I/am_proc_start(123): [0,100,123,ru.yandex.music,top]
I/am_proc_bound(123): [0,100,ru.yandex.music:metrica]
I/am_proc_start(123): [0,101,123,pro.celikom.yandex.nativeclonelab,top]
I/am_proc_died(123): [0,101,pro.celikom.yandex.nativeclonelab]
"""
        self.assertEqual(case.parse_events(events,case.ORIGINAL),{"BOUND_AUX":1,"START_MAIN":1})
        self.assertEqual(case.parse_events(events,case.CLONE),{"DIED_MAIN":1,"START_MAIN":1})
    def test_exact_process_name_api_safely_classified(self):
        self.assertEqual(case._api_category("Landroid/app/ActivityThread;","currentProcessName"),
                         "ANDROID_PROCESS_NAME_SUPPLIER")
        self.assertEqual(case._api_category("Ljava/lang/String;","equals"),
                         "JAVA_STRING_EQUALITY")
        self.assertEqual(case._api_category("Landroid/app/ActivityThread;","secretMethod"),"OTHER")
    def test_bounded_invoke_body(self):
        code=bytes([0x71,0x00,0x00,0x00,0x00,0x00, 0x0c,0x00, 0x12,0x01,0x0f,0x01])
        result,refs=case._body(FakeDex(),0,code)
        self.assertTrue(result["decoded"])
        self.assertEqual(refs,{0})
        self.assertEqual(result["direct_process_supply"],["ANDROID_PROCESS_NAME_SUPPLIER"])
        self.assertEqual(result["return_op_count"],1)
    def test_manifest_default_vs_explicit_original(self):
        xml="""E: manifest
  E: application
    A: android:name="ru.example.App"
    E: activity
      A: android:name="ru.yandex.music.main.MainScreenActivity"
      A: android:process="ru.yandex.music"
"""
        res=case._manifest(xml)
        self.assertEqual(res["application_process"],"DEFAULT")
        self.assertEqual(res["main_activity_process"],"STOCK_ABSOLUTE")
        self.assertTrue(res["main_activity_manifest_seen"])

if __name__=="__main__":unittest.main()
