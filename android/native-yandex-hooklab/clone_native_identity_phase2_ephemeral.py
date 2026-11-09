#!/usr/bin/env python3
"""EPHEMERAL: tightly scoped five-split package-identity research, no distribution.

One known AppMetrica authority DEX string, four manifest provider authorities
and one Passport sync resource are changed only in disposable CI copies.
This is not a real CELIKOM-enabled Yandex client and NEVER installs on a device.
No DRM, auth/security checks, Play Protect, certificates or accounts bypassed.
"""
from __future__ import annotations
import hashlib
import json
import os
import struct
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path
import clone_native_splits_ephemeral as source
import clone_native_splits_arsclib_ephemeral as arsc

OLD_METRICA = "com.yandex.preinstallsatellite.appmetrica.provider"
NEW_METRICA = "pro.celikom.nativeclonelab.appmetrica.provider.v01"
OLD_SYNC = "com.yandex.passport.sync.ru.yandex.music"
NEW_SYNC = "com.yandex.passport.sync." + source.DEST
SYNC_KEY = "passport_sync_adapter_content_authority"
PASSPORT_PREFIX = "com.yandex.passport."
ANDROID = "{" + source.ANDROID + "}"


def patch_one_dex(data):
    original = OLD_METRICA.encode("ascii")
    replacement = NEW_METRICA.encode("ascii")
    if len(original) != len(replacement):
        raise arsc.TrialError("DECODED_DEX_LITERAL_LENGTH_DRIFT")
    count = data.count(original)
    if count == 0:
        return data, False
    if count != 1 or not data.startswith(b"dex\n"):
        raise arsc.TrialError("DEX_TARGET_NOT_ONE_EXACT_LITERAL")
    updated = bytearray(data.replace(original, replacement, 1))
    updated[12:32] = hashlib.sha1(updated[32:]).digest()
    updated[8:12] = struct.pack("<I", zlib.adler32(updated[12:]) & 0xffffffff)
    return bytes(updated), True


def rewrite_passport_and_metrica(xml):
    root = source.ET.fromstring(xml)
    changed = 0
    for provider in root.iter("provider"):
        attr = ANDROID + "authorities"
        value = provider.attrib.get(attr, "")
        if value == OLD_METRICA:
            provider.set(attr, NEW_METRICA)
            changed += 1
        elif value.startswith(PASSPORT_PREFIX) and value.endswith(source.SOURCE):
            provider.set(attr, value[:-len(source.SOURCE)] + source.DEST)
            changed += 1
    return source.ET.tostring(root, encoding="utf-8", xml_declaration=True), changed


def replace_sync_resource(decoded):
    matches = []
    for file in decoded.rglob("strings.xml"):
        if file.stat().st_size > 3 * 1024 * 1024:
            continue
        root = source.ET.parse(file).getroot()
        edited = False
        for element in root.iter("string"):
            if element.attrib.get("name") == SYNC_KEY:
                if (element.text or "").strip() != OLD_SYNC:
                    raise arsc.TrialError("PASSPORT_SYNC_RESOURCE_VALUE_DRIFT")
                element.text = NEW_SYNC
                edited = True
        if edited:
            file.write_bytes(source.ET.tostring(root, encoding="utf-8", xml_declaration=True))
            matches.append(str(file.relative_to(decoded)))
    return matches


def resolved_provider_authorities(manifest_bytes, sync_value):
    """Compare actual public provider identities, resolving the one pinned sync resource.

    This catches literal and resource-backed collisions before attempting an
    install next to the publisher-signed original. No device or private state.
    Unknown resource references fail closed rather than guess.
    """
    root = source.ET.fromstring(manifest_bytes)
    names = set()
    for provider in root.iter("provider"):
        value = provider.attrib.get(ANDROID + "authorities", "")
        for part in value.split(";"):
            name = part.strip()
            if not name:
                continue
            if name == "@string/" + SYNC_KEY:
                name = sync_value
            elif name.startswith("@"):
                raise arsc.TrialError("UNRESOLVED_PROVIDER_AUTHORITY_RESOURCE")
            if name in names:
                raise arsc.TrialError("DUPLICATE_PROVIDER_AUTHORITY")
            names.add(name)
    return names


# These TWO custom permissions are already owned by the publisher-signed
# original, with Android signature protection. For a disposable install-only
# research clone, OMIT duplicate DECLARATIONS; keep original ownership and all
# uses-permission requests unchanged (thus cross-signature access is NOT granted).
# This is never used in the structural baseline or a distributed application.
SHADOWED_SIGNATURE_PERMISSIONS = {
    "com.yandex.permission.READ_CREDENTIALS",
    "com.yandex.music.RELAY_PERMISSION",
}


def omit_shadowed_signature_permission_declarations(manifest_bytes):
    root = source.ET.fromstring(manifest_bytes)
    omitted = set()
    for child in list(root):
        if child.tag != "permission":
            continue
        name = child.attrib.get(ANDROID + "name", "")
        if name not in SHADOWED_SIGNATURE_PERMISSIONS:
            continue
        if child.attrib.get(ANDROID + "protectionLevel") != "signature":
            raise arsc.TrialError("SHADOWED_PERMISSION_PROTECTION_LEVEL_DRIFT")
        root.remove(child)
        omitted.add(name)
    if omitted != SHADOWED_SIGNATURE_PERMISSIONS:
        raise arsc.TrialError("SIGNED_DUPLICATE_PERMISSION_SET_DRIFT")
    # Signature-protected uses-permission entries remain intact; do not silently
    # rewrite them into clone-owned permissions or bypass issuer signature.
    used = {child.attrib.get(ANDROID + "name") for child in root.iter()
            if child.tag in ("uses-permission", "uses-permission-sdk-23")}
    if "com.yandex.permission.READ_CREDENTIALS" not in used:
        raise arsc.TrialError("ORIGINAL_SIGNATURE_PERMISSION_REQUEST_CHANGED")
    return source.ET.tostring(root, encoding="utf-8", xml_declaration=True), len(omitted)


def classify_clone_launch_logcat(raw):
    """Report bounded public Java CLASS names and flags only, never raw log text.

    No arbitrary message, exception stack, URL, token or process metadata can
    escape in this result. All names must match package/class grammar and
    preapproved non-personal Java namespace prefixes.
    """
    import re
    raw_candidates = []
    patterns = (
        r'Didn.t find class "([A-Za-z0-9_.$/]+)"',
        r'Failed resolution of: L([A-Za-z0-9_$/]+);',
        r'(?:ClassNotFoundException|NoClassDefFoundError):\s*(?:class\s+)?([A-Za-z0-9_.$/]+)',
    )
    for regex in patterns:
        raw_candidates.extend(re.findall(regex, raw, flags=re.IGNORECASE))
    allowed = ("com.yandex.", "ru.yandex.", "pro.celikom.",
               "androidx.", "android.", "com.google.", "kotlin.",
               "org.jetbrains.", "org.chromium.")
    class_hints = []
    for candidate in raw_candidates:
        name = candidate.replace("/", ".")
        if (len(name) < 8 or len(name) > 180 or
                not name.startswith(allowed) or
                not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_.$]*", name)):
            continue
        if name not in class_hints:
            class_hints.append(name)
        if len(class_hints) >= 4:
            break
    return {
        "bounded_missing_public_class_hints": class_hints,
        "fatal_exception_seen": "FATAL EXCEPTION" in raw,
        "clone_process_named_in_crash": "Process: " + source.DEST in raw,
        "security_exception_seen": "SecurityException" in raw,
        "class_loading_exception_seen": (
            "ClassNotFoundException" in raw or "NoClassDefFoundError" in raw),
        "native_library_error_seen": "UnsatisfiedLinkError" in raw,
        "dex_verify_error_seen": "VerifyError" in raw,
        "resources_inflation_error_seen": "InflateException" in raw,
        "illegal_state_error_seen": "IllegalStateException" in raw,
        "permission_denial_seen": "Permission Denial" in raw,
        "runtime_exception_seen": "RuntimeException" in raw,
        "raw_log_included": False
    }


def run():
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise arsc.TrialError("CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-five-split-identity-") as td:
        work = Path(td)
        archive = work / "signed-pinned.xapk"
        size, sha = source.gpr.download(archive)
        if size != 60433885 or sha != source.ARCHIVE_SHA:
            raise arsc.TrialError("PINNED_ARCHIVE_CHANGED")
        apks = source.gpr.split_apks(archive, work)
        if len(apks) != 5:
            raise arsc.TrialError("FIVE_SPLITS_REQUIRED")
        source.gpr.inspect_publisher(apks)
        editor = work / "APKEditor.jar"
        arsc.download_editor(editor)
        key = work / "ephemeral.jks"
        arsc.run(["keytool", "-genkeypair", "-storetype", "JKS",
                  "-keystore", str(key), "-storepass", "ephemeral-lab-only",
                  "-keypass", "ephemeral-lab-only", "-alias", "research",
                  "-keyalg", "RSA", "-keysize", "2048", "-validity", "1",
                  "-dname", "CN=CELIKOM Non-distributable Lab, O=CELIKOM, C=XX"],
                 "IDENTITY_LAB_KEY", 60)
        original_splits, modified_splits = set(), set()
        clone_output_apks = []
        total_passport_provider_rewrites = 0
        total_dex_literal_rewrites = 0
        total_resource_rewrites = 0
        omitted_permission_declarations = 0
        omit_shadowed = os.getenv("CELIKOM_OMIT_SHADOWED_SIGNATURE_DECLS") == "1"
        if omit_shadowed and os.getenv("CELIKOM_CLEAN_ANDROID_ARMV7_TRANSLATION") != "1":
            raise arsc.TrialError("SHADOWED_SIGNATURE_TEST_REQUIRES_DISPOSABLE_X86_ARMV7")
        for i, apk in enumerate(apks):
            meta = source.apkmeta(apk)
            if meta.get("name") != source.SOURCE or meta.get("versionCode") != "24026531":
                raise arsc.TrialError("SOURCE_SPLIT_VERSION_DRIFT")
            split = meta.get("split", "")
            original_splits.add(split)
            decoded = work / ("decoded-" + str(i))
            arsc.run(["java", "-Xmx3g", "-jar", str(editor), "d", "-t", "xml",
                      "-dex", "-i", str(apk), "-o", str(decoded)],
                     "IDENTITY_DECODE_SPLIT_" + str(i), 240)
            manifest = decoded / "AndroidManifest.xml"
            publisher_manifest = manifest.read_bytes()
            initial, _ = source.rewrite_manifest(publisher_manifest.decode("utf-8"))
            next_manifest, rewritten = rewrite_passport_and_metrica(initial)
            # Only the BASE APK declares app-level custom permissions;
            # config splits must NOT be forced to have those declarations.
            if omit_shadowed and not split:
                next_manifest, count = omit_shadowed_signature_permission_declarations(next_manifest)
                omitted_permission_declarations += count
            publisher_auths = resolved_provider_authorities(publisher_manifest, OLD_SYNC)
            clone_auths = resolved_provider_authorities(next_manifest, NEW_SYNC)
            if publisher_auths & clone_auths:
                raise arsc.TrialError("SIDE_BY_SIDE_PROVIDER_AUTHORITY_COLLISION")
            if len(publisher_auths) != len(clone_auths):
                raise arsc.TrialError("PROVIDER_AUTHORITY_COUNT_DRIFT")
            manifest.write_bytes(next_manifest)
            total_passport_provider_rewrites += rewritten
            resource_changes = replace_sync_resource(decoded)
            total_resource_rewrites += len(resource_changes)

            patched_source_dexes = {}
            with zipfile.ZipFile(apk) as original_zip:
                src_dex = {n: original_zip.read(n) for n in original_zip.namelist()
                           if n.startswith("classes") and n.endswith(".dex")}
            # Copy-mode dex entries can be located in the decoded root or a raw subdir.
            for file in decoded.rglob("classes*.dex"):
                relative = file.name
                if relative not in src_dex or relative in patched_source_dexes:
                    raise arsc.TrialError("DEX_PATH_OR_DUPLICATE_MISMATCH")
                original_bytes = src_dex[relative]
                if file.read_bytes() != original_bytes:
                    raise arsc.TrialError("SOURCE_DECODE_CHANGED_DEX")
                edited, patched = patch_one_dex(original_bytes)
                file.write_bytes(edited)
                patched_source_dexes[relative] = edited
                total_dex_literal_rewrites += int(patched)
            if set(patched_source_dexes) != set(src_dex):
                raise arsc.TrialError("DECODED_DEX_SET_DRIFT")
            unsigned = work / ("unsigned-" + str(i) + ".apk")
            arsc.run(["java", "-Xmx3g", "-jar", str(editor), "b", "-t", "xml",
                      "-i", str(decoded), "-o", str(unsigned)],
                     "IDENTITY_BUILD_SPLIT_" + str(i), 300)
            aligned = work / ("aligned-" + str(i) + ".apk")
            arsc.run([source.sdk_tool("zipalign"), "-f", "-p", "4",
                      str(unsigned), str(aligned)], "IDENTITY_ZIPALIGN", 75)
            arsc.run([source.sdk_tool("apksigner"), "sign",
                      "--ks", str(key), "--ks-pass", "pass:ephemeral-lab-only",
                      "--ks-key-alias", "research",
                      "--key-pass", "pass:ephemeral-lab-only",
                      "--min-sdk-version", "28", "--v4-signing-enabled", "false",
                      str(aligned)], "IDENTITY_SIGN", 80)
            cert = arsc.run([source.sdk_tool("apksigner"), "verify",
                             "--print-certs", str(aligned)],
                            "IDENTITY_VERIFY_SIGNATURE", 60)
            signer_lines = [x for x in cert.splitlines()
                            if "certificate SHA-256 digest:" in x]
            if len(signer_lines) != 1:
                raise arsc.TrialError("IDENTITY_SIGNER_COUNT_DRIFT")
            new_fingerprint = signer_lines[0].split("digest:", 1)[-1].strip().replace(":", "").lower()
            if len(new_fingerprint) != 64 or new_fingerprint == source.RUSTORE_SHA256_CERT:
                raise arsc.TrialError("IDENTITY_SIGNER_NOT_INDEPENDENT")
            new_meta = source.apkmeta(aligned)
            if (new_meta.get("name") != source.DEST or
                new_meta.get("split", "") != split or
                new_meta.get("versionCode") != "24026531"):
                raise arsc.TrialError("IDENTITY_SPLIT_METADATA_DRIFT")
            with zipfile.ZipFile(apk) as old_zip, zipfile.ZipFile(aligned) as new_zip:
                if not split:
                    # Compare only public Android application loader flags from
                    # the actually compiled signed manifests (not XML source).
                    def compiled_loader_flags(target, stage):
                        dump = arsc.run(
                            [source.sdk_tool("aapt"), "dump", "xmltree",
                             str(target), "AndroidManifest.xml"],
                            stage, 70)
                        allowed = ("android:hasCode(", "android:useEmbeddedDex(",
                                   "android:extractNativeLibs(",
                                   "android:isolatedSplits(",
                                   "android:classLoader(")
                        return sorted(line.strip()[:180] for line in dump.splitlines()
                                      if "A: " in line and
                                      any(tag in line for tag in allowed))
                    original_flags = compiled_loader_flags(apk, "ORIGINAL_COMPILED_MANIFEST")
                    clone_flags = compiled_loader_flags(aligned, "CLONE_COMPILED_MANIFEST")
                    print(json.dumps({
                        "compiled_application_loader_flags_original": original_flags,
                        "compiled_application_loader_flags_clone": clone_flags,
                        "compiled_flags_preserved": original_flags == clone_flags
                    },sort_keys=True))
                    dex_storage = {}
                    for dex_name in sorted(src_dex):
                        original_entry = old_zip.getinfo(dex_name)
                        rebuilt_entry = new_zip.getinfo(dex_name)
                        dex_storage[dex_name] = {
                            "original_zip_compression": original_entry.compress_type,
                            "clone_zip_compression": rebuilt_entry.compress_type,
                            "original_size": original_entry.file_size,
                            "clone_size": rebuilt_entry.file_size,
                            "compression_preserved": original_entry.compress_type == rebuilt_entry.compress_type
                        }
                    print(json.dumps({"base_dex_zip_storage_audit": dex_storage,
                                      "raw_apk_bytes_published": False}, sort_keys=True))
                for path in old_zip.namelist():
                    if path.startswith("lib/") and path.endswith(".so"):
                        if old_zip.read(path) != new_zip.read(path):
                            raise arsc.TrialError("IDENTITY_NATIVE_LIBRARY_DRIFT")
                    if path in src_dex:
                        if patched_source_dexes[path] != new_zip.read(path):
                            raise arsc.TrialError("IDENTITY_UNEXPECTED_DEX_DIFFERENCES")
            modified_splits.add(split)
            clone_output_apks.append(aligned)
            print(json.dumps({"split_index": i, "built_and_verified": True,
                              "dex_patch_count_total": total_dex_literal_rewrites,
                              "provider_identity_rewrites_total": total_passport_provider_rewrites}))
        if original_splits != modified_splits or len(modified_splits) != 5:
            raise arsc.TrialError("IDENTITY_FIVE_SPLIT_SET_DRIFT")
        if total_passport_provider_rewrites != 4:
            raise arsc.TrialError("IDENTITY_PROVIDER_REWRITE_COUNT_DRIFT")
        if total_resource_rewrites != 1:
            raise arsc.TrialError("IDENTITY_SYNC_RESOURCE_COUNT_DRIFT")
        if total_dex_literal_rewrites != 1:
            raise arsc.TrialError("IDENTITY_DEX_LITERAL_COUNT_DRIFT")
        if omit_shadowed and omitted_permission_declarations != 2:
            raise arsc.TrialError("SHADOWED_SIGNATURE_PERMISSION_COUNT_DRIFT")
        emulator_runtime = {}
        native_arm = os.getenv("CELIKOM_CLEAN_ARM_EMULATOR") == "1"
        translated_x64 = os.getenv("CELIKOM_CLEAN_ANDROID_TRANSLATION") == "1"
        translated_x86_armv7 = os.getenv("CELIKOM_CLEAN_ANDROID_ARMV7_TRANSLATION") == "1"
        if sum((native_arm, translated_x64, translated_x86_armv7)) > 1:
            raise arsc.TrialError("RUNTIME_MODE_AMBIGUOUS")
        if native_arm or translated_x64 or translated_x86_armv7:
            # Disposable GitHub Android emulator ONLY. No owner device, login,
            # Play Protect bypass, LSPatch, media playback or modified vendor
            # APK distribution. Translation is NOT ARM-device compatibility.
            import time
            abi = arsc.run(["adb", "shell", "getprop", "ro.product.cpu.abilist"],
                           "ANDROID_EMULATOR_ABI", 30).strip()
            bridge = arsc.run(["adb", "shell", "getprop", "ro.dalvik.vm.native.bridge"],
                              "ANDROID_NATIVE_BRIDGE", 30).strip()
            if translated_x64:
                if "x86_64" not in abi or "arm64-v8a" not in abi:
                    raise arsc.TrialError("API35_X64_ARM64_TRANSLATION_UNAVAILABLE")
                if not bridge or bridge in ("0", "false"):
                    raise arsc.TrialError("API35_X64_NATIVE_BRIDGE_UNAVAILABLE")
            elif translated_x86_armv7:
                if "x86" not in abi.split(",") or "armeabi-v7a" not in abi.split(","):
                    raise arsc.TrialError("API30_X86_ARMV7_TRANSLATION_UNAVAILABLE")
                if not bridge or bridge in ("0", "false"):
                    raise arsc.TrialError("API30_X86_NATIVE_BRIDGE_UNAVAILABLE")
            elif "arm64-v8a" not in abi or "x86_64" in abi:
                raise arsc.TrialError("NATIVE_ARM64_RUNTIME_REQUIRED")
            arsc.run(["adb", "install-multiple", *[str(p) for p in apks]],
                     "ARM_INSTALL_PUBLISHER_ORIGINAL", 240)
            if os.getenv("CELIKOM_ORIGINAL_CONTROL_LAUNCH") == "1":
                # Unmodified publisher app is a control. If it fails on the
                # same translated emulator, a clone crash alone proves nothing.
                # Explicit signed launcher activity; monkey with one random
                # event could press BACK and spuriously make the process exit.
                arsc.run(["adb", "shell", "am", "start", "-W",
                          "-a", "android.intent.action.MAIN",
                          "-c", "android.intent.category.LAUNCHER",
                          "-n", source.SOURCE + "/ru.yandex.music.main.MainScreenActivity"],
                         "ORIGINAL_CONTROL_DIRECT_LAUNCH", 60)
                time.sleep(5)
                original_pid = arsc.run(
                    ["adb", "shell", "pidof " + source.SOURCE + " || true"],
                    "ORIGINAL_CONTROL_PROCESS_PROBE", 30).strip()
                if not original_pid:
                    original_raw = arsc.run(
                        ["adb", "logcat", "-d", "-v", "brief", "-t", "1000",
                         "-s", "AndroidRuntime:E", "ActivityManager:W",
                         "ActivityTaskManager:W"],
                        "ORIGINAL_CONTROL_SAFE_CRASH_CLASSIFICATION", 35)
                    hints = classify_clone_launch_logcat(original_raw)
                    print(json.dumps({
                        "original_control_runtime": "PROCESS_NOT_ALIVE",
                        "original_crash_categories": hints,
                        "original_publisher_signature_untouched": True,
                        "clone_installed": False,
                        "raw_logs_published": False
                    },sort_keys=True))
                    raise arsc.TrialError("ORIGINAL_CONTROL_PROCESS_NOT_ALIVE")
                print(json.dumps({
                    "original_control_runtime": "PROCESS_ALIVE_AFTER_LAUNCH",
                    "original_signature_untouched": True,
                    "login_tested": False, "audio_tested": False}))
            arsc.run(["adb", "install-multiple", *[str(p) for p in clone_output_apks]],
                     "ARM_INSTALL_TEST_CLONE", 240)
            original_paths = arsc.run(["adb", "shell", "pm", "path", source.SOURCE],
                                      "ARM_PM_ORIGINAL", 40)
            clone_paths = arsc.run(["adb", "shell", "pm", "path", source.DEST],
                                   "ARM_PM_CLONE", 40)
            original_count = sum(x.startswith("package:") for x in original_paths.splitlines())
            clone_count = sum(x.startswith("package:") for x in clone_paths.splitlines())
            if original_count != 5 or clone_count != 5:
                raise arsc.TrialError("ARM_SIDE_BY_SIDE_SPLIT_COUNT_INVALID")
            if omit_shadowed:
                package_dump = arsc.run(["adb", "shell", "dumpsys", "package", source.DEST],
                                        "CLONE_SIGNATURE_PERMISSION_AUDIT", 45)
                # Only check an explicit positive grant: if a different-signer
                # clone somehow receives credential permission, fail immediately.
                if __import__("re").search(
                    r"com\.yandex\.permission\.READ_CREDENTIALS\s*:\s*granted=true",
                    package_dump):
                    raise arsc.TrialError("CLONE_RECEIVED_UNAUTHORIZED_CREDENTIAL_PERMISSION")
            print(json.dumps({"emulator_install_gate": "SIDE_BY_SIDE_5_AND_5_PASS",
                              "owner_phone_touched": False, "credential_use": False}))
            arsc.run(["adb", "shell", "am", "start", "-W",
                      "-a", "android.intent.action.MAIN",
                      "-c", "android.intent.category.LAUNCHER",
                      "-n", source.DEST + "/ru.yandex.music.main.MainScreenActivity"],
                     "ARM_CLONE_DIRECT_LAUNCH", 60)
            time.sleep(5)
            # pidof normally exits nonzero when app crashed; this is a
            # diagnostic case, not a subprocess invocation failure.
            pid = arsc.run(["adb", "shell", "pidof " + source.DEST + " || true"],
                           "ARM_CLONE_PROCESS_PROBE", 30).strip()
            if not pid:
                # Read only limited system crash tags on an empty, unauthenticated
                # emulator. Emit ONLY boolean classifications, never raw logs,
                # URLs, requests, tokens, stack traces or account contents.
                raw_crashes = arsc.run(
                    ["adb", "logcat", "-d", "-v", "brief", "-t", "1000",
                     "-s", "AndroidRuntime:E", "ActivityManager:W",
                     "ActivityTaskManager:W"],
                    "ARM_CLONE_PRIVACY_SAFE_CRASH_CLASSIFICATION", 35)
                print(json.dumps({
                    "clone_launch_result": "PROCESS_NOT_ALIVE",
                    "crash_classification": classify_clone_launch_logcat(raw_crashes),
                    "original_publisher_app_unmodified": True,
                    "owner_phone_touched": False,
                    "raw_log_published": False
                }, sort_keys=True))
                raise arsc.TrialError("ARM_CLONE_PROCESS_NOT_ALIVE")
            emulator_runtime = {
                "clean_arm_emulator_side_by_side_installed": True,
                "original_split_count": original_count,
                "clone_split_count": clone_count,
                "clone_process_alive_after_launch": True,
                "emulator_abi": abi,
                "arm_binary_translation": translated_x64 or translated_x86_armv7,
                "translation_abi": ("armeabi-v7a" if translated_x86_armv7 else
                                    "arm64-v8a" if translated_x64 else "native-arm64"),
                "native_bridge_present": bool(bridge) and bridge not in ("0", "false")
            }
        result = {
            "verdict": "FIVE_SPLIT_IDENTITY_STRUCTURAL_PASS_ONLY",
            "split_count": 5,
            "manifest_passport_metrica_provider_rewrites": total_passport_provider_rewrites,
            "passport_sync_resource_rewrites": total_resource_rewrites,
            "single_reversible_appmetrica_dex_literal_rewrite": True,
            "resolved_original_vs_clone_provider_collisions": 0,
            "shadowed_signature_declarations_omitted_in_install_only_clone": omitted_permission_declarations,
            "issuer_permission_protection_not_weakened": True,
            "published_vendor_apks": False,
            "installed_on_owner_phone": False,
            "app_auth_or_login_tested": False,
            "fileinfo_decoder_proven": False,
            "native_audio_tested": False,
            "play_protect_tested": False
        }
        if emulator_runtime:
            result.update(emulator_runtime)
            result["verdict"] = (
                "SIDE_BY_SIDE_X86_ARMV7_TRANSLATED_INSTALL_LAUNCH_ONLY"
                if translated_x86_armv7 else
                "SIDE_BY_SIDE_X64_ARM_TRANSLATED_INSTALL_LAUNCH_ONLY"
                if translated_x64 else
                "SIDE_BY_SIDE_ARM_EMULATOR_INSTALL_AND_LAUNCH_PASS_NOT_AUDIO")
    return result


if __name__ == "__main__":
    try:
        print(json.dumps(run(), sort_keys=True))
    except arsc.TrialError as e:
        print(json.dumps({"verdict": "FIVE_SPLIT_IDENTITY_BLOCKED",
                          "stage": e.stage, "diagnostic": e.hints,
                          "published_vendor_apks": False}))
        sys.exit(2)
    except Exception as e:
        print(json.dumps({"verdict": "FIVE_SPLIT_IDENTITY_BLOCKED",
                          "stage": "UNEXPECTED_"+type(e).__name__.upper(),
                          "published_vendor_apks": False}))
        sys.exit(2)
