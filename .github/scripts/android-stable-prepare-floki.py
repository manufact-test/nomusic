#!/usr/bin/env python3
"""Prepare an immutable private Android stable candidate, not a public release."""
import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import tempfile

ORIGIN = "https://celikom.com"
OLD_ORIGIN = "https://lemonchiffon-narwhal-791953.hostingersite.com"
PACKAGE = "pro.celikom.nativeprobe"
SIGNER = "67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f"
MAX_APK = 200 * 1024 * 1024
FIELDS = {"schemaVersion", "enabled", "channel", "packageName", "versionCode",
          "versionName", "signerSha256", "apkSha256", "sizeBytes", "minSdk",
          "apkUrl", "notesRu"}


def require(ok, code):
    if not ok:
        raise ValueError(code)


def regular(path, low, high):
    st = path.lstat()
    require(stat.S_ISREG(st.st_mode) and low <= st.st_size <= high, "APK_FILE_BOUNDS")
    return st


def unique_json(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "MANIFEST_DUPLICATE_FIELD")
        result[key] = value
    return result


def load_manifest(path):
    regular(path, 100, 16384)
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_json)


def validate_manifest(m, origin=ORIGIN):
    require(isinstance(m, dict) and set(m) == FIELDS, "MANIFEST_FIELDS")
    require(type(m["schemaVersion"]) is int and m["schemaVersion"] == 1
            and m["enabled"] is True and m["channel"] == "stable"
            and m["packageName"] == PACKAGE and m["signerSha256"] == SIGNER,
            "MANIFEST_IDENTITY")
    require(type(m["versionCode"]) is int and 1 <= m["versionCode"] <= 2147483647
            and isinstance(m["versionName"], str) and
            re.fullmatch(r"0\.3\.[0-9]{1,4}", m["versionName"]), "MANIFEST_VERSION")
    require(type(m["sizeBytes"]) is int and 100000 <= m["sizeBytes"] <= MAX_APK
            and type(m["minSdk"]) is int and m["minSdk"] == 28
            and isinstance(m["apkSha256"], str)
            and re.fullmatch(r"[a-f0-9]{64}", m["apkSha256"]), "MANIFEST_MEDIA")
    require(isinstance(m["notesRu"], str) and len(m["notesRu"].encode("utf-16-le")) <= 1600
            and "<" not in m["notesRu"] and ">" not in m["notesRu"], "MANIFEST_NOTES")
    require(origin in (ORIGIN, OLD_ORIGIN) and m["apkUrl"] ==
            f'{origin}/releases/android/{m["versionCode"]}-{m["apkSha256"]}.apk',
            "MANIFEST_URL")
    return m


def verify_tool_output(signature, badging, m):
    # apksigner must itself have exited successfully before parsing its proof.
    require(re.findall(r"(?m)^Signer #(\d+) certificate SHA-256 digest: ([a-fA-F0-9]{64})\s*$",
                       signature) == [("1", SIGNER)], "APK_SIGNER")
    for scheme in ("v2", "v3"):
        require(re.search(r"(?m)^Verified using " + scheme +
                          r" scheme \([^\r\n]+\): true\s*$", signature), "APK_SIGNATURE_" + scheme)
    package = re.findall(r"(?m)^package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", badging)
    require(package == [(PACKAGE, str(m["versionCode"]), m["versionName"])], "APK_PACKAGE_VERSION")
    sdk = re.findall(r"(?m)^sdkVersion:'([0-9]+)'\s*$", badging)
    require(len(sdk) == 1 and 1 <= int(sdk[0]) <= m["minSdk"], "APK_MIN_SDK")


def run_tool(args):
    result = subprocess.run([str(x) for x in args], check=True, capture_output=True,
                            text=True, encoding="utf-8", timeout=120)
    require(len(result.stdout) <= 2 * 1024 * 1024, "APK_TOOL_OUTPUT_LIMIT")
    return result.stdout


def apk_digest(path):
    before = regular(path, 100000, MAX_APK)
    with path.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()
    after = regular(path, 100000, MAX_APK)
    require((before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns), "APK_CHANGED")
    return after.st_size, digest


def verify_apk(path, m, apksigner, aapt):
    validate_manifest(m)
    require(apk_digest(path) == (m["sizeBytes"], m["apkSha256"]), "APK_HASH_SIZE")
    signature = run_tool([apksigner, "verify", "--verbose", "--print-certs",
                          "--min-sdk-version", "28", path.resolve()])
    badging = run_tool([aapt, "dump", "badging", path.resolve()])
    verify_tool_output(signature, badging, m)
    require(apk_digest(path) == (m["sizeBytes"], m["apkSha256"]), "APK_CHANGED")


def prepare(current, apk, output, version, code, notes, apksigner, aapt):
    prior = load_manifest(current)
    # During migration the independently preserved legacy manifest is still valid
    # as a sequence floor. No network or live Hostinger access is required.
    validate_manifest(prior, OLD_ORIGIN if prior.get("apkUrl", "").startswith(OLD_ORIGIN + "/") else ORIGIN)
    require(type(code) is int and code > prior["versionCode"], "APK_VERSION_NOT_INCREASING")
    require(not output.exists() and not output.is_symlink(), "CANDIDATE_EXISTS")
    parent = output.parent
    st = parent.lstat()
    require(stat.S_ISDIR(st.st_mode) and st.st_uid == os.getuid() and not st.st_mode & 0o077,
            "CANDIDATE_PARENT_NOT_PRIVATE")
    size, digest = apk_digest(apk)
    name = f"{code}-{digest}.apk"
    m = dict(schemaVersion=1, enabled=True, channel="stable", packageName=PACKAGE,
             versionCode=code, versionName=version, signerSha256=SIGNER,
             apkSha256=digest, sizeBytes=size, minSdk=28,
             apkUrl=ORIGIN + "/releases/android/" + name, notesRu=notes)
    validate_manifest(m)
    work = pathlib.Path(tempfile.mkdtemp(prefix=".android-candidate-", dir=parent))
    try:
        staged = work / name
        shutil.copyfile(apk, staged)
        staged.chmod(0o600)
        verify_apk(staged, m, apksigner, aapt)
        manifest = work / "stable.json"
        manifest.write_text(json.dumps(m, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        manifest.chmod(0o600)
        # mkdir is an exclusive reservation; do not overwrite any prior candidate.
        output.mkdir(mode=0o700)
        try:
            os.rename(staged, output / name)
            os.rename(manifest, output / "stable.json")
        except BaseException:
            shutil.rmtree(output)
            raise
    finally:
        shutil.rmtree(work)
    return m


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="mode", required=True)
    check = sub.add_parser("verify")
    check.add_argument("--manifest", type=pathlib.Path, required=True)
    check.add_argument("--apk", type=pathlib.Path, required=True)
    stage = sub.add_parser("prepare")
    stage.add_argument("--current", type=pathlib.Path, required=True)
    stage.add_argument("--apk", type=pathlib.Path, required=True)
    stage.add_argument("--output", type=pathlib.Path, required=True)
    stage.add_argument("--version", required=True)
    stage.add_argument("--code", type=int, required=True)
    stage.add_argument("--notes", default="")
    for s in (check, stage):
        s.add_argument("--apksigner", type=pathlib.Path, required=True)
        s.add_argument("--aapt", type=pathlib.Path, required=True)
    args = p.parse_args()
    if args.mode == "verify":
        m = load_manifest(args.manifest)
        verify_apk(args.apk, m, args.apksigner, args.aapt)
    else:
        m = prepare(args.current, args.apk, args.output, args.version, args.code,
                    args.notes, args.apksigner, args.aapt)
    print("CELIKOM_ANDROID_PRIVATE_CANDIDATE_VERIFIED", m["versionCode"], m["apkSha256"])


if __name__ == "__main__":
    main()
