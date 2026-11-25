#!/usr/bin/env python3
"""Data-only Windows release intake. No shell, root, signing key or promotion.

This entrypoint is intended for a dedicated nonprivileged forced-command SSH
identity. A second independent, root-owned import with the actual stable
floor remains mandatory before any release is considered accepted.
"""
import fcntl
import hashlib
import os
import pathlib
import re
import runpy
import shutil
import stat
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
core = runpy.run_path(str(HERE / "windows-stable-private-import.py"))
MAX_BUNDLE = core["MAX_BUNDLE"]
MAX_PENDING = 2
SHA = re.compile(r"[a-f0-9]{64}")
NUMBER = re.compile(r"[1-9][0-9]{0,15}")
need = core["need"]


def parse_command(command):
    words = command.split(" ")
    need(len(words) == 4 and words[0] == "stage-windows", "COMMAND_REFUSED")
    _, version, seq, digest = words
    need(NUMBER.fullmatch(seq) and SHA.fullmatch(digest), "COMMAND_REFUSED")
    sequence = int(seq)
    core["identity"](version, sequence)
    return version, sequence, digest


def receive(stream, spool, pin, command, trust_uid=0):
    version, sequence, digest = parse_command(command)
    core["private_dir"](spool)
    st = core["bounded_file"](pin, 64, 256)
    need(st.st_uid == trust_uid and not st.st_mode & 0o022, "UNSAFE_TRUST_PIN")
    target = spool / ("windows-" + version + "-" + str(sequence) + "-" + digest + ".zip")
    # Only one receiver can use the bounded spool at once. Never follow links.
    lock = os.open(spool / ".intake.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        st = os.fstat(lock)
        need(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid() and
             st.st_nlink == 1 and stat.S_IMODE(st.st_mode) == 0o600, "UNSAFE_LOCK")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        pending = [x for x in spool.iterdir() if x.name != ".intake.lock"]
        # An interrupted or unexpected spool never resets a quota.
        need(all(re.fullmatch(r"windows-[0-9.]+-[0-9]+-[a-f0-9]{64}\.zip", p.name)
                 and p.is_file() and not p.is_symlink() for p in pending), "SPOOL_REVIEW_REQUIRED")
        replay = target in pending
        if not replay:
            need(len(pending) < MAX_PENDING, "PRIVATE_INTAKE_FULL")
        work = pathlib.Path(tempfile.mkdtemp(prefix=".incoming-", dir=spool))
        try:
            bundle = work / "transfer.zip"
            with bundle.open("xb") as f:
                core["copy_bounded"](stream, f, MAX_BUNDLE)
            need(core["sha"](bundle) == digest, "TRANSFER_SHA_MISMATCH")
            core["unpack_verified"](bundle, work / "verified", version, sequence, pin)
            if replay:
                st = core["bounded_file"](target, 22, MAX_BUNDLE)
                need(st.st_uid == os.getuid() and st.st_nlink == 1 and
                     stat.S_IMODE(st.st_mode) == 0o600 and core["sha"](target) == digest,
                     "IMMUTABLE_INTAKE_CONFLICT")
                return "already-staged", version, sequence, digest
            bundle.chmod(0o600)
            # Same-filesystem atomic rename, under the exclusive intake lock.
            os.rename(bundle, target)
            return "private-staged", version, sequence, digest
        finally:
            shutil.rmtree(work)
    finally:
        os.close(lock)


def main():
    # Fixed production paths, no arguments from the remote caller.
    need(os.getuid() != 0 and len(sys.argv) == 1, "UNPRIVILEGED_FORCED_COMMAND_REQUIRED")
    os.umask(0o077)
    command = os.environ.get("SSH_ORIGINAL_COMMAND", "")
    result = receive(sys.stdin.buffer,
                     pathlib.Path("/var/lib/celikom-windows-intake/incoming"),
                     pathlib.Path("/etc/celikom-windows-intake/windows-stable-public.der"),
                     command)
    print("CELIKOM_WINDOWS_DATA_ONLY_INTAKE_OK", *result)


if __name__ == "__main__":
    main()
