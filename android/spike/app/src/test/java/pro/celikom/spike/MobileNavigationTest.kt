package pro.celikom.spike
import org.junit.Assert.*
import org.junit.Test
class MobileNavigationTest {
    @Test fun onlyExactHttpsServiceAndLoginHosts(){
        assertTrue(MobileSurface.navigationAllowed("https://passport.yandex.ru/auth"))
        assertTrue(MobileSurface.navigationAllowed("https://music.yandex.ru/track/144530503"))
        for(u in listOf("http://music.yandex.ru/","https://evil.music.yandex.ru/","https://passport.yandex.ru.evil.test/","https://user@passport.yandex.ru/","intent://music.yandex.ru/","https://music.yandex.ru:444/"))assertFalse(u,MobileSurface.navigationAllowed(u))
    }
}
