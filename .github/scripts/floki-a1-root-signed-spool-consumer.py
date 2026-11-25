#!/usr/bin/env python3
"""Root-owned, data-only A1 release promoter for the isolated Floki CI spool.

NEVER execute scripts from the runner. This file is installed out of band by
a trusted administrator, remains root owned, and independently verifies
APK signing identity, application ID, source provenance, size and SHA-256.
A verified APK is handed to the EXISTING unprivileged A1 receiver, so the
existing capability-only Nginx route and all production services stay intact.
"""
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
import urllib.error
import urllib.request

SPOOL = Path("/srv/celikom/ci-runner/runner/celikom-a1-signed-spool")
RECEIPTS = SPOOL / "receipts"
PRIVATE = Path("/root/celikom-a1-signed-import")
RECEIVER = Path("/usr/local/sbin/celikom-a1-apk-receive")
BRANCH = "experiment/android-a1-metrica-init-state-observer-arm13-20261112"
CERT = "048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf"
PKG = "pro.celikom.yandex.nativeclonelab"
RUN_DIR = re.compile(r"a1-([1-9][0-9]{0,13})-([1-9][0-9]{0,2})-([0-9a-f]{64})\Z")
APK_NAME = re.compile(r"CELIKOM-A1-[A-Za-z0-9_-]{1,100}\.apk\Z")
SHA = re.compile("[0-9a-f]{64}\\Z")
URL = re.compile(r"https://celikom\.com/downloads/a1/[0-9a-f]{48}/(CELIKOM-A1-[A-Za-z0-9_-]{1,100}\.apk)\Z")
MAX = 160 * 1024 * 1024


def check(ok, reason):
    if not ok:
        raise RuntimeError("A1_ROOT_" + reason)


def safe_json(dirfd, filename, owner, max_size=4096):
    fd = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                 dir_fd=dirfd)
    try:
        st = os.fstat(fd)
        check(stat.S_ISREG(st.st_mode) and st.st_uid == owner and st.st_nlink == 1
              and stat.S_IMODE(st.st_mode) == 0o600 and st.st_size <= max_size,
              "UNSAFE_JSON")
        with os.fdopen(fd, "rb") as source:
            fd = -1
            raw = source.read(max_size + 1)
        check(len(raw) == st.st_size, "JSON_CHANGED")
        return json.loads(raw)
    finally:
        if fd >= 0:
            os.close(fd)


def validate_dir(path, owner, mode):
    st = path.lstat()
    check(stat.S_ISDIR(st.st_mode) and st.st_uid == owner
          and stat.S_IMODE(st.st_mode) == mode, "UNSAFE_DIRECTORY")
    return st


def validate_provenance(meta, proof, run, attempt, digest):
    check(set(meta) == {"run", "attempt", "name", "size", "sha256"},
          "INVALID_METADATA")
    name, size = meta["name"], meta["size"]
    check(type(meta["run"]) is int and meta["run"] == run and
          type(meta["attempt"]) is int and meta["attempt"] == attempt,
          "WRONG_RUN_ID")
    check(isinstance(name, str) and APK_NAME.fullmatch(name)
          and type(size) is int and 1024 * 1024 <= size <= MAX
          and meta["sha256"] == digest, "WRONG_APK")
    check(proof.get("schema") == 1 and proof.get("distribution_only") is True
          and proof.get("distribution_target") == "main"
          and proof.get("source_repository") == "manufact-test/nomusic"
          and proof.get("source_branch") == BRANCH
          and proof.get("workflow_run_id") == run
          and proof.get("workflow_run_attempt") == attempt
          and proof.get("apk") == name and proof.get("apk_size") == size
          and proof.get("apk_sha256") == digest
          and proof.get("acoustic_replacement_proven") is False
          and re.fullmatch(r"[0-9a-f]{40}", str(proof.get("source_commit", ""))),
          "INVALID_PROVENANCE")
    return name, size


def snapshot_apk(dirfd, filename, owner, size, digest, tempdir):
    fd = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                 dir_fd=dirfd)
    out = tempdir / "verified.apk"
    hash_obj = hashlib.sha256()
    total = 0
    try:
        st = os.fstat(fd)
        check(stat.S_ISREG(st.st_mode) and st.st_uid == owner
              and st.st_nlink == 1 and stat.S_IMODE(st.st_mode) == 0o600
              and st.st_size == size, "UNSAFE_APK_INPUT")
        with os.fdopen(fd, "rb") as inp, out.open("xb") as output:
            fd = -1
            while data := inp.read(1024 * 1024):
                total += len(data)
                check(total <= size, "APK_OVERFLOW")
                hash_obj.update(data)
                output.write(data)
            output.flush()
            os.fsync(output.fileno())
    finally:
        if fd >= 0:
            os.close(fd)
    check(total == size and hash_obj.hexdigest() == digest,
          "APK_SHA256_MISMATCH")
    return out


def verify_signature(apk):
    result = subprocess.run(["/usr/bin/apksigner", "verify", "--verbose",
                             "--print-certs", str(apk)],
                            capture_output=True, text=True, timeout=75, check=True)
    signatures = re.findall(r"^Signer #[0-9]+ certificate SHA-256 digest: ([0-9a-f]{64})$",
                            result.stdout, re.MULTILINE)
    check(signatures == [CERT], "UNEXPECTED_SIGNING_CERT")
    check(re.search(r"^Verified using v[23] scheme .*: true$",
                    result.stdout, re.MULTILINE), "APK_V2V3_INVALID")
    badge = subprocess.run(["/usr/bin/aapt", "dump", "badging", str(apk)],
                           capture_output=True, text=True, timeout=60, check=True)
    check(re.search(r"^package: name='" + re.escape(PKG) + r"'(?: |$)",
                    badge.stdout, re.MULTILINE), "UNEXPECTED_PACKAGE_NAME")
    print("A1_ROOT_SIGNER_AND_PACKAGE_VERIFIED")


def hand_to_existing_receiver(apk, meta, tempdir):
    wire = tempdir / "intake.bin"
    with wire.open("xb") as output:
        output.write((json.dumps(meta, separators=(",", ":")) + "\n").encode())
        with apk.open("rb") as source:
            shutil.copyfileobj(source, output, 1024 * 1024)
        output.flush()
        os.fsync(output.fileno())
    os.chmod(wire, 0o600)
    with wire.open("rb") as input_stream:
        result = subprocess.run(["/usr/sbin/runuser", "-u", "celikom-deploy",
                                 "--", str(RECEIVER)],
                                stdin=input_stream, capture_output=True,
                                text=True, timeout=320, check=True)
    output = result.stdout.splitlines()
    check(len(output) == 2 and output[0].startswith("A1_DOWNLOAD_URL=")
          and output[1] == "A1_RECEIVED_SHA256=" + meta["sha256"],
          "RECEIVER_RECEIPT_INVALID")
    url = output[0].removeprefix("A1_DOWNLOAD_URL=")
    match = URL.fullmatch(url)
    check(match and match.group(1) == meta["name"], "RECEIVER_URL_INVALID")
    return url


def verify_live_https(url, size, digest):
    request = urllib.request.Request(url, headers={"User-Agent": "CELIKOM-A1-Owner-Root-Check"})
    with urllib.request.urlopen(request, timeout=180) as response:
        check(response.status == 200, "HTTP_NOT_200")
        check(response.headers.get_content_type() == "application/vnd.android.package-archive",
              "HTTP_CONTENT_TYPE")
        h = hashlib.sha256()
        count = 0
        while data := response.read(1024 * 1024):
            count += len(data)
            check(count <= size, "HTTP_TOO_LARGE")
            h.update(data)
    check(count == size and h.hexdigest() == digest,
          "HTTPS_SIZE_OR_SHA256_MISMATCH")
    print("A1_ROOT_EXTERNAL_HTTPS_200_SIZE_SHA256_VERIFIED")


def atomic_receipt(receipts_fd, run, attempt, digest, name, size, url):
    record = {"run": run, "attempt": attempt, "sha256": digest, "name": name,
              "size": size, "url": url, "https_verified": True}
    filename = f"a1-{run}-{attempt}.json"
    payload = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode()
    try:
        fd = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=receipts_fd)
    except FileNotFoundError:
        fd = -1
    if fd >= 0:
        with os.fdopen(fd, "rb") as prior:
            st = os.fstat(prior.fileno())
            check(stat.S_ISREG(st.st_mode) and st.st_uid == 0
                  and prior.read() == payload, "RECEIPT_CONFLICT")
    else:
        import secrets
        tmp = ".receipt-" + secrets.token_hex(16)
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o644, dir_fd=receipts_fd)
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
            os.chmod(tmp, 0o644, dir_fd=receipts_fd, follow_symlinks=False)
            os.link(tmp, filename, src_dir_fd=receipts_fd,
                    dst_dir_fd=receipts_fd, follow_symlinks=False)
        finally:
            os.unlink(tmp, dir_fd=receipts_fd)
    print("A1_ROOT_OWNER_DOWNLOAD_READY", run, attempt, url)


def main():
    check(os.geteuid() == 0, "ROOT_REQUIRED")
    validate_dir(PRIVATE, 0, 0o700)
    check(RECEIVER.is_file() and not RECEIVER.is_symlink() and
          RECEIVER.stat().st_uid == 0, "MISSING_TRUSTED_RECEIVER")
    # Ubuntu's apt tools may be root-owned symlinks (for example via
    # /etc/alternatives). Reject untrusted targets, not legitimate symlinks.
    for binary in ("/usr/bin/apksigner", "/usr/bin/aapt", "/usr/sbin/runuser"):
        path = Path(binary)
        resolved = path.resolve(strict=True)
        check(resolved.is_file() and os.access(path, os.X_OK),
              "MISSING_SIGNING_VERIFIER")
        check(resolved.is_relative_to("/usr/") and not
              resolved.is_relative_to("/usr/local/"),
              "UNTRUSTED_SIGNING_VERIFIER_PATH")
        for component in (path, resolved, *path.parents, *resolved.parents):
            st = component.lstat()
            # POSIX symlinks conventionally report 0777; their mode bits
            # do not confer write access. Require root ownership of the
            # link itself and non-writable permissions on real directories
            # and executable files (including the resolved final target).
            check(st.st_uid == 0 and
                  (stat.S_ISLNK(st.st_mode) or not (st.st_mode & 0o022)),
                  "UNTRUSTED_SIGNING_VERIFIER_PATH")
    spool_fd = os.open(SPOOL, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        spool_st = os.fstat(spool_fd)
        check(stat.S_ISDIR(spool_st.st_mode) and spool_st.st_uid != 0
              and stat.S_IMODE(spool_st.st_mode) == 0o700,
              "UNSAFE_RUNNER_SPOOL")
        receipts_fd = os.open("receipts", os.O_RDONLY | os.O_DIRECTORY |
                              os.O_NOFOLLOW, dir_fd=spool_fd)
        try:
            receipts_st = os.fstat(receipts_fd)
            check(stat.S_ISDIR(receipts_st.st_mode) and receipts_st.st_uid == 0
                  and stat.S_IMODE(receipts_st.st_mode) == 0o755,
                  "UNSAFE_RECEIPTS_DIR")
            lock_fd = os.open(PRIVATE / "lock", os.O_CREAT | os.O_RDWR |
                              os.O_NOFOLLOW, 0o600)
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                pending = []
                for dirname in os.listdir(spool_fd):
                    if dirname == "receipts" or dirname.startswith(".incoming-"):
                        continue
                    match = RUN_DIR.fullmatch(dirname)
                    check(match, "UNKNOWN_SPOOL_MEMBER")
                    pending.append((dirname, *match.groups()))
                check(len(pending) <= 12, "SPOOL_OVER_LIMIT")
                for dirname, run_str, attempt_str, digest in sorted(
                        pending, key=lambda item: int(item[1])):
                    item_fd = os.open(dirname, os.O_RDONLY | os.O_DIRECTORY |
                                      os.O_NOFOLLOW, dir_fd=spool_fd)
                    try:
                        item_st = os.fstat(item_fd)
                        check(stat.S_ISDIR(item_st.st_mode) and
                              item_st.st_uid == spool_st.st_uid and
                              stat.S_IMODE(item_st.st_mode) == 0o700,
                              "UNSAFE_PENDING_DIR")
                        run, attempt = int(run_str), int(attempt_str)
                        meta = safe_json(item_fd, "metadata.json", spool_st.st_uid)
                        proof = safe_json(item_fd, "BUILD-PROVENANCE.json",
                                          spool_st.st_uid)
                        name, size = validate_provenance(meta, proof, run,
                                                         attempt, digest)
                        with tempfile.TemporaryDirectory(prefix=".a1-import-",
                                                         dir=PRIVATE) as td:
                            apk = snapshot_apk(item_fd, name, spool_st.st_uid,
                                               size, digest, Path(td))
                            verify_signature(apk)
                            url = hand_to_existing_receiver(apk, meta, Path(td))
                            verify_live_https(url, size, digest)
                            atomic_receipt(receipts_fd, run, attempt, digest,
                                           name, size, url)
                        current = os.stat(dirname, dir_fd=spool_fd,
                                          follow_symlinks=False)
                        check(current.st_ino == item_st.st_ino and
                              current.st_dev == item_st.st_dev,
                              "PENDING_DIR_SWAPPED")
                    finally:
                        os.close(item_fd)
                    # Only remove verified runner-owned data, not its receipt.
                    shutil.rmtree(SPOOL / dirname)
            finally:
                os.close(lock_fd)
        finally:
            os.close(receipts_fd)
    finally:
        os.close(spool_fd)


if __name__ == "__main__":
    main()
