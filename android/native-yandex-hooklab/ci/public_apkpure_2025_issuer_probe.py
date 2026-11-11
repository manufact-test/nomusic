#!/usr/bin/env python3
"""Ephemeral PUBLIC APKPure historic 2025 GPR candidate — signer gate, NO install.

No auth, private/undocumented API calls or browser security bypass: only public
download URL pattern previously established by this repo for publisher-signed
2026 APKPure source. A THIRD PARTY mirror is never trusted until the exact
issuer signature and 2025 package/version verify with Android SDK. All bytes
remain in TemporaryDirectory and are never uploaded, logged or executed.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from uptodown_2025_gpr_ephemeral_verify import unbundle_candidate, verify_split_set
from publisher_2025_provenance_gate import GateError

PACKAGE = "ru.yandex.music"
LIMIT = 170 * 1024 * 1024
HOSTS = ("apkpure.com", "apkpure.net", "winudf.com", "winudf.net")

def allow_url(url: str) -> str:
    parsed=urllib.parse.urlsplit(url)
    host=(parsed.hostname or "").lower()
    if (parsed.scheme!="https" or parsed.username or parsed.password
            or parsed.port not in (None,443)
            or not any(host==h or host.endswith("."+h) for h in HOSTS)):
        raise GateError("UNTRUSTED_PUBLIC_ARCHIVE_REDIRECT")
    return url

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        allow_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

OPENER=urllib.request.build_opener(SafeRedirect())

def read_candidate(url: str, path: Path) -> tuple[int,str]:
    allow_url(url)
    request=urllib.request.Request(url,headers={
        "User-Agent":"Mozilla/5.0 (compatible; CELIKOM read-only app compatibility)",
        "Accept":"application/octet-stream,application/zip,*/*",
    })
    digest=hashlib.sha256()
    total=0
    with OPENER.open(request,timeout=75) as response, path.open("wb") as output:
        if response.status!=200:
            raise GateError("PUBLIC_MIRROR_HTTP_NON_200")
        declared=int(response.headers.get("Content-Length") or "0")
        if declared>LIMIT:
            raise GateError("PUBLIC_MIRROR_SIZE_CAP")
        while chunk:=response.read(1024*1024):
            total+=len(chunk)
            if total>LIMIT:
                raise GateError("PUBLIC_MIRROR_SIZE_CAP")
            output.write(chunk)
            digest.update(chunk)
    if total<4096 or not zipfile.is_zipfile(path):
        raise GateError("PUBLIC_MIRROR_NOT_APK_ARCHIVE")
    return total,digest.hexdigest()


def main() -> int:
    base="https://d.apkpure.com/b/"
    paths=[
        "XAPK/"+PACKAGE+"?version="+urllib.parse.quote("2025.10.4 #120.1gpr",safe=""),
        "APK/"+PACKAGE+"?version="+urllib.parse.quote("2025.10.4 #120.1gpr",safe=""),
        "XAPK/"+PACKAGE+"?version=24025542",
        "APK/"+PACKAGE+"?version=24025542",
    ]
    outcomes=[]
    for i,endpoint in enumerate(paths):
        try:
            with tempfile.TemporaryDirectory(prefix="celikom-apkpure-2025-ephemeral-") as folder:
                work=Path(folder)
                candidate=work/"candidate-untrusted.zip"
                size,sha=read_candidate(base+endpoint,candidate)
                parts=unbundle_candidate(candidate,work)
                result=verify_split_set(parts)
                print(json.dumps({
                    "verdict":"PUBLIC_2025_GPR_ISSUER_SIGNED_SOURCE_CONFIRMED",
                    "mirror":"APKPURE_PUBLIC_BINARY",
                    "candidate_attempt_number":i+1,
                    "source_independently_publisher_authorized":False,
                    "original_source_sha256":sha,"original_source_size":size,
                    **result,
                    "original_apk_modified":False,
                    "original_apk_installed":False,
                    "original_apk_uploaded_or_published":False,
                    "stage_a":"NO_GO",
                },sort_keys=True))
                return 0
        except (urllib.error.HTTPError,urllib.error.URLError,OSError,ValueError,
                GateError,zipfile.BadZipFile) as error:
            if isinstance(error,urllib.error.HTTPError):
                status=error.code
                outcome="HTTP_"+str(status) if status in (400,401,403,404,429,500,502,503) else "HTTP_OTHER"
            elif isinstance(error,GateError):
                outcome=str(error)[:90]
            else:
                outcome="MIRROR_ARCHIVE_OR_NETWORK_UNVERIFIED"
            outcomes.append(outcome)
            # A successful HTTP download signed by a different entity must
            # never be retried as a valid old original or quietly accepted.
    print(json.dumps({
        "verdict":"NO_PUBLIC_2025_GPR_ISSUER_VERIFIED_APK_FROM_DOCUMENTED_SOURCE",
        "attempts":len(outcomes),
        "bounded_outcomes":outcomes,
        "publisher_cert_verified":False,
        "apk_installed":False,
        "apk_distributed":False,
        "stage_a":"NO_GO",
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
