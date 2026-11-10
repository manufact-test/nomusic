import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from observe_native_startup_trace import classify_art_trace


def synthetic_trace(version=3, actual=True):
    header = (
        "*version\n3\nclock=dual\n*threads\n12\tmain\n19\tAppMetrica\n"
        "*methods\n0x00000100\tru/yandex/music/YMApplication\tonCreate\t()V\n"
        "0x00000200\tck7\tuncaughtException\t(Ljava/lang/Thread;Ljava/lang/Throwable;)V\n"
        "0x00000300\tjava/lang/System\texit\t(I)V\n"
        "0x00000400\tandroid/os/Process\tkillProcess\t(I)V\n"
        "0x00000500\tjava/lang/Thread\tsetDefaultUncaughtExceptionHandler\t(Ljava/lang/Thread$UncaughtExceptionHandler;)V\n"
        "*end\n"
    ).encode()
    rec_size = {1: 9, 2: 10, 3: 14}[version]
    binary = b"SLOW" + struct.pack("<HHQ", version, 32, 0) + struct.pack("<H", rec_size) + bytes(14)
    def record(tid, mid, action=0):
        if version == 1:
            return struct.pack("<BII", tid, mid + action, 999)
        if version == 2:
            return struct.pack("<HII", tid, mid + action, 999)
        return struct.pack("<HIII", tid, mid + action, 999, 999)
    binary += record(12, 0x100) + record(12, 0x500)
    binary += record(19, 0x200) + record(19, 0x300)
    if actual:
        binary += record(12, 0x200) + record(12, 0x300)
    return header + binary


class TraceDecoderSafetyTests(unittest.TestCase):
    def test_v3_main_and_helper_are_separate(self):
        x = classify_art_trace(synthetic_trace())
        self.assertTrue(x["trace_format_verified"])
        self.assertTrue(x["trace_main_thread_mapped"])
        self.assertTrue(x["ymapplication_oncreate_entered_main"])
        self.assertTrue(x["uncaught_handler_entered_main"])
        self.assertTrue(x["system_exit_entered_main"])
        self.assertFalse(x["process_kill_entered_main"])
        self.assertTrue(x["handler_install_entered_main"])

    def test_helper_only_never_counts_as_main(self):
        x = classify_art_trace(synthetic_trace(actual=False))
        self.assertTrue(x["system_exit_entered_any"])
        self.assertFalse(x["system_exit_entered_main"])
        self.assertFalse(x["uncaught_handler_entered_main"])

    def test_older_trace_versions(self):
        for v in (1, 2):
            with self.subTest(v=v):
                x = classify_art_trace(synthetic_trace(version=v))
                self.assertTrue(x["trace_format_verified"])
                self.assertTrue(x["system_exit_entered_main"])

    def test_no_sensitive_strings_or_unsupported_format(self):
        for blob in (b"SECRET_ACCESS_TOKEN", b"*version\n3\nsecret=never", b"",
                     synthetic_trace()[:45]):
            with self.subTest(size=len(blob)):
                x = classify_art_trace(blob)
                self.assertFalse(x["trace_format_verified"])
                self.assertFalse(x["raw_trace_exposed"])
                self.assertNotIn("SECRET", str(x))


if __name__ == "__main__":
    unittest.main()
