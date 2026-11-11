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

    def test_offline_original_package_scope_is_exact_and_never_crosses_apps(self):
        from clone_main_crash_buffer import classify_main_exit_status
        original="ru.yandex.music"
        dump=(f"ApplicationExitInfo #0: pid=712 process={original} reason=4 status=0\n"
              f"ApplicationExitInfo #1: pid=431 process={CLONE} reason=1 status=0\n")
        crash=(row(712,"E","AndroidRuntime","FATAL EXCEPTION: main")
               +row(712,"E","AndroidRuntime","java.lang.IllegalStateException: " + SECRET)
               +row(431,"E","AndroidRuntime","java.lang.SecurityException: " + SECRET))
        x=classify_main_crash_buffer(dump, crash, target_package=original)
        self.assertEqual(x["fatal_category"],"APPLICATION_STATE")
        self.assertTrue(x["android_runtime_fatal_main_seen"])
        self.assertEqual(main_exit_pids(dump,target_package=original),{712})
        self.assertEqual(classify_main_exit_status(dump,target_package=original)["latest_main_exit_reason"],"JAVA_CRASH")
        self.assertNotIn("712",str(x))
        self.assertNotIn("TOPSECRET",str(x))

    def test_fixed_java_exception_subtypes_are_only_static_enums(self):
        raw=(row(431,"E","AndroidRuntime",
                "java.lang.IllegalStateException: private=TOPSECRET")
             +row(431,"E","AndroidRuntime",
                "Caused by: java.lang.NullPointerException: " + SECRET)
             +row(432,"E","AndroidRuntime",
                "Caused by: java.lang.SecurityException: helper only " + SECRET))
        summary=classify_main_crash_buffer(EXIT,raw)
        self.assertEqual(summary["fixed_java_exception_subtypes"],
                         ["ILLEGAL_STATE","NULL_POINTER"])
        self.assertNotIn("TOPSECRET",str(summary))
        self.assertNotIn("private.invalid",str(summary))
        self.assertNotIn("SecurityException",str(summary))

    def test_java_main_top_and_caused_by_stack_origin_families_are_privacy_safe(self):
        original="ru.yandex.music"
        exit_info=f"ApplicationExitInfo #0: pid=712 process={original} reason=4 status=0\n"
        crash=(
            row(712,"E","AndroidRuntime","FATAL EXCEPTION: main")
            +row(712,"E","AndroidRuntime","Process: ru.yandex.music, PID: 712")
            +row(712,"E","AndroidRuntime","java.lang.RuntimeException: " + SECRET)
            +row(712,"E","AndroidRuntime","    at android.app.ActivityThread.handleBindApplication(SECRET.java:12)")
            +row(712,"E","AndroidRuntime","Caused by: java.lang.IllegalStateException: " + SECRET)
            +row(712,"E","AndroidRuntime","    at ru.yandex.music.private.SECRET.invoke(SECRET.java:17)")
            +row(712,"E","AndroidRuntime","    at com.google.android.gms.internal.SECRET.run(SECRET.java:19)")
            +row(731,"E","AndroidRuntime","FATAL EXCEPTION: main")
            +row(731,"E","AndroidRuntime","Caused by: java.lang.SecurityException: helper " + SECRET)
            +row(731,"E","AndroidRuntime","    at java.lang.Thread.run(Thread.java:123)")
        )
        result=classify_main_crash_buffer(exit_info,crash,target_package=original)
        self.assertTrue(result["java_fatal_seen_scoped"])
        self.assertEqual(result["java_top_exception_enum"],"RUNTIME_EXCEPTION")
        self.assertEqual(result["java_last_cause_exception_enum"],"ILLEGAL_STATE")
        self.assertEqual(result["java_top_stack_family"],"ANDROID_FRAMEWORK")
        self.assertEqual(result["java_last_cause_stack_family"],"YANDEX_APP")
        self.assertEqual(result["java_caused_by_count_bounded"],1)
        self.assertEqual(result["java_stack_frame_count_bounded"],3)
        self.assertFalse(result["java_stack_raw_exposed"])
        self.assertFalse(result["java_vendor_class_names_exposed"])
        for secret in ("SECRET","712","731","ru.yandex.music.private","access_token","private.invalid"):
            self.assertNotIn(secret,str(result))

    def test_java_main_without_causes_treats_first_exception_as_root(self):
        crash=(row(431,"E","AndroidRuntime","FATAL EXCEPTION: main")
               +row(431,"E","AndroidRuntime","java.lang.IllegalStateException: " + SECRET)
               +row(431,"E","AndroidRuntime","   at com.google.firebase.SECRET.run(Secret.java:101)"))
        summary=classify_main_crash_buffer(EXIT,crash)
        self.assertEqual(summary["java_top_exception_enum"],"ILLEGAL_STATE")
        self.assertEqual(summary["java_last_cause_exception_enum"],"ILLEGAL_STATE")
        self.assertEqual(summary["java_top_stack_family"],"GOOGLE_SDK")
        self.assertEqual(summary["java_last_cause_stack_family"],"GOOGLE_SDK")
        self.assertEqual(summary["java_caused_by_count_bounded"],0)
        self.assertNotIn("firebase",str(summary).lower())

    def test_java_scope_failure_does_not_claim_stack_or_cause(self):
        crash=(row(431,"E","AndroidRuntime","java.lang.IllegalStateException: " + SECRET)
               +row(432,"E","AndroidRuntime","FATAL EXCEPTION: main")
               +row(432,"E","AndroidRuntime","at ru.yandex.secret.CLASS.run(Secret.java:1)"))
        summary=classify_main_crash_buffer(EXIT,crash)
        self.assertFalse(summary["java_fatal_seen_scoped"])
        self.assertEqual(summary["java_top_stack_family"],"NOT_OBSERVED")
        self.assertEqual(summary["java_top_exception_enum"],"NOT_OBSERVED")
        self.assertEqual(summary["java_last_cause_exception_enum"],"NOT_OBSERVED")
        self.assertEqual(summary["java_stack_frame_count_bounded"],0)

    def test_java_lifecycle_first_exc_message_hint_only_is_static_enum(self):
        raw=(row(431,"E","AndroidRuntime","FATAL EXCEPTION: main")
            +row(431,"E","AndroidRuntime",
                 "java.lang.IllegalStateException: A certificate is untrusted " + SECRET)
            +row(431,"E","AndroidRuntime",
                 "    at ru.yandex.music.SECRET.x(Private.java:42)")
            +row(431,"E","AndroidRuntime",
                 "    at android.app.Instrumentation.callApplicationOnCreate(Instrumentation.java:123)")
            +row(432,"E","AndroidRuntime",
                 "java.lang.IllegalStateException: service missing; token=TOPSECRET"))
        result=classify_main_crash_buffer(EXIT,raw)
        self.assertEqual(result["java_exception_message_hint_enum"],"TRUST_OR_PACKAGE")
        self.assertEqual(result["java_startup_lifecycle_enum"],"APPLICATION_ON_CREATE")
        self.assertNotIn("certificate",str(result).lower())
        self.assertNotIn("TOPSECRET",str(result))
        self.assertNotIn("PRIVATE",str(result))

    def test_java_lifecycle_detects_activity_launch_without_vendor_code(self):
        raw=(row(431,"E","AndroidRuntime","FATAL EXCEPTION: main")
             +row(431,"E","AndroidRuntime",
                  "java.lang.IllegalStateException: not initialized " + SECRET)
             +row(431,"E","AndroidRuntime",
                  "at android.app.ActivityThread.performLaunchActivity(ActivityThread.java:1234)")
             +row(431,"E","AndroidRuntime",
                  "at android.os.Looper.loop(Looper.java:235)"))
        summary=classify_main_crash_buffer(EXIT,raw)
        self.assertEqual(summary["java_startup_lifecycle_enum"],"ACTIVITY_CREATE")
        self.assertEqual(summary["java_exception_message_hint_enum"],"STARTUP_ORDER")
        self.assertNotIn("SECRET",str(summary))

    def test_java_hint_does_not_trust_helper_crash_or_stack_fragments(self):
        raw=(row(431,"E","AndroidRuntime","FATAL EXCEPTION: main")
             +row(431,"E","AndroidRuntime",
                  "java.lang.IllegalStateException: " + SECRET)
             +row(431,"E","AndroidRuntime",
                  "at ru.yandex.music.SECRET.certificateAndPackage(Secret.java:3)")
             +row(432,"E","AndroidRuntime",
                  "java.lang.IllegalStateException: certificate invalid"))
        summary=classify_main_crash_buffer(EXIT,raw)
        self.assertEqual(summary["java_exception_message_hint_enum"],"NONE")
        self.assertEqual(summary["java_startup_lifecycle_enum"],"NOT_OBSERVED")
        self.assertNotIn("certificate",str(summary).lower())

    def test_offline_crash_classifier_rejects_untrusted_package_identity(self):
        with self.assertRaises(ValueError):
            classify_main_crash_buffer(EXIT, "", target_package="arbitrary.package")
        with self.assertRaises(ValueError):
            main_exit_pids(EXIT,target_package="ru.yandex.music:any_helper")

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


    def test_linker_cause_matrix_with_secret_redaction(self):
        samples = (
            ("dlopen failed: library 'liblspatch.so' needed by '/secret/token/libfoo.so' not found", "DEP_MISSING"),
            ("dlopen failed: library 'libprivate.so' is not accessible for the namespace 'classloader-namespace'", "NAMESPACE_DENIED"),
            ("dlopen failed: cannot locate symbol 'privateToken' referenced by '/secret/liblspatch.so'", "SYMBOL_UNRESOLVED"),
            ("dlopen failed: bad ELF magic in /private/liblspatch.so", "ELF_INVALID"),
            ("dlopen failed: wrong ELF class: ELFCLASS64 /private/liblspatch.so", "ELF_ARCH_INVALID"),
            ("dlopen failed: zip entry not uncompressed /private/app.apk!/assets/lspatch/so/x86/liblspatch.so", "ZIP_ENTRY_INVALID"),
            ("dlopen failed: couldn't map /data/app/private.apk!/assets/lspatch/so/x86/liblspatch.so", "PAGE_OR_MMAP"),
            ("dlopen failed: permission denied /secret/path/liblspatch.so", "LIBRARY_SECURITY_DENIED"),
            ("dlopen failed: unknown private failure access_token=VERYSECRET", "UNKNOWN_DLOPEN"),
        )
        for line, expected in samples:
            with self.subTest(expected=expected):
                result = classify_main_crash_buffer(EXIT, row(431, "E", "AndroidRuntime", line))
                self.assertEqual(result["native_link_failure_mode"], expected)
                self.assertNotIn("VERYSECRET", str(result))
                self.assertNotIn("/private", str(result))
                self.assertNotIn("token", str(result).lower())

    def test_zip_loader_path_family_and_scoped_pid(self):
        raw = (row(431, "E", "AndroidRuntime",
                   "java.lang.UnsatisfiedLinkError: dlopen failed: "
                   "/data/app/PRIVATE/base.apk!/assets/lspatch/so/armeabi-v7a/liblspatch.so")
               + row(432, "E", "AndroidRuntime",
                     "dlopen failed: bad ELF magic /secret/libother.so"))
        out = classify_main_crash_buffer(EXIT, raw)
        self.assertEqual(out["native_link_path_family"], "ZIP_ASSET_LOADER")
        self.assertEqual(out["native_link_failure_mode"], "UNKNOWN_DLOPEN")
        self.assertTrue(out["native_link_error_line_observed"])
        self.assertNotIn("PRIVATE", str(out))

    def test_dlopen_terms_statically_whitelisted(self):
        raw = (row(431, "E", "AndroidRuntime",
                   "dlopen failed: could not open shared library from zip: "
                   "/data/USER_PRIVATE/path/secret_file.apk "
                   "unexpected error access_token=VERYSECRET")
               + row(432, "E", "AndroidRuntime",
                     "dlopen failed: permission denied HELPER_SECRET"))
        report = classify_main_crash_buffer(EXIT, raw)
        self.assertIn("could", report["native_link_allowlisted_terms"])
        self.assertIn("not", report["native_link_allowlisted_terms"])
        self.assertIn("open", report["native_link_allowlisted_terms"])
        self.assertIn("library", report["native_link_allowlisted_terms"])
        self.assertNotIn("token", str(report).lower())
        self.assertNotIn("verysecret", str(report).lower())
        self.assertNotIn("user_private", str(report).lower())
        self.assertNotIn("permission", report["native_link_allowlisted_terms"])

    def test_bionic_elf_machine_mismatch_is_extracted_as_fixed_pair(self):
        msg = ('java.lang.UnsatisfiedLinkError: dlopen failed: '
               '"/data/app/SECRET_PATH/base.apk!/assets/lspatch/so/x86/liblspatch.so" '
               'is for EM_386 (3) instead of EM_ARM (40) '
               'access_token=VERY_SECRET')
        result = classify_main_crash_buffer(EXIT, row(431, "E", "AndroidRuntime", msg))
        self.assertEqual(result["native_link_failure_mode"], "ELF_ARCH_INVALID")
        self.assertEqual(result["native_link_machine_mismatch"],
                         {"seen": True, "actual": "EM_386", "expected": "EM_ARM"})
        self.assertNotIn("SECRET", str(result))
        self.assertNotIn("access_token", str(result))
        self.assertFalse(result["raw_crash_buffer_exposed"])

    def test_unknown_machine_pair_never_leaks_dynamic_values(self):
        msg = 'dlopen failed: private.so is for EM_PRIVATE (123) instead of EM_ARM (40)'
        result = classify_main_crash_buffer(EXIT, row(431, "E", "AndroidRuntime", msg))
        self.assertFalse(result["native_link_machine_mismatch"]["seen"])
        self.assertNotIn("EM_PRIVATE", str(result))

    def test_native_tombstone_debuggerd_reporter_is_scoped_to_main(self):
        raw = (row(431, "F", "libc", "Fatal signal 11 (SIGSEGV), private=HIDE_THIS")
               + row(930, "F", "DEBUG",
                     f"pid: 431, tid: 431, name: PRIVATE >>> {CLONE} <<<")
               + row(930, "F", "DEBUG",
                     "#00 pc 0000001c /data/app/SECRET/liblspatch.so (token=SECRET)")
               + row(930, "F", "DEBUG",
                     "#01 pc 00000050 /system/lib/libndk_translation.so")
               + row(931, "F", "DEBUG",
                     "pid: 432, tid: 432, name: helper >>> " + CLONE + ":AppMetrica <<<")
               + row(931, "F", "DEBUG",
                     "#00 pc 00000099 /secret/libart.so token=PRIVATE")
               + row(934, "F", "DEBUG",
                     "pid: 543, tid: 543, name: other >>> ru.yandex.music <<<")
               + row(934, "F", "DEBUG",
                     "#00 pc 00000097 /secret/libc.so token=PRIVATE"))
        out = classify_main_crash_buffer(EXIT, raw)
        self.assertEqual(out["fatal_category"], "NATIVE_SIGNAL")
        self.assertEqual(out["native_main_signal"], "SIGSEGV")
        self.assertTrue(out["main_tombstone_header_matched"])
        self.assertEqual(out["native_backtrace_first_frame_group"], "LSPATCH")
        self.assertEqual(out["native_backtrace_frame_groups"],
                         ["LSPATCH", "NATIVE_BRIDGE"])
        self.assertEqual(out["native_backtrace_frame_count_bounded"], 2)
        for secret in ("HIDE_THIS", "SECRET", "PRIVATE", "liblspatch.so", "930", "431"):
            self.assertNotIn(secret, str(out))
        self.assertFalse(out["raw_native_crash_exposed"])

    def test_helper_tombstone_cannot_count_as_main_native_crash(self):
        raw = (row(432, "F", "libc", "Fatal signal 11 (SIGSEGV)")
               + row(930, "F", "DEBUG",
                     f"pid: 432, tid: 432, name: helper >>> {CLONE}:AppMetrica <<<")
               + row(930, "F", "DEBUG",
                     "#00 pc deadbeef /data/app/liblspatch.so"))
        out=classify_main_crash_buffer(EXIT,raw)
        self.assertEqual(out["fatal_category"],"NOT_OBSERVED")
        self.assertFalse(out["main_tombstone_header_matched"])
        self.assertEqual(out["native_main_signal"],"NOT_OBSERVED")
        self.assertEqual(out["native_backtrace_frame_groups"], [])

    def test_unknown_pid_crash_does_not_publish_details(self):
        raw = (row(431,"F","libc","Fatal signal 11 (SIGSEGV)")
               +row(930,"F","DEBUG",f"pid: 431, tid: 431, name: MAIN >>> {CLONE} <<<")
               +row(930,"F","DEBUG","#00 pc PRIVATE /data/app/liblspatch.so"))
        out=classify_main_crash_buffer(
            f"ApplicationExitInfo #0: process={CLONE} reason=5",
            raw)
        self.assertEqual(out["native_main_signal"],"NOT_OBSERVED")
        self.assertFalse(out["main_tombstone_header_matched"])
        self.assertNotIn("PRIVATE",str(out))



class MainExitStatusPrivacyTests(unittest.TestCase):
    def test_exact_main_exit_self_zero_even_with_helpers(self):
        from clone_main_crash_buffer import classify_main_exit_status
        dump = (
            f"ApplicationExitInfo #0:\n pid=123 process={CLONE}:AppMetrica reason=5 status=11\n"
            f"ApplicationExitInfo #1:\n pid=124 process={CLONE} reason=1 status=0 private={SECRET}\n"
            "ApplicationExitInfo #2:\n pid=125 process=ru.yandex.music reason=4 status=66\n"
        )
        x = classify_main_exit_status(dump)
        self.assertEqual(x["latest_main_exit_reason"], "EXIT_SELF")
        self.assertEqual(x["latest_main_exit_status"], "ZERO")
        self.assertEqual(x["main_exit_record_count_bounded"], 1)
        self.assertNotIn("123", str(x))
        self.assertNotIn(SECRET, str(x))
        self.assertFalse(x["raw_exit_info_exposed"])

    def test_absent_main_fails_closed(self):
        from clone_main_crash_buffer import classify_main_exit_status
        x = classify_main_exit_status(
            f"ApplicationExitInfo #0: pid=123 process={CLONE}:helper reason=1 status=0")
        self.assertFalse(x["exact_main_exit_record_seen"])
        self.assertEqual(x["latest_main_exit_reason"], "NOT_OBSERVED")

    def test_native_crash_exit_vs_java(self):
        from clone_main_crash_buffer import classify_main_exit_status
        for code, expected in [(4,"JAVA_CRASH"),(5,"NATIVE_CRASH"),
                               (7,"INITIALIZATION_FAILURE"),(99,"UNKNOWN")]:
            with self.subTest(code=code):
                x = classify_main_exit_status(
                    f"ApplicationExitInfo #0: process={CLONE} reason={code} status=11")
                self.assertEqual(x["latest_main_exit_reason"], expected)
                self.assertEqual(x["latest_main_exit_status"], "NONZERO")

if __name__=="__main__":
    unittest.main()
