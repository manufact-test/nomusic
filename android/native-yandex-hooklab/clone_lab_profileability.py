"""Only enable standard Android shell profiling on an independent ephemeral clone.

No issuer signature spoof, code patching, accounts, permission weakening or
Play Protect modification. Never apply to original, device or release binary.
"""
from __future__ import annotations
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
