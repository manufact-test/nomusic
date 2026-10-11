package pro.celikom.spike

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URI
import java.security.KeyStore
import java.util.UUID
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** Credentials stay in native storage; no bearer/refresh token goes to Yandex. */
class MobileAccount(context: Context):PlaybackAccount {
    private val prefs = context.getSharedPreferences("celikom-account", Context.MODE_PRIVATE)
    private val installation = prefs.getString("installation", null) ?: UUID.randomUUID().toString().also {
        prefs.edit().putString("installation", it).commit()
    }
    private var session: JSONObject? = restore()
    val signedIn: Boolean get() = session != null
    var verificationEmail:String?=null; private set
    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey("celikom-session", null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder("celikom-session", KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build())
        }.generateKey()
    }
    private fun restore(): JSONObject? = runCatching {
        val data = prefs.getString("session", null) ?: return null
        val bytes = Base64.decode(data, Base64.NO_WRAP)
        require(bytes.size in 29..8192)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, bytes.copyOfRange(0,12)))
        JSONObject(String(cipher.doFinal(bytes.copyOfRange(12, bytes.size)), Charsets.UTF_8))
    }.getOrNull()
    private fun save(value: JSONObject?) {
        if (value == null) { session=null; prefs.edit().remove("session").commit(); return }
        require(value.optString("access_token").matches(Regex("[0-9a-f]{64}")))
        require(value.optString("refresh_token").matches(Regex("[0-9a-f]{64}")))
        val cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.ENCRYPT_MODE, key())
        val data = cipher.iv + cipher.doFinal(value.toString().toByteArray(Charsets.UTF_8))
        check(prefs.edit().putString("session", Base64.encodeToString(data, Base64.NO_WRAP)).commit())
        session=value
    }
    @Synchronized override fun request(path: String, body: JSONObject?, authenticated: Boolean, retry: Boolean): JSONObject {
        require(path.startsWith("/api/v1/"))
        val c = URI(ORIGIN + path).toURL().openConnection() as HttpURLConnection
        try {
            c.connectTimeout=10000; c.readTimeout=10000; c.instanceFollowRedirects=false
            c.setRequestProperty("Accept", "application/json")
            c.setRequestProperty("X-Celikom-Platform", "android")
            c.setRequestProperty("X-Celikom-App-Version", "0.2.0")
            if (authenticated) c.setRequestProperty("Authorization", "Bearer " + (session?.getString("access_token") ?: error("Войдите в аккаунт CELIKOM")))
            if (body != null) {
                c.requestMethod="POST"; c.doOutput=true; c.setRequestProperty("Content-Type", "application/json")
                c.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            }
            val status=c.responseCode
            if (status==401 && authenticated && retry) {
                val token=session?.getString("refresh_token") ?: error("Войдите снова")
                c.disconnect()
                try { save(request("/api/v1/auth/refresh", JSONObject().put("refresh_token",token).put("installation_id",installation),false,false)) }
                catch (e: Exception) { if (e is AccessExpired) save(null); throw e }
                return request(path,body,true,false)
            }
            if (status==401 && (authenticated||path.endsWith("/refresh"))) throw AccessExpired()
            if (status !in 200..299) {
                val errorCode=runCatching { c.errorStream?.use { input ->
                    val out=java.io.ByteArrayOutputStream();val buffer=ByteArray(1024)
                    while(true){val n=input.read(buffer);if(n<0)break;require(out.size()+n<=8192);out.write(buffer,0,n)}
                    JSONObject(out.toString("UTF-8")).optString("error")
                } }.getOrNull()
                error(when(errorCode){
                    "invalid_credentials"->"Проверьте почту и пароль"
                    "weak_password"->"Пароль должен содержать от 12 до 128 символов"
                    "invalid_code"->"Неверный или истёкший код из письма"
                    "account_disabled"->"Аккаунт заблокирован"
                    "invalid_promo","promo_unavailable"->"Промокод недоступен или уже использован"
                    "promo_payment_pending"->"Скидка сохранена для будущей оплаты"
                    "promo_lifetime_active"->"У вас уже есть бессрочный доступ"
                    "email_unavailable"->"Отправка писем временно недоступна"
                    else->if(status==429) "Слишком много запросов. Попробуйте позже" else "Запрос не выполнен ($status)"
                })
            }
            require(c.contentType?.startsWith("application/json") == true)
            val bytes=c.inputStream.use { input ->
                val out=java.io.ByteArrayOutputStream();val buffer=ByteArray(4096)
                while(true){val n=input.read(buffer);if(n<0)break;require(out.size()+n<=65536);out.write(buffer,0,n)}
                out.toByteArray()
            }
            return JSONObject(String(bytes,Charsets.UTF_8))
        } finally { c.disconnect() }
    }
    @Synchronized fun login(email:String,password:String,register:Boolean=false) {
        if(signedIn) logout()
        val result=request("/api/v1/auth/"+(if(register) "register" else "login"),JSONObject()
            .put("email",email.trim()).put("password",password).put("installation_id",installation),false)
        if(result.optBoolean("verification_required")){verificationEmail=email.trim();return}
        save(result);verificationEmail=null
    }
    @Synchronized fun verify(code:String){
        val email=verificationEmail?:error("Сначала запросите код при входе")
        save(request("/api/v1/auth/verify-email",JSONObject().put("email",email).put("code",code.trim()).put("installation_id",installation),false))
        verificationEmail=null
    }
    @Synchronized fun requestReset(email:String){request("/api/v1/auth/request-reset",JSONObject().put("email",email.trim()),false)}
    @Synchronized fun resetPassword(email:String,code:String,password:String){
        request("/api/v1/auth/reset-password",JSONObject().put("email",email.trim()).put("code",code.trim()).put("new_password",password),false)
    }
    @Synchronized override fun entitlement(activate:Boolean):JSONObject {
        val e=if(activate)request("/api/v1/auth/activate",JSONObject()).getJSONObject("entitlement") else request("/api/v1/entitlement")
        require(e.get("allowed") is Boolean && e.get("reason") is String && e.get("source") is String && e.has("valid_until"))
        if(!e.isNull("valid_until")){val until=e.getString("valid_until");require(until.endsWith("Z"));java.time.Instant.parse(until)}
        return e
    }
    @Synchronized fun redeem(code:String):JSONObject {
        require(code.trim().matches(Regex("[A-Za-z0-9_-]{8,64}"))) { "Проверьте текст промокода" }
        return request("/api/v1/promos/redeem",JSONObject().put("code",code.trim()))
    }
    @Synchronized fun logout() {
        val old=session
        try { if(old!=null) request("/api/v1/auth/logout",JSONObject().put("refresh_token",old.getString("refresh_token")).put("installation_id",installation)) }
        finally { save(null) }
    }
    class AccessExpired: IllegalStateException("Сессия истекла. Войдите снова")
    companion object { const val ORIGIN="https://darkred-camel-588676.hostingersite.com" }
}
