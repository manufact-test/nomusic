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

EVENTS={"ARMED","HI2_EXCEPTION","METRICA_EXCEPTION","PREFIX_HOOK",
        "RUN_HOOK","RUN_ENTER","PREFIX_CHECK"}
ORIGINS={"METRICA_SDK","MUSIC_APP","NO_METRICA_FRAME",
         "STATIC_COROUTINE","VENDOR","REGISTERED","NO_HOOK",
         "STATIC_RUN_B","OWN_MAIN","OWN_AUX","ORIGINAL_MAIN","ORIGINAL_AUX",
         "UNKNOWN","NONE"}
ERRORS={"EXC_UNKNOWN","EXC_SIGN_AND_AUTH","EXC_SIGNATURE","EXC_AUTH",
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
    return {
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
