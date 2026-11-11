#!/usr/bin/env python3
"""Only public official RuStore package metadata; no APK download or install.

A current-version metadata response is not evidence historical APK is available.
The missing historical binary may never be substituted with third-party MOD.
"""
from __future__ import annotations
import json
import urllib.request

URL = "https://backapi.rustore.ru/applicationData/overallInfo/ru.yandex.music"
TARGET_CODE = 24025542
TARGET_VERSION = "2025.10.4 #120.1rur"


def classify(data: dict) -> dict:
    body = data.get("body")
    if not isinstance(body, dict) or body.get("packageName") != "ru.yandex.music":
        return {"verdict": "OFFICIAL_STORE_METADATA_IDENTITY_UNVERIFIED",
                "historical_2025_binary_obtained": False}
    current = body.get("versionName")
    code = body.get("versionCode")
    matches = current == TARGET_VERSION and str(code) == str(TARGET_CODE)
    return {
        "verdict": "CURRENT_STORE_METADATA_MATCHES_TARGET_VERSION" if matches
                   else "CURRENT_STORE_METADATA_NOT_TARGET_2025_RELEASE",
        "current_store_version_name": current if isinstance(current, str) and len(current) < 75 else None,
        "historical_2025_binary_obtained": False,
        "publisher_2025_signing_verified": False,
        "historical_download_url_verified": False,
        "no_archive_api_exhaustiveness_claimed": True,
    }


def main() -> int:
    try:
        req = urllib.request.Request(URL, headers={
            "ruStoreVerCode": "1000", "Accept": "application/json",
            "User-Agent": "CELIKOM-readonly-native-A1-research/1.0",
        })
        with urllib.request.urlopen(req, timeout=35) as response:
            if response.status != 200:
                raise ValueError("STORE_HTTP_NON_200")
            blob = response.read(1024 * 1024 + 1)
        if len(blob) > 1024 * 1024:
            raise ValueError("STORE_METADATA_SIZE_EXCEEDED")
        print(json.dumps(classify(json.loads(blob)), sort_keys=True))
    except Exception:
        # Never print raw network responses, store tokens or unexpected host data.
        print(json.dumps({
            "verdict": "OFFICIAL_STORE_METADATA_CHECK_UNAVAILABLE",
            "historical_2025_binary_obtained": False,
            "native_2025_test_permitted": False,
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
