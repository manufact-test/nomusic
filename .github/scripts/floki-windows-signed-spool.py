#!/usr/bin/env python3
"""Store an already verified signed Windows transfer in the isolated Floki spool.

The bind mount is untrusted: root must separately check the P-256 signature,
trusted key, monotonic sequence, package hash, and every file before promotion.
No SSH/deploy privileges, network, production path, or executable payload.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import stat
import tempfile

VERSION = re.compile(r"(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,4})")
ROOT = Path("/home/runner/celikom-windows-signed-spool")
LIMIT = 125_100_000


def require(ok, code):
    if not ok:
        raise ValueError(code)


def sha(path):
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            total += len(chunk)
            require(total <= LIMIT, "SIGNED_TRANSFER_TOO_LARGE")
            digest.update(chunk)
    return digest.hexdigest(), total


def publish(bundle, version, sequence, spool=ROOT):
    require(bool(VERSION.fullmatch(version)) and isinstance(sequence, int) and
            0 < sequence < 2**53, "BAD_SIGNED_RELEASE_IDENTITY")
    st = bundle.lstat()
    require(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid()
            and st.st_nlink == 1 and 22 <= st.st_size <= LIMIT,
            "UNSAFE_SIGNED_SOURCE")
    digest, length = sha(bundle)
    spool.mkdir(mode=0o700, exist_ok=True)
    st = spool.lstat()
    require(stat.S_ISDIR(st.st_mode) and st.st_uid == os.getuid()
            and stat.S_IMODE(st.st_mode) == 0o700,
            "UNSAFE_RUNNER_SPOOL")
    dest = spool / f"windows-{version}-{sequence}-{digest}.zip"
    if dest.exists() or dest.is_symlink():
        old = dest.lstat()
        require(stat.S_ISREG(old.st_mode) and old.st_uid == os.getuid()
                and old.st_nlink == 1 and stat.S_IMODE(old.st_mode) == 0o600
                and old.st_size == length and sha(dest)[0] == digest,
                "IMMUTABLE_SIGNED_TRANSFER_CONFLICT")
        print("CELIKOM_WINDOWS_SIGNED_RUNNER_SPOOL_READY", version, sequence,
              digest, length, "already-staged")
        return dest
    fd, tmp = tempfile.mkstemp(prefix=".incoming-", dir=spool)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as dest_stream, bundle.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                dest_stream.write(chunk)
            dest_stream.flush()
            os.fsync(dest_stream.fileno())
        require(sha(Path(tmp)) == (digest, length), "STAGING_COPY_MISMATCH")
        os.link(tmp, dest)
        dirfd = os.open(spool, os.O_DIRECTORY | os.O_RDONLY)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    print("CELIKOM_WINDOWS_SIGNED_RUNNER_SPOOL_READY", version, sequence,
          digest, length, "private-staged")
    return dest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--bundle", required=True, type=Path)
    p.add_argument("--version", required=True)
    p.add_argument("--sequence", required=True, type=int)
    x = p.parse_args()
    publish(x.bundle, x.version, x.sequence)
