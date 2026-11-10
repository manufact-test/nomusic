#!/usr/bin/env python3
"""Read-only signed six-DEX Lemb.t/remove dispatch candidates to selected source.

Lero/Locv implement Lemb. We examine ACTUAL invoke-interface references
and their owner contexts (incl. obfuscated player candidates) but never
resolve polymorphic receivers to a selected instance without real runtime
object dataflow. No APK/DEX/media/URL/user data emitted or modified.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/"tools"/"android-native-gate1"))
from inspect_android_host import Dex,DexError,DEX_MAX
from trace_native_callers import method_definitions,INVOKES
from audit_native_register_bridge import instructions,invoke_registers
from audit_native_ga4_field2_value_origins import safe_operand_metadata
from audit_native_media_implementors import relations,transitive_implementors
from audit_native_typed_wrapper_coroutines import method_profile,brief_type
from trace_native_model_to_decoder import bounded_obfuscated
import clone_native_splits_ephemeral as exact

ABSTRACT="Lemb;"
DESIRED={"t","remove"}
KNOWN_MEDIA={"Lfxc;","Lro7;","Lwxc;","Lyzt;"}
MAX_METHOD_BODIES=230600
MAX_CALLS=1800
MAX_ENTRIES=70
MAX_FIELDS=500
MAX_WINDOWS=16


def classification(owner, hierarchy, media_implementors):
    if owner in media_implementors:return "concrete_public_exoplayer_implementor"
    if owner in KNOWN_MEDIA:return "obfuscated_exoplayer_candidate"
    if owner.startswith("Landroidx/media3/"):return "named_media3_owner"
    if owner in (ABSTRACT,"Lero;","Locv;","Lmir;","Lga4;"):
        return "known_source_lifecycle_owner"
    return "other_unknown"


def callsite_window(d,ins,idx):
    _,op,words=ins[idx]
    source=d.method(words[1])
    args=invoke_registers(op,words)
    before=[{
        "relative_ordinal":j-idx,
        **safe_operand_metadata(d,ins[j][1],ins[j][2]),
    } for j in range(max(0,idx-MAX_WINDOWS),idx)]
    return {
        "target":method_profile(source),
        "opcode_is_invoke_interface":op in (0x72,0x78),
        "receiver_register_coordinate":args[0] if args else None,
        "argument_word_count":len(args),
        "preceding_safe_op_roles":[item for item in before if item["kind"]!="other"],
        "receiver_class_or_selected_player_proven":False,
    }


def extract_declared_fields(d):
    count,offset=d.table(80,8)
    rows=Counter()
    for i in range(count):
        position=offset+i*8
        owner=d.descriptor(d.u16(position))
        typ=d.descriptor(d.u16(position+2))
        if typ==ABSTRACT or owner in ("Lero;","Locv;","Lmir;"):
            rows[(owner,typ)]+=1
    return rows


def inspect_signed(apks):
    sources=[]
    actor_classes={}
    fields=Counter()
    num_dex=0
    total_bodies=0
    call_count=0
    callers=defaultdict(list)
    instantiations=defaultdict(list)
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for member in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",member.filename):
                    continue
                if member.file_size>DEX_MAX:raise ValueError("SIGNED_DEX_SIZE")
                d=Dex(z.read(member.filename))
                num_dex+=1
                rel=relations(d)
                if set(actor_classes)&set(rel):
                    raise ValueError("SIGNED_CLASS_DUPLICATE")
                actor_classes.update(rel)
                fields.update(extract_declared_fields(d))
                if len(fields)>MAX_FIELDS:raise ValueError("SIGNED_FIELD_COUNT_BOUND")
                for mid,coff in method_definitions(d):
                    total_bodies+=1
                    if total_bodies>MAX_METHOD_BODIES:
                        raise ValueError("SIGNED_METHOD_LIMIT")
                    caller=d.method(mid)
                    ins=list(instructions(d,coff))
                    for idx,(_,op,w) in enumerate(ins):
                        if op==0x22:
                            typ=d.descriptor(w[1])
                            if typ in ("Lero;","Locv;"):
                                instantiations[typ].append(bounded_obfuscated(caller))
                        if op not in INVOKES:continue
                        callee=d.method(w[1])
                        if callee[0]!=ABSTRACT or callee[1] not in DESIRED:
                            continue
                        call_count+=1
                        if call_count>MAX_CALLS:raise ValueError("INTERFACE_CALLSITE_BOUND")
                        callers[caller].append(callsite_window(d,ins,idx))
    if num_dex!=6:raise ValueError("SIGNED_SIX_DEX_REQUIRED")
    descendants=transitive_implementors(actor_classes,ABSTRACT)
    explicit_media=set()
    for iface in ["Landroidx/media3/exoplayer/ExoPlayer;",
                  "Lcom/google/android/exoplayer2/ExoPlayer;"]:
        explicit_media.update(transitive_implementors(actor_classes,iface))
    if "Lero;" not in descendants or "Locv;" not in descendants:
        raise ValueError("EXPECTED_LERO_LOCV_IMPLEMENTORS_MISSING")
    grouped=Counter(classification(m[0],actor_classes,explicit_media)
                    for m in callers)
    by_method=[{
        "caller":method_profile(m),
        "caller_category":classification(m[0],actor_classes,explicit_media),
        "direct_reference_site_count":len(events),
        "bounded_sites":events[:MAX_WINDOWS],
        "exact_Lero_or_Locv_runtime_dispatch_proven":False,
    } for m,events in sorted(callers.items())]
    by_method.sort(key=lambda x:(-x["direct_reference_site_count"],
                                   x["caller"]["owner"],x["caller"]["method"]))
    return {
        "publisher_original_signed_apk_count":5,
        "signed_dex_count":num_dex,
        "signed_method_bodies_scanned":total_bodies,
        "Lemb_concrete_implementor_count":len(descendants),
        "source_concrete_implementor_examples":[brief_type(n) for n in descendants[:35]],
        "Lemb_t_or_remove_direct_callsite_count":call_count,
        "Lemb_direct_caller_method_count":len(callers),
        "callers_grouped_by_static_owner_class":dict(sorted(grouped.items())),
        "caller_examples":by_method[:MAX_ENTRIES],
        "new_instance_Lero_direct_method_caller_count":len(set(instantiations["Lero;"])),
        "new_instance_Locv_direct_method_caller_count":len(set(instantiations["Locv;"])),
        "Lero_constructor_method_hints":sorted(set(instantiations["Lero;"]))[:MAX_ENTRIES],
        "Locv_constructor_method_hints":sorted(set(instantiations["Locv;"]))[:MAX_ENTRIES],
        "typed_fields_of_Lemb_or_owned_by_source":[
            {"declaring_type":brief_type(owner),
             "field_value_type":brief_type(typ),"field_ref_count":count}
            for (owner,typ),count in sorted(fields.items())[:MAX_ENTRIES]],
        "active_player_selected_media_source_object_proven":False,
        "native_decoder_preprepare_object_match_proven":False,
        "real_runtime_audio_substitution_proven":False,
    }


def run():
    if os.getenv("GITHUB_ACTIONS")!="true":raise RuntimeError("CI_ORIGINAL_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-signed-lemb-caller-") as temp:
        directory=Path(temp)
        original=directory/"publisher-signed-original-unchanged.xapk"
        size,digest=exact.gpr.download(original)
        if size!=60433885 or digest!=exact.ARCHIVE_SHA:
            raise ValueError("SIGNATURE_SOURCE_PIN")
        splits=exact.gpr.split_apks(original,directory)
        if len(splits)!=5:raise ValueError("SIGNED_FIVE_SPLITS")
        exact.gpr.inspect_publisher(splits)
        evidence=inspect_signed(splits)
    return {
        "verdict":"SIGNED_LEMB_SELECTION_CALLSITES_STATIC_NO_RECEIVER_BINDING",
        **evidence,
        "no_vendor_binary_user_data_media_access_or_export":True,
    }


if __name__=="__main__":
    try:
        print(json.dumps(run(),sort_keys=True,ensure_ascii=False))
    except (RuntimeError,ValueError,DexError,OSError,zipfile.BadZipFile) as ex:
        errors={
            "SIGNED_DEX_SIZE","SIGNED_CLASS_DUPLICATE","SIGNED_FIELD_COUNT_BOUND",
            "SIGNED_METHOD_LIMIT","INTERFACE_CALLSITE_BOUND",
            "SIGNED_SIX_DEX_REQUIRED","EXPECTED_LERO_LOCV_IMPLEMENTORS_MISSING",
            "SIGNATURE_SOURCE_PIN","SIGNED_FIVE_SPLITS",
        }
        err=str(ex)
        print(json.dumps({
            "verdict":"SIGNED_LEMB_SELECTION_SCAN_INCOMPLETE",
            "error_code":err if err in errors else type(ex).__name__,
            "active_player_selected_media_source_object_proven":False,
        }))
        sys.exit(2)
