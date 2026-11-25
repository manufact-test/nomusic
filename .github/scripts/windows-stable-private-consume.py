#!/usr/bin/env python3
"""Independent root-side import of the dedicated nonprivileged inbox.

No network, shell command execution from data, signing secrets, or publication.
The existing signed stable floor and public pin are independently verified.
"""
import fcntl
import os
import pathlib
import pwd
import re
import runpy
import shutil
import stat
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
core = runpy.run_path(str(HERE / "windows-stable-private-import.py"))
need = core["need"]
NAME = re.compile(r"windows-((?:0|[1-9][0-9]{0,3})\.(?:0|[1-9][0-9]{0,3})\.(?:0|[1-9][0-9]{0,4}))-([1-9][0-9]{0,15})-([a-f0-9]{64})\.zip")


def consume(spool, dest, floor, pin, sender_uid):
    need(os.getuid() == 0 and sender_uid != 0, "ROOT_IMPORT_REQUIRED")
    core["private_dir"](dest)
    # The inbox's parent is root-owned; only incoming itself belongs to
    # the data-only identity. Open all inbox members relative to its fd.
    parent = spool.parent.lstat()
    need(stat.S_ISDIR(parent.st_mode) and parent.st_uid == 0 and not parent.st_mode & 0o022,
         "UNSAFE_INBOX_PARENT")
    fd = os.open(spool, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        need(st.st_uid == sender_uid and stat.S_IMODE(st.st_mode) == 0o700, "UNSAFE_INBOX")
        lock = os.open(".intake.lock", os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            st = os.fstat(lock)
            need(stat.S_ISREG(st.st_mode) and st.st_uid == sender_uid and st.st_nlink == 1
                 and stat.S_IMODE(st.st_mode) == 0o600, "UNSAFE_INBOX_LOCK")
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            pending = [n for n in os.listdir(fd) if n != ".intake.lock"]
            need(1 <= len(pending) <= 2, "INBOX_EMPTY_OR_OVER_LIMIT")
            candidates = []
            for name in pending:
                match = NAME.fullmatch(name)
                need(match, "UNEXPECTED_INBOX_ENTRY")
                version, seq, digest = match.groups()
                sequence = int(seq)
                core["identity"](version, sequence)
                candidates.append((sequence, version, digest, name))
            for sequence, version, digest, name in sorted(candidates):
                # Never execute or follow uploader-controlled paths.
                item = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
                work = pathlib.Path(tempfile.mkdtemp(prefix=".root-windows-consume-", dir=dest))
                try:
                    with os.fdopen(item, "rb") as stream:
                        st = os.fstat(stream.fileno())
                        need(stat.S_ISREG(st.st_mode) and st.st_uid == sender_uid and st.st_nlink == 1
                             and stat.S_IMODE(st.st_mode) == 0o600 and 22 <= st.st_size <= core["MAX_BUNDLE"],
                             "UNSAFE_INBOX_FILE")
                        local = work / "transfer.zip"
                        with local.open("xb") as output:
                            need(core["copy_bounded"](stream, output, core["MAX_BUNDLE"]) == st.st_size,
                                 "INBOX_SIZE_CHANGED")
                    need(core["sha"](local) == digest, "INBOX_DIGEST_MISMATCH")
                    # Exact current replay is fully verified but never duplicated
                    # into another persistent release directory.
                    replay = os.readlink(floor / "current") == "versions/" + version
                    import_root = dest
                    if replay:
                        import_root = work / "replay"
                        import_root.mkdir(mode=0o700)
                    with local.open("rb") as stream:
                        result = core["receive"](stream, import_root, floor, pin, version, sequence)
                    now = os.stat(name, dir_fd=fd, follow_symlinks=False)
                    need(now.st_dev == st.st_dev and now.st_ino == st.st_ino and now.st_size == st.st_size,
                         "INBOX_FILE_REPLACED")
                    os.unlink(name, dir_fd=fd)
                    print("CELIKOM_WINDOWS_ROOT_PRIVATE_CONSUMED", version, sequence, digest,
                          "exact-current-replay" if replay else result)
                finally:
                    shutil.rmtree(work)
        finally:
            os.close(lock)
    finally:
        os.close(fd)


if __name__ == "__main__":
    need(len(sys.argv) == 1, "FIXED_PATHS_ONLY")
    os.umask(0o077)
    consume(pathlib.Path("/var/lib/celikom-windows-intake/incoming"),
            pathlib.Path("/root/celikom-release-import"),
            pathlib.Path("/srv/celikom-releases/windows/stable"),
            pathlib.Path("/root/celikom-secrets/windows-stable-public.der"),
            pwd.getpwnam("celikom-windows-intake").pw_uid)
