"""Synthetic only: MAIN-exit PID bounded events, no user data leak."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from a1_metrica_witness_private_parser import scoped_metrica_witness
PKG="pro.celikom.yandex.nativeclonelab"
EXIT=f"ApplicationExitInfo #0: pid=431 process={PKG} reason=4 status=0\n"

def log(pid,s):
    return f"11-12 12:00:01.123 {pid} {pid} I CELIKOM_A1_EXIT_WITNESS: {s}\n"


class ReadOnlyMetricaWitnessTest(unittest.TestCase):
    def test_own_main_exact_events_return_enums_and_redact(self):
        value=(
            log(431,"event=ARMED;origin=REGISTERED;error=NONE;thread=MAIN")
            +log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_OTHER;thread=OTHER")
            +log(431,"event=METRICA_EXCEPTION;origin=MUSIC_APP;error=EXC_AUTH;thread=OTHER")
            +log(432,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_SIGNATURE;thread=OTHER")
            +"secret access_token=PRIVATESECRET\n")
        result=scoped_metrica_witness(EXIT,value)
        self.assertTrue(result["read_only_witness_arm_marker_seen"])
        self.assertTrue(result["read_only_metrica_exception_marker_seen"])
        self.assertEqual(result["metrica_exception_event_count_bounded"],2)
        self.assertEqual(result["metrica_exception_message_categories"],["EXC_AUTH","EXC_OTHER"])
        for secret in ("PRIVATESECRET","432","431","access_token"):
            self.assertNotIn(secret,str(result))

    def test_bounded_context_identity_and_metrica_before_uncaught(self):
        events=(
            log(431,"event=ARMED;origin=REGISTERED;error=NONE;thread=MAIN")
            +log(431,"event=APP_CONTEXT;origin=CLONE;error=APPINFO_CLONE;thread=MAIN")
            +log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_SDK_INIT;thread=OTHER")
            +log(431,"event=UNCAUGHT;origin=VENDOR;error=ILLEGAL_STATE;thread=OTHER")
            +log(433,"event=APP_CONTEXT;origin=ORIGINAL;error=APPINFO_ORIGINAL;thread=OTHER"))
        x=scoped_metrica_witness(EXIT,events)
        self.assertEqual(x["read_only_attach_context_identity_categories"],["CLONE"])
        self.assertEqual(x["read_only_attach_appinfo_identity_categories"],["APPINFO_CLONE"])
        self.assertTrue(x["metrica_exception_precedes_uncaught"])
        self.assertTrue(x["uncaught_illegal_state_observed"])
        self.assertEqual(x["metrica_exception_message_categories"],["EXC_SDK_INIT"])
        self.assertNotIn("433",str(x))

    def test_exact_exception_object_observed_at_android_fatal_dispatch(self):
        events=(
            log(431,"event=FATAL_HOOK;origin=THREAD_DISPATCH;error=REGISTERED;thread=MAIN")
            +log(431,"event=FATAL_HOOK;origin=RUNTIME_KILL_HANDLER;error=REGISTERED;thread=MAIN")
            +log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_SDK_INIT;thread=OTHER")
            +log(431,"event=FATAL_DISPATCH;origin=RUNTIME_KILL_HANDLER;error=DIRECT_METRICA;thread=OTHER")
            +log(432,"event=FATAL_DISPATCH;origin=RUNTIME_KILL_HANDLER;error=NOT_METRICA;thread=OTHER"))
        x=scoped_metrica_witness(EXIT,events)
        self.assertEqual(x["fatal_throwable_link_verdict"],"DIRECT_IDENTITY")
        self.assertTrue(x["fatal_throwable_metrica_direct_identity_seen"])
        self.assertFalse(x["fatal_throwable_metrica_cause_identity_seen"])
        self.assertEqual(x["fatal_dispatch_paths"],["RUNTIME_KILL_HANDLER"])
        self.assertEqual(x["fatal_dispatch_event_count_bounded"],1)
        self.assertEqual(x["fatal_handler_hook_registration"],
                         ["RUNTIME_KILL_HANDLER","THREAD_DISPATCH"])
        self.assertNotIn("432",str(x))

    def test_fatal_sdk_detail_only_whitelisted_error_category(self):
        events=(
            log(431,"event=METRICA_DETAIL;origin=METRICA_SDK;error=DETAIL_NOT_INITIALIZED;thread=OTHER")
            +log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_SDK_INIT;thread=OTHER")
            +log(431,"event=FATAL_DISPATCH;origin=RUNTIME_KILL_HANDLER;error=DIRECT_METRICA;thread=OTHER")
            +log(431,"event=FATAL_DETAIL;origin=RUNTIME_KILL_HANDLER;error=DETAIL_NOT_INITIALIZED;thread=OTHER")
            +log(433,"event=FATAL_DETAIL;origin=RUNTIME_KILL_HANDLER;error=DETAIL_API_KEY;thread=OTHER"))
        x=scoped_metrica_witness(EXIT,events)
        self.assertEqual(x["fatal_throwable_link_verdict"],"DIRECT_IDENTITY")
        self.assertEqual(x["bounded_fatal_metrica_detail_categories"],["DETAIL_NOT_INITIALIZED"])
        self.assertEqual(x["bounded_metrica_constructor_detail_categories"],["DETAIL_NOT_INITIALIZED"])
        self.assertTrue(x["fatal_metrica_detail_observed"])
        self.assertNotIn("433",str(x))

    def test_activation_hook_and_callbacks_with_context_and_no_private_keys(self):
        events=(
            log(431,"event=ACTIVATION_HOOK;origin=METRICA_SDK;error=REGISTERED;thread=MAIN")
            +log(431,"event=METRICA_ACTIVATE;origin=CLONE;error=ENTER;thread=MAIN")
            +log(431,"event=METRICA_ACTIVATE;origin=CLONE;error=THROW;thread=MAIN")
            +log(432,"event=METRICA_ACTIVATE;origin=ORIGINAL;error=RETURN;thread=MAIN"))
        x=scoped_metrica_witness(EXIT,events)
        self.assertTrue(x["sdk_activate_hook_registered"])
        self.assertFalse(x["sdk_activate_hook_missing"])
        self.assertEqual(x["sdk_activate_enter_count_bounded"],1)
        self.assertEqual(x["sdk_activate_throw_count_bounded"],1)
        self.assertEqual(x["sdk_activate_return_count_bounded"],0)
        self.assertEqual(x["sdk_activate_context_categories"],["CLONE"])
        self.assertNotIn("432",str(x))

    def test_sdk_hook_missing_does_not_imply_never_initialized(self):
        events=log(431,"event=ACTIVATION_HOOK;origin=METRICA_SDK;error=NO_HOOK;thread=MAIN")
        x=scoped_metrica_witness(EXIT,events)
        self.assertTrue(x["sdk_activate_hook_missing"])
        self.assertFalse(x["sdk_activate_hook_registered"])
        self.assertEqual(x["sdk_activate_enter_count_bounded"],0)

    def test_arbitrary_sensitive_fatal_message_category_is_rejected(self):
        events=(log(431,"event=FATAL_DETAIL;origin=RUNTIME_KILL_HANDLER;error=API_KEY_SECRET;thread=OTHER")
                +log(431,"event=FATAL_DETAIL;origin=RUNTIME_KILL_HANDLER;error=DETAIL_CONFIG;thread=OTHER path=/private"))
        x=scoped_metrica_witness(EXIT,events)
        self.assertFalse(x["fatal_metrica_detail_observed"])
        self.assertEqual(x["bounded_fatal_metrica_detail_categories"],[])

    def test_exact_cause_not_constructor_time_nearby(self):
        events=(
            log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_SDK_INIT;thread=OTHER")
            +log(431,"event=FATAL_DISPATCH;origin=THREAD_GROUP;error=CAUSE_METRICA;thread=OTHER"))
        x=scoped_metrica_witness(EXIT,events)
        self.assertEqual(x["fatal_throwable_link_verdict"],"CAUSE_IDENTITY")
        self.assertTrue(x["fatal_throwable_metrica_cause_identity_seen"])

    def test_no_equality_claim_when_no_dispatch_hook_fires(self):
        events=(
            log(431,"event=FATAL_HOOK;origin=THREAD_DISPATCH;error=NO_HOOK;thread=MAIN")
            +log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_SDK_INIT;thread=OTHER"))
        x=scoped_metrica_witness(EXIT,events)
        self.assertEqual(x["fatal_throwable_link_verdict"],"FATAL_DISPATCH_NOT_OBSERVED")
        self.assertFalse(x["fatal_dispatch_observed"])
        self.assertEqual(x["fatal_handler_hook_missing"],["THREAD_DISPATCH"])

    def test_not_matched_is_inconclusive_not_exonerating(self):
        events=(
            log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_SDK_INIT;thread=OTHER")
            +log(431,"event=FATAL_DISPATCH;origin=THREAD_GROUP;error=NOT_METRICA;thread=OTHER"))
        x=scoped_metrica_witness(EXIT,events)
        self.assertEqual(x["fatal_throwable_link_verdict"],
                         "FATAL_SEEN_NO_CONSTRUCTOR_IDENTITY")
        self.assertFalse(x["fatal_throwable_metrica_direct_identity_seen"])
        self.assertFalse(x["fatal_throwable_metrica_cause_identity_seen"])

    def test_disallow_arbitrary_event_or_injected_message(self):
        bad=(log(431,"event=METRICA_EXCEPTION;origin=SECRET_VENDOR;error=EXC_OTHER;thread=OTHER")
             +log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_OTHER;thread=OTHER token=secret"))
        out=scoped_metrica_witness(EXIT,bad)
        self.assertFalse(out["read_only_metrica_exception_marker_seen"])
        self.assertEqual(out["all_witness_events_bounded"],0)

    def test_unknown_main_exit_cannot_attach_helper_events(self):
        out=scoped_metrica_witness(f"process={PKG}:Metrica pid=432 reason=4",
                log(432,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_OTHER;thread=OTHER"))
        self.assertEqual(out["metrica_exception_event_count_bounded"],0)
        self.assertFalse(out["read_only_witness_arm_marker_seen"])


if __name__=="__main__":
    unittest.main()
