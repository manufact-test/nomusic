package pro.celikom.spike

import org.junit.Assert.*
import org.junit.Test

class SurfaceOriginTest {
    @Test fun exactHttpsServiceOnly() {
        assertTrue(SurfaceOrigin.allowed("https://music.yandex.ru/track/144530503"))
        for (url in listOf("http://music.yandex.ru", "https://music.yandex.ru.attacker.invalid",
            "https://attacker.invalid@music.yandex.ru", "https://music.yandex.ru:444",
            "file:///music.yandex.ru", "javascript:alert(1)", "https://passport.yandex.ru")) {
            assertFalse(url, SurfaceOrigin.allowed(url))
        }
    }
}
