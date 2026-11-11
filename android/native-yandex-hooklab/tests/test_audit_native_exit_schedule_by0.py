"""No-network unit tests for read-only native exit scheduler summary."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from audit_native_exit_schedule_by0 import summarize, safe_invocation, SCHEDULER_BODIES


class SchedulingSummaryTests(unittest.TestCase):
    def test_safe_invocation_tracks_public_apis_not_argument_values(self):
        item = safe_invocation(("Landroid/os/Handler;", "post",
                                "(Ljava/lang/Runnable;)Z"), 37)
        self.assertTrue(item["scheduler_api_by_name"])
        self.assertEqual(item["code_units_bounded"], 37)
        self.assertNotIn("register", repr(item))
        self.assertIsNone(safe_invocation(("bad class!", "post", "()V"), 1))


    def test_nearby_const_direct_ctor_three_registers(self):
        import struct
        from audit_native_exit_schedule_by0 import constructor_mode_nearby_constant
        class Fake:
            def __init__(self, words):
                self.data = bytearray(16 + len(words) * 2)
                struct.pack_into("<I", self.data, 12, len(words))
                for n, w in enumerate(words):
                    struct.pack_into("<H", self.data, 16 + n * 2, w)
            def u16(self, off):
                return struct.unpack_from("<H", self.data, off)[0]
            def u32(self, off):
                return struct.unpack_from("<I", self.data, off)[0]
        # const/4 v2,#2 then invoke-direct {v0,v1,v2}
        fake = Fake([0x2212, 0x3070, 0x0001, 0x0210, 0x000e])
        value = constructor_mode_nearby_constant(fake, 0, 1, 0x70)
        self.assertEqual(value["mode"], 2)
        self.assertEqual(value["reason"], "NEARBY_CONST_ONLY")
        not_three = constructor_mode_nearby_constant(
            Fake([0x2212, 0x2070, 0x0001, 0x0210]), 0, 1, 0x70)
        self.assertEqual(not_three["mode"], "NOT_PROVEN")

    def test_missing_scheduler_body_fails_closed(self):
        with self.assertRaises(ValueError):
            summarize([])

    def test_all_scheduler_bodies_and_dedupe_incoming(self):
        bodies = [{
            "method": dict(owner=o, method=m, prototype=p),
            "xx0_constructor": False,
            "calls": [], "body_contains_scheduler_like_method": False,
        } for o, m, p in SCHEDULER_BODIES]
        item = {
            "signed_scheduler_bodies": bodies, "signed_class_info": [],
            "bounded_incoming_method_refs": [
                {"invoked": list(next(iter(SCHEDULER_BODIES))),
                 "caller": dict(owner="Lexample;", method="startup", prototype="()V"),
                 "caller_is_ymapplication": False},
            ] * 2,
        }
        result = summarize([item])
        self.assertEqual(result["own_sched_lookups"], 3)
        self.assertEqual(result["inbound_ctor_and_scheduler_site_count_bounded"], 1)
        self.assertTrue(result["vendor_signed_host_untouched"])


if __name__ == "__main__":
    unittest.main()
