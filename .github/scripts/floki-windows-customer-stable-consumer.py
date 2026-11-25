#!/usr/bin/env python3
"""CELIKOM Windows customer-stable publisher (separate from owner candidates).

Only explicit main-branch acceptance can expose a signed version to customers.
Never run this from a CI runner. Never read an unsigned runner spool directly.
"""
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

MIRROR = Path("/home/celikom-mirror/github-mirror.git")
APPROVAL = ".github/release/windows-customer-stable.json"
SIGNED_ROOT = Path("/srv/celikom-releases/windows/stable/versions")
CUSTOMER = Path("/srv/celikom-releases/windows/customer-stable")
PIN = Path("/root/celikom-secrets/windows-stable-public.der")
TOOLS = Path("/root/celikom-release-tools")
PIN_SHA = "46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95"
VERIFY_BLOB = "bb4d19672d45bdd0393497c3b33280308d67ef32"
VERSION = re.compile(r"(?:0|[1-9][0-9]{0,3})\.(?:0|[1-9][0-9]{0,3})\.(?:0|[1-9][0-9]{0,4})")
HEX = re.compile(r"[a-f0-9]{64}")


def require(condition, code):
    if not condition:
        raise RuntimeError("CELIKOM_CUSTOMER_WINDOWS_" + code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def regular(path, max_bytes, root_owned=True):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        s = os.fstat(fd)
        require(stat.S_ISREG(s.st_mode) and s.st_size > 0 and s.st_size <= max_bytes
                and not s.st_mode & 0o022, "UNSAFE_INPUT")
        if root_owned:
            require(s.st_uid == 0, "UNTRUSTED_OWNER")
        with os.fdopen(fd, "rb", closefd=False) as inp:
            data = inp.read(max_bytes + 1)
        require(len(data) == s.st_size, "INPUT_CHANGED")
        return data
    finally:
        os.close(fd)


def secure_directory(path):
    for p in (path, *path.parents):
        s = p.lstat()
        require(stat.S_ISDIR(s.st_mode) and s.st_uid == 0 and not s.st_mode & 0o022,
                "UNSAFE_DIRECTORY")


def version_tuple(v):
    require(isinstance(v, str) and VERSION.fullmatch(v), "INVALID_VERSION")
    return tuple(int(x) for x in v.split("."))


def approved():
    git = ["/usr/bin/git", "-c", "safe.directory=" + str(MIRROR),
           "--git-dir=" + str(MIRROR)]
    r = subprocess.run(git + ["show", "refs/heads/main:" + APPROVAL],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=30)
    require(len(r.stdout) <= 4096, "APPROVAL_SIZE")
    data = json.loads(r.stdout)
    require(isinstance(data, dict) and set(data) == {"schema", "channel", "approved"} and
            data["schema"] == 1 and data["channel"] == "customer-stable", "APPROVAL_SCHEMA")
    a = data["approved"]
    if a is None:
        return None
    require(isinstance(a, dict) and set(a) ==
            {"version", "sequence", "sha256", "owner_accepted"}, "APPROVAL_FIELDS")
    version_tuple(a["version"])
    require(type(a["sequence"]) is int and a["sequence"] > 0 and a["sequence"] < 2**53 and
            type(a["sha256"]) is str and HEX.fullmatch(a["sha256"]) and
            a["owner_accepted"] is True, "APPROVAL_INVALID")
    return a


VERIFY = r"""
import {readFile} from 'node:fs/promises';
import {verifyExistingStableLatest} from './windows-stable-existing-latest.mjs';
const [manifestPath,sigPath,pinPath]=process.argv.slice(1);
const key=(await readFile(pinPath)).toString('base64');
const manifest=await readFile(manifestPath);
const signature=await readFile(sigPath);
const verified=verifyExistingStableLatest(manifest,signature,{
 origin:'https://celikom.com',pinnedPublicKeyDerBase64:key
});
process.stdout.write(JSON.stringify(verified));
"""


def verify_signed(v, a):
    pin = regular(PIN, 256)
    require(sha(pin) == PIN_SHA, "PIN_CHANGED")
    # Do not execute a publisher script from a mutable CI workspace.
    verifier = TOOLS / "windows-stable-existing-latest.mjs"
    data = regular(verifier, 8192)
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    require(blob == VERIFY_BLOB, "TRUSTED_VERIFIER_CHANGED")
    directory = SIGNED_ROOT / v
    secure_directory(directory)
    manifest = regular(directory / "manifest.json", 16384)
    signature = regular(directory / "manifest.json.sig", 80)
    result = subprocess.run(["/usr/bin/node", "--input-type=module", "-e", VERIFY,
                             str(directory / "manifest.json"),
                             str(directory / "manifest.json.sig"), str(PIN)],
                            cwd=TOOLS, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=20, check=True)
    data = json.loads(result.stdout)
    m = json.loads(manifest)
    require(m["version"] == v and data["sequence"] == a["sequence"]
            and m["sequence"] == a["sequence"] and
            m["sha256"] == a["sha256"] and
            m["packageUrl"] ==
                "https://celikom.com/CELIKOM/Windows/Updates/stable/" + v +
                "/CELIKOM-Windows-" + v + ".exe", "SIGNED_IDENTITY_MISMATCH")
    require(len(signature) >= 64, "BAD_SIGNATURE")
    expire = m["expiresAt"]
    from datetime import datetime, timezone
    expiration = datetime.fromisoformat(expire.replace("Z", "+00:00")).timestamp()
    require(expiration > time.time() + 180, "SIGNED_MANIFEST_EXPIRED")
    exe = "CELIKOM-Windows-" + v + ".exe"
    file = directory / exe
    s = file.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_uid == 0 and not s.st_mode & 0o022 and
            s.st_size == m["packageSize"] and s.st_size <= 125_000_000,
            "SIGNED_EXE_UNSAFE")
    h = hashlib.sha256()
    with file.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    require(h.hexdigest() == a["sha256"], "SIGNED_EXE_HASH_MISMATCH")
    return {"manifest.json": manifest, "manifest.json.sig": signature, exe: None}


def atomic_immutable_copy(src, dest, expected_sha, size):
    if dest.exists() or dest.is_symlink():
        s = dest.lstat()
        require(stat.S_ISREG(s.st_mode) and s.st_uid == 0 and
                s.st_size == size and not s.st_mode & 0o022, "IMMUTABLE_CONFLICT")
        with dest.open("rb") as file:
            require(hashlib.file_digest(file, "sha256").hexdigest() == expected_sha,
                    "IMMUTABLE_HASH_CHANGED")
        return
    fd, temp = tempfile.mkstemp(prefix=".celikom-windows-copy-", dir=dest.parent)
    try:
        with os.fdopen(fd, "wb") as output, src.open("rb") as inp:
            shutil.copyfileobj(inp, output, 1024 * 1024)
            output.flush()
            os.fsync(output.fileno())
        os.chown(temp, 0, 0)
        os.chmod(temp, 0o644)
        with open(temp, "rb") as check:
            require(hashlib.file_digest(check, "sha256").hexdigest() == expected_sha,
                    "COPY_HASH_CHANGED")
        os.link(temp, dest)
    finally:
        if os.path.lexists(temp):
            os.unlink(temp)


def atomically_point_accepted_installer(source, destination):
    # A public stable URL exists only after owner acceptance. It is a hard link
    # to an already-verified immutable installer, never a mutable CI artifact.
    fd, tmp = tempfile.mkstemp(prefix=".windows-customer-current-", dir=destination.parent)
    os.close(fd)
    os.unlink(tmp)
    try:
        os.link(source, tmp)
        os.replace(tmp, destination)
    finally:
        if os.path.lexists(tmp):
            os.unlink(tmp)


def replace_file(dest, data):
    fd, temp = tempfile.mkstemp(prefix=".latest-verified-", dir=dest.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.chown(temp, 0, 0)
        os.chmod(temp, 0o644)
        os.replace(temp, dest)
    finally:
        if os.path.lexists(temp):
            os.unlink(temp)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def verify_public(v, m, a):
    client = urllib.request.build_opener(NoRedirect())
    exe = "CELIKOM-Windows-" + v + ".exe"
    payloads = [
        ("/CELIKOM/Windows/Updates/stable/latest.json", m["manifest.json"]),
        ("/CELIKOM/Windows/Updates/stable/latest.json.sig", m["manifest.json.sig"]),
        ("/CELIKOM/Windows/Updates/stable/" + v + "/manifest.json", m["manifest.json"]),
        ("/CELIKOM/Windows/Updates/stable/" + v + "/manifest.json.sig", m["manifest.json.sig"]),
    ]
    for suffix, content in payloads:
        with client.open("https://celikom.com" + suffix, timeout=40) as r:
            require(r.status == 200 and r.read(16385) == content, "PUBLIC_MANIFEST_MISMATCH")
    expected_size = json.loads(m["manifest.json"])["packageSize"]
    for public_path in (
        "/CELIKOM/Windows/Updates/stable/" + v + "/" + exe,
        "/downloads/windows/CELIKOM-Windows-stable.exe",
    ):
        with client.open("https://celikom.com" + public_path, timeout=180) as r:
            require(r.status == 200, "EXE_NOT_200")
            h = hashlib.sha256()
            size = 0
            while chunk := r.read(1024 * 1024):
                size += len(chunk)
                require(size <= 125_000_000, "EXE_OVERSIZE")
                h.update(chunk)
        require(size == expected_size, "EXE_SIZE")
        require(h.hexdigest() == a["sha256"], "EXE_HASH")
    print("CELIKOM_CUSTOMER_WINDOWS_HTTPS_200_FULL_SHA256", v, a["sha256"])


def publish(a):
    v = a["version"]
    # Normal timer checks must not download an 85 MB installer every two minutes.
    # An accepted version is immutable and a full HTTPS proof was recorded at
    # first promotion; re-check only when an explicitly newer approval appears.
    existing_latest = CUSTOMER / "latest.json"
    existing_sig = CUSTOMER / "latest.json.sig"
    if existing_latest.exists():
        current = json.loads(regular(existing_latest, 16384))
        require(existing_sig.exists(), "INCOMPLETE_EXISTING_SIGNATURE")
        require(version_tuple(v) >= version_tuple(current["version"]) and
                a["sequence"] >= current["sequence"], "DOWNGRADE_REFUSED")
        if (current["version"] == v and current["sequence"] == a["sequence"]
                and current["sha256"] == a["sha256"]):
            print("CELIKOM_CUSTOMER_WINDOWS_ALREADY_ACCEPTED",v)
            return
    m = verify_signed(v, a)
    versions = CUSTOMER / "versions"
    secure_directory(versions)
    version_dir = versions / v
    if version_dir.exists():
        secure_directory(version_dir)
    else:
        version_dir.mkdir(mode=0o755)
    src = SIGNED_ROOT / v
    for name, content in m.items():
        if content is None:
            source = src / name
            atomic_immutable_copy(source, version_dir / name, a["sha256"],
                                  source.stat().st_size)
        else:
            atomic_immutable_copy(src / name, version_dir / name,
                                  sha(content), len(content))
    latest = CUSTOMER / "latest.json"
    latest_sig = CUSTOMER / "latest.json.sig"
    current_m = regular(latest, 16384) if latest.exists() else None
    current_s = regular(latest_sig, 80) if latest_sig.exists() else None
    require((current_m is None) == (current_s is None), "INCOMPLETE_CURRENT_PAIR")
    if current_m:
        old = json.loads(current_m)
        require(version_tuple(v) >= version_tuple(old["version"]) and
                a["sequence"] >= old["sequence"], "DOWNGRADE_REFUSED")
        if version_tuple(v) == version_tuple(old["version"]):
            require(current_m == m["manifest.json"] and current_s == m["manifest.json.sig"],
                    "CURRENT_SIGNATURE_CONFLICT")
            verify_public(v, m, a)
            return
    stable_link = CUSTOMER / "CELIKOM-Windows-stable.exe"
    previous_stable = None
    if current_m is not None:
        old_version = json.loads(current_m)["version"]
        previous_stable = versions / old_version / ("CELIKOM-Windows-" + old_version + ".exe")
        require(previous_stable.is_file(), "PREVIOUS_ACCEPTED_INSTALLER_MISSING")
    replace_file(latest, m["manifest.json"])
    replace_file(latest_sig, m["manifest.json.sig"])
    atomically_point_accepted_installer(version_dir / ("CELIKOM-Windows-" + v + ".exe"),
                                       stable_link)
    try:
        verify_public(v, m, a)
    except BaseException:
        if current_m is not None:
            replace_file(latest, current_m)
            replace_file(latest_sig, current_s)
            atomically_point_accepted_installer(previous_stable, stable_link)
        else:
            latest.unlink(missing_ok=True)
            latest_sig.unlink(missing_ok=True)
            stable_link.unlink(missing_ok=True)
        raise
    print("CELIKOM_CUSTOMER_WINDOWS_SIGNED_RELEASE_APPROVED", v, a["sequence"])


def main():
    require(os.geteuid() == 0, "ROOT_REQUIRED")
    secure_directory(CUSTOMER)
    require(MIRROR.is_dir() and not MIRROR.is_symlink(), "MIRROR_UNAVAILABLE")
    lock = os.open(CUSTOMER / ".publish.lock",
                   os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        a = approved()
        if a is None:
            print("CELIKOM_CUSTOMER_WINDOWS_STABLE_NOT_APPROVED_KEEP_FEED_PRIVATE")
            return
        publish(a)
    finally:
        os.close(lock)


if __name__ == "__main__":
    main()
