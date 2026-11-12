"""Exact native MAIN PID-owned LibXposed event decoder: only static enums.

Never return logcat message, thread, PID, package string, stack or any values
from the tested Yandex app. No telemetry or account access.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from clone_main_crash_buffer import main_exit_pids, LOG

EVENTS={"ARMED","HI2_EXCEPTION","METRICA_EXCEPTION","APP_CONTEXT","UNCAUGHT",
        "FATAL_HOOK","FATAL_DISPATCH","METRICA_DETAIL","FATAL_DETAIL",
        "LAB_METRICA_FAILOPEN","PREFIX_HOOK",
        "RUN_HOOK","RUN_ENTER","PREFIX_CHECK"}
ORIGINS={"METRICA_SDK","MUSIC_APP","NO_METRICA_FRAME",
         "CLONE","ORIGINAL","MISSING","OTHER",
         "STATIC_COROUTINE","VENDOR","REGISTERED","NO_HOOK",
         "STATIC_RUN_B","OWN_MAIN","OWN_AUX","ORIGINAL_MAIN","ORIGINAL_AUX",
         "THREAD_DISPATCH","THREAD_GROUP","RUNTIME_KILL_HANDLER",
         "RUNTIME_LOG_HANDLER","RUNTIME_LOOKUP",
         "UNKNOWN","NONE"}
ERRORS={"EXC_UNKNOWN","EXC_SIGN_AND_AUTH","EXC_SIGNATURE","EXC_AUTH",
        "EXC_SDK_INIT","EXC_CONFIG","EXC_ASYNC",
        "APPINFO_CLONE","APPINFO_ORIGINAL","APPINFO_MISSING","APPINFO_OTHER",
        "ILLEGAL_STATE","SECURITY","LINK","OTHER_THROWABLE",
        "DIRECT_METRICA","CAUSE_METRICA","NOT_METRICA","NON_THROWABLE",
        "DETAIL_UNKNOWN","DETAIL_NOT_INITIALIZED","DETAIL_ALREADY_ACTIVE",
        "DETAIL_API_KEY","DETAIL_PACKAGE_CONTEXT","DETAIL_ANDROID_COMPONENT",
        "DETAIL_CONFIG","DETAIL_PERMISSION","DETAIL_CRASH_HANDLER",
        "DETAIL_OTHER","DETAIL_UNOBSERVED",
        "EXC_PERMISSION","EXC_LOCALE","EXC_LIFECYCLE","EXC_OTHER",
        "REGISTERED","NO_HOOK","NONE","CASE_0","CASE_1","CASE_2",
        "CASE_3","CASE_4","CASE_5","CASE_6","CASE_7","CASE_OTHER",
        "CASE_UNKNOWN","MATCH_TRUE","MATCH_FALSE"}
MARKER=re.compile(r"^event=([A-Z_]+);origin=([A-Z_]+);"
                  r"error=([A-Z_0-9]+);thread=(MAIN|OTHER)$")


def scoped_metrica_witness(exit_info:str,logcat:str)->dict:
    owned=main_exit_pids(exit_info,"pro.celikom.yandex.nativeclonelab")
    seen=[]
    for line in logcat.splitlines()[-25000:]:
        parsed=LOG.match(line)
        if parsed is None or int(parsed.group(1)) not in owned:
            continue
        _,severity,tag,msg=parsed.groups()
        if tag.strip()!="CELIKOM_A1_EXIT_WITNESS" or severity not in ("I","D"):
            continue
        match=MARKER.fullmatch(msg.strip())
        if match is None:
            continue
        event,origin,error,thread=match.groups()
        if event not in EVENTS or origin not in ORIGINS or error not in ERRORS:
            continue
        seen.append((event,origin,error,thread))
        if len(seen)>=250:break
    metrica=[x for x in seen if x[0]=="METRICA_EXCEPTION"]
    contexts=[x for x in seen if x[0]=="APP_CONTEXT"]
    uncaught=[x for x in seen if x[0]=="UNCAUGHT"]
    dispatch=[x for x in seen if x[0]=="FATAL_DISPATCH"]
    installed=[x for x in seen if x[0]=="FATAL_HOOK"]
    same=[x for x in dispatch if x[2] in ("DIRECT_METRICA","CAUSE_METRICA")]
    constructor_details=[x for x in seen if x[0]=="METRICA_DETAIL"]
    fatal_details=[x for x in seen if x[0]=="FATAL_DETAIL"]
    failopen=[x for x in seen if x[0]=="LAB_METRICA_FAILOPEN"]
    first_metrica=next((i for i,x in enumerate(seen) if x[0]=="METRICA_EXCEPTION"),None)
    first_uncaught=next((i for i,x in enumerate(seen) if x[0]=="UNCAUGHT"),None)
    return {
        "read_only_application_attach_context_seen":bool(contexts),
        "read_only_attach_context_identity_categories":sorted({x[1] for x in contexts}),
        "read_only_attach_appinfo_identity_categories":sorted({x[2] for x in contexts}),
        "uncaught_exception_observed":bool(uncaught),
        "fatal_handler_hook_registration":sorted({
            x[1] for x in installed if x[2]=="REGISTERED"}),
        "fatal_handler_hook_missing":sorted({
            x[1] for x in installed if x[2]=="NO_HOOK"}),
        "fatal_dispatch_observed":bool(dispatch),
        "fatal_dispatch_paths":sorted({x[1] for x in dispatch}),
        "bounded_metrica_constructor_detail_categories":sorted({
            x[2] for x in constructor_details}),
        "bounded_fatal_metrica_detail_categories":sorted({
            x[2] for x in fatal_details}),
        "fatal_metrica_detail_observed":bool(fatal_details),
        "lab_only_metrica_fatal_suppression_observed":bool(failopen),
        "lab_only_metrica_fatal_suppression_count_bounded":len(failopen),
        "fatal_dispatch_event_count_bounded":len(dispatch),
        "fatal_throwable_metrica_direct_identity_seen":any(
            x[2]=="DIRECT_METRICA" for x in dispatch),
        "fatal_throwable_metrica_cause_identity_seen":any(
            x[2]=="CAUSE_METRICA" for x in dispatch),
        "fatal_throwable_link_verdict":(
            "DIRECT_IDENTITY" if any(x[2]=="DIRECT_METRICA" for x in dispatch)
            else "CAUSE_IDENTITY" if any(x[2]=="CAUSE_METRICA" for x in dispatch)
            else "FATAL_SEEN_NO_CONSTRUCTOR_IDENTITY" if dispatch
            else "FATAL_DISPATCH_NOT_OBSERVED"),

        "uncaught_illegal_state_observed":any(x[2]=="ILLEGAL_STATE" for x in uncaught),
        "metrica_exception_precedes_uncaught": (
            first_metrica is not None and first_uncaught is not None
            and first_metrica < first_uncaught),

        "read_only_witness_arm_marker_seen":any(x[0]=="ARMED" for x in seen),
        "read_only_metrica_exception_marker_seen":bool(metrica),
        "metrica_exception_callsite_origins":sorted({x[1] for x in metrica}),
        "metrica_exception_message_categories":sorted({x[2] for x in metrica}),
        "metrica_exception_thread_roles":sorted({x[3] for x in metrica}),
        "metrica_exception_event_count_bounded":len(metrica),
        "all_witness_events_bounded":len(seen),
        "raw_logcat_disclosed":False,"pid_disclosed":False,
        "message_or_vendor_symbol_disclosed":False,
    }
