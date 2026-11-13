"""Synthetic only: MAIN-exit PID bounded events, no user data leak."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from a1_metrica_witness_private_parser import scoped_metrica_witness
PKG="pro.celikom.yandex.nativeclonelab"
EXIT=f"ApplicationExitInfo #0: pid=431 process={PKG} reason=4 status=0\n"

def log(pid,s):
    return f"11-12 12:00:01.123 {pid} {pid} I CELIKOM_A1_EXIT_WITNESS: {s}\n"


class ReadOnlyMetricaWitnessTest(unittest.TestCase):
    def test_own_main_exact_events_return_enums_and_redact(self):
        value=(
            log(431,"event=ARMED;origin=REGISTERED;error=NONE;thread=MAIN")
            +log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_OTHER;thread=OTHER")
            +log(431,"event=METRICA_EXCEPTION;origin=MUSIC_APP;error=EXC_AUTH;thread=OTHER")
            +log(432,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_SIGNATURE;thread=OTHER")
            +"secret access_token=PRIVATESECRET\n")
        result=scoped_metrica_witness(EXIT,value)
        self.assertTrue(result["read_only_witness_arm_marker_seen"])
        self.assertTrue(result["read_only_metrica_exception_marker_seen"])
        self.assertEqual(result["metrica_exception_event_count_bounded"],2)
        self.assertEqual(result["metrica_exception_message_categories"],["EXC_AUTH","EXC_OTHER"])
        for secret in ("PRIVATESECRET","432","431","access_token"):
            self.assertNotIn(secret,str(result))

    def test_bounded_context_identity_and_metrica_before_uncaught(self):
        events=(
            log(431,"event=ARMED;origin=REGISTERED;error=NONE;thread=MAIN")
            +log(431,"event=APP_CONTEXT;origin=CLONE;error=APPINFO_CLONE;thread=MAIN")
            +log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_SDK_INIT;thread=OTHER")
            +log(431,"event=UNCAUGHT;origin=VENDOR;error=ILLEGAL_STATE;thread=OTHER")
            +log(433,"event=APP_CONTEXT;origin=ORIGINAL;error=APPINFO_ORIGINAL;thread=OTHER"))
        x=scoped_metrica_witness(EXIT,events)
        self.assertEqual(x["read_only_attach_context_identity_categories"],["CLONE"])
        self.assertEqual(x["read_only_attach_appinfo_identity_categories"],["APPINFO_CLONE"])
        self.assertTrue(x["metrica_exception_precedes_uncaught"])
        self.assertTrue(x["uncaught_illegal_state_observed"])
        self.assertEqual(x["metrica_exception_message_categories"],["EXC_SDK_INIT"])
        self.assertNotIn("433",str(x))

    def test_push_origin_and_order_bounded_privacy(self):
        sample=(
            log(431,"event=APP_LIFECYCLE;origin=APPLICATION;error=ENTER;thread=MAIN")
            +log(431,"event=MODULES_IS_ACTIVATED;origin=METRICA_MODERN;error=FALSE;thread=OTHER")
            +log(431,"event=METRICA_ACTIVATE;origin=METRICA_MODERN;error=RETURN;thread=MAIN")
            +log(431,"event=METRICA_PUSH_THROW_CLASS;origin=METRICA_SDK;error=PUSH_IMPL;thread=OTHER")
            +log(431,"event=METRICA_PUSH_THROW_METHOD;origin=METRICA_SDK;error=PUSH_METHOD_OBFUSCATED_A;thread=OTHER")
            +log(432,"event=METRICA_PUSH_THROW_CLASS;origin=METRICA_SDK;error=PUSH_CORE;thread=OTHER")
            +log(431,"event=METRICA_PUSH_THROW_CLASS;origin=METRICA_SDK;error=private_api;thread=OTHER"))
        got=scoped_metrica_witness(EXIT,sample)
        self.assertEqual(got["push_throw_subpackage_categories"],["PUSH_IMPL"])
        self.assertEqual(got["push_throw_method_categories"],["PUSH_METHOD_OBFUSCATED_A"])
        self.assertEqual([x[0] for x in got["activation_push_order_bounded"]],
                         ["APP_LIFECYCLE","MODULES_IS_ACTIVATED",
                          "METRICA_ACTIVATE","METRICA_PUSH_THROW_CLASS",
                          "METRICA_PUSH_THROW_METHOD"])
        self.assertNotIn("private_api",str(got))
        self.assertNotIn("432",str(got))

    def test_ephemeral_private_push_bool_results_are_bounded_readonly(self):
        rows=(
            log(431,"event=PUSH_HELPER_HOOK;origin=PUSH_HELPER;error=REGISTERED;thread=MAIN")
            +log(431,"event=PUSH_HELPER_BOOL;origin=PUSH_HELPER;error=ENTER;thread=OTHER")
            +log(431,"event=PUSH_HELPER_BOOL;origin=PUSH_HELPER;error=FALSE;thread=OTHER")
            +log(431,"event=PUSH_HELPER_BOOL;origin=PUSH_HELPER;error=TRUE;thread=OTHER")
            +log(999,"event=PUSH_HELPER_BOOL;origin=PUSH_HELPER;error=TRUE;thread=OTHER"))
        result=scoped_metrica_witness(EXIT,rows)
        self.assertTrue(result["private_push_helper_bool_hook_registered"])
        self.assertEqual(result["private_push_helper_bool_call_states"],
                         {"ENTER":1,"TRUE":1,"FALSE":1,"THROW":0})
        self.assertFalse(result["private_push_target_names_disclosed"])
        self.assertNotIn("999",str(result))


    def test_private_exact_push_guard_and_crash_enums_only(self):
        rows=(
            log(431,"event=PUSH_GUARD_HOOK;origin=PUSH_GUARD;error=REGISTERED;thread=MAIN")
            +log(431,"event=PUSH_FATAL_HOOK;origin=PUSH_FATAL;error=REGISTERED;thread=MAIN")
            +log(431,"event=PUSH_GUARD_VALUE;origin=PUSH_GUARD;error=ENTER;thread=OTHER")
            +log(431,"event=PUSH_GUARD_INPUT;origin=PUSH_GUARD;error=EMPTY;thread=OTHER")
            +log(431,"event=PUSH_GUARD_VALUE;origin=PUSH_GUARD;error=FALSE;thread=OTHER")
            +log(431,"event=PUSH_FATAL_CALL;origin=PUSH_FATAL;error=ENTER;thread=OTHER")
            +log(431,"event=PUSH_FATAL_CALL;origin=PUSH_FATAL;error=DIRECT_METRICA;thread=OTHER")
            +log(432,"event=PUSH_GUARD_VALUE;origin=PUSH_GUARD;error=TRUE;thread=OTHER")
            +log(431,"event=PUSH_GUARD_VALUE;origin=private.sdk;error=FALSE;thread=OTHER"))
        result=scoped_metrica_witness(EXIT,rows)
        self.assertTrue(result["private_push_guard_hook_registered"])
        self.assertEqual(result["private_push_guard_result_states"]["FALSE"],1)
        self.assertEqual(result["private_push_guard_input_states"]["EMPTY"],1)
        self.assertTrue(result["private_push_fatal_hook_registered"])
        self.assertEqual(result["private_push_fatal_result_states"]["DIRECT_METRICA"],1)
        self.assertNotIn("private.sdk",str(result))
        self.assertNotIn("432",str(result))






    def test_metrica_service_routing_owner_enums_no_intent_data(self):
        sample=(
            log(431,"event=METRICA_SERVICE_HOOK;origin=METRICA_SDK;error=REGISTERED;thread=MAIN")
            +log(431,"event=METRICA_SERVICE_CALL;origin=STOCK_TARGET;error=ENTER;thread=OTHER")
            +log(431,"event=METRICA_SERVICE_CALL;origin=STOCK_TARGET;error=FALSE_RESULT;thread=OTHER")
            +log(431,"event=METRICA_SERVICE_CALL;origin=CLONE_TARGET;error=ENTER;thread=MAIN")
            +log(431,"event=METRICA_SERVICE_CALL;origin=CLONE_TARGET;error=SUCCESS_RESULT;thread=MAIN")
            +log(432,"event=METRICA_SERVICE_CALL;origin=STOCK_TARGET;error=THROW;thread=OTHER")
            +log(431,"event=METRICA_SERVICE_CALL;origin=PRIVATE_INTENT;error=THROW;thread=OTHER"))
        report=scoped_metrica_witness(EXIT,sample)
        self.assertTrue(report["service_hook_registered"])
        self.assertEqual(report["service_sdk_target_states"]["STOCK_TARGET"]["FALSE_RESULT"],1)
        self.assertEqual(report["service_sdk_target_states"]["STOCK_TARGET"]["THROW"],0)
        self.assertEqual(report["service_sdk_target_states"]["CLONE_TARGET"]["SUCCESS_RESULT"],1)
        self.assertNotIn("PRIVATE_INTENT",str(report))
        self.assertNotIn("432",str(report))

    def test_provider_authority_metadata_and_sdk_query_are_bounded_enums(self):
        sample=(
            log(431,"event=METRICA_PROVIDER_RESOLVE;origin=STOCK_AUTH;error=STOCK_OWNER;thread=MAIN")
            +log(431,"event=METRICA_PROVIDER_RESOLVE;origin=CLONE_AUTH;error=CLONE_OWNER;thread=MAIN")
            +log(431,"event=METRICA_PROVIDER_QUERY_HOOK;origin=METRICA_SDK;error=REGISTERED;thread=MAIN")
            +log(431,"event=METRICA_PROVIDER_QUERY;origin=STOCK_AUTH;error=ENTER;thread=OTHER")
            +log(431,"event=METRICA_PROVIDER_QUERY;origin=STOCK_AUTH;error=NULL_RESULT;thread=OTHER")
            +log(999,"event=METRICA_PROVIDER_QUERY;origin=STOCK_AUTH;error=THROW;thread=OTHER")
            +log(431,"event=METRICA_PROVIDER_QUERY;origin=PRIVATE_DATA;error=NONNULL_RESULT;thread=OTHER"))
        report=scoped_metrica_witness(EXIT,sample)
        self.assertEqual(report["provider_metadata_owners"],
                         {"STOCK_AUTH":["STOCK_OWNER"],"CLONE_AUTH":["CLONE_OWNER"]})
        self.assertTrue(report["provider_query_hook_registered"])
        self.assertEqual(report["provider_query_sdk_states"]["STOCK_AUTH"]["ENTER"],1)
        self.assertEqual(report["provider_query_sdk_states"]["STOCK_AUTH"]["NULL_RESULT"],1)
        self.assertEqual(report["provider_query_sdk_states"]["STOCK_AUTH"]["THROW"],0)
        self.assertNotIn("PRIVATE_DATA",str(report))
        self.assertNotIn("999",str(report))

    def test_all_exact_fatal_guard_boolean_cases_and_pid_privacy(self):
        sample=(
            log(431,"event=PUSH_ALL_FATAL_GUARD_HOOK;origin=PUSH_GUARD;error=REGISTERED;thread=MAIN")
            +log(431,"event=PUSH_ALL_FATAL_GUARD_VALUE;origin=CASE_0;error=ENTER;thread=OTHER")
            +log(431,"event=PUSH_ALL_FATAL_GUARD_VALUE;origin=CASE_0;error=FALSE;thread=OTHER")
            +log(431,"event=PUSH_ALL_FATAL_GUARD_VALUE;origin=CASE_1;error=ENTER;thread=OTHER")
            +log(431,"event=PUSH_ALL_FATAL_GUARD_VALUE;origin=CASE_1;error=TRUE;thread=OTHER")
            +log(999,"event=PUSH_ALL_FATAL_GUARD_VALUE;origin=CASE_1;error=THROW;thread=OTHER")
            +log(431,"event=PUSH_ALL_FATAL_GUARD_VALUE;origin=PRIVATE_CLASS;error=FALSE;thread=OTHER"))
        report=scoped_metrica_witness(EXIT,sample)
        self.assertTrue(report["private_all_exact_guard_hook_registered"])
        self.assertEqual(report["private_all_exact_guard_case_states"]["CASE_0"]["FALSE"],1)
        self.assertEqual(report["private_all_exact_guard_case_states"]["CASE_1"]["TRUE"],1)
        self.assertEqual(report["private_all_exact_guard_case_states"]["CASE_1"]["THROW"],0)
        self.assertNotIn("PRIVATE_CLASS",str(report))
        self.assertNotIn("999",str(report))

    def test_near_fatal_boolean_guard_is_pid_scoped_no_argv(self):
        sample=(
            log(431,"event=PUSH_INIT;origin=PUSH_LEGACY;error=ENTER;thread=MAIN")
            +log(431,"event=PUSH_NEAR_GUARD_HOOK;origin=PUSH_NEAR_GUARD;error=REGISTERED;thread=MAIN")
            +log(431,"event=PUSH_NEAR_GUARD_VALUE;origin=PUSH_NEAR_GUARD;error=ENTER;thread=OTHER")
            +log(431,"event=PUSH_NEAR_GUARD_VALUE;origin=PUSH_NEAR_GUARD;error=FALSE;thread=OTHER")
            +log(431,"event=METRICA_PUSH_THROW_CLASS;origin=METRICA_SDK;error=PUSH_IMPL;thread=OTHER")
            +log(999,"event=PUSH_NEAR_GUARD_VALUE;origin=PUSH_NEAR_GUARD;error=TRUE;thread=OTHER")
            +log(431,"event=PUSH_NEAR_GUARD_VALUE;origin=SECRET;error=TRUE;thread=OTHER"))
        result=scoped_metrica_witness(EXIT,sample)
        self.assertTrue(result["private_push_near_fatal_guard_hook_registered"])
        self.assertEqual(result["private_push_near_fatal_guard_states"]["FALSE"],1)
        self.assertEqual(result["private_push_near_fatal_guard_states"]["TRUE"],0)
        self.assertIn(("PUSH_NEAR_GUARD_VALUE","PUSH_NEAR_GUARD","FALSE"),
                      result["activation_push_order_bounded"])
        self.assertNotIn("999",str(result))
        self.assertNotIn("SECRET",str(result))

    def test_actual_legacy_push_init_is_observed_without_any_mutation(self):
        rows=(
            log(431,"event=PUSH_INIT_HOOK;origin=PUSH_LEGACY;error=REGISTERED;thread=MAIN")
            +log(431,"event=PUSH_INIT;origin=PUSH_LEGACY;error=ENTER;thread=MAIN")
            +log(431,"event=PUSH_INIT;origin=PUSH_LEGACY;error=RETURN;thread=MAIN")
            +log(431,"event=METRICA_PUSH_THROW_CLASS;origin=METRICA_SDK;error=PUSH_IMPL;thread=OTHER")
            +log(999,"event=PUSH_INIT;origin=PUSH_LEGACY;error=THROW;thread=MAIN"))
        result=scoped_metrica_witness(EXIT,rows)
        self.assertEqual(result["push_init_hook"]["PUSH_LEGACY"],["REGISTERED"])
        self.assertEqual(result["push_init_callbacks"]["PUSH_LEGACY"],
                         {"ENTER":1,"RETURN":1,"THROW":0})
        self.assertEqual([x[0] for x in result["activation_push_order_bounded"]],
                         ["PUSH_INIT","PUSH_INIT","METRICA_PUSH_THROW_CLASS"])
        self.assertNotIn("999",str(result))

    def test_push_sdk_modules_predicate_and_activation_are_readonly(self):
        sample=(
            log(431,"event=MODULES_HOOK;origin=METRICA_MODERN;error=REGISTERED;thread=MAIN")
            +log(431,"event=MODULES_IS_ACTIVATED;origin=METRICA_MODERN;error=FALSE;thread=OTHER")
            +log(431,"event=MODULES_IS_ACTIVATED;origin=METRICA_MODERN;error=TRUE;thread=OTHER")
            +log(431,"event=PUSH_ACTIVATE_HOOK;origin=PUSH_MODERN;error=REGISTERED;thread=MAIN")
            +log(431,"event=PUSH_ACTIVATE;origin=PUSH_MODERN;error=ENTER;thread=MAIN")
            +log(431,"event=PUSH_ACTIVATE;origin=PUSH_MODERN;error=THROW;thread=MAIN")
            +log(999,"event=MODULES_IS_ACTIVATED;origin=METRICA_LEGACY;error=TRUE;thread=OTHER")
            +log(431,"event=PUSH_ACTIVATE;origin=BAD_EXTERNAL_TOKEN;error=THROW;thread=MAIN"))
        got=scoped_metrica_witness(EXIT,sample)
        self.assertEqual(got["modules_activation_predicate_checks"]["METRICA_MODERN"],
                         {"TRUE":1,"FALSE":1,"THROW":0})
        self.assertEqual(got["modules_activation_predicate_checks"]["METRICA_LEGACY"],
                         {"TRUE":0,"FALSE":0,"THROW":0})
        self.assertEqual(got["push_activation_callbacks"]["PUSH_MODERN"],
                         {"ENTER":1,"RETURN":0,"THROW":1})
        self.assertEqual(got["push_activation_hook"]["PUSH_MODERN"],["REGISTERED"])
        self.assertNotIn("BAD_EXTERNAL_TOKEN",str(got))

    def test_metrica_sdk_component_families_only_bounded_enums(self):
        sample=(
            log(431,"event=METRICA_THROW_SITE;origin=METRICA_SDK;error=SDK_COMMON_API;thread=OTHER")
            +log(431,"event=FATAL_THROW_SITE;origin=RUNTIME_KILL_HANDLER;error=SDK_PUSH;thread=OTHER")
            +log(432,"event=FATAL_THROW_SITE;origin=RUNTIME_KILL_HANDLER;error=SDK_IDENTIFIERS;thread=OTHER"))
        out=scoped_metrica_witness(EXIT,sample)
        self.assertEqual(out["sdk_exception_throw_sites"],["SDK_COMMON_API"])
        self.assertEqual(out["exact_fatal_sdk_throw_sites"],["SDK_PUSH"])

    def test_legacy_namespace_subfamily_public_api_presence_and_message_hint(self):
        sample=(
            log(431,"event=FATAL_THROW_SITE;origin=RUNTIME_KILL_HANDLER;error=SDK_LEGACY_IMPL;thread=OTHER")
            +log(431,"event=FATAL_THROW_HINT;origin=RUNTIME_KILL_HANDLER;error=HINT_LEGACY_API;thread=OTHER")
            +log(431,"event=SDK_CLASS;origin=METRICA_MODERN;error=CLASS_PRESENT;thread=MAIN")
            +log(431,"event=SDK_CLASS;origin=METRICA_LEGACY;error=CLASS_MISSING;thread=MAIN")
            +log(431,"event=SDK_ACTIVATE_SIGNATURE;origin=METRICA_MODERN;error=ACTIVATE_PRESENT;thread=MAIN")
            +log(432,"event=SDK_CLASS;origin=METRICA_LEGACY;error=CLASS_PRESENT;thread=MAIN")
            +log(431,"event=FATAL_THROW_HINT;origin=RUNTIME_KILL_HANDLER;error=API_KEY_PRIVATE;thread=OTHER"))
        x=scoped_metrica_witness(EXIT,sample)
        self.assertEqual(x["exact_fatal_sdk_throw_sites"],["SDK_LEGACY_IMPL"])
        self.assertEqual(x["fatal_sdk_init_message_hints"],["HINT_LEGACY_API"])
        self.assertEqual(x["sdk_public_class_probe"]["METRICA_LEGACY"],["CLASS_MISSING"])
        self.assertEqual(x["sdk_public_class_probe"]["METRICA_MODERN"],["CLASS_PRESENT"])
        self.assertEqual(x["sdk_activate_method_probe"]["METRICA_MODERN"],["ACTIVATE_PRESENT"])
        self.assertNotIn("PRIVATE",str(x))

    def test_exact_sdk_throw_site_exec_loader_and_pid_privacy(self):
        sample=(
            log(431,"event=METRICA_THROW_SITE;origin=METRICA_SDK;error=SDK_LEGACY;thread=OTHER")
            +log(431,"event=METRICA_THROW_EXEC;origin=METRICA_SDK;error=EXEC_COROUTINE;thread=OTHER")
            +log(431,"event=METRICA_THROW_LOADER;origin=METRICA_SDK;error=LOADER_DIFFERENT;thread=OTHER")
            +log(431,"event=FATAL_THROW_SITE;origin=RUNTIME_KILL_HANDLER;error=SDK_LEGACY;thread=OTHER")
            +log(432,"event=FATAL_THROW_SITE;origin=RUNTIME_KILL_HANDLER;error=SDK_INTERNAL;thread=OTHER")
            +log(431,"event=METRICA_THROW_SITE;origin=METRICA_SDK;error=private.vendor.Class;thread=OTHER"))
        out=scoped_metrica_witness(EXIT,sample)
        self.assertEqual(out["sdk_exception_throw_sites"],["SDK_LEGACY"])
        self.assertEqual(out["sdk_exception_exec_contexts"],["EXEC_COROUTINE"])
        self.assertEqual(out["sdk_exception_thread_loader_categories"],["LOADER_DIFFERENT"])
        self.assertEqual(out["exact_fatal_sdk_throw_sites"],["SDK_LEGACY"])
        self.assertTrue(out["fatal_throw_site_observed"])
        for secret in ("private.vendor.Class","431","432"):
            self.assertNotIn(secret,str(out))

    def test_actual_reporter_calls_must_be_scoped_enum_only(self):
        events=(
            log(431,"event=REPORTER_HOOK;origin=METRICA_SDK;error=REGISTERED;thread=MAIN")
            +log(431,"event=REPORTER_CALL;origin=REPORTER_EVENT;error=ENTER;thread=OTHER")
            +log(431,"event=REPORTER_CALL;origin=REPORTER_EVENT;error=THROW;thread=OTHER")
            +log(432,"event=REPORTER_CALL;origin=REPORTER_FATAL;error=THROW;thread=OTHER")
            +log(431,"event=REPORTER_CALL;origin=SECRET_VENDOR;error=THROW;thread=OTHER"))
        result=scoped_metrica_witness(EXIT,events)
        self.assertTrue(result["reporter_hook_registered"])
        self.assertEqual(result["reporter_throw_categories"],["REPORTER_EVENT"])
        self.assertEqual(result["reporter_calls_bounded"],2)
        self.assertNotIn("SECRET_VENDOR",str(result))
        self.assertNotIn("432",str(result))

    def test_readonly_metrica_internal_state_and_public_failure_categories(self):
        sample=(
            log(431,"event=METRICA_STATE_HOOK;origin=METRICA_SDK;error=REGISTERED;thread=MAIN")
            +log(431,"event=METRICA_API_HOOK;origin=METRICA_SDK;error=REGISTERED;thread=MAIN")
            +log(431,"event=METRICA_STATE;origin=STATE_MARK_FULL;error=ENTER;thread=MAIN")
            +log(431,"event=METRICA_STATE;origin=STATE_MARK_FULL;error=RETURN;thread=MAIN")
            +log(431,"event=METRICA_STATE;origin=STATE_CHECK_APP;error=FALSE;thread=OTHER")
            +log(431,"event=METRICA_API;origin=API_GET_REPORTER;error=ENTER;thread=OTHER")
            +log(431,"event=METRICA_API;origin=API_GET_REPORTER;error=THROW;thread=OTHER")
            +log(431,"event=METRICA_STATE;origin=STATE_KILL;error=RETURN;thread=OTHER")
            +log(777,"event=METRICA_STATE;origin=STATE_CHECK_APP;error=TRUE;thread=OTHER"))
        x=scoped_metrica_witness(EXIT,sample)
        self.assertTrue(x["sdk_internal_hook_registered"])
        self.assertTrue(x["sdk_public_hook_registered"])
        self.assertTrue(x["sdk_internal_mark_full_returned"])
        self.assertTrue(x["sdk_internal_kill_returned"])
        self.assertEqual(x["sdk_public_throw_categories"],["API_GET_REPORTER"])
        self.assertEqual(x["sdk_internal_state_timeline"][-1],("STATE_KILL","RETURN"))
        self.assertNotIn("777",str(x))

    def test_sdk_activation_order_loader_context_and_pid_sanitization(self):
        sample=(
            log(431,"event=APP_LIFECYCLE;origin=APPLICATION;error=ENTER;thread=MAIN")
            +log(431,"event=ACTIVATION_HOOK;origin=METRICA_SDK;error=REGISTERED;thread=MAIN")
            +log(431,"event=METRICA_CONTEXT;origin=METRICA_MODERN;error=CLONE;thread=MAIN")
            +log(431,"event=METRICA_LOADER;origin=METRICA_MODERN;error=LOADER_MATCH;thread=MAIN")
            +log(431,"event=METRICA_PHASE;origin=METRICA_MODERN;error=DURING_ONCREATE;thread=MAIN")
            +log(431,"event=METRICA_ACTIVATE;origin=METRICA_MODERN;error=ENTER;thread=MAIN")
            +log(431,"event=METRICA_ACTIVATE;origin=METRICA_MODERN;error=RETURN;thread=MAIN")
            +log(431,"event=APP_LIFECYCLE;origin=APPLICATION;error=RETURN;thread=MAIN")
            +log(888,"event=METRICA_ACTIVATE;origin=METRICA_LEGACY;error=THROW;thread=OTHER"))
        result=scoped_metrica_witness(EXIT,sample)
        self.assertTrue(result["metrica_activation_hook_registered"])
        self.assertEqual(result["metrica_activation_by_sdk"]["METRICA_MODERN"],
                         {"ENTER":1,"RETURN":1,"THROW":0})
        self.assertEqual(result["metrica_activation_by_sdk"]["METRICA_LEGACY"],
                         {"ENTER":0,"RETURN":0,"THROW":0})
        self.assertEqual(result["metrica_context_categories"],["CLONE"])
        self.assertEqual(result["metrica_loader_categories"],["LOADER_MATCH"])
        self.assertEqual(result["metrica_activation_phases"],["DURING_ONCREATE"])
        self.assertTrue(result["app_oncreate_enter_seen"])
        self.assertTrue(result["app_oncreate_return_seen"])
        self.assertNotIn("888",str(result))

    def test_exact_exception_object_observed_at_android_fatal_dispatch(self):
        events=(
            log(431,"event=FATAL_HOOK;origin=THREAD_DISPATCH;error=REGISTERED;thread=MAIN")
            +log(431,"event=FATAL_HOOK;origin=RUNTIME_KILL_HANDLER;error=REGISTERED;thread=MAIN")
            +log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_SDK_INIT;thread=OTHER")
            +log(431,"event=FATAL_DISPATCH;origin=RUNTIME_KILL_HANDLER;error=DIRECT_METRICA;thread=OTHER")
            +log(432,"event=FATAL_DISPATCH;origin=RUNTIME_KILL_HANDLER;error=NOT_METRICA;thread=OTHER"))
        x=scoped_metrica_witness(EXIT,events)
        self.assertEqual(x["fatal_throwable_link_verdict"],"DIRECT_IDENTITY")
        self.assertTrue(x["fatal_throwable_metrica_direct_identity_seen"])
        self.assertFalse(x["fatal_throwable_metrica_cause_identity_seen"])
        self.assertEqual(x["fatal_dispatch_paths"],["RUNTIME_KILL_HANDLER"])
        self.assertEqual(x["fatal_dispatch_event_count_bounded"],1)
        self.assertEqual(x["fatal_handler_hook_registration"],
                         ["RUNTIME_KILL_HANDLER","THREAD_DISPATCH"])
        self.assertNotIn("432",str(x))

    def test_fatal_sdk_detail_only_whitelisted_error_category(self):
        events=(
            log(431,"event=METRICA_DETAIL;origin=METRICA_SDK;error=DETAIL_NOT_INITIALIZED;thread=OTHER")
            +log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_SDK_INIT;thread=OTHER")
            +log(431,"event=FATAL_DISPATCH;origin=RUNTIME_KILL_HANDLER;error=DIRECT_METRICA;thread=OTHER")
            +log(431,"event=FATAL_DETAIL;origin=RUNTIME_KILL_HANDLER;error=DETAIL_NOT_INITIALIZED;thread=OTHER")
            +log(433,"event=FATAL_DETAIL;origin=RUNTIME_KILL_HANDLER;error=DETAIL_API_KEY;thread=OTHER"))
        x=scoped_metrica_witness(EXIT,events)
        self.assertEqual(x["fatal_throwable_link_verdict"],"DIRECT_IDENTITY")
        self.assertEqual(x["bounded_fatal_metrica_detail_categories"],["DETAIL_NOT_INITIALIZED"])
        self.assertEqual(x["bounded_metrica_constructor_detail_categories"],["DETAIL_NOT_INITIALIZED"])
        self.assertTrue(x["fatal_metrica_detail_observed"])
        self.assertNotIn("433",str(x))

    def test_only_direct_metrica_crash_suppression_is_counted(self):
        events=(
            log(431,"event=LAB_METRICA_FAILOPEN;origin=RUNTIME_KILL_HANDLER;error=DIRECT_METRICA;thread=OTHER")
            +log(432,"event=LAB_METRICA_FAILOPEN;origin=RUNTIME_KILL_HANDLER;error=DIRECT_METRICA;thread=OTHER")
            +log(431,"event=LAB_METRICA_FAILOPEN;origin=RUNTIME_LOG_HANDLER;error=UNRELATED;thread=OTHER"))
        result=scoped_metrica_witness(EXIT,events)
        self.assertTrue(result["lab_only_metrica_fatal_suppression_observed"])
        self.assertEqual(result["lab_only_metrica_fatal_suppression_count_bounded"],1)

    def test_live_stable_main_events_without_any_exit_record(self):
        logcat=(log(431,"event=ARMED;origin=REGISTERED;error=NONE;thread=MAIN")
                +log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_SDK_INIT;thread=OTHER")
                +log(431,"event=LAB_METRICA_FAILOPEN;origin=RUNTIME_KILL_HANDLER;error=DIRECT_METRICA;thread=OTHER")
                +log(432,"event=LAB_METRICA_FAILOPEN;origin=RUNTIME_KILL_HANDLER;error=DIRECT_METRICA;thread=OTHER"))
        result=scoped_metrica_witness("",logcat,stable_live_main_pid="431")
        self.assertTrue(result["stable_live_main_pid_admitted_without_disclosure"])
        self.assertTrue(result["read_only_witness_arm_marker_seen"])
        self.assertTrue(result["lab_only_metrica_fatal_suppression_observed"])
        self.assertEqual(result["lab_only_metrica_fatal_suppression_count_bounded"],1)
        self.assertNotIn("431",str(result))
        self.assertNotIn("432",str(result))

    def test_malformed_live_pid_never_joins_witness_scope(self):
        text=log(431,"event=LAB_METRICA_FAILOPEN;origin=RUNTIME_KILL_HANDLER;error=DIRECT_METRICA;thread=OTHER")
        for invalid in ("431 432","0","-1","abc","000431","123456789012345"):
            out=scoped_metrica_witness("",text,stable_live_main_pid=invalid)
            self.assertFalse(out["stable_live_main_pid_admitted_without_disclosure"])
            self.assertFalse(out["lab_only_metrica_fatal_suppression_observed"])

    def test_arbitrary_sensitive_fatal_message_category_is_rejected(self):
        events=(log(431,"event=FATAL_DETAIL;origin=RUNTIME_KILL_HANDLER;error=API_KEY_SECRET;thread=OTHER")
                +log(431,"event=FATAL_DETAIL;origin=RUNTIME_KILL_HANDLER;error=DETAIL_CONFIG;thread=OTHER path=/private"))
        x=scoped_metrica_witness(EXIT,events)
        self.assertFalse(x["fatal_metrica_detail_observed"])
        self.assertEqual(x["bounded_fatal_metrica_detail_categories"],[])

    def test_exact_cause_not_constructor_time_nearby(self):
        events=(
            log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_SDK_INIT;thread=OTHER")
            +log(431,"event=FATAL_DISPATCH;origin=THREAD_GROUP;error=CAUSE_METRICA;thread=OTHER"))
        x=scoped_metrica_witness(EXIT,events)
        self.assertEqual(x["fatal_throwable_link_verdict"],"CAUSE_IDENTITY")
        self.assertTrue(x["fatal_throwable_metrica_cause_identity_seen"])

    def test_no_equality_claim_when_no_dispatch_hook_fires(self):
        events=(
            log(431,"event=FATAL_HOOK;origin=THREAD_DISPATCH;error=NO_HOOK;thread=MAIN")
            +log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_SDK_INIT;thread=OTHER"))
        x=scoped_metrica_witness(EXIT,events)
        self.assertEqual(x["fatal_throwable_link_verdict"],"FATAL_DISPATCH_NOT_OBSERVED")
        self.assertFalse(x["fatal_dispatch_observed"])
        self.assertEqual(x["fatal_handler_hook_missing"],["THREAD_DISPATCH"])

    def test_not_matched_is_inconclusive_not_exonerating(self):
        events=(
            log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_SDK_INIT;thread=OTHER")
            +log(431,"event=FATAL_DISPATCH;origin=THREAD_GROUP;error=NOT_METRICA;thread=OTHER"))
        x=scoped_metrica_witness(EXIT,events)
        self.assertEqual(x["fatal_throwable_link_verdict"],
                         "FATAL_SEEN_NO_CONSTRUCTOR_IDENTITY")
        self.assertFalse(x["fatal_throwable_metrica_direct_identity_seen"])
        self.assertFalse(x["fatal_throwable_metrica_cause_identity_seen"])

    def test_exact_push_object_state_only_bounded_enums(self):
        events=(
            log(431,"event=PUSH_FATAL_OBJECT_HOOK;origin=PUSH_ARG;error=REGISTERED;thread=OTHER")
            +log(431,"event=PUSH_FATAL_OBJECT;origin=ARG_ENTER;error=OBJECT_NULL_DEPENDENCY;thread=OTHER")
            +log(431,"event=PUSH_FATAL_OBJECT;origin=RECEIVER_ENTER;error=OBJECT_ALL_REFERENCES_SET;thread=OTHER")
            +log(431,"event=PUSH_FATAL_OBJECT_LOADER;origin=PUSH_ARG;error=LOADER_MATCH;thread=OTHER")
            +log(431,"event=PUSH_FATAL_OBJECT_OUTCOME;origin=PUSH_ARG;error=DIRECT_METRICA;thread=OTHER")
            +log(431,"event=PUSH_FATAL_OBJECT;origin=ARG_THROW;error=OBJECT_NULL_DEPENDENCY;thread=OTHER")
            +log(431,"event=PUSH_FATAL_OBJECT;origin=ARG_THROW;error=secret_field_value;thread=OTHER")
            +log(432,"event=PUSH_FATAL_OBJECT;origin=ARG_THROW;error=OBJECT_ALL_REFERENCES_SET;thread=OTHER")
        )
        got=scoped_metrica_witness(EXIT,events)
        self.assertTrue(got["exact_push_object_hook_registered"])
        self.assertEqual(got["exact_push_object_state_timeline"],[
            ("ARG_ENTER","OBJECT_NULL_DEPENDENCY"),
            ("RECEIVER_ENTER","OBJECT_ALL_REFERENCES_SET"),
            ("ARG_THROW","OBJECT_NULL_DEPENDENCY")])
        self.assertEqual(got["exact_push_object_loader_categories"],["LOADER_MATCH"])
        self.assertEqual(got["exact_push_object_outcome_timeline"],["DIRECT_METRICA"])
        self.assertFalse(got["exact_push_object_raw_fields_or_values_disclosed"])
        self.assertNotIn("secret_field_value",str(got))

    def test_exact_fatal_direct_receiver_field_read_is_enum_only(self):
        events=(
            log(431,"event=PUSH_FATAL_READ_FIELD_ENTER;origin=CASE_0;error=FIELD_NULL;thread=OTHER")
            +log(431,"event=PUSH_FATAL_READ_FIELD_THROW;origin=CASE_0;error=FIELD_SET;thread=OTHER")
            +log(432,"event=PUSH_FATAL_READ_FIELD_THROW;origin=CASE_0;error=FIELD_NULL;thread=OTHER")
            +log(431,"event=PUSH_FATAL_READ_FIELD_THROW;origin=CASE_0;error=private_field;thread=OTHER"))
        out=scoped_metrica_witness(EXIT,events)
        self.assertEqual(out["exact_push_direct_receiver_field_states"],[
            ("PUSH_FATAL_READ_FIELD_ENTER","CASE_0","FIELD_NULL"),
            ("PUSH_FATAL_READ_FIELD_THROW","CASE_0","FIELD_SET")])
        self.assertNotIn("private_field",str(out))

    def test_exact_push_guard_correlation_is_scoped_and_private(self):
        events=(
            log(431,"event=PUSH_FATAL_GUARD_THROW;origin=PUSH_ARG;error=GUARD_TRUE_ONLY;thread=OTHER")
            +log(431,"event=PUSH_FATAL_GUARD_RETURN;origin=PUSH_ARG;error=GUARD_NOT_IN_CALL;thread=OTHER")
            +log(432,"event=PUSH_FATAL_GUARD_THROW;origin=PUSH_ARG;error=GUARD_FALSE_ONLY;thread=OTHER")
            +log(431,"event=PUSH_FATAL_GUARD_THROW;origin=PUSH_ARG;error=VENDOR_PRIVATE;thread=OTHER")
        )
        result=scoped_metrica_witness(EXIT,events)
        self.assertEqual(result["exact_push_same_call_guard_states"],[
            ("PUSH_FATAL_GUARD_THROW","GUARD_TRUE_ONLY"),
            ("PUSH_FATAL_GUARD_RETURN","GUARD_NOT_IN_CALL")])
        self.assertNotIn("VENDOR_PRIVATE",str(result))

    def test_exact_push_constructor_phase_is_identity_only_and_main_scoped(self):
        events=(
            log(431,"event=PUSH_FATAL_CONSTRUCTOR_ORDER;origin=PUSH_ARG;error=CTOR_AFTER_TRUE;thread=OTHER")
            +log(431,"event=PUSH_FATAL_CONSTRUCTOR_ORDER;origin=PUSH_ARG;error=CTOR_OTHER_IDENTITY;thread=OTHER")
            +log(432,"event=PUSH_FATAL_CONSTRUCTOR_ORDER;origin=PUSH_ARG;error=CTOR_BEFORE_TRUE;thread=OTHER")
            +log(431,"event=PUSH_FATAL_CONSTRUCTOR_ORDER;origin=PUSH_ARG;error=secret_private_throw;thread=OTHER")
        )
        result=scoped_metrica_witness(EXIT,events)
        self.assertEqual(result["exact_push_same_call_constructor_order"],
                         ["CTOR_AFTER_TRUE","CTOR_OTHER_IDENTITY"])
        self.assertNotIn("secret_private_throw",str(result))

    def test_exact_post_true_push_service_witness_only_finite_main_events(self):
        rows=(
            log(431,"event=PUSH_SERVICE_HOOK;origin=PUSH_SERVICE;error=REGISTERED;thread=MAIN")
            +log(431,"event=PUSH_SERVICE_PHASE;origin=PUSH_SERVICE;error=AFTER_TRUE;thread=OTHER")
            +log(431,"event=PUSH_SERVICE_CALL;origin=PUSH_SERVICE;error=ENTER;thread=OTHER")
            +log(431,"event=PUSH_SERVICE_CALL;origin=PUSH_SERVICE;error=THROW;thread=OTHER")
            +log(431,"event=PUSH_SERVICE_ERROR;origin=PUSH_SERVICE;error=ILLEGAL_STATE;thread=OTHER")
            +log(432,"event=PUSH_SERVICE_CALL;origin=PUSH_SERVICE;error=RETURN;thread=OTHER")
            +log(431,"event=PUSH_SERVICE_ERROR;origin=PUSH_SERVICE;error=PRIVATE_THROWABLE_NAME;thread=OTHER"))
        result=scoped_metrica_witness(EXIT,rows)
        self.assertTrue(result["exact_post_true_push_service_hook_registered"])
        self.assertEqual(result["exact_post_true_push_service_states"],
                         {"ENTER":1,"RETURN":0,"THROW":1})
        self.assertEqual(result["exact_post_true_push_service_phase"],["AFTER_TRUE"])
        self.assertEqual(result["exact_post_true_push_service_error"],["ILLEGAL_STATE"])
        self.assertNotIn("PRIVATE_THROWABLE_NAME",str(result))
        self.assertNotIn("432",str(result))

    def test_exact_pushservice_events_survive_existing_250_legacy_cap(self):
        prefix=log(431,"event=ARMED;origin=REGISTERED;error=NONE;thread=OTHER")*260
        suffix=(log(431,"event=PUSH_SERVICE_HOOK;origin=PUSH_SERVICE;error=REGISTERED;thread=OTHER")
                +log(431,"event=PUSH_SERVICE_PHASE;origin=PUSH_SERVICE;error=AFTER_TRUE;thread=OTHER")
                +log(431,"event=PUSH_SERVICE_CALL;origin=PUSH_SERVICE;error=RETURN;thread=OTHER"))
        result=scoped_metrica_witness(EXIT,prefix+suffix)
        self.assertTrue(result["exact_post_true_push_service_hook_registered"])
        self.assertEqual(result["exact_post_true_push_service_states"]["RETURN"],1)
        self.assertEqual(result["exact_post_true_push_service_phase"],["AFTER_TRUE"])
        self.assertEqual(result["all_witness_events_bounded"],250)

    def test_exact_provider_return_throw_and_main_pid(self):
        sample=(
            log(431,"event=PUSH_PROVIDER_HOOK;origin=PUSH_PROVIDER;error=REGISTERED;thread=MAIN")
            +log(431,"event=PUSH_PROVIDER_PHASE;origin=PUSH_PROVIDER;error=AFTER_TRUE;thread=OTHER")
            +log(431,"event=PUSH_PROVIDER_CALL;origin=PUSH_PROVIDER;error=ENTER;thread=OTHER")
            +log(431,"event=PUSH_PROVIDER_CALL;origin=PUSH_PROVIDER;error=THROW;thread=OTHER")
            +log(431,"event=PUSH_PROVIDER_ERROR;origin=PUSH_PROVIDER;error=ILLEGAL_STATE;thread=OTHER")
            +log(432,"event=PUSH_PROVIDER_CALL;origin=PUSH_PROVIDER;error=RETURN;thread=OTHER")
            +log(431,"event=PUSH_PROVIDER_ERROR;origin=PUSH_PROVIDER;error=SECRET;thread=OTHER"))
        got=scoped_metrica_witness(EXIT,sample)
        self.assertTrue(got["exact_post_true_push_provider_hook_registered"])
        self.assertEqual(got["exact_post_true_push_provider_states"],
                         {"ENTER":1,"RETURN":0,"THROW":1})
        self.assertEqual(got["exact_post_true_push_provider_phase"],["AFTER_TRUE"])
        self.assertEqual(got["exact_post_true_push_provider_error"],["ILLEGAL_STATE"])
        self.assertNotIn("SECRET",str(got))
        self.assertNotIn("432",str(got))

    def test_provider_events_survive_legacy_cap(self):
        old=log(431,"event=ARMED;origin=REGISTERED;error=NONE;thread=OTHER")*260
        nxt=(log(431,"event=PUSH_PROVIDER_HOOK;origin=PUSH_PROVIDER;error=REGISTERED;thread=OTHER")
             +log(431,"event=PUSH_PROVIDER_CALL;origin=PUSH_PROVIDER;error=RETURN;thread=OTHER"))
        got=scoped_metrica_witness(EXIT,old+nxt)
        self.assertTrue(got["exact_post_true_push_provider_hook_registered"])
        self.assertEqual(got["exact_post_true_push_provider_states"]["RETURN"],1)
        self.assertEqual(got["all_witness_events_bounded"],250)

    def test_provider_failure_reason_categorized_only_and_correlated(self):
        rows=(
            log(431,"event=PUSH_PROVIDER_REASON;origin=PUSH_PROVIDER;error=PROVIDER_CUSTOM_META_PAIR;thread=OTHER")
            +log(431,"event=PUSH_FATAL_PROVIDER_LINK;origin=PUSH_ARG;error=SAME_CALL_PROVIDER_THROW;thread=OTHER")
            +log(432,"event=PUSH_PROVIDER_REASON;origin=PUSH_PROVIDER;error=PROVIDER_REASON_OTHER;thread=OTHER")
            +log(431,"event=PUSH_PROVIDER_REASON;origin=PUSH_PROVIDER;error=TOKEN_123;thread=OTHER"))
        got=scoped_metrica_witness(EXIT,rows)
        self.assertEqual(got["exact_post_true_push_provider_reason"],["PROVIDER_CUSTOM_META_PAIR"])
        self.assertEqual(got["exact_post_true_push_provider_same_fatal_call"],
                         ["SAME_CALL_PROVIDER_THROW"])
        self.assertNotIn("TOKEN_123",str(got))

    def test_exact_provider_config_presence_finite_owned_pid_only(self):
        events=(
            log(431,"event=PUSH_PROVIDER_REASON;origin=PUSH_PROVIDER;error=PROVIDER_NO_VALID_CONTROLLER;thread=OTHER")
            +log(431,"event=PUSH_PROVIDER_CONFIG_CUSTOM;origin=PUSH_PROVIDER;error=PAIR_NONE;thread=OTHER")
            +log(431,"event=PUSH_PROVIDER_CONFIG_DEFAULT;origin=PUSH_PROVIDER;error=PAIR_SENDER_ONLY;thread=OTHER")
            +log(431,"event=PUSH_PROVIDER_CONFIG_RESOURCE;origin=PUSH_PROVIDER;error=PAIR_BOTH;thread=OTHER")
            +log(432,"event=PUSH_PROVIDER_CONFIG_CUSTOM;origin=PUSH_PROVIDER;error=PAIR_BOTH;thread=OTHER")
            +log(431,"event=PUSH_PROVIDER_CONFIG_RESOURCE;origin=PUSH_PROVIDER;error=SECRET_SENDER;thread=OTHER"))
        got=scoped_metrica_witness(EXIT,events)
        self.assertEqual(got["exact_post_true_push_provider_reason"],
                         ["PROVIDER_NO_VALID_CONTROLLER"])
        self.assertEqual(got["exact_post_true_provider_config_presence"],
            {"CUSTOM_META":["PAIR_NONE"],"DEFAULT_META":["PAIR_SENDER_ONLY"],
             "GOOGLE_RESOURCE":["PAIR_BOTH"]})
        self.assertNotIn("SECRET_SENDER",str(got))
        self.assertNotIn("432",str(got))

    def test_firebase_namespace_resource_probe_only_enums(self):
        rows=(log(431,"event=PUSH_PROVIDER_CONFIG_CLONE_ID;origin=PUSH_PROVIDER;error=PAIR_NONE;thread=OTHER")
              +log(431,"event=PUSH_PROVIDER_CONFIG_STOCK_ID;origin=PUSH_PROVIDER;error=PAIR_BOTH;thread=OTHER")
              +log(431,"event=PUSH_PROVIDER_CONFIG_STOCK_VALUE;origin=PUSH_PROVIDER;error=PAIR_BOTH;thread=OTHER")
              +log(432,"event=PUSH_PROVIDER_CONFIG_STOCK_VALUE;origin=PUSH_PROVIDER;error=PAIR_UNKNOWN;thread=OTHER")
              +log(431,"event=PUSH_PROVIDER_CONFIG_STOCK_VALUE;origin=PUSH_PROVIDER;error=SECRET_VALUE;thread=OTHER"))
        got=scoped_metrica_witness(EXIT,rows)["exact_post_true_provider_namespace_lookup"]
        self.assertEqual(got["CLONE_RESOURCE_ID"],["PAIR_NONE"])
        self.assertEqual(got["PUBLISHER_NAMESPACE_ID"],["PAIR_BOTH"])
        self.assertEqual(got["PUBLISHER_NAMESPACE_VALUE"],["PAIR_BOTH"])
        self.assertNotIn("SECRET_VALUE",str(got))

    def test_disallow_arbitrary_event_or_injected_message(self):
        bad=(log(431,"event=METRICA_EXCEPTION;origin=SECRET_VENDOR;error=EXC_OTHER;thread=OTHER")
             +log(431,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_OTHER;thread=OTHER token=secret"))
        out=scoped_metrica_witness(EXIT,bad)
        self.assertFalse(out["read_only_metrica_exception_marker_seen"])
        self.assertEqual(out["all_witness_events_bounded"],0)

    def test_unknown_main_exit_cannot_attach_helper_events(self):
        out=scoped_metrica_witness(f"process={PKG}:Metrica pid=432 reason=4",
                log(432,"event=METRICA_EXCEPTION;origin=METRICA_SDK;error=EXC_OTHER;thread=OTHER"))
        self.assertEqual(out["metrica_exception_event_count_bounded"],0)
        self.assertFalse(out["read_only_witness_arm_marker_seen"])


if __name__=="__main__":
    unittest.main()
