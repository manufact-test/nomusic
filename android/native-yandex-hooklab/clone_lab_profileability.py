"""Only enable standard Android shell profiling on an independent ephemeral clone.

No issuer signature spoof, code patching, accounts, permission weakening or
Play Protect modification. Never apply to original, device or release binary.
"""
from __future__ import annotations
import re
import xml.etree.ElementTree as ET

ANDROID = "{http://schemas.android.com/apk/res/android}"
CLONE = "pro.celikom.yandex.nativeclonelab"
APP_CLASS = "ru.yandex.music.YMApplication"


def enable_private_lab_shell_profiling(manifest: bytes) -> bytes:
    root = ET.fromstring(manifest)
    if root.tag != "manifest" or root.get("package") != CLONE:
        raise ValueError("NOT_THE_ISOLATED_CLONE_PACKAGE")
    if root.get(ANDROID + "sharedUserId"):
        raise ValueError("NO_SHARED_USER_ID")
    application = root.find("application")
    if application is None or application.get(ANDROID + "name") != APP_CLASS:
        raise ValueError("UNEXPECTED_NATIVE_APPLICATION_CLASS")
    if application.get(ANDROID + "debuggable", "false") == "true":
        raise ValueError("DEBUGGABLE_APPLICATION_NOT_ACCEPTED")
    profiles = application.findall("profileable")
    if len(profiles) > 1:
        raise ValueError("AMBIGUOUS_PROFILEABILITY")
    profile = profiles[0] if profiles else ET.SubElement(application, "profileable")
    if profile.get(ANDROID + "enabled", "true") == "false":
        raise ValueError("DISABLED_PROFILEABILITY_NOT_OVERRIDDEN")
    profile.set(ANDROID + "shell", "true")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def classify_compiled_shell_profiler(xmltree: str) -> dict:
    """Recognize only fixed aapt XML-tree profileable shell boolean.

    Check the compiled, independently lab-signed APK, not editable XML source.
    Never return a manifest snippet, third-party package name or raw symbols.
    """
    lines = xmltree.splitlines()[:25000]
    present = False
    flag = False
    for pos, line in enumerate(lines):
        if "E: profileable" not in line:
            continue
        present = True
        for item in lines[pos + 1:pos + 12]:
            if "E: " in item:
                break
            if "A: android:shell(" in item:
                flag = re.search(r"\)\s*0x(?:ffffffff|0*1)\s*$", item.lower()) is not None
        break
    return {"compiled_profileable_declaration_seen": present,
            "compiled_shell_profiler_true": flag,
            "raw_manifest_exposed": False}
