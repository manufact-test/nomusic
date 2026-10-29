"""Shared byte-for-byte APK archive guard.

Used by both the signed release verifier and explicitly unsigned inspection.
No credentials, network calls or mutation. Strict asset allowlist prevents silent
insertion of resources as well as modification/removal of original catalogue.
"""
from pathlib import Path
from zipfile import ZipFile
import re

RECOVERY = "assets/identity-integration-source.zip"
FORBIDDEN = (".java", ".py", ".ts", ".map", ".p12", ".jks", ".pem", ".zip")
DEX_NAMES = ["classes.dex", "classes2.dex"]


def inspect_zip(rebuilt, original, compiled_dex):
    """Accept file paths or opened ZipFile objects; raise on any divergence."""
    with ZipFile(rebuilt) if not isinstance(rebuilt, ZipFile) else _borrow(rebuilt) as apk:
        with ZipFile(original) if not isinstance(original, ZipFile) else _borrow(original) as base:
            members = apk.namelist()
            if len(members) != len(set(members)):
                raise ValueError("Duplicate ZIP entries in packaged APK")
            if any(n.startswith("/") or "\\" in n or ".." in n.split("/") for n in members):
                raise ValueError("Unsafe path inside APK ZIP")
            found_dex = sorted(n for n in members if re.fullmatch(r"classes\d*\.dex", n))
            if found_dex != DEX_NAMES:
                raise ValueError("Missing, duplicate or extra DEX files")
            expected_dex = compiled_dex if isinstance(compiled_dex, bytes) else Path(compiled_dex).read_bytes()
            if apk.read("classes2.dex") != expected_dex:
                raise ValueError("Addon DEX is not byte-identical to trusted compilation")
            if not expected_dex.startswith(b"dex\n"):
                raise ValueError("Invalid compiled DEX header")
            if RECOVERY in members:
                raise ValueError("Recovered source embedded in APK")
            if any(name.lower().endswith(FORBIDDEN) for name in members):
                raise ValueError("Development or signing material embedded in APK")
            orig_assets = {n for n in base.namelist() if n.startswith("assets/") and n != RECOVERY}
            built_assets = {n for n in members if n.startswith("assets/")}
            if built_assets != orig_assets:
                raise ValueError("Unexpected added/removed assets: "+str(sorted(built_assets ^ orig_assets)))
            for name in orig_assets:
                if apk.read(name) != base.read(name):
                    raise ValueError("Modified original asset: "+name)
            return {"asset_count": len(orig_assets), "dex_count": len(found_dex),
                    "archive_entries": len(members), "original_assets_unchanged": True}


class _borrow:
    """Context manager that does not close caller-owned ZipFile handles."""
    def __init__(self, zipfile):
        self.zipfile = zipfile
    def __enter__(self):
        return self.zipfile
    def __exit__(self, *_):
        return False
