"""Build a genuinely separate, signed CELIKOM Test APK.

This isolated path never changes stable release metadata and never publishes to an OTA endpoint.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
import xml.etree.ElementTree as ET

from release_archive import inspect_zip

ROOT = Path(__file__).resolve().parent
SPEC = json.loads((ROOT / "test-app-spec.json").read_text(encoding="utf-8"))
UPDATER_SOURCES = {"UpdateCenter.java", "UpdateCheckJob.java", "UpdateInstallReceiver.java"}
ANDROID_NS = "http://schemas.android.com/apk/res/android"
A = "{" + ANDROID_NS + "}"


def run(command, **kwargs):
    subprocess.run(list(map(str, command)), check=True, **kwargs)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_fingerprint(source_root, included_only=True):
    files = sorted(Path(source_root).rglob("*.java"))
    if included_only:
        files = [p for p in files if p.name not in UPDATER_SOURCES]
    digests = {str(p.relative_to(source_root)): sha(p) for p in files}
    return hashlib.sha256(json.dumps(digests, sort_keys=True).encode("utf-8")).hexdigest()


def replace_once(path, old, new, label):
    content = path.read_text(encoding="utf-8")
    count = content.count(old)
    if count != 1:
        raise ValueError(f"Expected exactly one {label} source marker; found {count}")
    path.write_text(content.replace(old, new), encoding="utf-8")


def patch_test_sources(source_root):
    activity = source_root / "pro/celikom/nativeprobe/identitydiag/RecorderActivity.java"
    replace_once(
        activity,
        "TextView status,mark,access,track,version,accountNote,reportNote;UpdateCenter updateCenter;",
        "TextView status,mark,access,track,version,accountNote,reportNote;",
        "updater field",
    )
    replace_once(
        activity,
        'label(updatesPanel,"Обновления CELIKOM",15,FG);updateCenter=new UpdateCenter(this,updatesPanel);',
        'label(updatesPanel,"Тестовая сборка · автоматические обновления отключены",13,MUTED);',
        "updater panel constructor",
    )
    replace_once(
        activity,
        'TextView brand=label(header,"CELIKOM",19,FG);',
        'TextView brand=label(header,"CELIKOM Test",19,FG);',
        "test app header label",
    )
    authority_literals = {
        SPEC["stable_package"] + ".package-export": SPEC["file_provider_authority"],
        SPEC["stable_package"] + ".androidx-startup": SPEC["startup_authority"],
        SPEC["stable_package"] + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION": SPEC["test_permission"],
    }
    for path in source_root.rglob("*.java"):
        source = path.read_text(encoding="utf-8")
        updated = source
        for old, new in authority_literals.items():
            updated = updated.replace(old, new)
        if updated != source:
            path.write_text(updated, encoding="utf-8")
    for path in source_root.rglob("*.java"):
        source = path.read_text(encoding="utf-8")
        for old in authority_literals:
            if old in source:
                raise ValueError(f"Stable authority literal remains in Java source: {path}:{old}")

    app_version = source_root / "pro/celikom/nativeprobe/identitydiag/AppVersion.java"
    replace_once(
        app_version,
        'static final String NAME="0.3.85";',
        'static final String NAME="0.3.85-test";',
        "test app version",
    )

    for path in source_root.rglob("*.java"):
        if path.name in UPDATER_SOURCES:
            continue
        source = path.read_text(encoding="utf-8")
        for forbidden in ("UpdateCenter", "UpdateCheckJob", "UpdateInstallReceiver"):
            if forbidden in source:
                raise ValueError(f"Updater reference remains in test source: {path}:{forbidden}")


def patch_manifest(decoded):
    manifest = decoded / "AndroidManifest.xml"
    ET.register_namespace("android", ANDROID_NS)
    tree = ET.parse(manifest)
    root = tree.getroot()
    if root.get("package") != SPEC["stable_package"]:
        raise ValueError("Pinned baseline manifest package is unexpected")
    root.set("package", SPEC["package"])

    permission_count = 0
    uses_permission_count = 0
    for node in root:
        if node.tag not in ("permission", "uses-permission"):
            continue
        if node.get(A + "name") == SPEC["stable_package"] + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION":
            node.set(A + "name", SPEC["test_permission"])
            if node.tag == "permission":
                permission_count += 1
            else:
                uses_permission_count += 1
    if permission_count != 1 or uses_permission_count != 1:
        raise ValueError("Could not isolate the AndroidX dynamic receiver signature permission")

    app = root.find("application")
    if app is None:
        raise ValueError("Baseline manifest has no application element")
    app.set(A + "label", SPEC["label"])
    app.set(A + "icon", "@drawable/celikom_test_icon")

    file_provider_count = 0
    startup_count = 0
    authorities = []
    for provider in app.findall("provider"):
        name = provider.get(A + "name")
        if name == "androidx.core.content.FileProvider":
            provider.set(A + "authorities", SPEC["file_provider_authority"])
            file_provider_count += 1
        elif name == "androidx.startup.InitializationProvider":
            provider.set(A + "authorities", SPEC["startup_authority"])
            startup_count += 1
        authority = provider.get(A + "authorities")
        if authority:
            authorities.append(authority)
    if file_provider_count != 1 or startup_count != 1:
        raise ValueError("Expected exactly one FileProvider and one AndroidX Startup provider")
    if len(authorities) != len(set(authorities)):
        raise ValueError("Duplicate provider authorities in test manifest")
    if set(authorities) != {SPEC["file_provider_authority"], SPEC["startup_authority"]}:
        raise ValueError("Unexpected provider authority in test manifest")

    forbidden_permissions = {
        "android.permission.REQUEST_INSTALL_PACKAGES",
    }
    for node in root.findall("uses-permission"):
        if node.get(A + "name") in forbidden_permissions:
            raise ValueError("Test APK must not request package-install permission")

    component_names = [
        node.get(A + "name", "")
        for node in app.iter()
        if node.tag in ("activity", "service", "receiver", "provider")
    ]
    if any(name.endswith("UpdateCheckJob") or name.endswith("UpdateInstallReceiver") for name in component_names):
        raise ValueError("Updater components must not be registered in the test manifest")

    tree.write(manifest, encoding="utf-8", xml_declaration=True)


def patch_apktool_metadata(decoded):
    path = decoded / "apktool.yml"
    content = path.read_text(encoding="utf-8")
    content, code_count = re.subn(
        r"(?m)^([ \t]*)versionCode: [0-9]+[ \t]*$",
        lambda m: m.group(1) + "versionCode: " + str(SPEC["version_code"]),
        content,
    )
    content, name_count = re.subn(
        r"(?m)^([ \t]*)versionName: [^\n]+$",
        lambda m: m.group(1) + "versionName: " + SPEC["version"],
        content,
    )
    if code_count != 1 or name_count != 1:
        raise ValueError("Unexpected baseline Apktool version metadata")
    path.write_text(content, encoding="utf-8")


def patch_smali_identity_and_version(decoded):
    old_to_new = {
        SPEC["stable_package"] + ".package-export": SPEC["file_provider_authority"],
        SPEC["stable_package"] + ".androidx-startup": SPEC["startup_authority"],
        SPEC["stable_package"] + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION": SPEC["test_permission"],
    }
    replacement_counts = {old: 0 for old in old_to_new}
    for path in decoded.rglob("*.smali"):
        original = path.read_text(encoding="utf-8")
        updated = original.replace("0.3.22-probe", SPEC["version"])
        for old, new in old_to_new.items():
            replacement_counts[old] += updated.count(old)
            updated = updated.replace(old, new)
        if path.name == "BuildConfig.smali":
            updated = re.sub(
                r"(\.field public static final VERSION_CODE:I = )0x[0-9a-f]+",
                lambda m: m.group(1) + hex(SPEC["version_code"]),
                updated,
            )
        if updated != original:
            path.write_text(updated, encoding="utf-8")
    for path in decoded.rglob("*.smali"):
        content = path.read_text(encoding="utf-8")
        for old in old_to_new:
            if old in content:
                raise ValueError(f"Stable authority literal remains in smali: {path}:{old}")
    print("Identity literal replacements:", json.dumps(replacement_counts, sort_keys=True))


def patch_test_icon(decoded):
    icon = decoded / "res/drawable/celikom_test_icon.xml"
    icon.parent.mkdir(parents=True, exist_ok=True)
    if icon.exists():
        raise ValueError("Refusing to overwrite a pre-existing test icon resource")
    icon.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="48dp"
    android:height="48dp"
    android:viewportWidth="48"
    android:viewportHeight="48">
    <path
        android:fillColor="#0B1013"
        android:pathData="M0,0h48v48h-48z" />
    <path
        android:fillColor="#66E0BF"
        android:pathData="M24,6 A18,18 0,1,0 24,42 A18,18 0,1,0 24,6 Z" />
    <path
        android:fillColor="#F4C66A"
        android:pathData="M34,33h10v10h-10z" />
    <path
        android:fillColor="#0B1013"
        android:pathData="M29,17 H43 V22 H38.5 V33 H33.5 V22 H29 Z" />
</vector>
""",
        encoding="utf-8",
    )


def patch_legacy_launcher(decoded):
    legacy = decoded / "smali/pro/celikom/nativeprobe/MainActivity.smali"
    text = legacy.read_text(encoding="utf-8")
    redirect = """.method protected onCreate(Landroid/os/Bundle;)V
    .locals 5
    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V
    new-instance v0, Landroid/content/Intent;
    const-class v1, Lpro/celikom/nativeprobe/identitydiag/RecorderActivity;
    invoke-direct {v0, p0, v1}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    invoke-virtual {p0}, Lpro/celikom/nativeprobe/MainActivity;->getIntent()Landroid/content/Intent;
    move-result-object v1
    if-eqz v1, :launch
    invoke-virtual {v1}, Landroid/content/Intent;->getAction()Ljava/lang/String;
    move-result-object v2
    const-string v3, "android.intent.action.SEND"
    invoke-virtual {v3, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :launch
    const-string v2, "android.intent.extra.TEXT"
    invoke-virtual {v1, v2}, Landroid/content/Intent;->getCharSequenceExtra(Ljava/lang/String;)Ljava/lang/CharSequence;
    move-result-object v4
    if-eqz v4, :launch
    invoke-virtual {v0, v3}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;
    const-string v3, "text/plain"
    invoke-virtual {v0, v3}, Landroid/content/Intent;->setType(Ljava/lang/String;)Landroid/content/Intent;
    invoke-virtual {v0, v2, v4}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/CharSequence;)Landroid/content/Intent;
    :launch
    invoke-virtual {p0, v0}, Lpro/celikom/nativeprobe/MainActivity;->startActivity(Landroid/content/Intent;)V
    invoke-virtual {p0}, Lpro/celikom/nativeprobe/MainActivity;->finish()V
    return-void
.end method"""
    text, count = re.subn(
        r"\.method protected onCreate\(Landroid/os/Bundle;\)V.*?\.end method",
        lambda _: redirect,
        text,
        flags=re.S,
    )
    if count != 1:
        raise ValueError("Unexpected legacy launcher layout")
    legacy.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sdk", "build-tools", "apktool", "base-apk", "signing-dir", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--deps-dir", type=Path, default=ROOT / "deps")
    parser.add_argument("--work-dir", type=Path, default=None)
    args = parser.parse_args()

    if args.output.exists() or args.output.resolve() == args.base_apk.resolve():
        parser.error("Output must be a new file and must not overwrite the pinned base APK")
    if "TEST" not in args.output.name.upper():
        parser.error("Test APK filename must visibly include TEST")
    if args.signing_dir.resolve().is_relative_to(ROOT):
        parser.error("Signing material must remain outside the repository")
    if SPEC["package"] == SPEC["stable_package"]:
        parser.error("Test and stable package IDs must differ")
    if SPEC["version_code"] <= 86:
        parser.error("Test versionCode must remain above the installed stable code 86")

    inputs = json.loads((ROOT / "build-inputs.json").read_text(encoding="utf-8"))
    if sha(args.base_apk) != inputs["base_apk_sha256"] or sha(args.base_apk) != SPEC["base_apk_sha256"]:
        raise ValueError("Pinned baseline APK SHA-256 mismatch")
    if sha(args.apktool) != inputs["apktool_sha256"]:
        raise ValueError("Apktool binary SHA-256 mismatch")
    for name, digest in inputs["dependencies"].items():
        if sha(args.deps_dir / name) != digest:
            raise ValueError("Pinned dependency checksum mismatch: " + name)

    for name in ("aapt", "zipalign", "lib/d8.jar", "lib/apksigner.jar"):
        if not (args.build_tools / name).is_file():
            raise FileNotFoundError("Missing Android build tool: " + name)
    android = args.sdk / "platforms/android-36/android.jar"
    if not android.is_file():
        raise FileNotFoundError("Android API 36 platform is missing")
    java_info = subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT, text=True)
    java_match = re.search(r'\bversion "([0-9]+)', java_info)
    if not java_match or int(java_match.group(1)) != inputs["jdk"]:
        raise ValueError("Test APK signing/build requires the pinned JDK 17")

    signing = args.signing_dir.resolve()
    p12 = signing / "celikom-native-probe.p12"
    signing_json = signing / "signing.json"
    if not p12.is_file() or not signing_json.is_file() or not 1000 < p12.stat().st_size < 65536:
        raise ValueError("Original signing inputs are missing or have an unexpected size")
    signing_data = json.loads(signing_json.read_text(encoding="utf-8"))
    if not all(isinstance(signing_data.get(k), str) and signing_data[k] for k in ("alias", "store_password", "key_password")):
        raise ValueError("Original signing metadata is incomplete")

    build_root = ROOT / "addon/build"
    build_root.mkdir(parents=True, exist_ok=True)
    work = args.work_dir.resolve() if args.work_dir else Path(tempfile.mkdtemp(prefix="celikom-test-0385-", dir=build_root))
    work.mkdir(parents=True, exist_ok=True)
    source_root = work / "src"
    if source_root.exists():
        shutil.rmtree(source_root)
    shutil.copytree(ROOT / "addon/src", source_root)
    patch_test_sources(source_root)
    source_digest = source_fingerprint(source_root)

    # Run the unchanged original regression suite, including the frozen seek guard.
    env = {**os.environ, "CELIKOM_ANDROID_DEPS": str(args.deps_dir.resolve())}
    run(["python3", ROOT / "tests/run_engine.py"], env=env)
    run(["python3", ROOT / "tests/check_0385_seek_baseline.py"])

    classes = work / "classes"
    shutil.rmtree(classes, ignore_errors=True)
    classes.mkdir()
    jars = [args.deps_dir / n for n in ("annotation.jar", "common.jar", "guava.jar", "session.jar")]
    classpath = os.pathsep.join(map(str, [android, *jars]))
    sources = sorted(p for p in source_root.rglob("*.java") if p.name not in UPDATER_SOURCES)
    if not sources:
        raise ValueError("No test application Java sources found")
    run([
        "java", "com.sun.tools.javac.Main", "-encoding", "UTF-8",
        "-source", "8", "-target", "8", "-cp", classpath, "-d", classes,
        *sources,
    ])

    test_sources = sorted((ROOT / "addon").glob("Test*.java"))
    tests = work / "tests"
    tests.mkdir(exist_ok=True)
    test_classpath = os.pathsep.join(map(str, [args.deps_dir / "json.jar", classes, android]))
    run([
        "java", "com.sun.tools.javac.Main", "-encoding", "UTF-8",
        "-source", "8", "-target", "8", "-cp", test_classpath, "-d", tests,
        *test_sources,
    ])
    for test in (
        "TestPure", "TestHybrid", "TestContracts", "TestMobileActions",
        "TestAppPresentation", "TestNotifications", "TestDiagnosticArchive",
        "TestAudioTransfer", "TestBufferedAudio", "TestTransitionReadFence",
        "TestTransitionRecovery", "TestRequestPacing", "TestSourceStateWatchdog",
        "TestDiagnosticAccess", "TestIncidentLog", "TestPresencePreview",
        "TestDiagnosticRequest", "TestUpdateState",
    ):
        run([
            "java", "-cp", os.pathsep.join(map(str, [args.deps_dir / "json.jar", classes, tests, android])),
            "pro.celikom.nativeprobe.identitydiag." + test,
        ])

    if source_fingerprint(source_root) != source_digest:
        raise ValueError("Test Java sources changed during compilation/regression")

    addon_jar = work / "celikom-test-addon.jar"
    run(["java", "sun.tools.jar.Main", "--create", "--file", addon_jar, "-C", classes, "."])
    dex_dir = work / "dex"
    shutil.rmtree(dex_dir, ignore_errors=True)
    dex_dir.mkdir()
    d8 = [
        "java", "-Xmx1500m", "-cp", args.build_tools / "lib/d8.jar",
        "com.android.tools.r8.D8", "--min-api", "28", "--lib", android,
        "--output", dex_dir,
    ]
    for jar in jars:
        d8.extend(["--classpath", jar])
    run([*d8, addon_jar])
    compiled_dex = dex_dir / "classes.dex"
    if not compiled_dex.is_file():
        raise ValueError("D8 did not produce the test addon DEX")

    decoded = work / "decoded"
    run(["java", "-jar", args.apktool, "d", args.base_apk, "-o", decoded, "-f"])
    shutil.rmtree(decoded / "smali_classes2", ignore_errors=True)
    patch_manifest(decoded)
    patch_apktool_metadata(decoded)
    patch_smali_identity_and_version(decoded)
    patch_test_icon(decoded)
    patch_legacy_launcher(decoded)

    unsigned = work / "unsigned.apk"
    run(["java", "-jar", args.apktool, "b", decoded, "-o", unsigned])
    addon_apk = work / "with-test-addon.apk"
    with zipfile.ZipFile(unsigned) as source_apk, zipfile.ZipFile(addon_apk, "w") as output_apk:
        names = source_apk.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP entries in rebuilt baseline APK")
        for info in source_apk.infolist():
            if info.filename not in ("classes2.dex", "assets/identity-integration-source.zip"):
                output_apk.writestr(info, source_apk.read(info.filename))
        output_apk.write(compiled_dex, "classes2.dex")

    aligned = work / "aligned-test.apk"
    run([args.build_tools / "zipalign", "-f", "4", addon_apk, aligned])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="celikom-test-sign-") as temporary:
        temporary = Path(temporary)
        store_password = temporary / "store-password"
        key_password = temporary / "key-password"
        store_password.write_text(signing_data["store_password"], encoding="utf-8")
        key_password.write_text(signing_data["key_password"], encoding="utf-8")
        store_password.chmod(0o600)
        key_password.chmod(0o600)
        run([
            "java", "-jar", args.build_tools / "lib/apksigner.jar", "sign",
            "--ks", p12, "--ks-key-alias", signing_data["alias"],
            "--ks-pass", "file:" + str(store_password),
            "--key-pass", "file:" + str(key_password),
            "--out", args.output, aligned,
        ])

    run([
        "python3", ROOT / "verify_test_release.py",
        "--apk", args.output, "--base-apk", args.base_apk,
        "--build-tools", args.build_tools, "--compiled-dex", compiled_dex,
        "--apktool", args.apktool,
    ])
    if source_fingerprint(source_root) != source_digest:
        raise ValueError("Test Java sources changed after APK verification")
    print(json.dumps({
        "apk": str(args.output),
        "apk_sha256": sha(args.output),
        "size_bytes": args.output.stat().st_size,
        "source_fingerprint": source_digest,
        "package": SPEC["package"],
        "version": SPEC["version"],
        "version_code": SPEC["version_code"],
        "stable_published": False,
    }, indent=2))


if __name__ == "__main__":
    main()
