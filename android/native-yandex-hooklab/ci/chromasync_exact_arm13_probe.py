#!/usr/bin/env python3
"""Exact ChromaSync APK runtime probe on a NEW disposable ARM Android13 guest.

Never modifies input APK, signer, vendor protections or user devices. Only
bounded sanitized install/MAIN/Activity observations; no accounts or playback.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

EXPECTED_SHA256 = "4e6edb1c471f6b3715eae4c0a35f0bd898b0daaa87f3f8fb3ba0b20d1638b53d"
CLONE_PACKAGE = "app.chromasync.yamclone"
STOCK_PACKAGE = "ru.yandex.music"
INSTALL_ERRORS = (
    "INSTALL_FAILED_CONFLICTING_PROVIDER",
    "INSTALL_FAILED_DUPLICATE_PERMISSION",
    "INSTALL_FAILED_SHARED_USER_INCOMPATIBLE",
    "INSTALL_FAILED_UPDATE_INCOMPATIBLE",
    "INSTALL_FAILED_INVALID_APK",
    "INSTALL_PARSE_FAILED",
    "INSTALL_FAILED_NO_MATCHING_ABIS",
    "INSTALL_FAILED_VERIFICATION_FAILURE",
    "INSTALL_FAILED_VERSION_DOWNGRADE",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_install(stdout: str, stderr: str, code: int) -> str:
    combined = stdout + "\n" + stderr
    for marker in INSTALL_ERRORS:
        if marker in combined:
            return marker
    if code == 0 and re.search(r"(?m)^Success\s*$", combined):
        return "INSTALLED"
    return "INSTALL_FAILED_OTHER"


def resumed_for_package(dump: str, package: str) -> bool:
    # Ignore stale history records: require the current resumed activity line.
    return any(package in line and
               re.search(r"(?:topResumedActivity|mResumedActivity|ResumedActivity:)", line)
               for line in dump.splitlines())


def package_installed(output: str, package: str) -> bool:
    return any(x.strip() == "package:" + package for x in output.splitlines())


class Guest:
    def __init__(self, serial: str = "127.0.0.1:5555", adb: str = "adb"):
        self.serial, self.adb = serial, adb

    def command(self, *args: str, timeout: int = 35):
        return subprocess.run(
            [self.adb, "-s", self.serial, *args],
            capture_output=True, text=True, errors="replace", timeout=timeout,
            check=False
        )

    def shell(self, *args: str) -> str:
        result = self.command("shell", *args)
        if result.returncode:
            raise RuntimeError("ADB_SHELL_FAILED")
        return result.stdout

    def install(self, apks: list[Path]) -> str:
        operation = "install-multiple" if len(apks) > 1 else "install"
        result = self.command(operation, "--no-streaming", *map(str, apks), timeout=150)
        return classify_install(result.stdout, result.stderr, result.returncode)

    def launch(self, package: str) -> str:
        result = self.command("shell", "am", "start", "-a",
                              "android.intent.action.MAIN", "-c",
                              "android.intent.category.LAUNCHER", "-p", package)
        response = result.stdout + result.stderr
        return ("MAIN_LAUNCH_REJECTED"
                if result.returncode or "Error:" in response or "Exception" in response
                else "MAIN_LAUNCH_ACCEPTED")

    def observe(self, package: str, sleeper=time.sleep) -> dict:
        # One package process *remaining* alive is insufficient if an app is
        # continuously crashing/restarting between samples. Track PID identity
        # privately; publish only a stable/changed boolean, never PID values.
        observations = []
        observed_pids = []
        for _ in range(16):
            sleeper(1)
            pid = self.command("shell", "pidof", package)
            if pid.returncode not in (0, 1):
                raise RuntimeError("ADB_PID_CHECK_FAILED")
            identity = pid.stdout.strip() if (pid.returncode == 0
                       and re.fullmatch(r"\d+", pid.stdout.strip())) else None
            observed_pids.append(identity)
            dump = self.shell("dumpsys", "activity", "activities")
            observations.append({
                "main_alive": identity is not None,
                "activity_resumed": resumed_for_package(dump, package),
            })
        ever_alive = all(row["main_alive"] for row in observations)
        stable_main_pid = ever_alive and len(set(observed_pids)) == 1
        return {
            "window_seconds": 16,
            "samples": observations,
            "main_survives": ever_alive and stable_main_pid,
            "stable_main_pid": stable_main_pid,
            "activity_resumed_all_samples": all(row["activity_resumed"] for row in observations),
        }


class DockerGuest(Guest):
    """Talk only to the pinned disposable Redroid container, NO ADB or device."""

    CONTAINER = "celikom-native-arm-android13"

    def __init__(self):
        super().__init__(serial="127.0.0.1:5555", adb="docker")

    def command(self, *args: str, timeout: int = 35):
        if not args or args[0] != "shell":
            raise RuntimeError("DOCKER_COMMAND_SCOPE_REJECTED")
        return subprocess.run(
            ["docker", "exec", self.CONTAINER, *args[1:]],
            capture_output=True, text=True, errors="replace",
            timeout=timeout, check=False
        )

    def install(self, apks: list[Path]) -> str:
        if not 1 <= len(apks) <= 5:
            raise RuntimeError("INVALID_INSTALL_APK_COUNT")
        guest_paths = []
        try:
            for i, apk in enumerate(apks):
                if not apk.is_file():
                    raise RuntimeError("HOST_APK_NOT_FOUND")
                destination = f"/data/local/tmp/celikom-probe-{i}.apk"
                cp = subprocess.run(
                    ["docker", "cp", str(apk), f"{self.CONTAINER}:{destination}"],
                    capture_output=True, text=True, errors="replace", timeout=120
                )
                if cp.returncode:
                    raise RuntimeError("DOCKER_APK_COPY_FAILED")
                guest_paths.append(destination)
            operation = "install-multiple" if len(apks) > 1 else "install"
            installed = self.command("shell", "pm", operation, *guest_paths, timeout=150)
            return classify_install(installed.stdout, installed.stderr, installed.returncode)
        finally:
            if guest_paths:
                self.command("shell", "rm", "-f", *guest_paths)


def probe(guest: Guest, apk: Path, mode: str, stock_apks: list[Path]) -> dict:
    if guest.serial != "127.0.0.1:5555":
        raise RuntimeError("NON_LOCAL_GUEST_FORBIDDEN")
    if sha256_file(apk) != EXPECTED_SHA256:
        raise RuntimeError("EXACT_APK_SHA256_MISMATCH")
    if (os.getenv("GITHUB_ACTIONS") != "true"
            or os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID") != "1"
            or platform.machine() != "aarch64"):
        raise RuntimeError("ONLY_DISPOSABLE_ARM_CI_GUEST_ALLOWED")
    if guest.shell("getprop", "ro.build.version.sdk").strip() != "33":
        raise RuntimeError("GUEST_NOT_ANDROID13")
    if "arm64-v8a" not in guest.shell("getprop", "ro.product.cpu.abilist"):
        raise RuntimeError("GUEST_NOT_ARM64")
    if guest.shell("getprop", "sys.boot_completed").strip() != "1":
        raise RuntimeError("ANDROID_NOT_BOOTED")
    package_list = guest.shell("pm", "list", "packages")
    if (package_installed(package_list, STOCK_PACKAGE) or
            package_installed(package_list, CLONE_PACKAGE)):
        raise RuntimeError("GUEST_NOT_CLEAN")

    outcome = {
        "mode": mode, "exact_sha256_verified": True, "android_api": 33,
        "arm64": True, "owner_device_touched": False,
        "account_login_tested": False, "audio_tested": False,
        "play_protect_tested": False,
    }
    if mode == "stock-first":
        if not stock_apks:
            raise RuntimeError("PINNED_STOCK_APKS_REQUIRED")
        outcome["stock_install"] = guest.install(stock_apks)
        if outcome["stock_install"] != "INSTALLED":
            outcome["verdict"] = "STOCK_INSTALL_FAILED"
            return outcome
        if not package_installed(guest.shell("pm", "list", "packages"), STOCK_PACKAGE):
            outcome["verdict"] = "STOCK_PACKAGE_MISMATCH"
            return outcome
    outcome["clone_install"] = guest.install([apk])
    if outcome["clone_install"] != "INSTALLED":
        outcome["verdict"] = "CLONE_INSTALL_FAILED"
        return outcome
    if not package_installed(guest.shell("pm", "list", "packages"), CLONE_PACKAGE):
        outcome["verdict"] = "CLONE_PACKAGE_MISMATCH"
        return outcome
    outcome["launch"] = guest.launch(CLONE_PACKAGE)
    if outcome["launch"] != "MAIN_LAUNCH_ACCEPTED":
        outcome["verdict"] = "MAIN_LAUNCH_REJECTED"
        return outcome
    observation = guest.observe(CLONE_PACKAGE)
    outcome.update(observation)
    outcome["verdict"] = (
        "NATIVE_MAIN_SAME_PID_RESUMED_16S"
        if observation["main_survives"] and observation["activity_resumed_all_samples"]
        else "MAIN_NOT_SUSTAINED_OR_RESUMED"
    )
    return outcome


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--mode", choices=("alone", "stock-first"), default="alone")
    parser.add_argument("--stock-apks", nargs="*", type=Path, default=[])
    parser.add_argument("--serial", default="127.0.0.1:5555")
    parser.add_argument("--transport", choices=("adb", "docker"), default="adb")
    args = parser.parse_args()
    try:
        guest = DockerGuest() if args.transport == "docker" else Guest(serial=args.serial)
        result = probe(guest, args.apk, args.mode, args.stock_apks)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["verdict"] == "NATIVE_MAIN_SAME_PID_RESUMED_16S" else 1
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print(json.dumps({
            "verdict": "NOT_RUN_OR_ABORTED", "owner_device_touched": False,
            "reason": str(error) if isinstance(error, RuntimeError)
            else type(error).__name__
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
