"""Tightly bounded repair of origin ZIP CRC or overlapping-entry directory metadata.

An upstream metaloader output may contain a STORED nested origin.apk whose
central-directory CRC does not match its intact bytes. This repairs only ZIP
container bookkeeping, preserves every uncompressed entry byte and re-signs
ONLY the independent clone with its existing ephemeral research key.
Never uses publisher credentials/signature or modifies the genuine Yandex APK.
"""
from __future__ import annotations

import copy
import io
import struct
import zipfile
import zlib
from pathlib import Path

HOST = "assets/lspatch/origin.apk"
MAX_ORIGIN = 128 * 1024 * 1024
MAX_UNCOMPRESSED = 512 * 1024 * 1024
MAX_ENTRIES = 10000

def raw_stored_member(archive: Path, info: zipfile.ZipInfo) -> bytes:
    """Manual raw member read ONLY for known STORED member with invalid CRC."""
    if (info.filename != HOST or info.compress_type != zipfile.ZIP_STORED or
            info.file_size != info.compress_size or
            not 0 < info.file_size <= MAX_ORIGIN):
        raise ValueError("NOT_EXACT_EXPECTED_STORED_ORIGIN")
    with archive.open("rb") as fh:
        fh.seek(info.header_offset)
        header = fh.read(30)
        if len(header) != 30 or header[:4] != b"PK\x03\x04":
            raise ValueError("INVALID_LOCAL_ZIP_HEADER")
        name_size, extra_size = struct.unpack_from("<HH", header, 26)
        if name_size > 256 or extra_size > 65535:
            raise ValueError("LOCAL_ZIP_HEADER_BOUNDS")
        actual_name = fh.read(name_size)
        if actual_name != HOST.encode("ascii"):
            raise ValueError("LOCAL_ZIP_MEMBER_NAME_MISMATCH")
        fh.seek(info.header_offset + 30 + name_size + extra_size)
        data = fh.read(info.file_size)
        if len(data) != info.file_size:
            raise ValueError("STORED_MEMBER_TRUNCATED")
    if not zipfile.is_zipfile(io.BytesIO(data)):
        raise ValueError("RAW_EMBEDDED_ORIGIN_NOT_APK")
    return data


def rewrite_only_if_origin_crc_mismatch(input_apk: Path,
                                        output_apk: Path) -> dict:
    """Pure ZIP operation: no SDK, signer, uploader, installer or network."""
    if output_apk.exists() or input_apk.resolve() == output_apk.resolve():
        raise ValueError("NEW_SEPARATE_OUTPUT_REQUIRED")
    with zipfile.ZipFile(input_apk) as src:
        entries = src.infolist()
        if len(entries) > MAX_ENTRIES or len(set(x.filename for x in entries)) != len(entries):
            raise ValueError("UNSAFE_DUPLICATE_OR_EXCESS_ZIP_ENTRIES")
        if sum(x.file_size for x in entries) > MAX_UNCOMPRESSED:
            raise ValueError("UNSAFE_ZIP_UNCOMPRESSED_SIZE")
        if HOST not in src.namelist():
            raise ValueError("NESTED_ORIGIN_MEMBER_MISSING")
        entry = src.getinfo(HOST)
        raw = raw_stored_member(input_apk, entry)
        actual_crc = zlib.crc32(raw) & 0xffffffff
        crc_repaired = entry.CRC != actual_crc
        reading_error = None
        try:
            src.read(entry)
        except zipfile.BadZipFile as exc:
            message = str(exc).lower()
            if "overlapped entries" in message:
                reading_error = "OVERLAPPING_DIRECTORY_LAYOUT"
            elif "bad crc" in message:
                reading_error = "CRC_MISMATCH"
            else:
                raise ValueError("UNKNOWN_EMBEDDED_ORIGIN_ZIP_CORRUPTION") from None
        if reading_error is None:
            if entry.CRC != actual_crc:
                raise ValueError("ZIP_READER_AND_RAW_CRC_DISAGREE")
            return {"crc_repaired": False, "layout_repacked": False,
                    "verified_outer_entry_count": len(entries)}
        if reading_error == "CRC_MISMATCH" and not crc_repaired:
            raise ValueError("ZIP_CRC_ERROR_BUT_RAW_CRC_MATCHES")
        # Intact native/DEX payload will be independently SHA compared to
        # the verified original clone AFTER this ZIP container rebuild.
        with zipfile.ZipFile(output_apk, "w", allowZip64=True) as rebuilt:
            rebuilt.comment = src.comment
            for member in entries:
                try:
                    body = raw if member.filename == HOST else src.read(member)
                except (zipfile.BadZipFile, RuntimeError):
                    raise ValueError("UNRELATED_APK_ENTRY_CRC_OR_COMPRESSION_FAILURE") from None
                # ZipFile recomputes CRC from plaintext, handles central + local
                # records consistently. Preserve every member's uncompressed
                # bytes and compression/metadata; no source DEX modifications.
                clone_info = copy.copy(member)
                clone_info.CRC = clone_info.compress_size = clone_info.file_size = 0
                if (member.filename.startswith("assets/lspatch/so/")
                        and member.filename.endswith("/liblspatch.so")
                        and member.compress_type == zipfile.ZIP_STORED):
                    # ZIP metadata rebuild MUST preserve 4096-byte direct-map
                    # layout for the native metaloader's STORED ELF assets.
                    # Use a well-formed extra-field padding record. This does
                    # not touch any library or embedded original bytes.
                    position = rebuilt.fp.tell()
                    utf8_name = member.filename.encode("utf-8")
                    padding = (-(position + 30 + len(utf8_name)
                                 + len(clone_info.extra))) % 4096
                    if 0 < padding < 4:
                        padding += 4096
                    if padding:
                        if len(clone_info.extra) + padding > 65535:
                            raise ValueError("LOADER_ZIP_ALIGNMENT_EXTRA_TOO_LARGE")
                        clone_info.extra += (struct.pack("<HH", 0xEFA1, padding - 4)
                                             + bytes(padding - 4))
                rebuilt.writestr(clone_info, body, compress_type=member.compress_type)
    with zipfile.ZipFile(output_apk) as check:
        for entry in check.infolist():
            try:
                check.read(entry)
            except (zipfile.BadZipFile, RuntimeError):
                raise ValueError("REBUILT_APK_MEMBER_CRC_FAILED") from None
    return {"crc_repaired": crc_repaired,
            "layout_repacked": True,
            "repacked_reason": reading_error,
            "verified_outer_entry_count": len(entries)}
