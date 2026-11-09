package pro.celikom.spike

import java.net.URI

object SurfaceOrigin {
    fun allowed(url: String): Boolean = runCatching {
        val u = URI(url)
        u.scheme == "https" && u.host == "music.yandex.ru" &&
            (u.port == -1 || u.port == 443) && u.rawUserInfo == null
    }.getOrDefault(false)
}
