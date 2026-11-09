#!/usr/bin/env python3
"""Read-only bounded DEX audit: is FileInfo model tied to a native decoder?

There is NO modified APK, network interception, account data or playback here.
This scan checks the exact signed #170gpr and only prints aggregate structural
counts and a small redacted set of obfuscated class/method identifiers.
"""
from __future__ import annotations
import json, re, subprocess, sys, tempfile, zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/"tools"/"android-native-gate1"))
import audit_gpr_apkpure_once as gpr
from audit_rustore_host_once import sdk_tool
from inspect_android_host import Dex,DEX_MAX,DexError
from trace_native_callers import method_definitions,invoked_method_indexes

MODEL="Leed;"
CONVERTER="Lsw7;"
CLASSES=(
    "Landroidx/media3/exoplayer/",
    "Landroidx/media3/datasource/",
    "Landroidx/media3/common/MediaItem;",
    "Lcom/google/android/exoplayer2/",
)
NAMES={"createMediaSource","createDataSource","setMediaItem","setMediaSource",
       "setMediaItems","setMediaSources","prepare","open"}
MAX_EXAMPLES=15

def is_model_method(triple):
    owner,method,signature=triple
    return owner==MODEL or MODEL in signature

def is_media_call(triple):
    owner,name,signature=triple
    return any(owner.startswith(x) for x in CLASSES) and name in NAMES

def bounded_obfuscated(triple):
    """Do not expose third-party snippets, method bodies or strings."""
    owner,name,signature=triple
    if re.fullmatch(r"L[a-zA-Z0-9_$]{1,14};",owner):
        return owner+"->"+name[:40]
    if owner==CONVERTER:return "exact-fileinfo-converter"
    return "named-other-class"

def analyze_dex(raw):
    d=Dex(raw)
    targets=set()
    converters=set()
    media=set()
    for i in range(d.method_count):
        m=d.method(i)
        if is_model_method(m):targets.add(i)
        if m[0]==CONVERTER and m[1] in ("y0","z0"):
            converters.add(i)
        if is_media_call(m):media.add(i)
    counts={"method_refs_with_model":len(targets),
            "exact_converter_method_refs":len(converters),
            "media3_source_method_refs":len(media),
            "defined_model_consumer_method_bodies":0,
            "defined_converter_callers":0,
            "model_and_media_calls_same_body":0,
            "converter_and_media_calls_same_body":0,
            "defined_methods_scanned":0,
            "invalid_code_bodies":0}
    examples=[]
    for idx,off in method_definitions(d):
        counts["defined_methods_scanned"]+=1
        try:
            invoked={method for method,_,_ in invoked_method_indexes(d,off)}
        except DexError:
            counts["invalid_code_bodies"]+=1
            continue
        contains_model=bool(invoked&targets) or idx in targets
        contains_converter=bool(invoked&converters)
        contains_media=bool(invoked&media)
        if contains_model:counts["defined_model_consumer_method_bodies"]+=1
        if contains_converter:counts["defined_converter_callers"]+=1
        if contains_model and contains_media:counts["model_and_media_calls_same_body"]+=1
        if contains_converter and contains_media:counts["converter_and_media_calls_same_body"]+=1
        if contains_model and len(examples)<MAX_EXAMPLES:
            examples.append({
                "method_hint":bounded_obfuscated(d.method(idx)),
                "calls_media_source_factory_same_body":contains_media,
                "calls_exact_converter_same_body":contains_converter,
            })
    return counts,examples

def run():
    with tempfile.TemporaryDirectory(prefix="celikom-native-model-link-readonly-") as name:
        root=Path(name)
        archive=root/"pinned-original.xapk"
        size,digest=gpr.download(archive)
        if size!=60433885 or digest!="918bd50599dc6a942e190a409303e843b83dcb6d11b90b03c00240331333cf84":
            raise ValueError("PINNED_SOURCE_MISMATCH")
        apks=gpr.split_apks(archive,root)
        gpr.inspect_publisher(apks)
        if len(apks)!=5:raise ValueError("WRONG_SPLIT_COUNT")
        bases=[]
        for apk in apks:
            a=subprocess.run([sdk_tool("aapt"),"dump","badging",str(apk)],
                capture_output=True,text=True,timeout=50)
            line=next((t for t in a.stdout.splitlines() if t.startswith("package:")),"")
            attrs=dict(re.findall(r"(\w+)='([^']*)'",line))
            if a.returncode or attrs.get("name")!="ru.yandex.music" or attrs.get("versionCode")!="24026531":
                raise ValueError("ORIGINAL_IDENTITY_MISMATCH")
            if not attrs.get("split"):bases.append(apk)
        if len(bases)!=1:raise ValueError("BASE_NOT_EXACT")
        totals={}
        examples=[]
        dex_files=0
        with zipfile.ZipFile(bases[0]) as z:
            for item in z.infolist():
                if not re.fullmatch("classes[0-9]*[.]dex",item.filename):continue
                if item.file_size>DEX_MAX:raise ValueError("DEX_LIMIT")
                counters,sample=analyze_dex(z.read(item))
                dex_files+=1
                for k,v in counters.items():totals[k]=totals.get(k,0)+v
                examples.extend(sample[:max(0,MAX_EXAMPLES-len(examples))])
        if dex_files==0:raise ValueError("NO_DEX")
        return {
            "verdict":"STATIC_MODEL_DOWNSTREAM_SCAN_ONLY",
            "signed_original":"2026.10.3 #170gpr",
            "verified_split_count":5,
            "dex_count":dex_files,
            "counts":totals,
            "bounded_method_hints":examples[:MAX_EXAMPLES],
            "authoritative_decoder_prepare_proven":False,
            "native_pause_seek_audible_proven":False,
            "replaced_audio":False,
            "installed_anything":False,
            "warning":"Dex callsite co-occurrence is NOT register-level producer/consumer proof",
        }

def main():
    try:
        print(json.dumps(run(),ensure_ascii=False,indent=2,sort_keys=True))
        return 0
    except Exception:
        print(json.dumps({"verdict":"SOURCE_GRAPH_NO_GO",
                          "reason":"STATIC_SOURCE_OR_DEX_UNAVAILABLE",
                          "patch_created":False}))
        return 2

if __name__=="__main__":
    sys.exit(main())
