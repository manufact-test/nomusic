#!/usr/bin/env python3
"""NAV44 private, publisher-signed-only field compiler for ONE live PeriodID->Timeline
Window MediaItem compared to the exact selected LiLb source's own MediaItem.
Only field names go to an ephemeral Java class; never print names, media or IDs.
Fail closed unless four exact signed method/field anchors and the pure getter hold.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

import lft2_class_inspection as trusted
import exo_queue_slot_role_exact as exact

audit=trusted.audit
ENGINE=exact.ENGINE
TRANSITION=exact.ENGINE_PERIOD_TIMELINE_TRANSITION
CURRENT_ITEM=("LrD0;","E","()LOf6;")
SOURCE_ITEM=("LiLb;","for","()LOf6;")
PERIOD_LOOKUP=("LTva;","goto","(Ljava/lang/Object;LTva$b;)LTva$b;")
WINDOW_LOOKUP=("LTva;","final","(ILTva$d;J)LTva$d;")
TARGETS=(ENGINE,TRANSITION,CURRENT_ITEM,SOURCE_ITEM)
COLUMNS=(
    ("PLAYBACK_TIMELINE",ENGINE,673,"LCD7;","LTva;"),
    ("PERIOD_WINDOW_INDEX",TRANSITION,105,"LTva$b;","I"),
    ("WINDOW_MEDIA_ITEM",CURRENT_ITEM,24,"LTva$d;","LOf6;"),
)

def derive(splits):
    methods={}
    dex_count=0
    seen_calls=set()
    item_id_fields=[]
    item_class_count=0
    for apk in splits:
        with zipfile.ZipFile(apk) as archive:
            for member in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",member.filename):
                    continue
                dex_count+=1
                dex=audit.Dex(archive.read(member.filename))
                # NAV45: only the exact already-pinned LOf6 MediaItem class.
                # Expect one final instance String. No names/values emitted to CI.
                for class_index in range(dex.class_count):
                    base=dex.class_offset+class_index*32
                    if dex.descriptor(dex.u32(base))!="LOf6;":
                        continue
                    item_class_count+=1
                    class_data=dex.u32(base+24)
                    if not class_data:raise ValueError("NAV45_ITEM_CLASS_NO_FIELDS")
                    nstatic,pos=audit.uleb(dex,class_data)
                    ninst,pos=audit.uleb(dex,pos)
                    _,pos=audit.uleb(dex,pos)
                    _,pos=audit.uleb(dex,pos)
                    if nstatic>256 or ninst>256:
                        raise ValueError("NAV45_ITEM_CLASS_FIELD_BOUND")
                    prior=0
                    for _ in range(nstatic):
                        delta,pos=audit.uleb(dex,pos)
                        prior+=delta
                        _,pos=audit.uleb(dex,pos)
                    prior=0
                    for _ in range(ninst):
                        delta,pos=audit.uleb(dex,pos)
                        prior+=delta
                        access,pos=audit.uleb(dex,pos)
                        owner,name,typ=audit.field_id(dex,prior)
                        if owner!="LOf6;":raise ValueError("NAV45_ITEM_FIELD_OWNER_DRIFT")
                        if typ=="Ljava/lang/String;":
                            if not (access&0x0010):
                                raise ValueError("NAV45_ITEM_ID_NOT_FINAL")
                            item_id_fields.append(name)
                for m,flags,off in audit.method_definitions_with_flags(dex):
                    if m in TARGETS:
                        if m in methods:raise ValueError("NAV44_DUPLICATE_SIGNED_METHOD")
                        if not off:raise ValueError("NAV44_EMPTY_SIGNED_BODY")
                        methods[m]=(dex,flags,off)
                    if m==TRANSITION and off:
                        for pc,op,words in audit.instructions(dex,off):
                            if op in audit.INVOKES and dex.method(words[1]) in (
                                PERIOD_LOOKUP,WINDOW_LOOKUP):
                                seen_calls.add(dex.method(words[1]))
    if dex_count!=6 or set(methods)!=set(TARGETS):
        raise ValueError("NAV44_EXACT_SIX_DEX_FOUR_METHODS")
    if item_class_count!=1 or len(item_id_fields)!=1:
        raise ValueError("NAV45_MEDIAITEM_UNIQUE_FINAL_STRING_FIELD_GUARD:"
                         +str(item_class_count)+":"+str(len(item_id_fields)))
    if seen_calls!={PERIOD_LOOKUP,WINDOW_LOOKUP}:
        raise ValueError("NAV44_PERIOD_TO_WINDOW_METHODS_NOT_BOTH_PINNED")
    fields={}
    for key,target,pc,owner,typ in COLUMNS:
        dex,flags,off=methods[target]
        row=next(((op,words) for p,op,words in audit.instructions(dex,off)
                  if p==pc),None)
        if row is None or row[0] not in (0x52,0x54):
            raise ValueError("NAV44_EXACT_FIELD_PC_OPCODE_DRIFT")
        actual_owner,name,actual_type=audit.field_id(dex,row[1][1])
        if (actual_owner!=owner or actual_type!=typ or not isinstance(name,str)
                or not re.fullmatch(r"[A-Za-z0-9_$-]{1,100}",name)):
            raise ValueError("NAV44_SIGNED_FIELD_OWNER_TYPE_DRIFT")
        fields[key]=name
    # Non-invasive source item access: do not invoke an unverified vendor
    # getter on a hot audio callback. Read its exact stable field instead.
    dex,flags,off=methods[SOURCE_ITEM]
    reads=[]
    returns=[]
    instructions=list(audit.instructions(dex,off))
    if len(instructions)>12:
        raise ValueError("NAV44_SOURCE_GETTER_NOT_BOUNDED")
    for pc,op,words in instructions:
        if op==0x54:
            f=audit.field_id(dex,words[1])
            if f[0]=="LiLb;" and f[2]=="LOf6;":
                reads.append(((words[0]>>8)&0x0f,(words[0]>>12)&0x0f,f[1]))
        elif op==0x11:
            returns.append((words[0]>>8)&0xff)
        elif op not in (0,0x0e):
            raise ValueError("NAV44_SOURCE_GETTER_NOT_PURE")
    if len(reads)!=1 or len(returns)!=1:
        raise ValueError("NAV44_SOURCE_GETTER_FIELD_OR_RETURN_AMBIGUOUS")
    registers=dex.u16(off)
    incoming=dex.u16(off+2)
    if incoming!=1 or reads[0][:2]!=(returns[0],registers-incoming):
        raise ValueError("NAV44_SOURCE_GETTER_REF_NOT_RETURNED_FROM_THIS")
    fields["SOURCE_MEDIA_ITEM"]=reads[0][2]
    fields["ITEM_LOGICAL_ID"]=item_id_fields[0]
    return fields

def run(path:Path):
    if os.environ.get("GITHUB_ACTIONS")!="true" or os.environ.get(
            "GITHUB_REPOSITORY")!="manufact-test/nomusic":
        raise RuntimeError("NAV44_EPHEMERAL_SIGNED_CI_ONLY")
    if path.stat().st_size!=trusted.PINNED_XAPK_BYTES or trusted.sha256_file(path)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("NAV44_EXACT_SIGNED_ARCHIVE_REQUIRED")
    with tempfile.TemporaryDirectory(prefix="celikom-nav44-signed-") as tmp:
        apks=audit.unbundle_candidate(path,Path(tmp))
        if len(apks)!=16 or audit.verify_split_set(apks).get("verified_issuer_signed_splits")!=16:
            raise ValueError("NAV44_SIGNED_16_SPLITS_REQUIRED")
        bases=[a for a in apks if not trusted.package_metadata(a).get("split")]
        if len(bases)!=1 or trusted.sha256_file(bases[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("NAV44_SIGNED_BASE_DRIFT")
        return derive(apks)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",type=Path,required=True)
    p.add_argument("--private-java",type=Path,required=True)
    args=p.parse_args()
    if args.private_java.exists():
        raise ValueError("NAV44_PRIVATE_TARGET_ALREADY_EXISTS")
    fields=run(args.xapk)
    output="package pro.celikom.a1exitwitness;\nfinal class PrivateNativeCurrentMediaItemTarget {\n"
    for key in ("PLAYBACK_TIMELINE","PERIOD_WINDOW_INDEX","WINDOW_MEDIA_ITEM","SOURCE_MEDIA_ITEM","ITEM_LOGICAL_ID"):
        output+="  static final String "+key+" = "+json.dumps(fields[key],ensure_ascii=True)+";\n"
    output+="  private PrivateNativeCurrentMediaItemTarget() {}\n}\n"
    args.private_java.parent.mkdir(parents=True,exist_ok=True)
    args.private_java.write_text(output,encoding="utf-8")
    print("NAV45_EXACT_MEDIAITEM_UNIQUE_FINAL_LOGICAL_STRING_GATE_PASS")

if __name__=="__main__":
    main()
