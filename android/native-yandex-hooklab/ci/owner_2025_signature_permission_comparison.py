"""Read-only exact-package Android 13 permission-grant A/B for signer controls.

Same original package name ru.yandex.music is used sequentially:
first issuer-signed APKs, then independently signed lab APKs, same clean guest.
Does not mutate permission grants, package identity, signatures or app logic.
Only bounded GROUP counts and a fixed named public READ_CREDENTIALS indicator
are returned. Raw Android dumpsys never leaves disposable CI.
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import native_arm13_platform_contract as permission

PACKAGE=permission.ORIGINAL
MAX=500

def compare_issuer_own_signer_package_grants(
    issuer_dumpsys: str, own_dumpsys: str
) -> dict:
    issuer=permission._parse(issuer_dumpsys,PACKAGE)
    own=permission._parse(own_dumpsys,PACKAGE)
    if not issuer["available"] or not own["available"]:
        return {"result":"INCONCLUSIVE_PACKAGE_MANAGER_SNAPSHOT",
                "source_dumpsys_exposed":False,
                "grant_mutation_attempted":False}
    requested_equal=issuer["requested"]==own["requested"]
    def grants(record):
        return {name for kind in ("install","runtime")
                for name,allowed in record[kind].items() if allowed}
    a,b=grants(issuer),grants(own)
    dropped=a-b
    gained=b-a
    issuer_focus=issuer["install"].get(permission.FOCUS)
    own_focus=own["install"].get(permission.FOCUS)
    def indicator(value):
        return ("GRANTED" if value is True else
                "DENIED" if value is False else "NOT_LISTED")
    return {
        "result":"SAME_PACKAGE_SIGNER_GRANT_DIFFERENTIAL",
        "requested_permissions_exactly_equal":requested_equal,
        "issuer_requested_count_bounded":min(MAX,len(issuer["requested"])),
        "own_requested_count_bounded":min(MAX,len(own["requested"])),
        "issuer_granted_count_bounded":min(MAX,len(a)),
        "own_granted_count_bounded":min(MAX,len(b)),
        "issuer_only_grant_count_bounded":min(MAX,len(dropped)),
        "own_only_grant_count_bounded":min(MAX,len(gained)),
        "issuer_only_grant_families":permission._counts(dropped),
        "own_only_grant_families":permission._counts(gained),
        "issuer_focus_credential_install_grant":indicator(issuer_focus),
        "own_focus_credential_install_grant":indicator(own_focus),
        "read_only_aosp_packagemanager_metadata":True,
        "source_dumpsys_exposed":False,
        "permission_names_except_known_focus_exposed":False,
        "grant_mutation_attempted":False,
        "signature_permission_bypass_attempted":False,
        "permission_mismatch_does_not_prove_java_crash_causation":True,
    }
