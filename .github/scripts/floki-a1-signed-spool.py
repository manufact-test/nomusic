#!/usr/bin/env python3
"""Stage an already CI-verified signed Android A1 release as UNTRUSTED DATA.

This program runs in the isolated CI container. It cannot publish, execute,
SSH into the host or modify the server's releases. A separately installed,
root-owned verifier must independently accept the APK before HTTPS delivery.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile

SPOOL = Path("/home/runner/celikom-a1-signed-spool")
APK_NAME = re.compile(r"CELIKOM-A1-[A-Za-z0-9_-]{1,100}\.apk\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
MAX_BYTES = 160 * 1024 * 1024
BRANCH = "experiment/android-a1-metrica-init-state-observer-arm13-20261112"


def check(value, message):
    if not value:
        raise ValueError("A1_SPOOL_" + message)


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def regular_owned(path):
    st = path.lstat()
    check(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid()
          and st.st_nlink == 1 and not st.st_mode & 0o022,
          "UNSAFE_SOURCE_FILE")
    return st


def stage(apk, metadata_path, provenance_path, spool=SPOOL):
    metadata = json.loads(metadata_path.read_text())
    proof = json.loads(provenance_path.read_text())
    check(set(metadata) == {"run", "attempt", "name", "size", "sha256"},
          "METADATA_SCHEMA")
    run, attempt = metadata["run"], metadata["attempt"]
    name, size, digest = metadata["name"], metadata["size"], metadata["sha256"]
    check(type(run) is int and 1 <= run <= 10**14
          and type(attempt) is int and 1 <= attempt <= 100,
          "INVALID_SOURCE_RUN")
    check(isinstance(name, str) and APK_NAME.fullmatch(name)
          and apk.name == name, "INVALID_APK_NAME")
    check(type(size) is int and 1024 * 1024 <= size <= MAX_BYTES
          and isinstance(digest, str) and SHA.fullmatch(digest),
          "INVALID_APK_DIGEST")
    check(proof.get("schema") == 1 and proof.get("distribution_only") is True
          and proof.get("distribution_target") == "main"
          and proof.get("source_repository") == "manufact-test/nomusic"
          and proof.get("source_branch") == BRANCH
          and proof.get("workflow_run_id") == run
          and proof.get("workflow_run_attempt") == attempt
          and proof.get("apk") == name
          and proof.get("apk_size") == size
          and proof.get("apk_sha256") == digest
          and proof.get("acoustic_replacement_proven") is False,
          "PROVENANCE_MISMATCH")
    check(re.fullmatch(r"[0-9a-f]{40}", str(proof.get("source_commit", ""))),
          "INVALID_SOURCE_COMMIT")
    for item in (apk, metadata_path, provenance_path):
        regular_owned(item)
    check(apk.stat().st_size == size and sha256_file(apk) == digest,
          "APK_SIZE_OR_SHA256")
    spool.mkdir(mode=0o700, parents=False, exist_ok=True)
    root_st = spool.lstat()
    check(stat.S_ISDIR(root_st.st_mode) and root_st.st_uid == os.getuid()
          and stat.S_IMODE(root_st.st_mode) == 0o700, "UNSAFE_SPOOL_DIR")
    existing = [entry for entry in spool.iterdir() if entry.name.startswith("a1-")]
    check(len(existing) <= 12, "SPOOL_LIMIT")
    dest = spool / f"a1-{run}-{attempt}-{digest}"
    if dest.exists() or dest.is_symlink():
        check(dest.is_dir() and not dest.is_symlink(), "EXISTING_NOT_DIR")
        for source, target in ((apk, dest / name),
                               (metadata_path, dest / "metadata.json"),
                               (provenance_path, dest / "BUILD-PROVENANCE.json")):
            regular_owned(target)
            check(sha256_file(source) == sha256_file(target),
                  "IMMUTABLE_STAGE_CONFLICT")
        print("A1_SIGNED_SPOOL_READY", run, attempt, digest, "existing")
        return dest
    tmp = Path(tempfile.mkdtemp(prefix=".incoming-", dir=spool))
    try:
        for source, filename in ((apk, name), (metadata_path, "metadata.json"),
                                 (provenance_path, "BUILD-PROVENANCE.json")):
            destination = tmp / filename
            with source.open("rb") as inp, destination.open("xb") as out:
                shutil.copyfileobj(inp, out, length=1024 * 1024)
                out.flush()
                os.fsync(out.fileno())
            destination.chmod(0o600)
            check(sha256_file(source) == sha256_file(destination),
                  "STAGE_COPY_CORRUPTION")
        os.rename(tmp, dest)
        fd = os.open(spool, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    print("A1_SIGNED_SPOOL_READY", run, attempt, digest, "root-promotion-pending")
    return dest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    args = parser.parse_args()
    stage(args.apk, args.metadata, args.provenance)
