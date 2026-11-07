"""Verify the signed side-by-side CELIKOM Test APK from its final bytes."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
import zipfile

from release_archive import inspect_zip

ROOT = Path(__file__).resolve().parent
SPEC = json.loads((ROOT / "test-app-spec.json").read_text(encoding="utf-8"))
ANDROID_NS = "http://schemas.android.com/apk/res/android"
A = "{" + ANDROID_NS + "}"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(command):
    subprocess.run(list(map(str, command)), check=True)


def certificate(apk, build_tools):
    output = subprocess.check_output([
        "java", "-jar", str(build_tools / "lib/apksigner.jar"),
        "verify", "--verbose", "--print-certs", str(apk),
    ], text=True)
    match = re.search(r"Signer #1 certificate SHA-256 digest: ([a-f0-9]+)", output)
    if not match:
        raise ValueError("APK signing certificate is missing")
    v2 = "Verified using v2 scheme (APK Signature Scheme v2): true" in output
    v3 = "Verified using v3 scheme (APK Signature Scheme v3): true" in output
    if not (v2 or v3):
        raise ValueError("APK has no verified modern v2/v3 signature")
    return match.group(1), v2, v3


def structure(node):
    attributes = [
        (key, "|".join(sorted(value.split("|"))) if key == A + "foregroundServiceType" else value)
        for key, value in node.attrib.items()
    ]
    return node.tag, sorted(attributes), [structure(child) for child in node]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("apk", "base-apk", "build-tools", "compiled-dex", "apktool"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()

    inputs = json.loads((ROOT / "build-inputs.json").read_text(encoding="utf-8"))
    if sha(args.base_apk) != inputs["base_apk_sha256"] or sha(args.base_apk) != SPEC["base_apk_sha256"]:
        raise ValueError("Pinned baseline APK checksum mismatch")
    if sha(args.apktool) != inputs["apktool_sha256"]:
        raise ValueError("Apktool checksum mismatch")
    if sha(args.compiled_dex) == "":
        raise ValueError("Compiled DEX is missing")

    signer, signer_v2, signer_v3 = certificate(args.apk, args.build_tools)
    base_signer, base_v2, base_v3 = certificate(args.base_apk, args.build_tools)
    if not base_v3:
        raise ValueError("Pinned original base APK must verify with its v3 signature")
    if not signer_v3:
        raise ValueError("Final CELIKOM Test APK must verify with its v3 signature")
    if signer != base_signer or signer != SPEC["signing_certificate_sha256"]:
        raise ValueError("Test APK signer does not match the original CELIKOM certificate")

    run([args.build_tools / "zipalign", "-c", "4", args.apk])
    badging = subprocess.check_output([
        str(args.build_tools / "aapt"), "dump", "badging", str(args.apk),
    ], text=True)
    for expected in (
        "package: name='" + SPEC["package"] + "'",
        "versionCode='" + str(SPEC["version_code"]) + "'",
        "versionName='" + SPEC["version"] + "'",
        "application-label:'" + SPEC["label"] + "'",
    ):
        if expected not in badging:
            raise ValueError("APK badging is missing expected identity: " + expected)

    resources = subprocess.check_output([
        str(args.build_tools / "aapt"), "dump", "resources", str(args.apk),
    ], text=True, errors="replace")
    if "celikom_test_icon" not in resources:
        raise ValueError("Dedicated CELIKOM Test launcher icon is missing from compiled resources")

    with tempfile.TemporaryDirectory(prefix="celikom-test-verify-") as directory:
        directory = Path(directory)
        baseline_decoded = directory / "baseline"
        final_decoded = directory / "final"
        run(["java", "-jar", args.apktool, "d", args.base_apk, "-o", baseline_decoded, "-f"])
        run(["java", "-jar", args.apktool, "d", args.apk, "-o", final_decoded, "-f"])
        baseline = ET.parse(baseline_decoded / "AndroidManifest.xml").getroot()
        current = ET.parse(final_decoded / "AndroidManifest.xml").getroot()
        if baseline.get("package") != SPEC["stable_package"]:
            raise ValueError("Baseline package is not the stable CELIKOM package")
        if current.get("package") != SPEC["package"]:
            raise ValueError("Final APK has the wrong application package")

        expected = ET.fromstring(ET.tostring(baseline))
        expected.set("package", SPEC["package"])
        app = expected.find("application")
        app.set(A + "label", SPEC["label"])
        app.set(A + "icon", "@drawable/celikom_test_icon")
        expected_launchers = []
        for activity in app.findall("activity"):
            actions = {
                node.get(A + "name")
                for intent_filter in activity.findall("intent-filter")
                for node in intent_filter.findall("action")
            }
            categories = {
                node.get(A + "name")
                for intent_filter in activity.findall("intent-filter")
                for node in intent_filter.findall("category")
            }
            if "android.intent.action.MAIN" in actions and "android.intent.category.LAUNCHER" in categories:
                activity.set(A + "label", SPEC["label"])
                expected_launchers.append(activity)
        if len(expected_launchers) != 1:
            raise ValueError("Expected exactly one launcher activity in baseline manifest")
        stable_permission = SPEC["stable_package"] + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
        for node in expected:
            if node.tag in ("permission", "uses-permission") and node.get(A + "name") == stable_permission:
                node.set(A + "name", SPEC["test_permission"])
        for provider in app.findall("provider"):
            name = provider.get(A + "name")
            if name == "androidx.core.content.FileProvider":
                provider.set(A + "authorities", SPEC["file_provider_authority"])
            elif name == "androidx.startup.InitializationProvider":
                provider.set(A + "authorities", SPEC["startup_authority"])
        if structure(current) != structure(expected):
            raise ValueError("Final manifest contains changes outside the approved test identity/authority/icon/launcher-label boundary")
        current_launchers = []
        for activity in current.find("application").findall("activity"):
            actions = {
                node.get(A + "name")
                for intent_filter in activity.findall("intent-filter")
                for node in intent_filter.findall("action")
            }
            categories = {
                node.get(A + "name")
                for intent_filter in activity.findall("intent-filter")
                for node in intent_filter.findall("category")
            }
            if "android.intent.action.MAIN" in actions and "android.intent.category.LAUNCHER" in categories:
                current_launchers.append(activity)
        if len(current_launchers) != 1 or current_launchers[0].get(A + "label") != SPEC["label"]:
            raise ValueError("Launcher icon label is not explicitly CELIKOM Test")

        providers = current.find("application").findall("provider")
        authorities = [p.get(A + "authorities") for p in providers if p.get(A + "authorities")]
        if set(authorities) != {SPEC["file_provider_authority"], SPEC["startup_authority"]}:
            raise ValueError("Test provider authorities are missing or unexpected")
        if len(authorities) != len(set(authorities)):
            raise ValueError("Provider authority collision detected")
        permissions = [
            n.get(A + "name", "")
            for n in current
            if n.tag in ("permission", "uses-permission")
        ]
        if SPEC["test_permission"] not in permissions:
            raise ValueError("Test-specific dynamic receiver permission is missing")
        if SPEC["stable_package"] + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION" in permissions:
            raise ValueError("Stable dynamic receiver permission leaked into test manifest")
        if "android.permission.REQUEST_INSTALL_PACKAGES" in permissions:
            raise ValueError("Test APK must not request REQUEST_INSTALL_PACKAGES")
        component_names = [
            n.get(A + "name", "")
            for n in current.find("application").iter()
            if n.tag in ("activity", "service", "receiver", "provider")
        ]
        if any(name.endswith("UpdateCheckJob") or name.endswith("UpdateInstallReceiver") for name in component_names):
            raise ValueError("OTA job or install receiver is registered in the test APK")

        build_config = (final_decoded / "smali/pro/celikom/nativeprobe/BuildConfig.smali").read_text(encoding="utf-8")
        for required in (
            '.field public static final APPLICATION_ID:Ljava/lang/String; = "' + SPEC["package"] + '"',
            ".field public static final VERSION_CODE:I = " + hex(SPEC["version_code"]),
            '.field public static final VERSION_NAME:Ljava/lang/String; = "' + SPEC["version"] + '"',
        ):
            if required not in build_config:
                raise ValueError("Test BuildConfig identity/version is missing: " + required)
        if '.field public static final APPLICATION_ID:Ljava/lang/String; = "' + SPEC["stable_package"] + '"' in build_config:
            raise ValueError("Stable application ID remains in test BuildConfig")

        legacy = (final_decoded / "smali/pro/celikom/nativeprobe/MainActivity.smali").read_text(encoding="utf-8")
        method = re.search(
            r"\.method protected onCreate\(Landroid/os/Bundle;\)V(.*?)\.end method",
            legacy, re.S,
        )
        if not method or "identitydiag/RecorderActivity" not in method.group(1) or "->finish()V" not in method.group(1):
            raise ValueError("Legacy launcher no longer redirects to the test RecorderActivity")

    with zipfile.ZipFile(args.apk) as apk:
        catalog = json.loads(apk.read("assets/catalog-diagnostic.json"))
        catalog_tracks = catalog.get("tracks") if isinstance(catalog, dict) else None
        catalog_generated = catalog.get("generated_at_ms") if isinstance(catalog, dict) else None
        catalog_total = catalog.get("total_tracks") if isinstance(catalog, dict) else None
        now_ms = int(time.time() * 1000)
        if catalog.get("schema") != 1 or catalog.get("source") != "celikom_owner_catalog_snapshot":
            raise ValueError("Final APK does not contain the owner catalogue snapshot")
        if catalog.get("complete") is not True or not isinstance(catalog_tracks, list):
            raise ValueError("Final APK catalogue snapshot is incomplete")
        if not isinstance(catalog_total, int) or catalog_total < 1 or catalog_total != len(catalog_tracks):
            raise ValueError("Final APK catalogue snapshot row count is invalid")
        if not isinstance(catalog_generated, int) or catalog_generated > now_ms + 60000 or now_ms - catalog_generated > 24 * 60 * 60 * 1000:
            raise ValueError("Final APK catalogue snapshot is stale")
        catalog_ids = [row.get("track_id") for row in catalog_tracks if isinstance(row, dict)]
        if len(catalog_ids) != len(catalog_tracks) or len(set(catalog_ids)) != len(catalog_ids):
            raise ValueError("Final APK catalogue snapshot contains invalid or duplicate rows")
        dex_names = sorted(n for n in apk.namelist() if re.fullmatch(r"classes\d*\.dex", n))
        if dex_names != ["classes.dex", "classes2.dex"]:
            raise ValueError("Unexpected DEX layout in final test APK")
        if apk.read("classes2.dex") != args.compiled_dex.read_bytes():
            raise ValueError("Final signed APK addon DEX differs from the freshly compiled test DEX")
        all_dex = b"\n".join(apk.read(name) for name in dex_names)
        if not all_dex.startswith(b"dex\n"):
            raise ValueError("Final APK DEX header is invalid")
        for marker in (
            b"UpdateCenter", b"UpdateCheckJob", b"UpdateInstallReceiver",
            b"stable.json", b"/updates/android/stable.json",
            b"REQUEST_INSTALL_PACKAGES",
            (SPEC["stable_package"] + ".package-export").encode(),
            (SPEC["stable_package"] + ".androidx-startup").encode(),
            (SPEC["stable_package"] + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION").encode(),
        ):
            if marker in all_dex:
                raise ValueError("Forbidden stable OTA/authority marker remains in DEX: " + marker.decode("utf-8", "replace"))
        if SPEC["update_notice"].encode("utf-8") not in all_dex:
            raise ValueError("Static OTA-disabled notice is missing from the app DEX")
        if SPEC["label"].encode("ascii") not in all_dex:
            raise ValueError("Test app header label is missing from the app DEX")

    archive_proof = inspect_zip(args.apk, args.base_apk, args.compiled_dex, allowed_asset_updates={"assets/catalog-diagnostic.json"})
    proof = {
        "package": SPEC["package"],
        "stable_package": SPEC["stable_package"],
        "version": SPEC["version"],
        "version_code": SPEC["version_code"],
        "label": SPEC["label"],
        "signer_sha256": signer,
        "signer_matches_original": signer == SPEC["signing_certificate_sha256"],
        "signature_v2_verified": signer_v2,
        "signature_v3_verified": signer_v3,
        "base_signature_v2_verified": base_v2,
        "base_signature_v3_verified": base_v3,
        "package_id_is_distinct": True,
        "separate_android_sandbox": True,
        "dedicated_launcher_icon_verified": True,
        "launcher_label_verified": True,
        "test_authorities_unique": True,
        "ota_updater_absent": True,
        "stable_manifest_reference_absent": True,
        "request_install_packages_absent": True,
        "original_assets_unchanged": archive_proof["original_assets_unchanged"],
        "non_allowlisted_assets_unchanged": archive_proof["non_allowlisted_assets_unchanged"],
        "allowed_asset_updates": archive_proof["allowed_asset_updates"],
        "catalog_snapshot_updated": True,
        "catalog_snapshot_generated_at_ms": catalog_generated,
        "catalog_snapshot_track_count": catalog_total,
        "apk_sha256": sha(args.apk),
        "size_bytes": args.apk.stat().st_size,
        "stable_published": False,
        "stable_ota_touched": False,
        "physical_phone_playback_verified": False,
        "acoustic_acceptance": False,
    }
    args.apk.with_suffix(".verification.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print("PASS: distinct package/sandbox, fresh owner catalogue snapshot, all other base assets unchanged, original signer v2/v3, exact test DEX, no OTA")


if __name__ == "__main__":
    main()
