#!/usr/bin/env python3
"""Parse the exact owner-enrolled pinned-host + OpenSSH key bundle.

Only harmless clipboard whitespace is normalized. Never print enrolled material,
infer missing key contents, obtain new host keys or disable SSH verification.
"""
import base64
import os
import pathlib
import re
import sys


def parse(raw):
    if len(raw) > 24576:
        raise ValueError("WINDOWS_INTAKE_ENROLLMENT_TOO_LARGE")
    envelope = b"CELIKOM-WINDOWS-INTAKE-V1:"
    cleaned = raw.strip()
    if cleaned.startswith(envelope):
        try:
            raw = base64.b64decode(cleaned[len(envelope):], validate=True)
        except (ValueError, TypeError):
            raise ValueError("WINDOWS_INTAKE_ENROLLMENT_ENVELOPE_INVALID") from None
    if len(raw) > 16384:
        raise ValueError("WINDOWS_INTAKE_ENROLLMENT_TOO_LARGE")
    try:
        lines = raw.decode("utf-8-sig").splitlines()
    except UnicodeError:
        raise ValueError("WINDOWS_INTAKE_ENROLLMENT_ENCODING_INVALID") from None
    lines = [x.strip() for x in lines if x.strip()]
    if len(lines) < 4:
        raise ValueError("WINDOWS_INTAKE_ENROLLMENT_LINES_INVALID")
    parts = lines[0].split()
    if len(parts) != 3 or parts[:2] != ["95.133.160.111", "ssh-ed25519"]:
        # Fixed classifications only. Never log any actual input or key material.
        if lines[0].startswith("-----BEGIN "):
            kind = "PRIVATE_KEY_FIRST"
        elif parts[:2] == ["95.133.160.111", "ssh-ed25519"]:
            kind = "HOST_PIN_EXTRA_OR_MISSING_FIELDS"
        elif parts and parts[0] == "95.133.160.111":
            kind = "HOST_PIN_ALGORITHM_OR_FIELDS"
        elif any(x.split()[:2] == ["95.133.160.111", "ssh-ed25519"] for x in lines[1:]):
            kind = "EXTRA_LEADING_TEXT"
        elif "\\n" in lines[0]:
            kind = "LITERAL_NEWLINE_ESCAPES"
        else:
            kind = "UNRECOGNIZED_FIRST_LINE"
        raise ValueError("WINDOWS_INTAKE_HOST_PIN_LINE_INVALID_" + kind)
    try:
        host_key = base64.b64decode(parts[2], validate=True)
    except (ValueError, TypeError):
        raise ValueError("WINDOWS_INTAKE_HOST_PIN_ENCODING_INVALID") from None
    if len(host_key) != 51 or host_key[:19] != b"\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20":
        raise ValueError("WINDOWS_INTAKE_HOST_PIN_TYPE_INVALID")
    if lines[1] != "-----BEGIN OPENSSH PRIVATE KEY-----" or lines[-1] != "-----END OPENSSH PRIVATE KEY-----":
        raise ValueError("WINDOWS_INTAKE_PRIVATE_KEY_BOUNDARY_INVALID")
    if not all(re.fullmatch(r"[A-Za-z0-9+/=]+", x) for x in lines[2:-1]):
        raise ValueError("WINDOWS_INTAKE_PRIVATE_KEY_TEXT_INVALID")
    return " ".join(parts) + "\n", "\n".join(lines[1:]) + "\n"


def main():
    try:
        if len(sys.argv) != 3:
            raise ValueError("WINDOWS_INTAKE_PARSER_ARGUMENTS_INVALID")
        pin, key = parse(pathlib.Path(sys.argv[1]).read_bytes())
        target = pathlib.Path(sys.argv[2])
        for name, value in (("known_hosts", pin), ("key", key)):
            fd = os.open(target / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(value)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
    print("WINDOWS_INTAKE_ENROLLMENT_FORMAT_OK")


if __name__ == "__main__":
    main()
