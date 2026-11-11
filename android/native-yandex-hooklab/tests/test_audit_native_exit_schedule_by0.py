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
