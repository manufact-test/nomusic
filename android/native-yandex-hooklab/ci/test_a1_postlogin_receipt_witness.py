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

    def test_scoped_to_real_clone_entry_only(self):
        s=self.code
        self.assertIn('!"ENTRY_ACTIVITY".equals(activityFamily(activity))',s)
        self.assertIn('postLoginHookAttempts.incrementAndGet() > 3',s)
        self.assertIn('NAV_V10_POSTLOGIN_RECEIPT_WITNESS',s)

if __name__=="__main__":
    unittest.main()
