#!/usr/bin/env python3
"""Publish a locally signed CELIKOM Android APK to the private Hostinger store.

Requires aapt and apksigner. Never stores signing keys or credentials.
Run on the same filesystem as the website private store, after uploading the
release candidate via a secure channel. No GitHub Actions auto-deployment.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

PACKAGE = "pro.celikom.nativeprobe"
SIGNER = "67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f"

def evidence(apk, aapt, apksigner, version_code, version_name):
    badging = subprocess.check_output([aapt, "dump", "badging", str(apk)], text=True)
    first = badging.splitlines()[0]
    if ("name='" + PACKAGE + "'") not in first:
        raise ValueError("Package mismatch")
    if ("versionCode='" + str(version_code) + "'") not in first:
        raise ValueError("Version code mismatch")
    if ("versionName='" + version_name + "'") not in first:
        raise ValueError("Version name mismatch")
    signed = subprocess.check_output([apksigner, "verify", "--verbose", "--print-certs", str(apk)], text=True)
    certs = re.findall(r"Signer #\\d+ certificate SHA-256 digest: ([0-9a-fA-F:]+)", signed)
    if len(certs) != 1 or certs[0].replace(":", "").lower() != SIGNER:
        raise ValueError("Original signing identity mismatch")
    if "Verified using v2 scheme (APK Signature Scheme v2): true" not in signed:
        raise ValueError("APK signature v2 missing")
    size = apk.stat().st_size
    if not 100000 <= size <= 200 * 1024 * 1024:
        raise ValueError("Unexpected APK size")
    digest = hashlib.file_digest(apk.open("rb"), "sha256").hexdigest()
    return digest, size

def atomic_write(path, data):
    fd, tmp = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def publish(args):
    if not args.base_url.startswith("https://") or "?" in args.base_url or "#" in args.base_url:
        raise ValueError("HTTPS base URL required")
    from urllib.parse import urlsplit
    parsed = urlsplit(args.base_url)
    if not parsed.hostname or parsed.username or parsed.password or parsed.path not in ("", "/"):
        raise ValueError("Bare HTTPS origin required")
    if args.version_code < 57 or not re.fullmatch(r"0\\.3\\.\\d+", args.version_name):
        raise ValueError("Unexpected release version")
    apk = args.apk.resolve(strict=True)
    digest, size = evidence(apk, args.aapt, args.apksigner, args.version_code, args.version_name)
    root = args.store.resolve()
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Private storage directory must already exist")
    releases = root / "releases"
    releases.mkdir(mode=0o750, exist_ok=True)
    import fcntl
    with (root / ".publish.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        pointer = root / "stable.json"
        current = json.loads(pointer.read_text()) if pointer.exists() else None
        if current and args.version_code <= current["versionCode"]:
            raise ValueError("Refusing stale, equal or downgrade release")
        filename = f"{args.version_code}-{digest}.apk"
        target = releases / filename
        if target.exists():
            if target.is_symlink() or hashlib.file_digest(target.open("rb"), "sha256").hexdigest() != digest:
                raise ValueError("Immutable APK collision")
        else:
            fd, temporary = tempfile.mkstemp(prefix=".apk-", dir=releases)
            try:
                with os.fdopen(fd, "wb") as output, apk.open("rb") as source:
                    shutil.copyfileobj(source, output)
                    output.flush()
                    os.fsync(output.fileno())
                if hashlib.file_digest(open(temporary, "rb"), "sha256").hexdigest() != digest:
                    raise ValueError("Uploaded APK integrity mismatch")
                os.chmod(temporary, 0o640)
                os.replace(temporary, target)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        notes = args.notes.strip()
        if not notes or len(notes) > 800 or "<" in notes or ">" in notes:
            raise ValueError("Notes must be plain text of 1-800 characters")
        manifest = {
            "schemaVersion": 1, "channel": "stable", "enabled": True,
            "packageName": PACKAGE, "versionCode": args.version_code,
            "versionName": args.version_name,
            "apkUrl": args.base_url.rstrip("/") + "/releases/android/" + filename,
            "apkSha256": digest, "sizeBytes": size, "signerSha256": SIGNER,
            "minSdk": 28,
            "publishedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "notesRu": notes,
        }
        atomic_write(pointer, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        print(json.dumps({"version": args.version_name, "versionCode": args.version_code,
                          "sha256": digest, "sizeBytes": size, "stable_pointer": str(pointer)}, ensure_ascii=False))

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apk", required=True, type=Path)
    p.add_argument("--store", required=True, type=Path)
    p.add_argument("--base-url", required=True)
    p.add_argument("--version-code", required=True, type=int)
    p.add_argument("--version-name", required=True)
    p.add_argument("--notes", required=True)
    p.add_argument("--aapt", default="aapt")
    p.add_argument("--apksigner", default="apksigner")
    publish(p.parse_args())
