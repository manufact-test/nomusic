#!/usr/bin/env python3
"""Read-only public AndroidManifest permission identity audit for pinned Yandex.

Never reads account credentials, device state, private data, media, token/key
values or network requests. Only public declaration names, flags and DEX
literal COUNTS are emitted. No vendor APK artifact is published or installed.
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path
import clone_native_splits_ephemeral as source
import clone_native_splits_arsclib_ephemeral as arsc

ANDROID = "{" + source.ANDROID + "}"
FOCUS = "com.yandex.permission.READ_CREDENTIALS"


def run():
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise arsc.TrialError("CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-permission-metadata-") as name:
        root = Path(name)
        archive = root / "original-signed.xapk"
        size, digest = source.gpr.download(archive)
        if size != 60433885 or digest != source.ARCHIVE_SHA:
            raise arsc.TrialError("PINNED_ORIGINAL_CHANGED")
        apks = source.gpr.split_apks(archive, root)
        if len(apks) != 5:
            raise arsc.TrialError("FIVE_SPLITS_REQUIRED")
        source.gpr.inspect_publisher(apks)
        editor = root / "APKEditor.jar"
        arsc.download_editor(editor)
        declaration_rows = []
        usage_rows = []
        component_references = []
        dex_counts = {}
        all_defined = set()
        for i, apk in enumerate(apks):
            split = source.apkmeta(apk).get("split", "") or "base"
            decoded = root / ("decoded-" + str(i))
            arsc.run(["java","-Xmx3g","-jar",str(editor),"d","-t","xml",
                      "-dex","-i",str(apk),"-o",str(decoded)],
                     "PERMISSION_DECODE_SPLIT_"+str(i),240)
            xml = source.ET.parse(decoded / "AndroidManifest.xml").getroot()
            if xml.attrib.get("package") != source.SOURCE:
                raise arsc.TrialError("MANIFEST_ORIGINAL_IDENTITY_DRIFT")
            for el in xml.iter():
                tag = el.tag
                name = el.attrib.get(ANDROID+"name", "")
                if tag in ("permission", "permission-group", "permission-tree"):
                    if name in all_defined:
                        raise arsc.TrialError("ORIGINAL_DUPLICATE_PERMISSION_DECLARATION")
                    all_defined.add(name)
                    declaration_rows.append({
                        "split": split, "kind": tag, "name": name,
                        "protection_level": el.attrib.get(ANDROID+"protectionLevel","")
                    })
                if tag in ("uses-permission", "uses-permission-sdk-23"):
                    if name.startswith("com.yandex.permission.") or name == FOCUS:
                        usage_rows.append({"split":split, "name":name, "kind":tag})
                for attr,val in el.attrib.items():
                    if val == FOCUS and attr != ANDROID+"name":
                        component_references.append({
                            "split": split, "element": tag, "attribute": attr.rsplit("}",1)[-1]
                        })
            with zipfile.ZipFile(apk) as z:
                for entry in z.namelist():
                    if entry.startswith("classes") and entry.endswith(".dex"):
                        dex_counts[entry] = dex_counts.get(entry,0) + z.read(entry).count(FOCUS.encode())
        if FOCUS not in all_defined:
            raise arsc.TrialError("EXPECTED_CREDENTIAL_PERMISSION_DECLARATION_MISSING")
        return {
            "verdict": "SIGNED_MANIFEST_PERMISSION_AUDIT_STATIC_ONLY",
            "source": "2026.10.3 #170gpr",
            "original_five_splits_verified": True,
            "declared_permission_count": len(declaration_rows),
            "declared_permissions": declaration_rows[:35],
            "public_yandex_permission_uses": usage_rows[:35],
            "credential_permission_non_declaration_attribute_refs": component_references[:35],
            "credential_permission_dex_literal_counts_by_entry": dex_counts,
            "credential_content_or_values_read": False,
            "authorization_runtime_tested": False,
            "clone_installation_attempted": False,
            "owner_honor_touched": False,
            "third_party_apk_distributed": False,
            "warning": "Manifest permissions are issuer-signature security boundaries, NOT safe to change blindly"
        }


if __name__ == "__main__":
    try:
        print(json.dumps(run(),sort_keys=True,ensure_ascii=False))
    except Exception as e:
        name = e.stage if isinstance(e,arsc.TrialError) else type(e).__name__.upper()
        print(json.dumps({"verdict":"SIGNED_PERMISSION_AUDIT_BLOCKED",
                          "stage":name,"third_party_apk_distributed":False}))
        sys.exit(2)
