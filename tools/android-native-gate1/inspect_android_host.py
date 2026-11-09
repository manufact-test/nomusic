#!/usr/bin/env python3
"""Read-only structural inventory of Android APK/XAPK DEX media-source candidates.

Never executes APK content, collects app data, hooks playback or probes credentials.
A structural library match is NOT proof of an actual Yandex source-replacement hook.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import struct
import sys
import zipfile
from functools import lru_cache
from pathlib import Path

DEX_MAX = 128 * 1024 * 1024
MAX_TABLE_ITEMS = 1_000_000
MAX_METHODS_PER_DEX = 80

TARGET_FAMILIES = {
    "media3": (
        "Landroidx/media3/exoplayer/source/DefaultMediaSourceFactory;",
        "Landroidx/media3/exoplayer/source/ProgressiveMediaSource$Factory;",
        "Landroidx/media3/exoplayer/ExoPlayerImpl;",
        "Landroidx/media3/common/MediaItem;",
        "Landroidx/media3/datasource/DefaultDataSource;",
    ),
    "exoplayer2": (
        "Lcom/google/android/exoplayer2/source/DefaultMediaSourceFactory;",
        "Lcom/google/android/exoplayer2/source/ProgressiveMediaSource$Factory;",
        "Lcom/google/android/exoplayer2/ExoPlayerImpl;",
        "Lcom/google/android/exoplayer2/MediaItem;",
        "Lcom/google/android/exoplayer2/upstream/DefaultDataSource;",
    ),
}
METHOD_NAMES = {
    "createMediaSource", "setMediaSource", "setMediaSources", "setMediaItem",
    "setMediaItems", "prepare", "getMediaItemAt", "getCurrentMediaItem",
    "open", "createDataSource",
}


class DexError(ValueError):
    """Malformed or unsupported DEX file."""


class Dex:
    def __init__(self, data: bytes):
        self.data = memoryview(data)
        if (len(data) < 112 or data[:4] != b"dex\n" or data[7] != 0
                or data[4:7] not in (b"035", b"036", b"037", b"038", b"039", b"040", b"041")):
            raise DexError("Unsupported DEX magic/version")
        if self.u32(32) != len(data):
            raise DexError("DEX header file_size mismatch")
        self.string_count, self.string_offset = self.table(56, 4)
        self.type_count, self.type_offset = self.table(64, 4)
        self.proto_count, self.proto_offset = self.table(72, 12)
        self.method_count, self.method_offset = self.table(88, 8)
        self.class_count, self.class_offset = self.table(96, 32)

    def bounds(self, offset: int, size: int):
        if offset < 0 or size < 0 or offset + size > len(self.data):
            raise DexError("DEX offset outside file")

    def u16(self, offset: int) -> int:
        self.bounds(offset, 2)
        return struct.unpack_from("<H", self.data, offset)[0]

    def u32(self, offset: int) -> int:
        self.bounds(offset, 4)
        return struct.unpack_from("<I", self.data, offset)[0]

    def table(self, header_pos: int, item_size: int) -> tuple[int, int]:
        count, offset = self.u32(header_pos), self.u32(header_pos + 4)
        if count > MAX_TABLE_ITEMS:
            raise DexError("DEX table count too large")
        if count:
            self.bounds(offset, count * item_size)
        return count, offset

    @lru_cache(maxsize=8192)
    def string(self, index: int) -> str:
        if index < 0 or index >= self.string_count:
            raise DexError("Invalid DEX string index")
        offset = self.u32(self.string_offset + 4 * index)
        for _ in range(5):
            self.bounds(offset, 1)
            value = self.data[offset]
            offset += 1
            if not (value & 0x80):
                break
        else:
            raise DexError("Invalid DEX string ULEB128")
        self.bounds(offset, 1)
        # DEX MUTF-8 strings can be substantially longer than 4096 bytes.
        # Scan only to the terminator, capped at 1MiB for malicious input.
        start = offset
        limit = min(len(self.data), start + 1024 * 1024)
        while offset < limit and self.data[offset] != 0:
            offset += 1
        if offset >= limit:
            raise DexError("DEX string terminator missing or length exceeds 1MiB")
        return self.data[start:offset].tobytes().decode("utf-8", errors="replace")

    @lru_cache(maxsize=4096)
    def descriptor(self, index: int) -> str:
        if index < 0 or index >= self.type_count:
            raise DexError("Invalid DEX type index")
        return self.string(self.u32(self.type_offset + 4 * index))

    @lru_cache(maxsize=4096)
    def prototype(self, index: int) -> str:
        pos = self.proto_offset + index * 12
        ret_idx, params_off = self.u32(pos + 4), self.u32(pos + 8)
        args = []
        if params_off:
            count = self.u32(params_off)
            if count > 128:
                raise DexError("Too many method parameters")
            self.bounds(params_off + 4, count * 2)
            args = [self.descriptor(self.u16(params_off + 4 + i * 2)) for i in range(count)]
        return "(" + "".join(args) + ")" + self.descriptor(ret_idx)

    def method(self, index: int) -> tuple[str, str, str]:
        pos = self.method_offset + 8 * index
        class_idx, proto_idx, name_idx = struct.unpack_from("<HHI", self.data, pos)
        if proto_idx >= self.proto_count:
            raise DexError("Invalid DEX prototype index")
        return self.descriptor(class_idx), self.string(name_idx), self.prototype(proto_idx)

    def defined_classes(self) -> set[str]:
        return {
            self.descriptor(self.u32(self.class_offset + i * 32))
            for i in range(self.class_count)
        }

    def candidates(self) -> dict:
        defined = self.defined_classes()
        hits = []
        count = 0
        for i in range(self.method_count):
            klass, name, signature = self.method(i)
            if name not in METHOD_NAMES:
                continue
            family = next(
                (fam for fam, members in TARGET_FAMILIES.items() if klass in members),
                None
            )
            if family is None:
                continue
            count += 1
            if len(hits) < MAX_METHODS_PER_DEX:
                hits.append({
                    "family": family, "class": klass, "method": name,
                    "signature": signature, "defined_in_this_dex": klass in defined
                })
        return {
            "defined_media_libraries": sorted(
                family for family, classes in TARGET_FAMILIES.items()
                if any(c in defined for c in classes)
            ),
            "method_references": hits, "method_reference_count": count,
            "class_count": self.class_count, "method_count": self.method_count
        }


def inspect_apk_zip(z: zipfile.ZipFile, digest: str, label: str) -> dict | None:
    names = sorted(n for n in z.namelist()
                   if n.startswith("classes") and n.endswith(".dex") and "/" not in n)
    if not names:
        return None  # Native/density/config-only split, no DEX.
    if len(names) > 64:
        raise ValueError("Too many DEX entries")
    report = {"apk_sha256": digest, "split_label": label, "dex": []}
    for name in names:
        info = z.getinfo(name)
        if info.file_size > DEX_MAX:
            raise ValueError("DEX exceeds static-analysis size limit")
        with z.open(info) as stream:
            data = stream.read(DEX_MAX + 1)
        if len(data) != info.file_size:
            raise ValueError("DEX read length mismatch")
        report["dex"].append({"entry": name, **Dex(data).candidates()})
    return report


def inspect_file(path: Path) -> list[dict]:
    """Read an APK or split-APK XAPK/APKS without extraction or installation."""
    if not zipfile.is_zipfile(path):
        raise ValueError("Not a valid APK/XAPK/APKS ZIP")
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    with zipfile.ZipFile(path, "r") as z:
        direct = inspect_apk_zip(z, digest, path.name)
        if direct is not None:
            return [direct]
        names = sorted(n for n in z.namelist()
                       if n.lower().endswith(".apk") and not n.startswith("__MACOSX/"))
        if not names:
            raise ValueError("Archive contains no DEX or embedded APK splits")
        if len(names) > 32:
            raise ValueError("Too many embedded APK splits")
        results = []
        for name in names:
            info = z.getinfo(name)
            if info.file_size > DEX_MAX:
                raise ValueError("Embedded APK exceeds static-analysis size limit")
            raw = z.read(info)
            if len(raw) != info.file_size:
                raise ValueError("Embedded APK size mismatch")
            with zipfile.ZipFile(io.BytesIO(raw), "r") as split:
                candidate = inspect_apk_zip(split, hashlib.sha256(raw).hexdigest(), name)
                if candidate is not None:
                    results.append(candidate)
        if not results:
            raise ValueError("Bundle APKs contain no DEX")
        return results


def inspect(paths: list[Path]) -> dict:
    if not paths or len(paths) > 32:
        raise ValueError("Expected 1..32 APK/XAPK paths")
    outputs = [result for path in paths for result in inspect_file(path)]
    return {
        "purpose": "READ_ONLY_NATIVE_HOST_API_INVENTORY",
        "apk_with_dex_count": len(outputs),
        "apks": outputs,
        "verdict": "NO_NATIVE_SOURCE_HOOK_PROVEN",
        "reason": (
            "DEX signatures alone do NOT prove executed source selection, "
            "exact Yandex track+edition identity, rootless installation, "
            "signer trust or Play Protect acceptance. Requires audited "
            "in-process test-host witness."
        )
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apks", nargs="+", type=Path,
                        help="APK(s), XAPK or APKS bundle; no app-private data is read")
    parser.add_argument("--output", type=Path,
                        help="optional LOCAL JSON path; never commit proprietary logs")
    args = parser.parse_args(argv)
    try:
        report = inspect(args.apks)
        payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")
        return 0
    except (DexError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"STATIC_HOST_INSPECT_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
