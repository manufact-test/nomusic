"""Read-only, no-secret original 2025 login receipt witness source gate."""
from pathlib import Path
import unittest
import ast
import re

SRC=(Path(__file__).resolve().parents[1] /
     "exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness/ExitCallsiteWitness.java")

class PostLoginReceiptSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code=SRC.read_text(encoding="utf-8")

    def test_account_password_preserved_and_never_logged(self):
        s=self.code
        self.assertIn('AccountManager.class.getDeclaredMethod("getPassword", Account.class)',s)
        self.assertIn('OWN_ACCOUNT_TYPE.equals(((Account) candidate).type)',s)
        self.assertIn('emit("MASTER_TOKEN_READ"',s)
        self.assertIn('result = chain.proceed();',s)
        self.assertIn('throw failure;',s)
        self.assertNotIn('emit("MASTER_TOKEN_READ", token',s)
        self.assertNotIn('emit("MASTER_TOKEN_READ", result',s)

    def test_exact_original_result_chain_version_pinned(self):
        s=self.code
        for snippet in (
          'Class.forName("ZX5", false, loader)',
          'Class.forName("WS3", false, loader)',
          'Class.forName("hT3", false, loader)',
          'Class.forName("YS3", false, loader)',
          'Class.forName("lw4", false, loader)',
          'receiver.getDeclaredMethod("if", resultType)',
          'receiver.getDeclaredMethod("try", Bundle.class, String.class)',
          'receiver.getDeclaredMethod("if", info, boolean.class)',
          'WS3$b',
          'EntryScreenCloseLoginKey',
          'POSTLOGIN_PUBLISH',
          'POSTLOGIN_CONSUME',
          'POSTLOGIN_MAIN_ROUTE'):
            self.assertIn(snippet,s)

    def test_original_login_and_autologin_source_are_fixed_enum_only(self):
        s=self.code
        start=s.index('private static String originalPostLoginCallerCategory()')
        end=s.index('private synchronized void observeOriginalPostLoginReceipts(',start)
        part=s[start:end]
        self.assertIn('Thread.currentThread().getStackTrace()',part)
        self.assertIn('Math.min(frames.length, 48)',part)
        self.assertIn('"oY5$a".equals(owner) && "emit".equals(method)',part)
        self.assertIn('"pY5$a".equals(owner) && "emit".equals(method)',part)
        self.assertIn('return "PASSPORT_LOGIN_RESULT"',part)
        self.assertIn('return "AUTOLOGIN_UID_RESULT"',part)
        self.assertIn('return "OTHER_CALLER"',part)
        self.assertNotIn('emit("LOGIN_PIPELINE_SOURCE", owner',part)
        self.assertNotIn('frame.toString()',part)
        observer=s[s.index('private synchronized void observeOriginalPostLoginReceipts('):
                   s.index('// Original LoginFragment flow emission:',s.index('private synchronized void observeOriginalPostLoginReceipts('))]
        self.assertIn('postLoginPipelineSourceEvents.incrementAndGet() <= 8',observer)
        self.assertIn('emit("LOGIN_PIPELINE_SOURCE", "ENTRY",',observer)
        self.assertIn('originalPostLoginCallerCategory()',observer)

    def test_exact_original_coroutine_terminal_stage_is_readonly(self):
        s=self.code
        start=s.index('private synchronized void observeOriginalPostLoginReceipts(')
        end=s.index('// Original LoginFragment flow emission:',start)
        part=s[start:end]
        self.assertIn('Class.forName("qY5", false, loader)',part)
        self.assertIn('Class.forName("nY5", false, loader)',part)
        self.assertIn('getDeclaredField("continue")',part)
        self.assertIn('"if", owner, boolean.class,',part)
        self.assertIn('chain.getArg(3)',part)
        self.assertIn('stateField.getInt(frame) & Integer.MAX_VALUE',part)
        self.assertIn('"AFTER_TOKEN_REQUEST"',part)
        self.assertIn('"AFTER_USERINFO_REQUEST"',part)
        self.assertIn('"AFTER_SYNC"',part)
        self.assertIn('postLoginPipelineEvents.incrementAndGet() <= 32',part)
        self.assertIn('emit("LOGIN_PIPELINE_RESULT", stage, category)',part)
        self.assertIn('emit("POSTLOGIN_HOOK", "PIPELINE", "REGISTERED")',part)
        self.assertIn('throw failure;',part)
        self.assertIn('return result;',part)
        self.assertNotIn('.getMessage()',part)
        self.assertNotIn('.getPassword(',part)
        self.assertNotIn('chain.proceed(new Object',part)

    def test_token_request_return_categories_do_not_read_or_log_credentials(self):
        s=self.code
        part=s[s.index('private static String tokenRequestErrorCategory('):
               s.index('// Original LoginFragment flow emission:',s.index('private static String tokenRequestErrorCategory('))]
        self.assertIn('resumed.getDeclaredField("private")',part)
        self.assertIn('Class.forName("zW8$b", false, loader)',part)
        self.assertIn('tokenFailure.getDeclaredField("default")',part)
        self.assertIn('"AFTER_TOKEN_REQUEST".equals(stage)',part)
        self.assertIn('postLoginTokenOutcomeEvents.incrementAndGet() <= 12',part)
        self.assertIn('emit("LOGIN_TOKEN_OUTCOME", "ENTRY", category)',part)
        self.assertIn('emit("LOGIN_TOKEN_ERROR_KIND", "ENTRY",',part)
        for category in ('"NULL"', '"FAILURE"', '"STRING_RESULT"',
                         '"OTHER_NONFAILURE_RESULT"', '"PASSPORT_API_A"',
                         '"PASSPORT_API_B"', '"SECURITY"', '"NETWORK_OR_IO"'):
            self.assertIn(category,part)
        self.assertIn('return chain.proceed();',part)
        self.assertIn('return result;',part)
        for forbidden in ('getMessage()', 'getStackTrace()', 'getPassword(',
                          '.toString()', '.setResult(', '.startActivity(',
                          'chain.proceed(new Object', 'emit("LOGIN_TOKEN_OUTCOME", reply'):
            self.assertNotIn(forbidden,part)

    def test_exact_original_flow_subtype_witness_is_bounded_and_readonly(self):
        s=self.code
        start=s.index('private synchronized void observeOriginalPostLoginReceipts(')
        end=s.index('/** Only compare the Intent action',start)
        part=s[start:end]
        self.assertIn('Class.forName("eY5$a", false, loader)',part)
        self.assertIn('Class.forName("kotlin.coroutines.Continuation", false, loader)',part)
        self.assertIn('"emit", Object.class, continuation',part)
        self.assertIn('postLoginFlowEvents.incrementAndGet() <= 24',part)
        self.assertIn('"qY5$a$a".equals(type) ? "NO_USERINFO_RESULT"',part)
        self.assertIn('"qY5$a$b".equals(type) ? "EXTERNAL_HANDOFF"',part)
        self.assertIn('"qY5$a$c".equals(type) ? "USERINFO_READY"',part)
        self.assertIn('emit("LOGIN_FLOW_RESULT", "ENTRY", category)',part)
        self.assertIn('emit("POSTLOGIN_HOOK", "FLOW", "REGISTERED")',part)
        self.assertIn('return chain.proceed();',part)
        self.assertNotIn('.getMessage()',part)
        self.assertNotIn('.toString()',part)
        self.assertNotIn('chain.proceed(new Object',part)

    def test_private_exact_dex_gate_pins_reflection_signatures_and_resume_stages(self):
        contract=(Path(__file__).resolve().parent /
                  "a1_private_postlogin_contract.py").read_text(encoding="utf-8")
        for snippet in (
            '("LeY5$a;", "emit")',
            '("Lru/yandex/music/entry/EntryScreenActivity;", "onCreate")',
            '"Entry screen activity entry type must not be null. Fallback to login"',
            '("Lcom/yandex/music/shared/utils/assertions/Assertions;", "throwOrSkip")',
            '("LxT3$b;", "<init>")',
            '("LoY5$a;", "emit")',
            '("LpY5$a;", "emit")',
            '{"login result = "}',
            '{"autologin result = "}',
            '"Lkotlin/coroutines/Continuation;"',
            '("LqY5;", "if")',
            '"Lcom/yandex/passport/api/n0;"',
            '"LOe2;"',
            '("LnY5;", "invokeSuspend")',
            '("LnY5;", "I", "continue")',
            '("LnY5;", "Ljava/lang/Object;", "private")',
            '("LzW8$b;", "Ljava/lang/Throwable;", "default")',
            '("LqY5$a$a;", "LqY5$a;")',
            '("LqY5$a$b;", "LqY5$a;")',
            '("LqY5$a$c;", "LqY5$a;")',
            '("LEd5;", "this")',
            '("LiE6;", "public")',
            '("Lol0;", "if")',
            'expected_sites = (',
            '(0x4A, 0xCE, 0xD2, 1, 6, ("LEd5;", "this"))',
            '(0x00, 0x106, 0x10A, 2, 0, ("LiE6;", "public"))',
            '(0x48, 0x14C, 0x154, 3, 5, ("Lol0;", "if"))',
            'const_value != label',
            'iput_reg != register',
            'dex.method(method_id) != target',
            '"coroutine_resume_stage_contract_exact": True'):
            self.assertIn(snippet,contract)
        self.assertIn('observer_contract = _private_login_observer_contract(dexes)',contract)

    def test_no_result_spoofing_or_forced_navigation(self):
        s=self.code
        part=s[s.index('private synchronized void observeOriginalPostLoginReceipts('):
               s.index('/** Only compare the Intent action',s.index('private synchronized void observeOriginalPostLoginReceipts('))]
        self.assertIn('return chain.proceed();',part)
        self.assertNotIn('.setResult(',part)
        self.assertNotIn('.startActivity(',part)
        self.assertNotIn('getParcelableExtra',part)
        self.assertNotIn('getPassword(',part)
        self.assertNotIn('.edit()',part)
        self.assertNotIn('putBoolean(',part)

    def test_vendor_master_token_decrypt_exception_only(self):
        s=self.code
        self.assertIn('Class.forName("com.yandex.passport.internal.core.accounts.v"',s.replace('\n                ',''))
        self.assertIn('Class.forName("com.yandex.passport.internal.core.accounts.v$c"',s.replace('\n                ',''))
        self.assertIn('getDeclaredField("for")',s)
        self.assertIn('getDeclaredMethod("if", String.class)',s)
        self.assertIn('emit("MASTER_TOKEN_DECRYPT"',s)
        self.assertIn('failureField.get(result) == null',s)
        self.assertIn('return chain.proceed();',s)
        self.assertNotIn('failure.getMessage()',s[s.index('private synchronized void observeOriginalPassportDecryptOutcome('):
                                           s.index('private synchronized void preparePassportDiagnostics(')])

    def test_fresh_install_original_key_preinit_is_scoped_and_idempotent(self):
        s=self.code
        start=s.index('private synchronized void preinitializeOriginalMasterKeyIfFresh(')
        end=s.index('private synchronized void observeOriginalPassportDecryptOutcome(',start)
        part=s[start:end]
        self.assertIn('masterKeyPreinitAttempted = true;',part)
        self.assertIn('!PACKAGE.equals(Application.getProcessName())',part)
        self.assertIn('prefs.contains("master_token_key")',part)
        self.assertIn('ownAccounts.length != 0',part)
        self.assertIn('"ACCOUNT_EXISTS_NO_KEY_UNCHANGED"',part)
        self.assertIn('Class.forName(',part)
        self.assertIn('"com.yandex.passport.internal.core.accounts.v"',part)
        self.assertIn('"com.yandex.passport.internal.storage.a"',part)
        self.assertIn('originalKeyMethod.invoke(originalCipher);',part)
        self.assertIn('prefs.edit().commit()',part)
        self.assertNotIn('putString(',part)
        self.assertNotIn('putBoolean(',part)
        self.assertNotIn('setPassword(',part)
        self.assertNotIn('setResult(',part)
        self.assertNotIn('startActivity(',part)
        self.assertNotIn('getPassword(',part)
        self.assertNotIn('getString(',part)

    def test_onboarding_writer_witness_is_exact_read_only_and_persist_observed(self):
        s=self.code
        self.assertIn('Class.forName("android.app.ContextImpl", false, null)',s)
        self.assertIn('"getSharedPreferences", String.class, int.class)',s)
        self.assertIn('"Yandex_Music".equals(name)',s)
        self.assertIn('Class.forName("android.app.SharedPreferencesImpl", false, null)',s)
        self.assertIn('"android.app.SharedPreferencesImpl$EditorImpl", false, null)',s)
        self.assertIn('"putBoolean", String.class, boolean.class)',s)
        self.assertIn('"onboarding".equals(key)',s)
        self.assertIn('getDeclaredMethod("commit")',s)
        self.assertIn('getDeclaredMethod("apply")',s)
        self.assertIn('emit("ONBOARDING_WRITE"',s)
        self.assertIn('emit("ONBOARDING_WRITE_PERSIST"',s)
        part=s[s.index('private synchronized void installOnboardingWriterWitness('):
                s.index('private void observeOnboardingReadOnly(',s.index('private synchronized void installOnboardingWriterWitness('))]
        self.assertIn('yandexMusicPreferenceEditors.containsKey(editor)',part)
        self.assertIn('onboardingPreferenceEditors.containsKey(editor)',part)
        self.assertNotIn('.putBoolean(',part)
        self.assertNotIn('.putString(',part)
        self.assertNotIn('.setResult(',part)
        self.assertNotIn('.startActivity(',part)
        self.assertIn('NAV_V12_ONBOARDING_WRITER_WITNESS',s)

    def test_native_gate_requires_receiver_hook_registration(self):
        runner=(Path(__file__).resolve().parent /
                "owner_2025_lspatch2_namespaced_clone_arm13.py").read_text(encoding="utf-8")
        self.assertIn("def _activity_result_delivery_hook_status(",runner)
        self.assertIn('report["activity_result_delivery_hook_status"]=_activity_result_delivery_hook_status(raw_logcat)',runner)
        self.assertGreaterEqual(runner.count('report["activity_result_delivery_hook_status"] == "REGISTERED"'),2)
        self.assertIn("def _master_token_read_hook_status(",runner)
        self.assertIn("def _master_token_decrypt_hook_status(",runner)
        self.assertGreaterEqual(runner.count('report["master_token_read_hook_status"] == "REGISTERED"'),2)
        self.assertGreaterEqual(runner.count('report["master_token_decrypt_hook_status"] == "REGISTERED"'),2)

    def test_native_gate_requires_exact_login_receipt_hook_registration(self):
        runner=(Path(__file__).resolve().parent /
                "owner_2025_lspatch2_namespaced_clone_arm13.py").read_text(encoding="utf-8")
        self.assertIn('def _postlogin_hook_status(raw_logcat: str, kind: str)',runner)
        self.assertIn('kind not in ("FLOW", "PIPELINE")',runner)
        self.assertIn('event=POSTLOGIN_HOOK;origin={kind};error=',runner)
        self.assertEqual(runner.count('report["postlogin_flow_hook_status"]=_postlogin_hook_status(raw_logcat, "FLOW")'),2)
        self.assertEqual(runner.count('report["postlogin_pipeline_hook_status"]=_postlogin_hook_status(raw_logcat, "PIPELINE")'),2)
        self.assertEqual(runner.count('report["postlogin_entry_created_observed"]=_postlogin_entry_seen(raw_logcat)'),2)
        self.assertEqual(runner.count('report["postlogin_registration_accepted"]=_postlogin_registration_accepted('),2)
        self.assertGreaterEqual(runner.count('report["postlogin_registration_accepted"]'),2)

    def test_native_postlogin_hook_parser_recognizes_real_logcat_shape(self):
        source=(Path(__file__).resolve().parent /
                "owner_2025_lspatch2_namespaced_clone_arm13.py").read_text(encoding="utf-8")
        function=next(n for n in ast.parse(source).body
                      if isinstance(n,ast.FunctionDef)
                      and n.name=="_postlogin_hook_status")
        namespace={"re":re}
        exec(compile(ast.Module(body=[function],type_ignores=[]),
                     "<postlogin-hook-parser-test>","exec"),namespace)
        parser=namespace["_postlogin_hook_status"]
        flow="11-14 13:15:00.000 123 456 I CELIKOM_A1_EXIT_WITNESS event=POSTLOGIN_HOOK;origin=FLOW;error=REGISTERED;thread=MAIN"
        pipeline="11-14 13:15:01.000 123 456 I CELIKOM_A1_EXIT_WITNESS event=POSTLOGIN_HOOK;origin=PIPELINE;error=REGISTERED;thread=MAIN"
        self.assertEqual(parser(flow,"FLOW"),"REGISTERED")
        self.assertEqual(parser(pipeline,"PIPELINE"),"REGISTERED")
        self.assertEqual(parser(flow,"PIPELINE"),"NOT_OBSERVED")
        self.assertEqual(parser(pipeline,"FLOW"),"NOT_OBSERVED")
        self.assertEqual(parser(pipeline.replace("REGISTERED","NO_HOOK"),"PIPELINE"),"NO_HOOK")
        self.assertEqual(parser(flow,"UNSUPPORTED"),"UNAVAILABLE")

    def test_native_entry_hook_smoke_uses_vendor_fallback_without_login_input(self):
        runner=(Path(__file__).resolve().parent /
                "owner_2025_lspatch2_namespaced_clone_arm13.py").read_text(encoding="utf-8")
        start=runner.index("def observe_entry_hook_registration():")
        end=runner.index("def observe_clone(",start)
        part=runner[start:end]
        self.assertIn('component=DEST+"/ru.yandex.music.entry.EntryScreenActivity"',part)
        self.assertIn('guest("am","start","--user","0","-n",component',part)
        self.assertIn('_postlogin_entry_seen(raw_logcat)',part)
        self.assertIn('_postlogin_hook_status(raw_logcat,"FLOW")',part)
        self.assertIn('_postlogin_hook_status(raw_logcat,"PIPELINE")',part)
        self.assertIn('"registration_pass":bool(accepted and entry_created',part)
        self.assertIn('"no_login_interaction":True',part)
        self.assertNotIn('input tap',part)
        self.assertNotIn('input text',part)
        self.assertNotIn('monkey',part)
        self.assertEqual(runner.count('report["postlogin_entry_hook_smoke"]=observe_entry_hook_registration()'),2)
        self.assertEqual(runner.count('report["postlogin_entry_hook_smoke_pass"]'),4)
        self.assertIn('report["postlogin_entry_hook_smoke_pass"]',runner)

    def test_native_postlogin_gate_scoped_to_real_entry(self):
        source=(Path(__file__).resolve().parent /
                "owner_2025_lspatch2_namespaced_clone_arm13.py").read_text(encoding="utf-8")
        names=("_postlogin_entry_seen","_postlogin_registration_accepted")
        funcs=[n for n in ast.parse(source).body
               if isinstance(n,ast.FunctionDef) and n.name in names]
        self.assertEqual(len(funcs),2)
        namespace={"re":re}
        exec(compile(ast.Module(body=funcs,type_ignores=[]),
                     "<postlogin-scoped-gate>","exec"),namespace)
        check=namespace["_postlogin_registration_accepted"]
        entry="11-14 13:15:00.000 123 456 I CELIKOM_A1_EXIT_WITNESS event=ACTIVITY_PHASE;origin=ENTRY_ACTIVITY;error=CREATED;thread=MAIN"
        idle="11-14 13:15:00.000 123 456 I CELIKOM_A1_EXIT_WITNESS event=ACTIVITY_PHASE;origin=MAIN_ACTIVITY;error=CREATED;thread=MAIN"
        self.assertFalse(namespace["_postlogin_entry_seen"](idle))
        self.assertTrue(namespace["_postlogin_entry_seen"](entry))
        self.assertTrue(check(idle,"NOT_OBSERVED","NOT_OBSERVED"))
        self.assertTrue(check(idle,"REGISTERED","NOT_OBSERVED"))
        self.assertFalse(check(entry,"NOT_OBSERVED","NOT_OBSERVED"))
        self.assertFalse(check(entry,"REGISTERED","NOT_OBSERVED"))
        self.assertTrue(check(entry,"REGISTERED","REGISTERED"))
        self.assertFalse(check(entry,"NO_HOOK","REGISTERED"))
        self.assertFalse(check(idle,"NO_HOOK","NOT_OBSERVED"))
        self.assertFalse(check("", "UNAVAILABLE", "REGISTERED"))
        self.assertFalse(check(None, "REGISTERED", "REGISTERED"))

    def test_passport_set_result_observer_has_independent_quota(self):
        s=self.code
        self.assertIn('activityResultProducerObservations =',s)
        start=s.index('private synchronized boolean observePassportResultDelivery(')
        end=s.index('private synchronized boolean observeEntryActivityResultDelivery()',start)
        part=s[start:end]
        self.assertIn('activityResultProducerObservations.incrementAndGet()<=32',part)
        self.assertNotIn('activityFinishesLogged.incrementAndGet()',part)
        self.assertIn('"PASSPORT_ACTIVITY".equals(activityFamily((Activity)receiver))',part)
        self.assertIn('return chain.proceed();',part)

    def test_entry_result_delivery_is_receiver_side_readonly_and_independently_bounded(self):
        s=self.code
        self.assertIn('private boolean activityResultDeliveryHooked;',s)
        self.assertIn('activityResultDeliveryObservations =',s)
        self.assertIn('Activity.class.getDeclaredMethod(',s)
        self.assertIn('"dispatchActivityResult", String.class, int.class, int.class, Intent.class, String.class',s)
        self.assertIn('activityResultDeliveryObservations.incrementAndGet() <= 48',s)
        self.assertIn('emit("ACTIVITY_RESULT_DELIVERY_HOOK", "ANDROID", "REGISTERED")',s)
        self.assertIn('emit("ACTIVITY_RESULT_DELIVERY_HOOK", "ANDROID", "NO_HOOK")',s)
        self.assertIn('emit("ACTIVITY_RESULT_DELIVERY", "ENTRY_ACTIVITY", category)',s)
        part=s[s.index('private synchronized boolean observeEntryActivityResultDelivery('):
                s.index('private boolean observeOwnActivityFinish(',s.index('private synchronized boolean observeEntryActivityResultDelivery('))]
        self.assertIn('return chain.proceed();',part)
        self.assertNotIn('chain.getArg(0)',part)
        self.assertNotIn('chain.getArg(1)',part)
        self.assertNotIn('chain.getArg(3)',part)
        self.assertNotIn('chain.getArg(4)',part)
        self.assertNotIn('getExtras(',part)
        self.assertNotIn('setResult(',part)
        self.assertNotIn('startActivity(',part)

    def test_scoped_to_real_clone_entry_only(self):
        s=self.code
        self.assertIn('!"ENTRY_ACTIVITY".equals(activityFamily(activity))',s)
        self.assertIn('postLoginHookAttempts.incrementAndGet() > 3',s)
        self.assertIn('NAV_V12_ONBOARDING_WRITER_WITNESS',s)

if __name__=="__main__":
    unittest.main()
