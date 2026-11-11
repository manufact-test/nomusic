"""Synthetic classifiers only; NO real Android runtime conclusion."""
import importlib.util
from pathlib import Path
import unittest

SRC = Path(__file__).resolve().parents[1] / "ci" / "chromasync_exact_arm13_probe.py"
spec = importlib.util.spec_from_file_location("probe", SRC)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class ExactCompetitorProbeTests(unittest.TestCase):
    def test_success(self):
        self.assertEqual(p.classify_install("Success\n", "", 0), "INSTALLED")

    def test_provider_and_other_install_failures(self):
        for failure in p.INSTALL_ERRORS:
            with self.subTest(failure=failure):
                self.assertEqual(p.classify_install("", "Failure [" + failure + "]", 1), failure)

    def test_dont_claim_success_on_exit_code(self):
        self.assertEqual(p.classify_install("Success\n", "", 1), "INSTALL_FAILED_OTHER")
        self.assertEqual(p.classify_install("Failure", "", 0), "INSTALL_FAILED_OTHER")

    def test_strict_package_identity(self):
        self.assertFalse(p.package_installed("package:app.chromasync.yamclone.other\n", p.CLONE_PACKAGE))
        self.assertTrue(p.package_installed("package:ru.yandex.music\npackage:app.chromasync.yamclone\n", p.CLONE_PACKAGE))

    def test_resumed_not_historic(self):
        self.assertFalse(p.resumed_for_package("ActivityRecord{app.chromasync.yamclone/.Main}", p.CLONE_PACKAGE))
        self.assertTrue(p.resumed_for_package(
            "mResumedActivity: ActivityRecord{app.chromasync.yamclone/.Main}", p.CLONE_PACKAGE))
        self.assertFalse(p.resumed_for_package(
            "mResumedActivity: ActivityRecord{ru.yandex.music/.Main}", p.CLONE_PACKAGE))

    def test_pidof_missing_is_not_a_false_pass(self):
        class Fake(p.Guest):
            def __init__(self):
                pass
            def command(self, *args, **kw):
                class Result:
                    returncode = 1
                    stdout = ""
                return Result()
            def shell(self, *args):
                return "mResumedActivity: ActivityRecord{app.chromasync.yamclone/.Main}"
        record = Fake().observe(p.CLONE_PACKAGE, sleeper=lambda _: None)
        self.assertEqual(record["window_seconds"], 16)
        self.assertFalse(record["main_survives"])
        self.assertTrue(record["activity_resumed_all_samples"])

    def test_guard_blocks_owner_phone(self):
        guest = p.Guest(serial="192.168.0.2:5555")
        with self.assertRaisesRegex(RuntimeError, "NON_LOCAL_GUEST_FORBIDDEN"):
            p.probe(guest, Path("/not/a/file"), "alone", [])

    def test_missing_file_before_any_adb_calls(self):
        class Fake(p.Guest):
            def __init__(self):
                self.serial = "127.0.0.1:5555"
            def shell(self, *args):
                raise AssertionError("ADB may not run yet")
        with self.assertRaises(FileNotFoundError):
            p.probe(Fake(), Path("/not/a/file"), "alone", [])


    def test_docker_transport_uses_only_disposable_container(self):
        guest = p.DockerGuest()
        self.assertEqual(guest.serial, "127.0.0.1:5555")
        self.assertEqual(guest.CONTAINER, "celikom-native-arm-android13")
        with self.assertRaisesRegex(RuntimeError, "DOCKER_COMMAND_SCOPE_REJECTED"):
            guest.command("install", "/tmp/test.apk")

    def test_docker_transport_requires_actual_apk(self):
        guest = p.DockerGuest()
        with self.assertRaisesRegex(RuntimeError, "HOST_APK_NOT_FOUND"):
            guest.install([Path("/does/not/exist.apk")])

    def test_docker_transport_rejects_unbounded_apks(self):
        guest = p.DockerGuest()
        with self.assertRaisesRegex(RuntimeError, "INVALID_INSTALL_APK_COUNT"):
            guest.install([])
        with self.assertRaisesRegex(RuntimeError, "INVALID_INSTALL_APK_COUNT"):
            guest.install([Path("/does/not/exist.apk")] * 6)


if __name__ == "__main__":
    unittest.main()
