#!/usr/bin/env python3
"""CELIKOM extension owner-only release publisher.

Runs on the trusted host, never in CI. CI may only write untrusted ZIP data.
A new owner release requires a main-branch approval entry with exact source
commit, CI run, size and SHA-256. This does NOT publish Chrome Web Store items.
"""
import base64
import fcntl
import grp
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import urllib.error
import urllib.request
import zipfile

MIRROR = Path("/home/celikom-mirror/github-mirror.git")
APPROVAL_FILE = ".github/release/extension-owner-promotions.json"
SPOOL = Path("/srv/celikom/ci-runner/runner/celikom-build-spool")
VERSIONS = Path("/srv/celikom-releases/private/extension/versions")
STATE = Path("/srv/celikom-releases/private/extension/current-owner.json")
OWNER = Path("/srv/celikom-releases/owner-downloads")
CREDENTIALS = Path("/root/celikom-secrets/celikom-owner-basic-verification.txt")
VER = re.compile(r"(0|[1-9][0-9]{0,4})\.(0|[1-9][0-9]{0,4})\.(0|[1-9][0-9]{0,4})")
SHA = re.compile("[0-9a-f]{64}")
COMMIT = re.compile("[0-9a-f]{40}")
RUN = re.compile("[1-9][0-9]{0,19}")
MAX_BYTES = 64 * 1024 * 1024


def ensure(ok, reason):
    if not ok:
        raise RuntimeError("EXTENSION_OWNER_" + reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def ver(s):
    ensure(type(s) is str and VER.fullmatch(s), "VERSION_FORMAT")
    return tuple(int(n) for n in s.split("."))


def read_file(path, maximum, owner=None):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        st = os.fstat(fd)
        ensure(stat.S_ISREG(st.st_mode) and st.st_nlink >= 1 and 0 < st.st_size <= maximum,
               "NOT_REGULAR")
        if owner is not None:
            ensure(st.st_uid == owner and not st.st_mode & 0o022, "UNSAFE_OWNER")
        with os.fdopen(fd, "rb", closefd=False) as f:
            data = f.read(maximum + 1)
        ensure(len(data) == st.st_size, "FILE_CHANGED")
        return data
    finally:
        os.close(fd)


def root_dir(directory):
    for path in [directory, *directory.parents]:
        st = path.lstat()
        ensure(stat.S_ISDIR(st.st_mode) and st.st_uid == 0 and not st.st_mode & 0o022,
               "UNSAFE_ROOT_DIRECTORY")


def trusted_approvals():
    ensure(os.geteuid() == 0 and MIRROR.is_dir() and not MIRROR.is_symlink(), "MIRROR")
    git = ["/usr/bin/git", "-c", "safe.directory=" + str(MIRROR), "--git-dir=" + str(MIRROR)]
    def cmd(*args):
        return subprocess.run(git + list(args), check=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=30).stdout
    result = cmd("show", "refs/heads/main:" + APPROVAL_FILE)
    ensure(len(result) <= 32768, "APPROVAL_SIZE")
    d = json.loads(result)
    ensure(type(d) is dict and set(d) == {"schema", "channel", "approved", "public_stable"} and
           d["schema"] == 1 and d["channel"] == "owner-only" and d["public_stable"] is None and
           type(d["approved"]) is list and len(d["approved"]) <= 50, "APPROVAL_SCHEMA")
    approved = {}
    for item in d["approved"]:
        ensure(type(item) is dict and
               set(item) == {"version", "source_commit", "run_id", "attempt", "name", "size", "sha256"},
               "APPROVAL_ITEM_SCHEMA")
        v = item["version"]
        ver(v)
        ensure(COMMIT.fullmatch(item["source_commit"]) and RUN.fullmatch(item["run_id"]) and
               RUN.fullmatch(item["attempt"]) and SHA.fullmatch(item["sha256"]) and
               type(item["size"]) is int and 1024 <= item["size"] <= MAX_BYTES and
               item["name"] == "celikom-extension-" + v + ".zip" and v not in approved,
               "APPROVAL_ITEM_INVALID")
        # The authorized source must be in trusted main history, not arbitrary CI input.
        subprocess.run(git + ["merge-base", "--is-ancestor", item["source_commit"],
                              "refs/heads/main"], check=True, timeout=30,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        approved[v] = item
    return approved


def check_zip(data, version):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        ensure(0 < len(names) <= 500 and len(names) == len(set(names)), "ZIP_DUPLICATE")
        ensure(sum(x.file_size for x in archive.infolist()) <= 2 * MAX_BYTES, "ZIP_BOMB")
        for info in archive.infolist():
            p = Path(info.filename)
            ensure(not p.is_absolute() and ".." not in p.parts and "\\" not in info.filename and
                   not stat.S_ISLNK(info.external_attr >> 16), "ZIP_PATH")
        manifest = json.loads(archive.read("manifest.json"))
        api = json.loads(archive.read("api/config.json"))
        ensure(manifest["version"] == version and "update_url" not in manifest and
               sorted(manifest["host_permissions"]) ==
                   ["https://api.celikom.com/*", "https://music.yandex.ru/*"] and
               api["baseUrl"] == "https://api.celikom.com", "ZIP_MANIFEST")
        ensure(archive.testzip() is None, "ZIP_CORRUPT")


def verify_spool(a):
    sd = SPOOL.lstat()
    ensure(stat.S_ISDIR(sd.st_mode) and sd.st_uid != 0 and stat.S_IMODE(sd.st_mode) == 0o700,
           "SPOOL_DIR")
    directory = SPOOL / (a["source_commit"] + "-" + a["run_id"] + "-" + a["attempt"])
    st = directory.lstat()
    ensure(stat.S_ISDIR(st.st_mode) and st.st_uid == sd.st_uid and not st.st_mode & 0o077,
           "SPOOL_BUILD_DIR")
    entry = json.loads(read_file(directory / "receipt.json", 16384, sd.st_uid))
    expect = {"schema": 1, "state": "private-unreleased-ci", "sha": a["source_commit"],
              "runId": a["run_id"], "attempt": a["attempt"],
              "files": [{"kind": "extension", "name": a["name"],
                         "bytes": a["size"], "sha256": a["sha256"]}]}
    ensure(entry == expect, "RECEIPT_MISMATCH")
    path = directory / a["name"]
    st = path.lstat()
    ensure(st.st_uid == sd.st_uid and stat.S_ISREG(st.st_mode) and
           stat.S_IMODE(st.st_mode) == 0o600 and st.st_nlink == 1, "UNTRUSTED_ZIP")
    data = read_file(path, MAX_BYTES, sd.st_uid)
    ensure(len(data) == a["size"] and digest(data) == a["sha256"], "ZIP_DIGEST")
    checksum = read_file(directory / (a["name"] + ".sha256"), 256, sd.st_uid)
    ensure(checksum == (a["sha256"] + "  " + a["name"] + "\n").encode(), "ZIP_SHA_FILE")
    check_zip(data, a["version"])
    return data


def write_immutable(directory, name, data):
    root_dir(directory)
    target = directory / name
    if target.exists() or target.is_symlink():
        ensure(read_file(target, MAX_BYTES + 4096, 0) == data, "IMMUTABLE_CONFLICT")
        return
    fd, tmp = tempfile.mkstemp(prefix=".celikom-extension-file-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chown(tmp, 0, grp.getgrnam("www-data").gr_gid)
        os.chmod(tmp, 0o640)
        os.link(tmp, target, follow_symlinks=False)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def replace_bytes(directory, name, data):
    root_dir(directory)
    fd, tmp = tempfile.mkstemp(prefix=".celikom-extension-state-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chown(tmp, 0, grp.getgrnam("www-data").gr_gid)
        os.chmod(tmp, 0o640)
        os.replace(tmp, directory / name)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def switch_link(source, target):
    root_dir(target.parent)
    fd, tmp = tempfile.mkstemp(prefix=".celikom-extension-link-", dir=target.parent)
    os.close(fd)
    os.unlink(tmp)
    try:
        os.link(source, tmp)
        os.replace(tmp, target)
    finally:
        if os.path.lexists(tmp):
            os.unlink(tmp)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def basic_header():
    data = read_file(CREDENTIALS, 4096, 0).decode()
    info = {}
    for line in data.splitlines():
        m = re.fullmatch(r"\s*(HTTP Basic username|HTTP Basic password)\s*[:=]\s*(.*?)\s*", line, re.I)
        if m:
            info[m[1].lower()] = m[2]
    ensure(set(info) == {"http basic username", "http basic password"}, "BASIC_CREDENTIALS")
    raw = info["http basic username"] + ":" + info["http basic password"]
    return "Basic " + base64.b64encode(raw.encode()).decode()


def verify_https(a):
    client = urllib.request.build_opener(NoRedirect())
    for name in [a["name"], "celikom-extension-latest.zip"]:
        url = "https://celikom.com/downloads/extension/" + name
        try:
            with client.open(url, timeout=25) as r:
                raise RuntimeError("EXTENSION_OWNER_ANONYMOUS_EXPOSED")
        except urllib.error.HTTPError as e:
            ensure(e.code == 401, "OWNER_AUTH_GATE")
        request = urllib.request.Request(url, headers={"Authorization": basic_header(),
                                      "User-Agent": "CELIKOM-Owner-Release-Check"})
        with client.open(request, timeout=180) as response:
            ensure(response.status == 200, "OWNER_DOWNLOAD_STATUS")
            h = hashlib.sha256()
            n = 0
            while chunk := response.read(1024 * 1024):
                n += len(chunk)
                ensure(n <= a["size"], "OWNER_DOWNLOAD_OVERSIZE")
                h.update(chunk)
            ensure(n == a["size"] and h.hexdigest() == a["sha256"],
                   "OWNER_DOWNLOAD_SHA")
    print("EXTENSION_OWNER_HTTPS_200_SIZE_SHA256_VERIFIED", a["version"], a["sha256"])


def publish(a, data):
    v = a["version"]
    current = json.loads(read_file(STATE, 4096, 0)) if STATE.exists() else None
    if current:
        ensure(ver(v) >= ver(current["version"]), "DOWNGRADE_REFUSED")
        if v == current["version"]:
            ensure(a["sha256"] == current["sha256"], "CURRENT_VERSION_CONFLICT")
    dest = VERSIONS / v
    dest.mkdir(mode=0o750, parents=True, exist_ok=True)
    write_immutable(dest, a["name"], data)
    write_immutable(OWNER, a["name"], data)
    write_immutable(OWNER, a["name"] + ".sha256",
                    (a["sha256"] + "  " + a["name"] + "\n").encode())
    latest = OWNER / "celikom-extension-latest.zip"
    previous = OWNER / ("celikom-extension-" + current["version"] + ".zip") if current else None
    switch_link(OWNER / a["name"], latest)
    try:
        verify_https(a)
    except BaseException:
        if previous and previous.exists():
            switch_link(previous, latest)
        elif latest.exists():
            latest.unlink()
        raise
    state = json.dumps({"version": v, "sha256": a["sha256"], "size": a["size"],
                        "filename": a["name"], "source_commit": a["source_commit"],
                        "run_id": a["run_id"], "attempt": a["attempt"],
                        "channel": "owner-only", "https_verified": True},
                       sort_keys=True, separators=(",", ":")).encode() + b"\n"
    replace_bytes(STATE.parent, STATE.name, state)
    print("EXTENSION_OWNER_RELEASE_READY", v, a["sha256"], a["size"])


def main():
    root_dir(OWNER)
    root_dir(VERSIONS.parent)
    allowed = trusted_approvals()
    if not allowed:
        print("EXTENSION_OWNER_NO_APPROVED_RELEASE_KEEP_EXISTING_DOWNLOAD_UNCHANGED")
        return
    fd = os.open(STATE.parent / ".owner-promoter.lock",
                 os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        current = json.loads(read_file(STATE, 4096, 0)) if STATE.exists() else None
        for version, approval in sorted(allowed.items(), key=lambda kv: ver(kv[0])):
            if current and ver(version) < ver(current["version"]):
                continue
            if current and version == current["version"]:
                ensure(current["sha256"] == approval["sha256"], "CURRENT_APPROVAL_CONFLICT")
                continue
            data = verify_spool(approval)
            publish(approval, data)
            current = json.loads(read_file(STATE, 4096, 0))
    finally:
        os.close(fd)


if __name__ == "__main__":
    main()
