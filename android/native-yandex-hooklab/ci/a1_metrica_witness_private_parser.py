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
        "LAB_METRICA_FAILOPEN","PREFIX_HOOK","APP_LIFECYCLE",
         "METRICA_ACTIVATE","METRICA_CONTEXT","METRICA_LOADER","METRICA_PHASE",
         "ACTIVATION_HOOK","METRICA_STATE_HOOK","METRICA_API_HOOK",
         "METRICA_STATE","METRICA_API","REPORTER_HOOK","REPORTER_CALL",
         "METRICA_THROW_SITE","METRICA_THROW_EXEC","METRICA_THROW_LOADER",
         "METRICA_THROW_HINT","FATAL_THROW_SITE","FATAL_THROW_HINT",
         "SDK_CLASS","SDK_ACTIVATE_SIGNATURE","MODULES_HOOK",
         "MODULES_IS_ACTIVATED","PUSH_ACTIVATE","PUSH_ACTIVATE_HOOK","PUSH_INIT","PUSH_INIT_HOOK",
          "PUSH_HELPER_HOOK","PUSH_HELPER_BOOL",
          "PUSH_GUARD_HOOK","PUSH_GUARD_VALUE","PUSH_GUARD_INPUT",
          "PUSH_FATAL_HOOK","PUSH_FATAL_CALL",
          "PUSH_NEAR_GUARD_HOOK","PUSH_NEAR_GUARD_VALUE",
          "PUSH_ALL_FATAL_GUARD_HOOK","PUSH_ALL_FATAL_GUARD_VALUE",
         "METRICA_PUSH_THROW_CLASS","METRICA_PUSH_THROW_METHOD",
        "RUN_HOOK","RUN_ENTER","PREFIX_CHECK"}
ORIGINS={"METRICA_SDK","MUSIC_APP","NO_METRICA_FRAME",
         "CLONE","ORIGINAL","MISSING","OTHER",
         "STATIC_COROUTINE","VENDOR","REGISTERED","NO_HOOK",
         "STATIC_RUN_B","OWN_MAIN","OWN_AUX","ORIGINAL_MAIN","ORIGINAL_AUX",
         "THREAD_DISPATCH","THREAD_GROUP","RUNTIME_KILL_HANDLER",
         "RUNTIME_LOG_HANDLER","RUNTIME_LOOKUP",
         "UNKNOWN","NONE","APPLICATION","METRICA_LEGACY","METRICA_MODERN",
         "PUSH_MODERN","PUSH_LEGACY","PUSH_HELPER","PUSH_GUARD","PUSH_FATAL","PUSH_NEAR_GUARD",
          "CASE_0","CASE_1","CASE_2","CASE_3",
          "CASE_4","CASE_5","CASE_6","CASE_7",
          "STATE_MARK_ACTIVATED","STATE_MARK_FULL","STATE_KILL",
          "STATE_CHECK_ACTIVATED","STATE_CHECK_FULL","STATE_CHECK_APP",
          "API_GET_REPORTER","API_ACTIVATE_REPORTER","API_REPORT_EVENT",
          "API_REPORT_ERROR","API_REPORT_FATAL","API_ACTIVITY_TRACK","API_DEVICE_ID",
          "REPORTER_EVENT","REPORTER_ERROR","REPORTER_FATAL",
          "REPORTER_SESSION","REPORTER_REVENUE","REPORTER_DATA"}
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
        "CASE_UNKNOWN","MATCH_TRUE","MATCH_FALSE",
         "ENTER","RETURN","THROW","TRUE","FALSE","NON_BOOLEAN",
         "OTHER_THROW","EMPTY","NONEMPTY","NULL","OTHER_INPUT",
         "CLONE","ORIGINAL","MISSING","OTHER",
         "LOADER_MATCH","LOADER_DIFFERENT","LOADER_NULL","LOADER_UNKNOWN",
         "SDK_LEGACY","SDK_LEGACY_PUBLIC","SDK_LEGACY_IMPL","SDK_LEGACY_OTHER",
         "SDK_COMMON_UTILS","SDK_COMMON_API","SDK_IDENTIFIERS","SDK_PUSH",
         "SDK_NETWORK","SDK_PLUGINS","SDK_BILLING","SDK_ANALYTICS",
         "SDK_COMMON_INTERNAL","SDK_UTILS",
         "SDK_CRASH","SDK_SERVICE","SDK_STARTUP","SDK_PROXY",
         "SDK_REPORTER","SDK_INTERNAL","SDK_PUBLIC","SDK_NO_FRAME",
         "EXEC_COROUTINE","EXEC_EXECUTOR","EXEC_HANDLER","EXEC_OTHER",
         "HINT_LEGACY_API","HINT_MODERN_API","HINT_METRICA_GENERAL","HINT_NONE",
         "CLASS_PRESENT","CLASS_MISSING","ACTIVATE_PRESENT","ACTIVATE_ABSENT",
         "PUSH_NONE","PUSH_IMPL","PUSH_COMMON","PUSH_SERVICE","PUSH_FIREBASE",
         "PUSH_CORE","PUSH_OTHER","PUSH_METHOD_NONE","PUSH_METHOD_INIT",
         "PUSH_METHOD_ACTIVATE","PUSH_METHOD_OBFUSCATED_A",
         "PUSH_METHOD_OBFUSCATED_L","PUSH_METHOD_OTHER",
         "BEFORE_ONCREATE","DURING_ONCREATE","AFTER_ONCREATE"}
MARKER=re.compile(r"^event=([A-Z_]+);origin=([A-Z_]+);"
                  r"error=([A-Z_0-9]+);thread=(MAIN|OTHER)$")


def scoped_metrica_witness(exit_info:str,logcat:str,
                           stable_live_main_pid:int|str|None=None)->dict:
    owned=main_exit_pids(exit_info,"pro.celikom.yandex.nativeclonelab")
    # Successful 75-second MAIN has no ApplicationExitInfo. Accept only the
    # separately verified CURRENT pidof MAIN, never helper/aux processes or
    # arbitrary PIDs. This number remains private inside the runner.
    admitted=False
    if stable_live_main_pid is not None:
        value=str(stable_live_main_pid)
        if re.fullmatch(r"[1-9][0-9]{0,8}",value):
            owned.add(int(value))
            admitted=True
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
    activation=[x for x in seen if x[0]=="METRICA_ACTIVATE"]
    phases=[x for x in seen if x[0]=="METRICA_PHASE"]
    loaders=[x for x in seen if x[0]=="METRICA_LOADER"]
    sdk_context=[x for x in seen if x[0]=="METRICA_CONTEXT"]
    lifecycle=[x for x in seen if x[0]=="APP_LIFECYCLE"]
    sdk_state=[x for x in seen if x[0]=="METRICA_STATE"]
    sdk_api=[x for x in seen if x[0]=="METRICA_API"]
    reporter_calls=[x for x in seen if x[0]=="REPORTER_CALL"]
    throw_sites=[x for x in seen if x[0]=="METRICA_THROW_SITE"]
    throw_execution=[x for x in seen if x[0]=="METRICA_THROW_EXEC"]
    throw_loaders=[x for x in seen if x[0]=="METRICA_THROW_LOADER"]
    exact_fatal_sites=[x for x in seen if x[0]=="FATAL_THROW_SITE"]
    exact_fatal_hints=[x for x in seen if x[0]=="FATAL_THROW_HINT"]
    sdk_class=[x for x in seen if x[0]=="SDK_CLASS"]
    sdk_activate_signature=[x for x in seen if x[0]=="SDK_ACTIVATE_SIGNATURE"]
    module_checks=[x for x in seen if x[0]=="MODULES_IS_ACTIVATED"]
    module_hooks=[x for x in seen if x[0]=="MODULES_HOOK"]
    push_activations=[x for x in seen if x[0]=="PUSH_ACTIVATE"]
    push_inits=[x for x in seen if x[0]=="PUSH_INIT"]
    push_init_hooks=[x for x in seen if x[0]=="PUSH_INIT_HOOK"]
    push_hooks=[x for x in seen if x[0]=="PUSH_ACTIVATE_HOOK"]
    private_helper=[x for x in seen if x[0]=="PUSH_HELPER_BOOL"]
    private_helper_hook=[x for x in seen if x[0]=="PUSH_HELPER_HOOK"]
    all_guard=[x for x in seen if x[0]=="PUSH_ALL_FATAL_GUARD_VALUE"]
    all_guard_hook=[x for x in seen if x[0]=="PUSH_ALL_FATAL_GUARD_HOOK"]
    near_guard=[x for x in seen if x[0]=="PUSH_NEAR_GUARD_VALUE"]
    near_guard_hook=[x for x in seen if x[0]=="PUSH_NEAR_GUARD_HOOK"]
    exact_guard=[x for x in seen if x[0]=="PUSH_GUARD_VALUE"]
    exact_input=[x for x in seen if x[0]=="PUSH_GUARD_INPUT"]
    exact_guard_hook=[x for x in seen if x[0]=="PUSH_GUARD_HOOK"]
    exact_fatal=[x for x in seen if x[0]=="PUSH_FATAL_CALL"]
    exact_fatal_hook=[x for x in seen if x[0]=="PUSH_FATAL_HOOK"]
    push_throw_classes=[x for x in seen if x[0]=="METRICA_PUSH_THROW_CLASS"]
    push_throw_methods=[x for x in seen if x[0]=="METRICA_PUSH_THROW_METHOD"]
    focus_events={"METRICA_ACTIVATE","MODULES_IS_ACTIVATED","PUSH_ACTIVATE","PUSH_INIT",
                  "PUSH_NEAR_GUARD_VALUE","PUSH_ALL_FATAL_GUARD_VALUE",
                  "METRICA_PUSH_THROW_CLASS","METRICA_PUSH_THROW_METHOD",
                  "APP_LIFECYCLE"}
    sequence=[(event,origin,category) for event,origin,category,_thread
              in seen if event in focus_events][:65]
    first_metrica=next((i for i,x in enumerate(seen) if x[0]=="METRICA_EXCEPTION"),None)
    first_uncaught=next((i for i,x in enumerate(seen) if x[0]=="UNCAUGHT"),None)
    return {
        "stable_live_main_pid_admitted_without_disclosure":admitted,
        "sdk_exception_throw_sites":sorted({x[2] for x in throw_sites}),
        "sdk_exception_exec_contexts":sorted({x[2] for x in throw_execution}),
        "sdk_exception_thread_loader_categories":sorted({x[2] for x in throw_loaders}),
        "exact_fatal_sdk_throw_sites":sorted({x[2] for x in exact_fatal_sites}),
        "fatal_throw_site_observed":bool(exact_fatal_sites),
        "fatal_sdk_init_message_hints":sorted({x[2] for x in exact_fatal_hints}),
        "push_throw_subpackage_categories":sorted({x[2] for x in push_throw_classes}),
        "push_throw_method_categories":sorted({x[2] for x in push_throw_methods}),
        "activation_push_order_bounded":sequence,
        "private_all_exact_guard_hook_registered":any(
            x[2]=="REGISTERED" for x in all_guard_hook),
        "private_all_exact_guard_case_states":{
            case:{state:sum(x[1]==case and x[2]==state for x in all_guard)
                  for state in ("ENTER","TRUE","FALSE","THROW")}
            for case in ("CASE_0","CASE_1","CASE_2","CASE_3",
                         "CASE_4","CASE_5","CASE_6","CASE_7")},
        "private_all_exact_guard_timeline":[(x[1],x[2]) for x in all_guard[:64]],
        "private_push_near_fatal_guard_hook_registered":any(
            x[2]=="REGISTERED" for x in near_guard_hook),
        "private_push_near_fatal_guard_states":{
            state:sum(x[2]==state for x in near_guard)
            for state in ("ENTER","TRUE","FALSE","NON_BOOLEAN","OTHER_THROW")},
        "private_push_near_fatal_guard_timeline":[x[2] for x in near_guard[:48]],
        "private_push_guard_hook_registered":any(x[2]=="REGISTERED" for x in exact_guard_hook),
        "private_push_guard_input_states":{
            state:sum(x[2]==state for x in exact_input)
            for state in ("NULL","EMPTY","NONEMPTY","OTHER_INPUT")},
        "private_push_guard_input_timeline":[x[2] for x in exact_input[:48]],
        "private_push_guard_result_states":{state:sum(x[2]==state for x in exact_guard)
            for state in ("ENTER","TRUE","FALSE","NON_BOOLEAN","OTHER_THROW")},
        "private_push_guard_timeline":[x[2] for x in exact_guard[:48]],
        "private_push_fatal_hook_registered":any(x[2]=="REGISTERED" for x in exact_fatal_hook),
        "private_push_fatal_result_states":{state:sum(x[2]==state for x in exact_fatal)
            for state in ("ENTER","RETURN","DIRECT_METRICA","OTHER_THROW")},
        "private_push_fatal_timeline":[x[2] for x in exact_fatal[:48]],
        "private_push_helper_bool_hook_registered":any(
            x[2]=="REGISTERED" for x in private_helper_hook),
        "private_push_helper_bool_call_states":{
            state:sum(x[2]==state for x in private_helper)
            for state in ("ENTER","TRUE","FALSE","THROW")},
        "private_push_helper_bool_timeline": [x[2] for x in private_helper[:48]],
        "private_push_target_names_disclosed":False,
        "modules_activation_predicate_checks": {
            family:{state:sum(x[1]==family and x[2]==state for x in module_checks)
                    for state in ("TRUE","FALSE","THROW")}
            for family in ("METRICA_MODERN","METRICA_LEGACY")},
        "modules_activation_predicate_hook": {
            family:sorted({x[2] for x in module_hooks if x[1]==family})
            for family in ("METRICA_MODERN","METRICA_LEGACY")},
        "push_init_callbacks": {
            family:{state:sum(x[1]==family and x[2]==state for x in push_inits)
                    for state in ("ENTER","RETURN","THROW")}
            for family in ("PUSH_MODERN","PUSH_LEGACY")},
        "push_init_hook":{
            family:sorted({x[2] for x in push_init_hooks if x[1]==family})
            for family in ("PUSH_MODERN","PUSH_LEGACY")},
        "push_activation_callbacks": {
            family:{state:sum(x[1]==family and x[2]==state for x in push_activations)
                    for state in ("ENTER","RETURN","THROW")}
            for family in ("PUSH_MODERN","PUSH_LEGACY")},
        "push_activation_hook": {
            family:sorted({x[2] for x in push_hooks if x[1]==family})
            for family in ("PUSH_MODERN","PUSH_LEGACY")},
        "sdk_public_class_probe": {
            family:sorted({x[2] for x in sdk_class if x[1]==family})
            for family in ("METRICA_LEGACY","METRICA_MODERN")},
        "sdk_activate_method_probe": {
            family:sorted({x[2] for x in sdk_activate_signature if x[1]==family})
            for family in ("METRICA_LEGACY","METRICA_MODERN")},
        "reporter_hook_registered":any(
            x[0]=="REPORTER_HOOK" and x[2]=="REGISTERED" for x in seen),
        "reporter_calls_bounded":len(reporter_calls),
        "reporter_call_timeline":[(x[1],x[2]) for x in reporter_calls[:70]],
        "reporter_throw_categories":sorted({
            x[1] for x in reporter_calls if x[2]=="THROW"}),
        "sdk_internal_hook_registered":any(
            x[0]=="METRICA_STATE_HOOK" and x[2]=="REGISTERED" for x in seen),
        "sdk_public_hook_registered":any(
            x[0]=="METRICA_API_HOOK" and x[2]=="REGISTERED" for x in seen),
        "sdk_internal_state_timeline": [(x[1],x[2]) for x in sdk_state[:55]],
        "sdk_public_api_timeline": [(x[1],x[2]) for x in sdk_api[:55]],
        "sdk_internal_mark_full_returned":any(
            x[1]=="STATE_MARK_FULL" and x[2]=="RETURN" for x in sdk_state),
        "sdk_internal_kill_returned":any(
            x[1]=="STATE_KILL" and x[2]=="RETURN" for x in sdk_state),
        "sdk_public_throw_categories":sorted({
            x[1] for x in sdk_api if x[2]=="THROW"}),
        "metrica_activation_by_sdk": {
            family:{state:sum(x[1]==family and x[2]==state for x in activation)
                    for state in ("ENTER","RETURN","THROW")}
            for family in ("METRICA_LEGACY","METRICA_MODERN")},
        "metrica_activation_hook_registered":any(
            x[0]=="ACTIVATION_HOOK" and x[2]=="REGISTERED" for x in seen),
        "metrica_context_categories":sorted({x[2] for x in sdk_context}),
        "metrica_loader_categories":sorted({x[2] for x in loaders}),
        "metrica_activation_phases":sorted({x[2] for x in phases}),
        "app_oncreate_enter_seen":any(x[2]=="ENTER" for x in lifecycle),
        "app_oncreate_return_seen":any(x[2]=="RETURN" for x in lifecycle),
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
