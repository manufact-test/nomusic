#!/usr/bin/env python3
"""Prepare/verify a signed Windows transfer ZIP; receive into PRIVATE staging only.

No SSH, GitHub token, signing key, Nginx or production pointer operations.
The receiver is intentionally a local CLI, not an installed remote command.
"""
import argparse
import base64
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
ORIGIN = "https://celikom.com"
VERSION = re.compile(r"(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,4})")
MAX_BUNDLE = 125_100_000


def need(ok, why):
    if not ok:
        raise ValueError(why)


def identity(version, sequence):
    need(isinstance(version, str) and VERSION.fullmatch(version), "BAD_VERSION")
    need(type(sequence) is int and 0 < sequence <= 2**53-1, "BAD_SEQUENCE")


def entries(version):
    return {
        "latest.json": (100, 16384), "latest.json.sig": (64, 80),
        "manifest-public-key.der": (64, 256),
        version + "/manifest.json": (100, 16384),
        version + "/manifest.json.sig": (64, 80),
        version + "/CELIKOM-Windows-" + version + ".exe": (10000, 125000000)
    }


def private_dir(path):
    st = path.lstat()
    need(stat.S_ISDIR(st.st_mode) and not st.st_mode & 0o077 and st.st_uid == os.getuid(),
         "UNSAFE_PRIVATE_DIRECTORY")


def bounded_file(path, low, high):
    st = path.lstat()
    need(stat.S_ISREG(st.st_mode) and low <= st.st_size <= high, "BAD_FILE")
    return st


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def verifier_env(pin):
    bounded_file(pin, 64, 256)
    return dict(os.environ, CELIKOM_STABLE_ORIGIN=ORIGIN,
                CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64=base64.b64encode(pin.read_bytes()).decode("ascii"))


def verify(directory, version, sequence, pin):
    identity(version, sequence)
    subprocess.run(["node", str(HERE / "windows-stable-release-verify.mjs"), str(directory),
                    version, str(sequence)], env=verifier_env(pin), check=True, timeout=90)


def pack(source, output, version, sequence, pin):
    """Create one transport file only from the verified six-file release contract."""
    verify(source, version, sequence, pin)
    need(not output.exists() and not output.is_symlink(), "BUNDLE_EXISTS")
    # Exclusive open ensures a repeated invocation cannot overwrite an archive.
    with output.open("xb") as target:
        try:
            with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as z:
                for name, (low, high) in entries(version).items():
                    p = source / name
                    bounded_file(p, low, high)
                    z.write(p, name)
            need(target.tell() <= MAX_BUNDLE, "BUNDLE_TOO_LARGE")
        except BaseException:
            target.close()
            output.unlink()
            raise


def copy_bounded(src, dst, limit):
    n = 0
    while True:
        chunk = src.read(1024*1024)
        if not chunk:
            return n
        n += len(chunk)
        need(n <= limit, "TRANSFER_LIMIT_EXCEEDED")
        dst.write(chunk)


def verify_floor(root, stage, version, sequence, pin):
    """A missing or invalid current pointer never resets the signed floor."""
    current = root / "current"
    link = current.lstat()
    need(stat.S_ISLNK(link.st_mode) and link.st_uid == os.getuid(), "UNSAFE_CURRENT")
    target = os.readlink(current)
    need(target.startswith("versions/") and VERSION.fullmatch(target[9:]), "UNSAFE_CURRENT")
    old = root / target
    for path in (root, root / "versions", old):
        st = path.lstat()
        need(stat.S_ISDIR(st.st_mode) and not st.st_mode & 0o022 and st.st_uid == os.getuid(),
             "UNSAFE_FLOOR_DIRECTORY")
    manifest, signature = old / "manifest.json", old / "manifest.json.sig"
    for file, low, high in ((manifest, 100, 16384), (signature, 64, 80)):
        st = bounded_file(file, low, high)
        need(st.st_uid == os.getuid() and not st.st_mode & 0o022, "UNSAFE_FLOOR_FILE")
    result = subprocess.run(["node", str(HERE / "windows-stable-existing-latest.mjs"),
                             str(manifest), str(signature)], env=verifier_env(pin),
                            check=True, capture_output=True, text=True, timeout=30)
    seq, _, _ = result.stdout.split()
    old_version = target[9:]
    need(json.loads(manifest.read_bytes())["version"] == old_version, "FLOOR_IDENTITY_MISMATCH")
    if version == old_version and sequence == int(seq):
        # Replay is allowed ONLY for the exact already-staged release bytes.
        old_exe = old / ("CELIKOM-Windows-" + old_version + ".exe")
        st = bounded_file(old_exe, 10000, 125000000)
        need(st.st_uid == os.getuid() and not st.st_mode & 0o022, "UNSAFE_FLOOR_FILE")
        need(manifest.read_bytes() == (stage / "latest.json").read_bytes()
             and signature.read_bytes() == (stage / "latest.json.sig").read_bytes()
             and sha(old_exe) == sha(stage / version / old_exe.name), "REPLAY_CONFLICT")
        return
    need(sequence > int(seq) and tuple(map(int, version.split("."))) >
         tuple(map(int, old_version.split("."))), "NON_MONOTONIC_TRANSFER")


def receive(stream, dest_root, floor_root, pin, version, sequence):
    """Read a bounded archive, reject extras/paths/links, then independently
    verify its signed content. No source tree or stable feed is ever modified.
    """
    identity(version, sequence)
    private_dir(dest_root)
    st = bounded_file(pin, 64, 256)
    need(st.st_uid == os.getuid() and not st.st_mode & 0o022, "UNSAFE_TRUST_PIN")
    work = pathlib.Path(tempfile.mkdtemp(prefix=".windows-import-", dir=dest_root))
    try:
        bundle = work / "incoming.zip"
        with bundle.open("xb") as f:
            copy_bounded(stream, f, MAX_BUNDLE)
        stage = work / "verified"
        stage.mkdir(mode=0o700)
        (stage / version).mkdir(mode=0o700)
        with zipfile.ZipFile(bundle) as z:
            expected = entries(version)
            members = z.infolist()
            need(len(members) == len(expected) and {x.filename for x in members} == set(expected),
                 "UNEXPECTED_ARCHIVE_MEMBERS")
            for member in members:
                low, high = expected[member.filename]
                mode = (member.external_attr >> 16) & 0xffff
                need(not member.is_dir() and stat.S_IFMT(mode) in (0, stat.S_IFREG)
                     and not member.flag_bits & 1 and member.compress_type == zipfile.ZIP_STORED
                     and low <= member.file_size <= high and member.compress_size == member.file_size,
                     "UNSAFE_ARCHIVE_MEMBER")
                # Paths come only from the fixed six-name allowlist, never extraction APIs.
                path = stage / member.filename
                with z.open(member) as src, path.open("xb") as dst:
                    need(copy_bounded(src, dst, high) == member.file_size, "MEMBER_SIZE_MISMATCH")
                path.chmod(0o600)
        verify(stage, version, sequence, pin)
        verify_floor(floor_root, stage, version, sequence, pin)
        destination = dest_root / ("windows-" + version)
        # Private staging can be repeated for the exact same release, never replaced.
        try:
            destination.mkdir(mode=0o700)
        except FileExistsError:
            private_dir(destination)
            private_dir(destination / version)
            for name, (low, high) in entries(version).items():
                old = destination / name
                st = bounded_file(old, low, high)
                need(st.st_uid == os.getuid() and stat.S_IMODE(st.st_mode) == 0o600
                     and st.st_nlink == 1 and sha(old) == sha(stage / name), "IMMUTABLE_IMPORT_CONFLICT")
            need({str(x.relative_to(destination)) for x in destination.rglob("*") if not x.is_dir()}
                 == set(entries(version)), "IMMUTABLE_IMPORT_EXTRAS")
            return "already-staged"
        try:
            # The reservation directory is private; no consumer uses it until
            # all six verified files have arrived. A partial import is removed.
            (destination / version).mkdir(mode=0o700)
            for name in entries(version):
                os.rename(stage / name, destination / name)
        except BaseException:
            shutil.rmtree(destination)
            raise
        return "private-staged"
    finally:
        shutil.rmtree(work)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("pack")
    a.add_argument("--source", type=pathlib.Path, required=True)
    a.add_argument("--output", type=pathlib.Path, required=True)
    b = sub.add_parser("receive")
    b.add_argument("--dest-root", type=pathlib.Path, required=True)
    b.add_argument("--floor-root", type=pathlib.Path, required=True)
    for q in (a, b):
        q.add_argument("--pin", type=pathlib.Path, required=True)
        q.add_argument("--version", required=True)
        q.add_argument("--sequence", type=int, required=True)
    args = p.parse_args()
    if args.command == "pack":
        pack(args.source, args.output, args.version, args.sequence, args.pin)
        print("CELIKOM_WINDOWS_PRIVATE_TRANSFER_PACKED", args.version, sha(args.output))
    else:
        os.umask(0o077)
        result = receive(sys.stdin.buffer, args.dest_root, args.floor_root, args.pin, args.version, args.sequence)
        print("CELIKOM_WINDOWS_PRIVATE_TRANSFER_VERIFIED", args.version, result)


if __name__ == "__main__":
    main()
