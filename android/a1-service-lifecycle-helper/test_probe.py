#!/usr/bin/env python3
"""Synthetic regression tests: no vendor binaries and no Android device needed."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location("helper_probe",Path(__file__).with_name("probe.py"))
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class LifecycleTests(unittest.TestCase):
    def test_events_are_scoped_and_finite(self):
        log = """
I/am_proc_start( 100): [0,1234,100,ru.yandex.music:metrica,service]
I/am_create_service( 100): [0,456,ru.yandex.music/com.vendor.metrica.Service]
I/am_bind_service( 100): [0,456,ru.yandex.music/com.vendor.metrica.Service]
I/am_proc_died( 100): [0,1234,ru.yandex.music:metrica]
I/am_create_service( 100): [0,333,pro.celikom.yandex.nativeclonelab/com.vendor.Unrelated]
"""
        stock=p.event_snapshot(log,p.STOCK)
        clone=p.event_snapshot(log,p.CLONE)
        self.assertEqual(stock["event_counts"]["am_create_service_METRICA"],1)
        self.assertEqual(stock["event_counts"]["am_proc_died_METRICA"],1)
        self.assertEqual(clone["event_counts"],{"am_create_service_APP_OTHER":1})
        self.assertNotIn("vendor",repr(stock))
        self.assertNotIn("1234",repr(stock))

    def test_processes_not_confused_by_coinstallation(self):
        ps="""USER PID PPID CMD
u0_a1 111 1 ru.yandex.music
u0_a1 112 1 ru.yandex.music:metrica
u0_a2 212 1 pro.celikom.yandex.nativeclonelab
u0_a2 213 1 pro.celikom.yandex.nativeclonelab:other
"""
        self.assertEqual(p.process_snapshot(ps,p.STOCK),(1,1,1))
        self.assertEqual(p.process_snapshot(ps,p.CLONE),(1,1,0))

    def test_manifest_private_process_and_stock_leak(self):
        manifest="""E: manifest
  E: application
    E: service
      A: android:name(0x01010003)="com.example.metrica.SyncService" (Raw: "com.example.metrica.SyncService")
      A: android:process(0x01010011)=":metrica" (Raw: ":metrica")
      A: android:exported(0x01010010)=(type 0x12)0x0
    E: service
      A: android:name(0x01010003)="com.example.metrica.BadService" (Raw: "com.example.metrica.BadService")
      A: android:process(0x01010011)="ru.yandex.music:metrica" (Raw: "ru.yandex.music:metrica")
"""
        actual=p.manifest_components(manifest,p.CLONE)
        self.assertEqual(actual["metrica_service_count"],2)
        self.assertEqual(actual["metrica_process_kinds"],{"PRIVATE":1,"STOCK_EXPLICIT":1})
        self.assertNotIn("BadService",str({k:v for k,v in actual.items() if not k.startswith("_")}))

    def test_active_service_record(self):
        dump="""ACTIVITY MANAGER SERVICES
  * ServiceRecord{12 u0 ru.yandex.music/com.vendor.metrica.Service}
    app=ProcessRecord{55 777:ru.yandex.music:metrica/u0a2}
    Bindings:
  * ServiceRecord{13 u0 pro.celikom.yandex.nativeclonelab/com.vendor.metrica.Service}
    app=null
"""
        self.assertEqual(p.service_snapshot(dump,p.STOCK),(1,1,1))
        self.assertEqual(p.service_snapshot(dump,p.CLONE),(1,0,0))

if __name__=="__main__":
    unittest.main()
