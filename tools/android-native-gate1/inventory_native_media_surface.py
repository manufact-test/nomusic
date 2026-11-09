#!/usr/bin/env python3
"""Non-executable privacy-limited Android music playback surface census from DEX.

Reports public class identifiers and structural invoke anchors only. A callsite
does not prove it is Yandex's active player, nor an authorized source hook.
"""
from __future__ import annotations
from collections import Counter
from inspect_android_host import Dex, DexError
from trace_native_callers import method_definitions, invoked_method_indexes

FRAMEWORK = {
    "Landroid/media/MediaPlayer;": {"setDataSource","prepare","prepareAsync","seekTo","start","pause"},
    "Landroid/media/AudioTrack;": {"write","play","pause","stop"},
    "Landroid/media/AudioTrack$Builder;": {"build"},
    "Landroid/media/MediaCodec;": {"configure","start","queueInputBuffer"},
    "Landroid/media/MediaExtractor;": {"setDataSource","readSampleData"},
    "Landroid/media/MediaDataSource;": {"readAt","getSize"},
    "Landroid/media/session/MediaSession;": {"setMetadata","setPlaybackState"},
}
TOKENS = ("player", "playback", "media", "audio", "stream", "source", "track", "buffer")
OWNER_PREFIX = ("Lru/yandex/", "Lcom/yandex/")
MAX_EXAMPLES=40

def inspect_surface(data:bytes)->dict:
    dex=Dex(data)
    all_types=[dex.descriptor(i) for i in range(dex.type_count)]
    classes=dex.defined_classes()
    yandex_classes=sorted(c for c in classes if c.startswith(OWNER_PREFIX))
    likely=[c for c in yandex_classes if any(t in c.lower() for t in TOKENS)]
    # Use prefix counts, not actual values (secrets and resources never inspected).
    prefixes=Counter()
    for c in yandex_classes:
        p=c.lstrip("L").split("/")
        prefixes["/".join(p[:4])] += 1
    ref_counts = {
        "androidx_media3_types":sum(s.startswith("Landroidx/media3/") for s in all_types),
        "google_exoplayer2_types":sum(s.startswith("Lcom/google/android/exoplayer2/") for s in all_types),
        "yandex_defined_classes":len(yandex_classes),
        "owner_media_keyword_classes":len(likely),
        "android_media_types":sum(s.startswith("Landroid/media/") for s in all_types),
    }
    refs={}
    for i in range(dex.method_count):
        clazz,name,sig=dex.method(i)
        if clazz in FRAMEWORK and name in FRAMEWORK[clazz]:
            refs[i]=(clazz,name,sig)
    example=[]
    count=0
    malformed=[]
    if refs:
        for caller_idx,code_off in method_definitions(dex):
            try:
                for target,offset,opcode in invoked_method_indexes(dex,code_off):
                    entry=refs.get(target)
                    if entry is None:continue
                    count+=1
                    if len(example)<MAX_EXAMPLES:
                        clazz,name,sig=dex.method(caller_idx)
                        tgt,method,signature=entry
                        example.append({
                            "from_class":clazz,"from_method":name,
                            "to_class":tgt,"to_method":method,"to_signature":signature
                        })
            except DexError as exc:
                if len(malformed)<12:malformed.append({"index":caller_idx,"reason":str(exc)})
    return {
        "type_counts":ref_counts,
        "most_common_yandex_package_prefixes":prefixes.most_common(12),
        "yandex_media_named_class_examples":likely[:MAX_EXAMPLES],
        "android_framework_media_method_refs":len(refs),
        "android_framework_media_invoke_calls":count,
        "android_framework_invoke_examples":example,
        "trace_anomalies":malformed,
        "evidence_level":"STATIC_ONLY_NOT_PROOF_OF_LIVE_SOURCE_SELECTION",
    }
