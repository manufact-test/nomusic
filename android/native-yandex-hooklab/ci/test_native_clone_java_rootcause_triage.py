"""Isolated synthetic MAIN-PID crash privacy and finite Java cause tests."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from clone_main_crash_buffer import classify_main_crash_buffer

CLONE="pro.celikom.yandex.nativeclonelab"
EXIT=f"ApplicationExitInfo #0: pid=431 process={CLONE} reason=4 status=0"


def log(pid, message):
    return f"11-12 12:00:01.123 {pid} {pid} E AndroidRuntime: {message}\n"


class JavaStartupTriageTest(unittest.TestCase):
    def test_bounded_kotlin_crash_message_and_thread_are_not_user_data(self):
        raw=(log(431,"FATAL EXCEPTION: DefaultDispatcher-worker-2")
             +log(431,"java.lang.IllegalStateException: Check failed. access_token=TOPSECRET")
             +log(431,"    at ru.yandex.music.private.Impl.run(Private.java:12)")
             +log(432,"FATAL EXCEPTION: main")
             +log(432,"java.lang.SecurityException: access_token=OTHER_SECRET"))
        x=classify_main_crash_buffer(EXIT,raw)
        self.assertEqual(x["java_fatal_background_role"],"KOTLIN_COROUTINE")
        self.assertEqual(x["java_top_frame_subsystem"],"YANDEX_MUSIC")
        self.assertEqual(x["java_startup_message_shape"],"PRESENT")
        self.assertEqual(x["java_startup_message_finite_hint"],"CHECK_FAILED")
        for private in ("TOPSECRET","OTHER_SECRET","private.Impl","DefaultDispatcher","431","432"):
            self.assertNotIn(private,str(x))
        self.assertFalse(x["java_vendor_class_names_exposed"])

    def test_no_exception_message_is_explicit_not_misread_as_none(self):
        raw=(log(431,"FATAL EXCEPTION: RxCachedThreadScheduler-1")
             +log(431,"java.lang.IllegalStateException")
             +log(431,"    at com.yandex.passport.private.SECRET.run(Secret.java:99)"))
        x=classify_main_crash_buffer(EXIT,raw)
        self.assertEqual(x["java_fatal_background_role"],"RX_BACKGROUND")
        self.assertEqual(x["java_top_frame_subsystem"],"YANDEX_PASSPORT")
        self.assertEqual(x["java_startup_message_shape"],"NO_MESSAGE")
        self.assertEqual(x["java_startup_message_finite_hint"],"NO_MESSAGE")
        self.assertNotIn("SECRET",str(x))

    def test_helper_process_cannot_create_main_crash_fingerprint(self):
        raw=log(432,"FATAL EXCEPTION: NetworkWorker") + log(
            432,"java.lang.IllegalStateException: required value was null")
        x=classify_main_crash_buffer(EXIT,raw)
        self.assertEqual(x["java_startup_message_shape"],"NOT_OBSERVED")
        self.assertEqual(x["java_fatal_background_role"],"NOT_OBSERVED")
        self.assertEqual(x["java_top_frame_subsystem"],"NOT_OBSERVED")
        self.assertEqual(x["java_startup_message_finite_hint"],"NOT_OBSERVED")

    def test_unrecognized_private_message_never_leaks_text_or_tokens(self):
        raw=(log(431,"FATAL EXCEPTION: work-account-SECRET")
             +log(431,"java.lang.IllegalStateException: request_id=SENSITIVE token=VERYPRIVATE")
             +log(431,"    at com.other.closed.SECRET.run(Private.java:12)"))
        x=classify_main_crash_buffer(EXIT,raw)
        self.assertEqual(x["java_startup_message_finite_hint"],"OTHER_NONEMPTY")
        self.assertEqual(x["java_fatal_background_role"],"OTHER_BACKGROUND")
        self.assertEqual(x["java_top_frame_subsystem"],"OTHER_FRAME")
        for secret in ("SENSITIVE","VERYPRIVATE","work-account","SECRET","com.other.closed"):
            self.assertNotIn(secret,str(x))


if __name__=="__main__":
    unittest.main()
