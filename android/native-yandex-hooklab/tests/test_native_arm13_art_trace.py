"""Private synthesized ART trace tests: only safe enums, never vendor methods."""
import pathlib
import struct
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from observe_native_startup_trace import classify_art_trace


def trace(records, methods, overflow="false"):
    header = ("*version\n3\ndata-file-overflow=" + overflow
              + "\n*threads\n1\tmain\n2\tworker\n*methods\n"
              + "".join("0x%x\tL%s;\t%s\t()V\n" % (i, klass, name)
                        for i, klass, name in methods)
              + "*end\n").encode("utf-8")
    body = b"SLOW" + struct.pack("<HH", 3, 18) + b"\0" * 8
    body += struct.pack("<H", 10)
    for tid, mid in records:
        body += struct.pack("<HII", tid, mid, 1000)
    return header + body


class OwnedArmArtTraceTests(unittest.TestCase):
    def test_direct_system_exit_caller_is_only_coarse_group(self):
        # Method ids already have their lower two action bits cleared.
        raw = trace([(1, 4), (1, 8), (1, 9), (1, 5)],
                    [(4, "ru/yandex/music/SecretClass", "privateCall"),
                     (8, "java/lang/System", "exit")])
        out = classify_art_trace(raw)
        self.assertTrue(out["trace_format_verified"])
        self.assertTrue(out["trace_records_observed"])
        self.assertTrue(out["system_exit_entered_main"])
        self.assertEqual(out["system_exit_entry_count_bounded"], 1)
        self.assertEqual(out["direct_exit_caller_groups"], ["YANDEX_MUSIC"])
        self.assertTrue(out["stack_tracking_available"])
        self.assertFalse(out["raw_trace_exposed"])
        self.assertNotIn("SecretClass", str(out))
        self.assertNotIn("privateCall", str(out))

    def test_process_kill_worker_caller_group_without_main_attribution(self):
        raw = trace([(2, 4), (2, 8), (2, 9), (2, 5)],
                    [(4, "com/yandex/passport/HiddenSecret", "method"),
                     (8, "android/os/Process", "killProcess")])
        out = classify_art_trace(raw)
        self.assertTrue(out["process_kill_entered_any"])
        self.assertFalse(out["process_kill_entered_main"])
        self.assertEqual(out["process_kill_entry_count_bounded"], 1)
        self.assertEqual(out["direct_exit_caller_groups"], ["YANDEX_PASSPORT"])
        self.assertNotIn("HiddenSecret", str(out))

    def test_runtime_exit_with_unknown_caller_never_invents_yandex(self):
        raw = trace([(1, 8)], [(8, "java/lang/Runtime", "exit")])
        out = classify_art_trace(raw)
        self.assertTrue(out["runtime_exit_entered_main"])
        self.assertEqual(out["direct_exit_caller_groups"], ["OTHER_OR_UNKNOWN"])
        self.assertEqual(out["runtime_exit_entry_count_bounded"], 1)

    def test_native_arm_uses_fixed_docker_not_missing_host_adb(self):
        import os
        import types
        from unittest.mock import patch
        from observe_native_startup_trace import (
            CONTAINER, TRACE_PATH, observe_disposable_trace,
        )
        env = {
            "GITHUB_ACTIONS": "true",
            "CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID": "1",
            "CELIKOM_NATIVE_ARM13_OWN_CLONE_ART_TRACE": "1",
        }
        calls = []
        def fake_run(args, **kwargs):
            calls.append(args)
            if "stat" in args:
                return types.SimpleNamespace(returncode=1, stdout="", stderr="")
            return types.SimpleNamespace(returncode=0, stdout=b"", stderr=b"")
        with patch.dict(os.environ, env), patch(
                "observe_native_startup_trace.subprocess.run", side_effect=fake_run):
            out = observe_disposable_trace(owned_arm_container=True)
        self.assertFalse(out["trace_available"])
        self.assertFalse(out["trace_read_error"])
        self.assertEqual(out["trace_transport"], "PRIVATE_DOCKER_EXEC")
        self.assertEqual(calls[0], ["docker", "exec", CONTAINER,
                                    "stat", "-c", "%s", TRACE_PATH])
        self.assertEqual(calls[-1], ["docker", "exec", CONTAINER,
                                     "rm", "-f", TRACE_PATH])
        self.assertTrue(all(cmd[0] == "docker" for cmd in calls))

    def test_native_art_trace_transport_requires_explicit_ci_permissions(self):
        import os
        from unittest.mock import patch
        from observe_native_startup_trace import observe_disposable_trace
        with patch.dict(os.environ, {
                "GITHUB_ACTIONS": "false",
                "CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID": "1",
                "CELIKOM_NATIVE_ARM13_OWN_CLONE_ART_TRACE": "1",
        }):
            out = observe_disposable_trace(owned_arm_container=True)
        self.assertTrue(out["trace_transport_guard_rejected"])
        self.assertTrue(out["trace_read_error"])
        self.assertFalse(out["trace_available"])

    def test_missing_docker_cli_fails_closed_without_raw_output(self):
        import os
        from unittest.mock import patch
        from observe_native_startup_trace import observe_disposable_trace
        with patch.dict(os.environ, {
                "GITHUB_ACTIONS": "true",
                "CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID": "1",
                "CELIKOM_NATIVE_ARM13_OWN_CLONE_ART_TRACE": "1",
        }), patch("observe_native_startup_trace.subprocess.run",
                  side_effect=FileNotFoundError("PRIVATE_USER_SECRET")):
            out = observe_disposable_trace(owned_arm_container=True)
        self.assertTrue(out["trace_read_error"])
        self.assertFalse(out["trace_available"])
        self.assertFalse(out["raw_trace_published"])
        self.assertNotIn("PRIVATE_USER_SECRET", str(out))

    def test_early_profile_stop_never_targets_original_or_dead_process(self):
        from observe_native_startup_trace import should_stop_owned_profile_early
        clone = "pro.celikom.yandex.nativeclonelab"
        original = "ru.yandex.music"
        self.assertTrue(should_stop_owned_profile_early(clone, True, False))
        self.assertFalse(should_stop_owned_profile_early(clone, False, False))
        self.assertFalse(should_stop_owned_profile_early(clone, True, True))
        self.assertFalse(should_stop_owned_profile_early(original, True, False))
        self.assertFalse(should_stop_owned_profile_early(clone + ":AppMetrica",
                                                        True, False))

    def test_ym_application_oncreate_normal_return_and_exception_constructor(self):
        raw = trace(
            [(1, 4), (1, 8), (1, 9), (1, 5), (1, 4 | 1)],
            [(4, "ru/yandex/music/YMApplication", "onCreate"),
             (8, "java/lang/IllegalStateException", "<init>")])
        out = classify_art_trace(raw)
        self.assertTrue(out["ymapplication_oncreate_entered_main"])
        self.assertTrue(out["ymapplication_oncreate_returned_main"])
        self.assertFalse(out["ymapplication_oncreate_unwound_main"])
        self.assertTrue(out["illegalstate_constructor_entered_main"])
        self.assertEqual(out["illegalstate_constructor_entries_bounded"], 1)
        self.assertEqual(out["illegalstate_constructor_caller_groups"],
                         ["YANDEX_MUSIC"])
        self.assertFalse(out["system_exit_entered_any"])
        self.assertFalse(out["raw_trace_exposed"])

    def test_app_oncreate_throw_unwind_not_misreported_as_normal_return(self):
        raw = trace([(1, 4), (1, 8), (1, 8 | 1), (1, 4 | 2)],
                    [(4, "ru/yandex/music/YMApplication", "onCreate"),
                     (8, "java/lang/Thread",
                      "setDefaultUncaughtExceptionHandler")])
        out = classify_art_trace(raw)
        self.assertTrue(out["ymapplication_oncreate_entered_main"])
        self.assertFalse(out["ymapplication_oncreate_returned_main"])
        self.assertTrue(out["ymapplication_oncreate_unwound_main"])
        self.assertTrue(out["handler_install_entered_main"])
        self.assertTrue(out["handler_install_returned_main"])

    def test_startup_activity_methods_and_exception_caller_privacy(self):
        raw = trace(
            [(1, 4), (1, 8), (1, 8 | 1), (1, 4 | 1),
             (1, 12), (1, 16), (1, 16 | 1), (1, 12 | 1)],
            [(4, "ru/yandex/music/main/MainScreenActivity", "onCreate"),
             (8, "java/lang/IllegalStateException", "<init>"),
             (12, "ru/yandex/music/main/MainScreenActivity", "onResume"),
             (16, "java/lang/IllegalStateException", "<init>")])
        out = classify_art_trace(raw)
        self.assertTrue(out["mainscreen_oncreate_returned_main"])
        self.assertTrue(out["mainscreen_onresume_returned_main"])
        self.assertEqual(out["illegalstate_constructor_entries_bounded"], 2)
        self.assertEqual(out["illegalstate_constructor_caller_groups"],
                         ["YANDEX_MUSIC"])
        self.assertNotIn("MainScreenActivity", str(out))

    def test_owned_trace_second_alive_sample_stop_stage(self):
        from observe_native_startup_trace import choose_owned_profile_stop_stage
        pkg = "pro.celikom.yandex.nativeclonelab"
        choose = choose_owned_profile_stop_stage
        self.assertEqual(
            choose(pkg, main_alive=True, activity_resumed=True,
                   live_sample_count=1, already_stopped=False),
            "WAIT_FOR_SECOND_ALIVE")
        self.assertEqual(
            choose(pkg, main_alive=True, activity_resumed=True,
                   live_sample_count=2, already_stopped=False),
            "SECOND_ALIVE_ACTIVITY_RESUMED")
        self.assertEqual(
            choose(pkg, main_alive=True, activity_resumed=False,
                   live_sample_count=2, already_stopped=False),
            "SECOND_ALIVE_NO_RESUME")
        self.assertEqual(
            choose(pkg, main_alive=False, activity_resumed=True,
                   live_sample_count=2, already_stopped=False),
            "NOT_ELIGIBLE")
        self.assertEqual(
            choose(pkg, main_alive=True, activity_resumed=True,
                   live_sample_count=2, already_stopped=True),
            "NOT_ELIGIBLE")
        self.assertEqual(
            choose("ru.yandex.music", main_alive=True, activity_resumed=True,
                   live_sample_count=2, already_stopped=False),
            "NOT_ELIGIBLE")

    def test_exception_ctor_ancestor_categories_are_only_safe_groups(self):
        raw = trace([
            (2, 4), (2, 8), (2, 12), (2, 16),
            (2, 16 | 1), (2, 12 | 1), (2, 8 | 1), (2, 4 | 1)
        ], [
            (4, "ru/yandex/music/private/TokenProcessor", "sensitive1"),
            (8, "android/os/Handler", "dispatchMessage"),
            (12, "java/lang/SomeRuntime", "doWork"),
            (16, "java/lang/IllegalStateException", "<init>")
        ])
        out = classify_art_trace(raw)
        self.assertEqual(out["illegalstate_constructor_entries_bounded"], 1)
        self.assertEqual(out["illegalstate_constructor_caller_groups"],
                         ["ANDROID_RUNTIME"])
        self.assertEqual(out["illegalstate_constructor_ancestor_groups"],
                         ["ANDROID_RUNTIME", "YANDEX_MUSIC"])
        self.assertTrue(out["constructor_trace_may_start_mid_call"])
        for secret in ("TokenProcessor", "sensitive1", "private"):
            self.assertNotIn(secret, str(out))

    def test_profiler_launch_error_categories_do_not_expose_raw(self):
        from observe_native_startup_trace import classify_profiler_launch
        samples = [
            ("Starting: Intent { account_token=HIDE_ME }",
             "ACTIVITY_START_COMMAND_ACCEPTED"),
            ("Unknown option: --start-profiler account_token=HIDE_ME",
             "PROFILER_OPTION_UNSUPPORTED"),
            ("SecurityException permission denied account_token=HIDE_ME",
             "PROFILER_PERMISSION_REJECTED"),
            ("Not profileable package HIDE_ME",
             "PROFILER_ACCESS_REJECTED"),
            ("This is arbitrary secret HIDE_ME", "ACTIVITY_START_UNCLASSIFIED"),
        ]
        for raw, expected in samples:
            with self.subTest(expected=expected):
                verdict = classify_profiler_launch(raw)
                self.assertEqual(verdict, expected)
                self.assertNotIn("HIDE_ME", verdict)

    def test_art_header_explicitly_flags_buffer_overflow(self):
        from observe_native_startup_trace import likely_default_art_trace_capacity_reached
        self.assertTrue(likely_default_art_trace_capacity_reached(
            599184, 14, 32))  # 599184 * 14 + 32 == exactly 8 MiB
        self.assertFalse(likely_default_art_trace_capacity_reached(
            100, 14, 32))
        self.assertFalse(likely_default_art_trace_capacity_reached(
            -1, 14, 32))
        self.assertFalse(likely_default_art_trace_capacity_reached(
            599184, 200, 32))
        data = trace([(1, 4), (1, 4 | 1)],
                     [(4, "ru/yandex/music/YMApplication", "onCreate")],
                     overflow="true")
        out = classify_art_trace(data)
        self.assertTrue(out["trace_format_verified"])
        self.assertTrue(out["ymapplication_oncreate_entered_main"])
        self.assertEqual(out["trace_overflow_header_status"], "CONFIRMED_OVERFLOW")
        self.assertTrue(out["negative_method_observations_unreliable"])
        self.assertFalse(out["default_8mib_capacity_likely_reached"])
        self.assertFalse(out["raw_trace_exposed"])

    def test_unfilled_trace_false_header_and_missing_metadata(self):
        data = trace([(1, 4), (1, 4 | 1)],
                     [(4, "java/lang/Thread",
                       "setDefaultUncaughtExceptionHandler")])
        out = classify_art_trace(data)
        self.assertEqual(out["trace_overflow_header_status"],
                         "NO_OVERFLOW_REPORTED")
        self.assertFalse(out["default_8mib_capacity_likely_reached"])
        self.assertFalse(out["negative_method_observations_unreliable"])
        unknown = classify_art_trace(data.replace(
            b"data-file-overflow=false", b"data-file-overflow=unknown"))
        self.assertEqual(unknown["trace_overflow_header_status"], "NOT_DECLARED")
        self.assertTrue(unknown["negative_method_observations_unreliable"])

    def test_sampled_stack_does_not_claim_exact_java_invocation(self):
        from observe_native_startup_trace import classify_sampled_art_trace
        raw = trace([(1, 4), (1, 8), (1, 8 | 1), (1, 4 | 1)],
                    [(4, "ru/yandex/music/YMApplication", "onCreate"),
                     (8, "java/lang/IllegalStateException", "<init>")])
        out = classify_sampled_art_trace(raw)
        self.assertTrue(out["trace_format_verified"])
        self.assertTrue(out["sampled_stacks_not_exact_method_calls"])
        self.assertEqual(out["sampling_interval_us"], 10000)
        self.assertIn("ymapplication_oncreate",
                      out["sampled_watch_names_main_thread"])
        self.assertIn("illegalstate_constructor",
                      out["sampled_watch_names_any_thread"])
        self.assertNotIn("illegalstate_constructor_caller_groups", out)
        self.assertNotIn("system_exit_entry_count_bounded", out)
        self.assertNotIn("returned_main", str(out))
        self.assertFalse(out["raw_trace_exposed"])

    def test_sampled_trace_transport_rejects_non_owned_non_ci_mode(self):
        import os
        from unittest.mock import patch
        from observe_native_startup_trace import observe_disposable_trace
        with patch.dict(os.environ, {
            "GITHUB_ACTIONS": "true",
            "CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID": "1",
            "CELIKOM_NATIVE_ARM13_OWN_CLONE_ART_TRACE": "1",
            "CELIKOM_OWN_ART_SAMPLING_10000US": "0",
        }), patch("observe_native_startup_trace.subprocess.run",
                  side_effect=AssertionError("SHOULD_NOT_RUN_DOCKER")):
            out = observe_disposable_trace(owned_arm_container=True,
                                            sampling_mode=True)
        self.assertTrue(out["trace_transport_guard_rejected"])
        self.assertFalse(out["raw_trace_published"])
        self.assertFalse(out["trace_available"])

    def test_corrupt_or_too_small_is_inconclusive(self):
        for raw in (b"", b"PRIVATE", b"*version\n3\n*methods\n", b"\0" * 20):
            with self.subTest(value=raw[:12]):
                out = classify_art_trace(raw)
                self.assertFalse(out["trace_format_verified"])
                self.assertFalse(out["trace_records_observed"])
                self.assertFalse(out["system_exit_entered_any"])
                self.assertEqual(out["direct_exit_caller_groups"], [])

    def test_exception_cannot_escape_as_raw_symbol(self):
        raw = trace([(1, 4), (1, 8), (1, 9), (1, 5)],
                    [(4, "com/private/ACCESS_TOKEN_DO_NOT_LEAK", "privateThing"),
                     (8, "java/lang/System", "exit")])
        out = classify_art_trace(raw)
        self.assertEqual(out["direct_exit_caller_groups"], ["OTHER_OR_UNKNOWN"])
        for secret in ("ACCESS_TOKEN", "privateThing", "com/private"):
            self.assertNotIn(secret, str(out))


if __name__ == "__main__":
    unittest.main()
