"""Portable negative test: never trust an unsigned APK or altered catalogue."""
from pathlib import Path
import sys
import warnings
from io import BytesIO
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from release_archive import inspect_zip, RECOVERY

DEX = b"dex\n" + bytes(48)
SOURCE = b"dex\n" + bytes(48) + b"old"
ASSETS = {"assets/music-catalogue.json": b"ORIGINAL", "assets/logo.png": b"IMAGE"}


def zipped(entries):
    stream = BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with ZipFile(stream, "w") as out:
            for key, value in entries:
                out.writestr(key, value)
    stream.seek(0)
    return stream


baseline = [("classes.dex", SOURCE), (RECOVERY, b"secret recovery source"), *ASSETS.items()]
valid = [("classes.dex", SOURCE), ("classes2.dex", DEX), *ASSETS.items()]
checks = 0


def inspect(items, expected=DEX):
    with ZipFile(zipped(items)) as candidate, ZipFile(zipped(baseline)) as original:
        return inspect_zip(candidate, original, expected)


result = inspect(valid)
assert result["dex_count"] == 2 and result["asset_count"] == 2
checks += 1


def bad(items, label, dex=DEX):
    global checks
    try:
        inspect(items, dex)
    except (ValueError, KeyError):
        checks += 1
        return
    raise AssertionError("Unsafe APK archive accepted: "+label)


bad(valid + [("classes2.dex", DEX)], "duplicate DEX name")
bad([x for x in valid if x[0] != "classes2.dex"], "missing addon DEX")
bad(valid + [("classes3.dex", DEX)], "third hidden decoder DEX")
bad([(k, (b"modified" if k == "classes2.dex" else v)) for k,v in valid], "stale addon DEX")
bad(valid, "modified trusted CI DEX argument", DEX + b"tampered")
bad([(k, (b"edited" if k == "assets/music-catalogue.json" else v)) for k,v in valid], "modified catalogue")
bad([x for x in valid if x[0] != "assets/music-catalogue.json"], "deleted original catalogue")
bad(valid + [("assets/unexpected.json", b"hidden")], "injected asset")
bad(valid + [(RECOVERY, b"full source")], "recovered source")
bad(valid + [("assets/keystore.p12", b"secret")], "embedded keystore")
bad(valid + [("assets/config.PEM", b"secret")], "case insensitive secret extension")
bad(valid + [("../outside/file", b"escape")], "path traversal")
bad(valid + [("/absolute", b"escape")], "absolute path")
bad(valid + [("src\\backslash", b"escape")], "backslash in archive")
bad(valid, "non DEX compilation", b"not_dex")

print("PASS:", checks, "release archive guard and tampered APK negative tests")
