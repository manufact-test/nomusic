#!/usr/bin/env python3
"""Read-only signed-Yandex provider identity linkage audit (CI-only).

No clone output, installation, login, media playback, secrets, APK artifacts,
owner phone changes or DEX mutation. Only public manifest provider metadata and
counts of selected public class/resource-name strings are emitted.
"""
from __future__ import annotations
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path
import clone_native_splits_ephemeral as original
import clone_native_splits_arsclib_ephemeral as arsc

PUBLIC_AUTHORITIES = (
    "com.yandex.passport.authsdk.provider.ru.yandex.music",
    "com.yandex.passport.internal.provider.ru.yandex.music",
    "com.yandex.passport.internal.sso.ru.yandex.music",
    "com.yandex.preinstallsatellite.appmetrica.provider",
)
RESOURCE_NAME = "passport_sync_adapter_content_authority"


def main():
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise arsc.TrialError("ONLY_EPHEMERAL_GITHUB_CI_ALLOWED")
    with tempfile.TemporaryDirectory(prefix="celikom-provider-audit-") as td:
        root = Path(td)
        archive = root / "pinned-official.xapk"
        size, sha = original.gpr.download(archive)
        if size != 60433885 or sha != original.ARCHIVE_SHA:
            raise arsc.TrialError("SIGNED_APK_PIN_MISMATCH")
        apks = original.gpr.split_apks(archive, root)
        if len(apks) != 5:
            raise arsc.TrialError("FIVE_SPLITS_MISSING")
        original.gpr.inspect_publisher(apks)
        base = next((p for p in apks if original.apkmeta(p).get("split", "") == ""), None)
        if base is None:
            raise arsc.TrialError("ORIGINAL_BASE_SPLIT_MISSING")
        editor = root / "APKEditor.jar"
        arsc.download_editor(editor)
        decoded = root / "base-readonly"
        arsc.run(["java", "-Xmx3g", "-jar", str(editor), "d", "-t", "xml",
                  "-dex", "-i", str(base), "-o", str(decoded)],
                 "READ_ONLY_BASE_DECODE", 240)

        manifest = (decoded / "AndroidManifest.xml").read_bytes()
        rewritten, _ = original.rewrite_manifest(manifest.decode("utf-8"))
        ns = "{" + original.ANDROID + "}"
        def providers(xml):
            m = original.ET.fromstring(xml)
            return [
                {"authority": v.strip(), "component": e.attrib.get(ns + "name", "")}
                for e in m.iter("provider")
                for v in e.attrib.get(ns + "authorities", "").split(";") if v.strip()
            ]
        before = providers(manifest)
        after = providers(rewritten)
        collisions = sorted({x["authority"] for x in before} &
                            {x["authority"] for x in after})
        collision_classes = [p for p in before if p["authority"] in collisions]
        needles = list(PUBLIC_AUTHORITIES) + [
            RESOURCE_NAME, "ru.yandex.music", "com.yandex.passport.authsdk.provider"
        ]
        dex_counts = {needle: 0 for needle in needles}
        with zipfile.ZipFile(base) as z:
            dexes = [n for n in z.namelist() if n.startswith("classes") and n.endswith(".dex")]
            for name in dexes:
                data = z.read(name)
                for needle in needles:
                    dex_counts[needle] += data.count(needle.encode())
        resource_matches = []
        for file in decoded.rglob("*"):
            if file.suffix.lower() not in (".xml", ".json") or file.stat().st_size > 2 * 1024 * 1024:
                continue
            raw = file.read_text(encoding="utf-8", errors="replace")
            if RESOURCE_NAME not in raw:
                continue
            try:
                document = original.ET.fromstring(raw)
                items = ["".join(element.itertext()).strip()
                         for element in document.iter("string")
                         if element.attrib.get("name") == RESOURCE_NAME]
            except original.ET.ParseError:
                items = []
            resource_matches.append({
                "relative_file": str(file.relative_to(decoded)),
                "found_named_value": bool(items),
                "public_configured_value": " ".join(items[0].split())[:200] if items else ""
            })
        result = {
            "verdict": "READ_ONLY_PROVIDER_IDENTITY_AUDIT_NOT_CLONE_PASS",
            "source_signature_verified": True,
            "exact_five_signed_splits": True,
            "original_base_dex_count": len(dexes),
            "original_provider_count": len(before),
            "parallel_identity_collisions": collision_classes,
            "targeted_dex_literal_counts": dex_counts,
            "resource_definition_hits": resource_matches[:15],
            "apk_installed": False,
            "private_data_accessed": False,
            "binaries_published": False
        }
    return result


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True, ensure_ascii=False))
    except Exception as e:
        code = e.stage if isinstance(e, arsc.TrialError) else type(e).__name__.upper()
        print(json.dumps({"verdict": "READ_ONLY_PROVIDER_AUDIT_BLOCKED",
                          "stage": code, "binaries_published": False}))
        sys.exit(2)
