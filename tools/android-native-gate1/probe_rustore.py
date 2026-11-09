#!/usr/bin/env python3
"""Metadata-only probe of official RuStore public Android showcase; never downloads APK."""
from __future__ import annotations
import json,sys,urllib.error,urllib.request

PKG="ru.yandex.music"
URL="https://backapi.rustore.ru/applicationData/overallInfo/"+PKG
EXPECTED_VERSION_CODE=24026531
EXPECTED_VERSION_NAME="2026.10.3 #170gpr"

def normalize(metadata:dict)->dict:
    body=metadata.get("body",{})
    if not isinstance(body,dict):
        raise ValueError("RuStore overallInfo missing body")
    if body.get("packageName")!=PKG:
        raise ValueError("Unexpected package name")
    version=str(body.get("versionName",""))
    code=body.get("versionCode")
    if not isinstance(code,int) or not version:
        raise ValueError("Missing version code/name")
    return {
        "package":PKG, "source":"RuStore public catalogue metadata",
        "version_name":version,"version_code":code,
        "exact_owner_gpr_build":code==EXPECTED_VERSION_CODE and version==EXPECTED_VERSION_NAME,
        "signing_claim":str(body.get("signature") or "")[:256],
        "source_note":"store metadata only; APK signature integrity not checked",
        "app_updated_at":str(body.get("appVerUpdatedAt") or "")[:64],
    }

def main():
    req=urllib.request.Request(URL,headers={
        "Accept":"application/json","ruStoreVerCode":"1000",
        "User-Agent":"CELIKOM-static-research/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=20) as response:
            if response.status!=200:raise ValueError("RuStore HTTP "+str(response.status))
            if int(response.headers.get("Content-Length") or 0)>1_000_000:
                raise ValueError("Unexpected metadata size")
            payload=response.read(1_000_001)
            if len(payload)>1_000_000:raise ValueError("Metadata too large")
        print(json.dumps(normalize(json.loads(payload)),ensure_ascii=False,indent=2))
        return 0
    except (urllib.error.URLError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("RUSTORE_METADATA_UNAVAILABLE: "+str(exc)[:300],file=sys.stderr)
        return 2

if __name__=="__main__":raise SystemExit(main())
