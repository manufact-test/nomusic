"""Private synthesized ART trace tests: only safe enums, never vendor methods."""
import pathlib
import struct
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from observe_native_startup_trace import classify_art_trace


def trace(records, methods):
    header = ("*version\n3\n*threads\n1\tmain\n2\tworker\n*methods\n"
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
