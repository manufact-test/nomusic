#!/usr/bin/env python3
"""Ephemeral offline Yandex #170gpr side-by-side clone *STRUCTURAL* trial.

No user device and no APK artifacts. This intentionally NEVER installs a
patched Yandex client, uses root, spoofs a publisher signature, accesses Yandex
accounts, or bypasses Play Protect. A clone's normal Yandex login and decoder
behavior are not established by a structural pass.
"""
from __future__ import annotations
import hashlib, io, json, os, re, subprocess, sys, tempfile, urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/"tools"/"android-native-gate1"))
import audit_gpr_apkpure_once as gpr
from audit_rustore_host_once import sdk_tool, RUSTORE_SHA256_CERT

SOURCE="ru.yandex.music"
DEST="pro.celikom.yandex.nativeclonelab"
APKTOOL_URL="https://github.com/iBotPeaches/Apktool/releases/download/v2.12.1/apktool_2.12.1.jar"
APKTOOL_SHA="66cf4524a4a45a7f56567d08b2c9b6ec237bcdd78cee69fd4a59c8a0243aeafa"
ARCHIVE_SHA="918bd50599dc6a942e190a409303e843b83dcb6d11b90b03c00240331333cf84"
ANDROID="http://schemas.android.com/apk/res/android"
MAX_MB=128
ET.register_namespace("android",ANDROID)

def action(cmd,reason,timeout=240):
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
    if p.returncode:
        if reason in ("APKTOOL_DECODE_FAILED", "APKTOOL_REBUILD_FAILED"):
            lines=(p.stderr+"\n"+p.stdout).lower()
            clue=("BAD_OPTION" if "unknown option" in lines or "unrecognized option" in lines else
                  "ANDROID_FRAMEWORK_MISSING" if "framework" in lines and "not found" in lines else
                  "MANIFEST_PARSE_FAILURE" if "manifest" in lines and ("error" in lines or "exception" in lines) else
                  "RESOURCE_DECODE_FAILURE" if "resource" in lines and ("error" in lines or "exception" in lines) else
                  "ZIP_ARCHIVE_FAILURE" if "zip" in lines and ("error" in lines or "exception" in lines) else
                  "JAVA_RUNTIME_FAILURE" if "classnotfound" in lines or "unsupportedclassversion" in lines else
                  "UNCLASSIFIED")
            # Only a category; no third-party contents, paths, or user data.
            raise ValueError(reason+"_"+clue)
        raise ValueError(reason)
    return p.stdout

def fetch_pin(file):
    with urllib.request.urlopen(APKTOOL_URL,timeout=120) as response, file.open("wb") as f:
        h=hashlib.sha256();total=0
        while True:
            part=response.read(1024*1024)
            if not part:break
            total+=len(part)
            if total>48*1024*1024:raise ValueError("APKTOOL_LIMIT")
            h.update(part);f.write(part)
    if h.hexdigest()!=APKTOOL_SHA:raise ValueError("APKTOOL_PIN_MISMATCH")

def rewrite_manifest(text):
    root=ET.fromstring(text)
    if root.tag!="manifest" or root.attrib.get("package")!=SOURCE:
        raise ValueError("MANIFEST_SOURCE_IDENTITY_MISMATCH")
    if "{"+ANDROID+"}sharedUserId" in root.attrib:
        raise ValueError("SHARED_USER_ID_UNSUPPORTED")
    root.set("package",DEST)
    changes={"package_identity":1,"provider_authorities":0,
             "declared_permissions":0,"non_component_identity_attributes":0,
             "unchanged_component_classes":0}
    # Names of Activity/Service/Receiver/Provider Java classes must NOT change.
    java_elements={"application","activity","activity-alias","service",
                   "receiver","provider","instrumentation"}
    permission_elements={"permission","uses-permission","permission-group","permission-tree"}
    identity_attrs={"permission","readPermission","writePermission",
                    "targetPackage","process","taskAffinity","authorities"}
    for element in root.iter():
        name=element.attrib.get("{"+ANDROID+"}name")
        if element.tag in java_elements and name and name.startswith(SOURCE):
            changes["unchanged_component_classes"]+=1
        for attr,value in list(element.attrib.items()):
            if not attr.startswith("{"+ANDROID+"}") or not value.startswith(SOURCE):
                continue
            local=attr.rsplit("}",1)[-1]
            rewrite=(local in identity_attrs or
                     element.tag in permission_elements and local=="name")
            if not rewrite:continue
            changed=DEST+value[len(SOURCE):]
            element.set(attr,changed)
            if local=="authorities":changes["provider_authorities"]+=1
            elif element.tag in permission_elements and local=="name":
                changes["declared_permissions"]+=1
            else:changes["non_component_identity_attributes"]+=1
    # No source provider authorities are permitted in a side-by-side clone.
    for provider in root.iter("provider"):
        auth=provider.attrib.get("{"+ANDROID+"}authorities","")
        if any(part.startswith(SOURCE) for part in auth.split(";")):
            raise ValueError("OLD_PROVIDER_AUTHORITY_REMAINS")
    if not changes["unchanged_component_classes"]:
        # This is not a problem for all split manifests. Baseline must be checked
        # in aggregate, not per-split.
        pass
    rewritten=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    return rewritten,changes

def apkmeta(apk):
    out=action([sdk_tool("aapt"),"dump","badging",str(apk)],"BAD_APK_METADATA",60)
    line=next((l for l in out.splitlines() if l.startswith("package:")),"")
    return dict(re.findall(r"(\w+)='([^']*)'",line))

def native_payload_hashes(apk):
    with zipfile.ZipFile(apk) as z:
        return {n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()
                if re.fullmatch(r"classes[0-9]*[.]dex",n)
                or (n.startswith("lib/") and n.endswith(".so"))}

def main():
    if os.getenv("GITHUB_ACTIONS")!="true":
        raise ValueError("ONLY_EPHEMERAL_GITHUB_CI_ALLOWED")
    with tempfile.TemporaryDirectory(prefix="celikom-nativeclone-structure-") as dirname:
        work=Path(dirname)
        arc=work/"owner-pinned.xapk"
        nbytes,digest=gpr.download(arc)
        if nbytes!=60433885 or digest!=ARCHIVE_SHA:
            raise ValueError("PINNED_SOURCE_ARCHIVE_MISMATCH")
        apks=gpr.split_apks(arc,work)
        if len(apks)!=5:raise ValueError("EXACT_FIVE_SPLITS_REQUIRED")
        gpr.inspect_publisher(apks)
        jar=work/"apktool.jar"
        fetch_pin(jar)
        key=work/"clone-lab.jks"
        action(["keytool","-genkeypair","-storetype","JKS",
                "-keystore",str(key),"-storepass","ephemeral-lab-only",
                "-keypass","ephemeral-lab-only","-alias","clone",
                "-keyalg","RSA","-keysize","2048","-validity","30",
                "-dname","CN=CELIKOM Structural Clone Research, O=CELIKOM, C=XX"],
               "LAB_KEY_GENERATION_FAILED",75)
        totals={"package_identity":0,"provider_authorities":0,
                "declared_permissions":0,"non_component_identity_attributes":0,
                "unchanged_component_classes":0}
        orig_splits=set(); rebuilt_splits=set()
        checked=0
        for i,apk in enumerate(apks):
            original=apkmeta(apk)
            if original.get("name")!=SOURCE or original.get("versionCode")!="24026531":
                raise ValueError("SOURCE_SPLIT_IDENTITY_DRIFT")
            split=original.get("split","")
            orig_splits.add(split)
            folder=work/("decoded"+str(i))
            action(["java","-jar",str(jar),"d","-f","-r","-s",
                    "-o",str(folder),str(apk)],"APKTOOL_DECODE_FAILED",220)
            manifest=folder/"AndroidManifest.xml"
            if not manifest.is_file():raise ValueError("MANIFEST_NOT_DECODED")
            payload=manifest.read_bytes()
            if not payload.lstrip().startswith(b"<"):
                raise ValueError("APKTOOL_MANIFEST_UNDECODED_BINARY")
            rewritten,changes=rewrite_manifest(payload.decode("utf-8"))
            manifest.write_bytes(rewritten)
            for k,v in changes.items():totals[k]+=v
            rebuilt=work/("new-unsigned"+str(i)+".apk")
            action(["java","-jar",str(jar),"b",str(folder),"-o",str(rebuilt)],
                   "APKTOOL_REBUILD_FAILED",300)
            aligned=work/("clone-aligned"+str(i)+".apk")
            action([sdk_tool("zipalign"),"-f","-p","4",str(rebuilt),str(aligned)],
                   "CLONE_ZIPALIGN_FAILED",90)
            action([sdk_tool("apksigner"),"sign","--ks",str(key),
                    "--ks-pass","pass:ephemeral-lab-only",
                    "--ks-key-alias","clone",
                    "--key-pass","pass:ephemeral-lab-only",
                    "--min-sdk-version","28","--v4-signing-enabled","false",
                    str(aligned)],"CLONE_SIGN_FAILED",80)
            meta=apkmeta(aligned)
            if (meta.get("name")!=DEST or
                meta.get("versionCode")!="24026531" or meta.get("split","")!=split):
                raise ValueError("CLONE_SPLIT_METADATA_DRIFT")
            cert=action([sdk_tool("apksigner"),"verify","--print-certs",str(aligned)],
                        "CLONE_SIGNATURE_INVALID",70)
            m=re.findall(r"Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F]+)",cert)
            if len(m)!=1 or m[0].lower()==RUSTORE_SHA256_CERT:
                raise ValueError("CLONE_SIGNING_IDENTITY_INVALID")
            if native_payload_hashes(apk)!=native_payload_hashes(aligned):
                raise ValueError("CLONE_NATIVE_DEX_PAYLOAD_CHANGED")
            rebuilt_splits.add(split)
            checked+=1
        if checked!=5 or orig_splits!=rebuilt_splits or len(rebuilt_splits)!=5:
            raise ValueError("CLONE_SPLIT_SET_DRIFT")
        # All created original and clone APKs and signing keys are deleted when
        # TemporaryDirectory exits. Never upload them to public Actions artifacts.
        report={
            "verdict":"STRUCTURAL_CLONE_PASS_NOT_RUNTIME_OR_LOGIN_PROOF",
            "origin":"pinned publisher signed 2026.10.3 #170gpr",
            "clone_package":DEST,
            "signed_splits":checked,
            "old_package_authorities_rewritten":totals["provider_authorities"],
            "other_identity_rewrites":totals["non_component_identity_attributes"]+totals["declared_permissions"],
            "existing_component_java_class_names_preserved":totals["unchanged_component_classes"],
            "dex_native_libraries_byte_identical":True,
            "original_publisher_signature_spoofed":False,
            "original_honor_install_touched":False,
            "play_protect_tested":False,
            "yandex_login_tested":False,
            "native_audio_tested":False,
            "binary_artifact_uploaded":False,
            "caveat":"Resources-table runtime identity, DEX self-checks, login and Play Protect remain unverified"
        }
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as err:
        reason=str(err)
        if not re.fullmatch(r"[A-Z_]{6,80}",reason):
            reason=(
                "MANIFEST_XML_PARSE_FAILED" if isinstance(err,ET.ParseError) else
                "REQUIRED_TOOL_OR_MANIFEST_FILE_MISSING" if isinstance(err,FileNotFoundError) else
                "UNEXPECTED_VALUE_ERROR" if isinstance(err,ValueError) else
                "UNEXPECTED_"+type(err).__name__.upper()+"_FAILURE")
            if not re.fullmatch(r"[A-Z_]{6,80}",reason):
                reason="EPHEMERAL_CLONE_TRIAL_FAILED"
        print(json.dumps({"verdict":"STRUCTURAL_CLONE_BLOCKED",
                          "reason":reason,"apks_distributed":False}))
        sys.exit(2)
