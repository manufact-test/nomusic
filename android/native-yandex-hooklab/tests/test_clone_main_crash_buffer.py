"""Synthetic only, ensures Android CRASH buffer analysis never leaks secrets."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clone_main_crash_buffer import classify_main_crash_buffer, main_exit_pids

CLONE = "pro.celikom.yandex.nativeclonelab"
EXIT = (f"ApplicationExitInfo #0:\n pid=431 process={CLONE} reason=4 status=0\n"
        f"ApplicationExitInfo #1:\n pid=432 process={CLONE}:AppMetrica reason=4\n")
SECRET = "access_token=TOPSECRET https://private.invalid/internal"


def row(pid, level, tag, message):
    return f"11-11 09:12:33.234 {pid} {pid} {level} {tag}: {message}\n"


class SafeMainCrashBufferTest(unittest.TestCase):
    def test_main_only_native_lspatch_loader_category(self):
        raw = (row(431,"E","AndroidRuntime","FATAL EXCEPTION: main")
               +row(431,"E","AndroidRuntime",
                    "java.lang.UnsatisfiedLinkError: dlopen failed: library "
                    "'liblspatch.so' not found " + SECRET)
               +row(432,"E","AndroidRuntime",
                    "java.lang.SecurityException: " + SECRET)
               +row(999,"E","AndroidRuntime",
                    "java.lang.VerifyError: original unrelated"))
        result = classify_main_crash_buffer(EXIT,raw)
        self.assertEqual(result["fatal_category"],"NATIVE_LINK")
        self.assertTrue(result["android_runtime_fatal_main_seen"])
        self.assertTrue(result["native_link_library_lspatch_named"])
        self.assertTrue(result["native_link_missing_library_marker"])
        self.assertFalse(result["native_link_wrong_elf_class"])
        for secret in (SECRET,"TOPSECRET","private.invalid","431","432","999","liblspatch.so"):
            self.assertNotIn(secret,str(result))
        self.assertFalse(result["raw_crash_buffer_exposed"])

    def test_explicit_main_scope_unknown_pid_fails_closed(self):
        raw = row(431,"E","AndroidRuntime","FATAL EXCEPTION: main java.lang.UnsatisfiedLinkError")
        result = classify_main_crash_buffer(
            "ApplicationExitInfo #0: pid=431 process=ru.yandex.music reason=4",
            raw)
        self.assertFalse(result["crash_main_pid_evidence_available"])
        self.assertFalse(result["crash_buffer_main_pid_lines_seen"])
        self.assertEqual(result["fatal_category"],"NOT_OBSERVED")

    def test_loader_class_and_abi_markers_are_bounded(self):
        raw = row(431,"E","AndroidRuntime",
                  "java.lang.UnsatisfiedLinkError: wrong ELF class: ELFCLASS32; "
                  "org.lsposed.lspatch.metaloader.LSPAppComponentFactoryStub " + SECRET)
        result = classify_main_crash_buffer(EXIT,raw)
        self.assertTrue(result["native_link_wrong_elf_class"])
        self.assertTrue(result["lspatch_bootstrap_mentioned"])
        self.assertFalse(result["native_link_library_lspatch_named"])
        self.assertNotIn("ELFCLASS32",str(result))

    def test_factory_failure_classification(self):
        raw = (row(431,"E","AndroidRuntime","FATAL EXCEPTION: main")
               +row(431,"E","AndroidRuntime",
                    "java.lang.RuntimeException: Unable to instantiate appComponentFactory")
               +row(431,"E","AndroidRuntime",
                    "Caused by: java.lang.ClassNotFoundException: " + SECRET))
        result=classify_main_crash_buffer(EXIT,raw)
        self.assertTrue(result["application_component_factory_failure"])
        self.assertEqual(result["fatal_category"],"CLASS_RESOLUTION")
        self.assertNotIn("ClassNotFoundException",str(result))

    def test_no_scoped_log_is_not_a_pass(self):
        result=classify_main_crash_buffer(EXIT,
                row(432,"E","AndroidRuntime","FATAL EXCEPTION: main " + SECRET))
        self.assertTrue(result["crash_main_pid_evidence_available"])
        self.assertFalse(result["crash_buffer_main_pid_lines_seen"])
        self.assertEqual(result["fatal_category"],"NOT_OBSERVED")

    def test_exit_info_formats_and_pid_are_private(self):
        self.assertEqual(main_exit_pids(EXIT),{431})
        self.assertEqual(main_exit_pids(
            f"#0: ApplicationExitInfo: process={CLONE} pid=55 reason=4"),{55})
        report=classify_main_crash_buffer(EXIT, "")
        self.assertFalse(report["process_identifiers_exposed"])
        self.assertFalse(report["exception_free_text_exposed"])


if __name__=="__main__":
    unittest.main()
