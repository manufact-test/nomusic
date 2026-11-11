#!/usr/bin/env python3
"""Documented PUBLIC Aptoide API metadata only; no vendor binary downloaded.

This third-party catalog is NOT the publisher: its metadata is only a candidate
discovery signal and never sufficient for APK acceptance or installation.
No private Aptoide endpoints, copied API keys, cookies or account credentials.
"""
from __future__ import annotations
import json
import urllib.error
import urllib.request

TARGET_CODE = 24025542
TARGET_PACKAGE = "ru.yandex.music"
TARGET_RUR = "2025.10.4 #120.1rur"
TARGET_GPR = "2025.10.4 #120.1gpr"
MAX_JSON = 512 * 1024
API_HOST = "https://ws2.aptoide.com"
# Public level 7 documented API: https://ws2.aptoide.com/api/7/app/getMeta?info=1
PATH = f"/api/7/app/getMeta/package_name={TARGET_PACKAGE}/vercode={TARGET_CODE}"


def classify(data: dict) -> dict:
    base = {
        "source": "PUBLIC_APTOIDE_APP_GETMETA_METADATA_ONLY",
        "third_party_catalog_not_issuer_attestation": True,
        "apk_downloaded": False,
        "publisher_2025_signing_verified": False,
        "native_2025_test_permitted": False,
    }
    if not isinstance(data, dict) or (data.get("info") or {}).get("status") != "OK":
        return {**base, "verdict": "CATALOG_TARGET_NOT_CONFIRMED"}
    entry = data.get("data")
    if not isinstance(entry, dict) or entry.get("package") != TARGET_PACKAGE:
        return {**base, "verdict": "CATALOG_PACKAGE_IDENTITY_NOT_CONFIRMED"}
    file = entry.get("file")
    if not isinstance(file, dict) or str(file.get("vercode")) != str(TARGET_CODE):
        return {**base, "verdict": "CATALOG_VERSION_CODE_NOT_CONFIRMED"}
    version = file.get("vername")
    if version == TARGET_RUR:
        verdict = "CATALOG_LISTS_TARGET_2025_RUR_UNTRUSTED_CANDIDATE"
    elif version == TARGET_GPR:
        verdict = "CATALOG_LISTS_ALTERNATE_2025_GPR_UNTRUSTED_CANDIDATE"
    else:
        verdict = "CATALOG_VERSION_NAME_NOT_TARGET"
    # Deliberately don't print the URL, file, store, sender or certificate text:
    # none of these are independently authenticated by the publisher.
    return {
        **base,
        "verdict": verdict,
        "exact_rur_claimed": verdict.endswith("RUR_UNTRUSTED_CANDIDATE"),
        "alternate_gpr_claimed": verdict.endswith("GPR_UNTRUSTED_CANDIDATE"),
        "historical_source_provenance_independently_verified": False,
    }


def probe() -> dict:
    request = urllib.request.Request(API_HOST + PATH, headers={
        "User-Agent": "CELIKOM-Android-A1-readonly-metadata/1.0",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(request, timeout=25) as response:
        if response.status != 200 or response.geturl().split("/")[2].lower() != "ws2.aptoide.com":
            raise ValueError("UNEXPECTED_REMOTE_ENDPOINT")
        raw = response.read(MAX_JSON + 1)
    if len(raw) > MAX_JSON:
        raise ValueError("METADATA_EXCEEDS_BOUNDED_LIMIT")
    return classify(json.loads(raw))


def main() -> int:
    try:
        output = probe()
    except (ValueError, urllib.error.URLError, OSError, TypeError):
        output = {
            "verdict": "PUBLIC_CATALOG_API_UNAVAILABLE",
            "apk_downloaded": False,
            "native_2025_test_permitted": False,
        }
    print(json.dumps(output, sort_keys=True))
    return 0  # Discovery not finding a candidate is not a test failure.


if __name__ == "__main__":
    raise SystemExit(main())
