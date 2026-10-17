package pro.celikom.spike
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.json.JSONObject
import android.content.Context

/** Emulator-only synthetic credentials: no HTTP, trial activation or real grant. */
@RunWith(AndroidJUnit4::class)
class MobileAccountStorageTest {
    @Test fun sessionSurvivesRecreationEncryptedAndTamperedCiphertextFailsClosed(){
        val context=InstrumentationRegistry.getInstrumentation().targetContext
        val prefs=context.getSharedPreferences("celikom-account",Context.MODE_PRIVATE)
        val save=MobileAccount::class.java.getDeclaredMethod("save",JSONObject::class.java).apply{isAccessible=true}
        val account=MobileAccount(context)
        val access="a".repeat(64);val refresh="b".repeat(64)
        try{
            save.invoke(account,JSONObject().put("access_token",access).put("refresh_token",refresh)
                .put("user",JSONObject().put("email","owned-fixture@example.invalid")))
            val stored=prefs.getString("session","")!!
            assertFalse(stored.contains(access));assertFalse(stored.contains(refresh));assertFalse(stored.contains("owned-fixture"))
            val restored=MobileAccount(context);assertTrue(restored.signedIn);assertEquals("owned-fixture@example.invalid",restored.email)
            prefs.edit().putString("session",stored.dropLast(8)+"AAAAAAAA").commit()
            assertFalse(MobileAccount(context).signedIn)
            save.invoke(account,null)
            assertFalse(MobileAccount(context).signedIn)
        }finally{prefs.edit().remove("session").commit()}
    }
}
