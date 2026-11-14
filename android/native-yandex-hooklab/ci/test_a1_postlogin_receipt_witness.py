"""Read-only, no-secret original 2025 login receipt witness source gate."""
from pathlib import Path
import unittest

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
