"""Strict CI-only independent clone-owned signature-permission A/B trial.

Purpose: test app initialization while preserving Android signature security.
No weakening/granting Yandex original permissions, no cross-app credential
access, no DEX edits and no original publisher APK changes.
"""
from __future__ import annotations
import xml.etree.ElementTree as ET

NS = "{http://schemas.android.com/apk/res/android}"
PACKAGE = "pro.celikom.yandex.nativeclonelab"
MAP = {
    "com.yandex.permission.READ_CREDENTIALS":
        PACKAGE + ".permission.READ_CREDENTIALS",
    "com.yandex.music.RELAY_PERMISSION":
        PACKAGE + ".permission.RELAY_PERMISSION",
}
FIELDS = {"name", "permission", "readPermission", "writePermission"}


def namespace_clone_signature_permissions(manifest: bytes) -> tuple[bytes, dict]:
    root = ET.fromstring(manifest)
    if root.tag != "manifest" or root.get("package") != PACKAGE:
        raise ValueError("NAMESPACED_PERMISSIONS_CLONE_ONLY")
    if root.get(NS + "sharedUserId"):
        raise ValueError("NO_SHARED_UID")
    old_declarations = set()
    renamed = {"declarations": 0, "requests": 0, "component_references": 0}
    for elem in root.iter():
        if elem.tag == "permission":
            name = elem.get(NS + "name")
            if name in MAP:
                if elem.get(NS + "protectionLevel") != "signature":
                    raise ValueError("ORIGINAL_SIGNATURE_PROTECTION_MUST_REMAIN")
                old_declarations.add(name)
        for field in FIELDS:
            attr = NS + field
            original = elem.get(attr)
            if original not in MAP:
                continue
            if elem.tag == "permission" and field == "name":
                renamed["declarations"] += 1
            elif elem.tag in ("uses-permission", "uses-permission-sdk-23") and field == "name":
                renamed["requests"] += 1
            else:
                renamed["component_references"] += 1
            elem.set(attr, MAP[original])
    if old_declarations != set(MAP) or renamed["declarations"] != 2:
        raise ValueError("UNEXPECTED_SIGNATURE_DECLARATION_SET")
    if renamed["requests"] < 1:
        raise ValueError("CLONE_LOCAL_PERMISSION_REQUEST_MISSING")
    # All original publisher permissions must now be entirely unrequested,
    # never claimed by CELIKOM. Own declarations still use signature level.
    for elem in root.iter():
        if elem.tag not in ("permission", "uses-permission", "uses-permission-sdk-23",
                            "activity", "service", "receiver", "provider", "application"):
            continue
        for field in FIELDS:
            if elem.get(NS + field) in MAP:
                raise ValueError("ISSUER_PERMISSION_REFERENCE_REMAINS")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True), renamed
