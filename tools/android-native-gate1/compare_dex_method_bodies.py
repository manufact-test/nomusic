"""Compare publisher-signed RUR and GPR DEX *code*, not just SHA-256 checksums.

No raw strings, audio, credentials, APK bytes or secrets are emitted. Differing
DEX file hashes do not imply changed bytecode because DEX headers and channel
metadata may differ. This is an offline comparative count, NOT live playback proof.
"""
from __future__ import annotations
from collections import Counter
from inspect_android_host import Dex, DexError
from trace_native_callers import method_definitions

MAX_CHANGED_NAMED_METHODS=24
AUDIO_PREFIX=("Lcom/yandex/music/shared/playback/",
              "Lcom/yandex/music/shared/play/audio2/",
              "Lcom/yandex/music/shared/media/session/")
AUDIO_EXTRA={"Lqdw;","Lsy5;","Lpdw;"}

def _code(d:Dex,off:int)->bytes:
    d.bounds(off,16)
    insns=d.u32(off+12)
    if insns>3_000_000:
        raise DexError("Unreasonable code item length")
    d.bounds(off+16,insns*2)
    return d.data[off+16:off+16+insns*2].tobytes()

def compare_dex_code(left:bytes,right:bytes)->dict:
    a,b=Dex(left),Dex(right)
    ids_equal=(a.type_count==b.type_count and a.method_count==b.method_count
       and a.type_count==b.type_count
       and a.data[a.type_offset:a.type_offset+a.type_count*4].tobytes() ==
               b.data[b.type_offset:b.type_offset+b.type_count*4].tobytes()
       and a.data[a.method_offset:a.method_offset+a.method_count*8].tobytes() ==
               b.data[b.method_offset:b.method_offset+b.method_count*8].tobytes())
    # Raw type-id equality not enough if string pool differs: require
    # semantic descriptor/method resolution before pairing code by index.
    types_equal= a.type_count==b.type_count and all(
        a.descriptor(i)==b.descriptor(i) for i in range(a.type_count))
    methods_equal=a.method_count==b.method_count and all(
        a.method(i)==b.method(i) for i in range(a.method_count))
    if not types_equal or not methods_equal:
        return {"type_names_equal":types_equal,"method_signatures_equal":methods_equal,
                "code_comparison":"INCOMPARABLE_METHOD_IDENTITY_CHANGED",
                "changed_named_audio_methods":[]}
    ma=dict(method_definitions(a))
    mb=dict(method_definitions(b))
    shared=ma.keys() & mb.keys()
    changed=0
    changed_named=[]
    for i in shared:
        if _code(a,ma[i])==_code(b,mb[i]):
            continue
        changed+=1
        c,name,sig=a.method(i)
        if ((c.startswith(AUDIO_PREFIX) or c in AUDIO_EXTRA)
               and len(changed_named)<MAX_CHANGED_NAMED_METHODS):
            changed_named.append({"class":c,"method":name,"signature":sig})
    type_count=a.type_count
    method_count=a.method_count
    string_count_equal=a.string_count==b.string_count
    changed_strings= sum(a.string(i)!=b.string(i) for i in range(a.string_count)) \
                    if string_count_equal else None
    return {
        "type_names_equal":types_equal,
        "method_signatures_equal":methods_equal,
        "raw_type_and_method_id_tables_equal":ids_equal,
        "string_ids_equal_count":string_count_equal,
        "string_value_different_at_same_index":changed_strings,
        "method_bodies_left":len(ma),
        "method_bodies_right":len(mb),
        "paired_code_bodies":len(shared),
        "added_code_bodies":len(mb.keys()-ma.keys()),
        "removed_code_bodies":len(ma.keys()-mb.keys()),
        "changed_instruction_body_count":changed,
        "changed_named_audio_methods":changed_named,
        "code_comparison": (
           "IDENTICAL_INSTRUCTIONS_ALL_PAIRED_METHODS" if changed==0 and len(ma)==len(mb)
           else "SOME_METHOD_INSTRUCTIONS_DIFFER"
        )
    }
