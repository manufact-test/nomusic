#!/usr/bin/env python3
"""Prepare a private migration-only legacy stable source checkout.

The archived owner-accepted 0.3.92 remains untouched. This is neither A1 nor
the unaccepted 0.3.93/Test.50 candidate. No APK signing, delivery or publication.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess

BASE = "8a215d59432d9b6d11ab1971af6189cd230b52f3"
BASE_VERSION = "0.3.92"
BASE_CODE = 93
# Code 94 belongs to the distinct unaccepted 0.3.93 staging candidate.
VERSION = "0.3.94"
CODE = 95
SIGNER = "67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f"
BASE_APK = "170b1883e292570d28a3b5c619cf000eaccd9d11ee85ca6f6c08f7b50e5f72c9"
OLD_API = "darkred-camel-588676.hostingersite.com"
OLD_UPDATER = "lemonchiffon-narwhal-791953.hostingersite.com"
API = "api.celikom.com"
UPDATER = "celikom.com"
PREFIX = "android/native-companion/"
JAVA = "addon/src/pro/celikom/nativeprobe/identitydiag/"


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True, timeout=60).stdout.strip()


def replace_once(raw, old, new):
    require(raw.count(old) == 1, "EXACT_BASE_SOURCE_MISMATCH")
    return raw.replace(old, new)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", required=True, type=pathlib.Path)
    args = parser.parse_args()
    checkout = args.checkout.resolve(strict=True)
    require(git(checkout, "rev-parse", "HEAD") == BASE, "WRONG_OWNER_ACCEPTED_BASE")
    require(not git(checkout, "status", "--porcelain"), "SOURCE_CHECKOUT_DIRTY")
    root = checkout / PREFIX
    spec = json.loads((root / "release-spec.json").read_bytes())
    require(spec == dict(version=BASE_VERSION, version_code=BASE_CODE,
                         previous_rejected_version="0.3.51", previous_rejected_code=52,
                         package="pro.celikom.nativeprobe", signing_certificate_sha256=SIGNER),
            "BASE_RELEASE_IDENTITY_CHANGED")
    require(json.loads((root / "build-inputs.json").read_bytes())["base_apk_sha256"] == BASE_APK,
            "BASE_APK_PIN_CHANGED")
    spec.update(version=VERSION, version_code=CODE)
    changes = {}
    for name, old, new in [
        (JAVA + "ApiContract.java", 'ORIGIN="https://' + OLD_API + '"', 'ORIGIN="https://' + API + '"'),
        (JAVA + "UpdateCenter.java", 'HOST="' + OLD_UPDATER + '"', 'HOST="' + UPDATER + '"'),
        (JAVA + "AppVersion.java", 'NAME="' + BASE_VERSION + '"', 'NAME="' + VERSION + '"'),
        ("addon/TestContracts.java", "http://" + OLD_API + "/api/v1/audio/7?",
         "http://" + API + "/api/v1/audio/7?"),
    ]:
        changes[name] = replace_once((root / name).read_text(encoding="utf-8"), old, new)
    # Verify that old signed endpoints do not become alternate allowed hosts.
    test = changes["addon/TestContracts.java"]
    changes["addon/TestContracts.java"] = replace_once(
        test, 'now,"cross-origin audio");',
        'now,"cross-origin audio");\n'
        '  rejects(copy(good).put("audio_url","https://' + OLD_API +
        '/api/v1/audio/7?"+query),now,"retired API origin rejected");')
    # Update only version-expectation fixtures in the original release-contract
    # tests. Keep all negative, signer, installer and archive safety assertions.
    name = "tests/check_release_contract.py"
    test = (root / name).read_text(encoding="utf-8")
    require('"0.3.92"' in test and "versionCode: 93" in test, "RELEASE_TEST_BASE_CHANGED")
    test = test.replace('("0.3.92", 93)', '("0.3.94", 95)')
    test = test.replace('NAME="0.3.92"', 'NAME="0.3.94"')
    test = test.replace('"0.3.92", 93)', '"0.3.94", 95)')
    test = test.replace("versionCode: 93", "versionCode: 95").replace("versionName: 0.3.92", "versionName: 0.3.94")
    test = replace_once(test, 'must_reject(dict(data,version_code=92),java,"previous code")',
                        'must_reject(dict(data,version_code=92),java,"previous code")\n'
                        'must_reject(dict(data,version="0.3.92",version_code=93),java,"retired stable code")\n'
                        'must_reject(dict(data,version="0.3.93",version_code=94),java,"unaccepted staging code")')
    changes[name] = test
    changes["release-spec.json"] = json.dumps(spec, indent=2) + "\n"

    for name, content in changes.items():
        path = root / name
        require(path.is_file() and not path.is_symlink(), "UNSAFE_SOURCE_FILE")
        path.write_text(content, encoding="utf-8")
    modified = set(git(checkout, "diff", "--name-only").splitlines())
    require(modified == {PREFIX + n for n in changes}, "UNEXPECTED_SOURCE_MUTATION")
    # Runtime source only: historical documentation, negative tests and old
    # frozen workflows may legitimately mention the retired host.
    runtime = root / "addon/src"
    for path in runtime.rglob("*.java"):
        raw = path.read_text(encoding="utf-8")
        if "hostingersite.com" in raw:
            raise ValueError("UNMIGRATED_RUNTIME_ORIGIN:" + str(path.relative_to(root)))
    # Never alter immutable audio/source algorithms, signer or build inputs.
    for name in ("ReplacementEngine.java", "AudioOwnership.java", "ProbeService.java",
                 "NativeApi.java", "AlbumProbe.java"):
        require(git(checkout, "diff", "--", PREFIX + JAVA + name) == "",
                "PLAYBACK_OR_CATALOGUE_SOURCE_CHANGED")
    print("CELIKOM_LEGACY_BRIDGE_SOURCE_PREPARED", BASE, VERSION, CODE,
          "changed_files=" + str(len(changes)))
    print("CELIKOM_LEGACY_BRIDGE_SOURCE_ONLY_NO_SIGNING_NO_PUBLICATION")


if __name__ == "__main__":
    main()
