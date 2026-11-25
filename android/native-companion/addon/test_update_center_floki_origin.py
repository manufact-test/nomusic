#!/usr/bin/env python3
"""Static regression for the future legacy stable updater source.
Not a live OTA or APK-installation test. This never activates the feed.
"""
from pathlib import Path

SOURCE = Path(__file__).parent / "src/pro/celikom/nativeprobe/identitydiag/UpdateCenter.java"
s = SOURCE.read_text(encoding="utf-8")

required = {
    'static final String HOST="celikom.com";': "new host",
    'static final String MANIFEST="https://"+HOST+"/updates/android/stable.json";': "new manifest",
    'static final String CERT="67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f";': "original stable signing pin",
    '"pro.celikom.nativeprobe".equals(j.getString("packageName"))': "stable package isolation",
    '"stable".equals(j.getString("channel"))': "stable channel isolation",
    'code<=current': "no downgrade",
    '"https://"+HOST+"/releases/android/"+code+"-"+sha+".apk"': "immutable same-origin filename",
    '!HOST.equals(target.getHost())': "no cross-origin connection",
    'c.setInstanceFollowRedirects(false);': "no URL redirect",
    'getApkContentsSigners()': "APK signature validation",
    '!CERT.equals(sha(signatures[0].toByteArray()))': "exact cert pin",
    'if(total!=r.size||!r.sha.equals(hex(digest.digest())))': "content hash verification",
}
for token, name in required.items():
    assert token in s, f"UPDATER_CONTRACT_LOST: {name}"
assert "hostingersite.com" not in s, "UPDATER_SOURCE_STILL_HOSTINGER"
assert s.count('static final String HOST="celikom.com";') == 1
assert 'static final String MANIFEST=' in s
print("CELIKOM_ANDROID_STABLE_FLOKINET_ORIGIN_SOURCE_PASS")
print("CAVEAT: old installations still need the signed v95 old-domain bridge; no public OTA enabled")
