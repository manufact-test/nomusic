#!/usr/bin/env python3
"""Read-only GUI presence witness for a clean, already-started ChromaSync guest.

This NEVER claims audio, Passport login, replacement or Play Protect.
It emits ONLY fixed booleans/counts. UI text/XML/screenshots remain ephemeral.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

PACKAGE = "app.chromasync.yamclone"
CONTAINER = "celikom-native-arm-android13"
SCREEN = "/data/local/tmp/celikom-native-a1-guest-screen.png"
TREE = "/data/local/tmp/celikom-native-a1-guest-window.xml"


def shell(*args: str, timeout: int = 40):
    return subprocess.run(
        ["docker", "exec", CONTAINER, *args],
        capture_output=True, text=True, errors="replace", timeout=timeout
    )


def classify_focus(data: str, package: str = PACKAGE) -> dict:
    lines = data.splitlines()
    focus = [line.strip() for line in lines if any(
        key in line for key in ("mCurrentFocus=", "mFocusedApp=", "mInputMethodTarget=")
    )]
    return {
        "window_focus_record_available": bool(focus),
        "clone_focused_or_targeted": any(package + "/" in line for line in focus),
        "contains_clone_window_line": any(
            package + "/" in line and any(k in line for k in (
                "Window{", "mCurrentFocus=", "mFocusedApp=", "mInputMethodTarget="
            )) for line in lines
        ),
    }


def classify_ui_tree(xml: str, package: str = PACKAGE) -> dict:
    root = ET.fromstring(xml)
    nodes = list(root.iter("node"))
    clone_count = sum(node.get("package") == package for node in nodes)
    return {
        "ui_hierarchy_decoded": True,
        "ui_node_count": len(nodes),
        "ui_clone_node_count": clone_count,
        "ui_contains_clone_nodes": clone_count > 0,
    }


def classify_png_header(data: bytes) -> dict:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return {"screenshot_png_valid": False}
    if data[12:16] != b"IHDR":
        return {"screenshot_png_valid": False}
    width, height = struct.unpack_from(">II", data, 16)
    return {
        "screenshot_png_valid": width >= 100 and height >= 100,
        "screenshot_width": width,
        "screenshot_height": height,
    }


def main():
    if (os.getenv("GITHUB_ACTIONS") != "true" or
            os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID") != "1" or
            os.uname().machine != "aarch64"):
        raise SystemExit("DISPOSABLE_NATIVE_ARM13_CI_ONLY")
    if shell("getprop", "ro.build.version.sdk").stdout.strip() != "33":
        raise SystemExit("GUEST_NOT_ANDROID13")

    result = {
        "package": PACKAGE,
        "read_only": True,
        "user_account_used": False,
        "audio_tested": False,
        "ui_snapshot_artifact_published": False,
    }
    try:
        win = shell("dumpsys", "window", "windows")
        if win.returncode == 0:
            result.update(classify_focus(win.stdout))
        else:
            result["window_query_failed"] = True

        ui = shell("uiautomator", "dump", TREE, timeout=65)
        if ui.returncode == 0:
            raw = shell("cat", TREE, timeout=20)
            if raw.returncode == 0:
                try:
                    result.update(classify_ui_tree(raw.stdout))
                except ET.ParseError:
                    result["ui_hierarchy_parse_failure"] = True
        else:
            result["ui_hierarchy_unavailable"] = True

        screen = shell("screencap", "-p", SCREEN, timeout=30)
        if screen.returncode == 0:
            with tempfile.TemporaryDirectory(prefix="celikom-own-screen-check-") as folder:
                target = Path(folder) / "shot.png"
                cp = subprocess.run(
                    ["docker", "cp", CONTAINER + ":" + SCREEN, str(target)],
                    capture_output=True, text=True, timeout=30
                )
                if cp.returncode == 0 and target.is_file():
                    # Only header (not pixels, file, raw bytes or checksum) is reported.
                    result.update(classify_png_header(target.read_bytes()[:24]))
        else:
            result["screenshot_unavailable"] = True
    finally:
        shell("rm", "-f", TREE, SCREEN)
    result["native_window_witness"] = bool(
        result.get("clone_focused_or_targeted") and
        result.get("ui_contains_clone_nodes")
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
