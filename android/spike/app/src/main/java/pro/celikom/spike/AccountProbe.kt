package pro.celikom.spike

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URI
import java.util.UUID

/** Fixed HTTPS origin, bounded JSON, no redirects or persistent bearer storage. */
class AccountProbe {
    private val installation = UUID.randomUUID().toString()
    private var access: String? = null
    private var refresh: String? = null
    private fun request(path: String, body: JSONObject? = null): JSONObject {
        val connection = URI("https://darkred-camel-588676.hostingersite.com" + path)
            .toURL().openConnection() as HttpURLConnection
        try {
            connection.connectTimeout = 10000; connection.readTimeout = 10000
            connection.instanceFollowRedirects = false
            connection.setRequestProperty("Accept", "application/json")
            connection.setRequestProperty("X-Celikom-Platform", "android-spike")
            connection.setRequestProperty("X-Celikom-App-Version", "0.1.0-spike")
            access?.let { connection.setRequestProperty("Authorization", "Bearer " + it) }
            if (body != null) {
                connection.requestMethod = "POST"; connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json")
                connection.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            }
            if (connection.responseCode !in 200..299) throw IllegalStateException("HTTP " + connection.responseCode)
            val bytes = connection.inputStream.use { input ->
                val output = java.io.ByteArrayOutputStream()
                val buffer = ByteArray(4096)
                while (true) {
                    val count = input.read(buffer)
                    if (count < 0) break
                    require(output.size() + count <= 65536)
                    output.write(buffer, 0, count)
                }
                output.toByteArray()
            }
            require(bytes.size <= 65536)
            return JSONObject(String(bytes, Charsets.UTF_8))
        } finally { connection.disconnect() }
    }
    fun login(email: String, password: String): String {
        if (access != null) logout()
        val result = request("/api/v1/auth/login", JSONObject()
            .put("email", email).put("password", password).put("installation_id", installation))
        val a = result.getString("access_token"); val r = result.getString("refresh_token")
        require(a.matches(Regex("[0-9a-f]{64}")) && r.matches(Regex("[0-9a-f]{64}")))
        access = a; refresh = r
        return state()
    }
    fun state(): String {
        val e = request("/api/v1/entitlement")
        return when {
            e.optString("reason") == "service_incident" -> "Подмена временно приостановлена"
            e.optBoolean("allowed") && e.isNull("valid_until") -> "Доступ: навсегда"
            e.optBoolean("allowed") -> "Доступ действует"
            else -> "Доступ сейчас не активен"
        }
    }
    fun logout() {
        try { refresh?.let { request("/api/v1/auth/logout", JSONObject()
            .put("refresh_token", it).put("installation_id", installation)) } }
        finally { access = null; refresh = null }
    }
}
