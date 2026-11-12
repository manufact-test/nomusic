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
