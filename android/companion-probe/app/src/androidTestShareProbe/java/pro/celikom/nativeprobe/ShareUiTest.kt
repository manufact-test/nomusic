package pro.celikom.nativeprobe

import android.content.ComponentName
import android.content.Intent
import android.content.pm.PackageManager
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ShareUiTest {
    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private fun menu(pkg:String="ru.yandex.music", inside:Boolean=true) = ShareUiPolicy.Control(pkg,"ru.yandex.music:id/overflow_menu",null,null,true,true,inside)
    @Test fun neverClicksPlaylistOtherAppsOrAmbiguousControls() {
        assertEquals(0,ShareUiPolicy.choose(listOf(menu()),0))
        assertNull(ShareUiPolicy.choose(listOf(menu(inside=false)),0))
        assertNull(ShareUiPolicy.choose(listOf(menu(pkg="other.app")),0))
        assertNull(ShareUiPolicy.choose(listOf(menu(),menu()),0))
        assertNull(ShareUiPolicy.choose(listOf(menu().copy(visible=false)),0))
        assertNull(ShareUiPolicy.choose(listOf(menu().copy(enabled=false)),0))
        val share=menu().copy(id=null,text="Поделиться")
        assertEquals(0,ShareUiPolicy.choose(listOf(share),1))
        assertNull(ShareUiPolicy.choose(listOf(share,share),1))
        assertNull(ShareUiPolicy.choose(listOf(share.copy(packageName="com.android.intentresolver")),1))
        assertNull(ShareUiPolicy.choose(listOf(share),3))
    }
    @Test fun sourceLinkReceiptRejectsNonSourceUrlsAndDoesNotVerifyCurrentItem() {
        ProbeStore.clear(context)
        assertTrue(ProbeStore.acceptSharedLink(context,"https://music.yandex.ru/album/4915498/track/38436680?ref_id=private"))
        assertEquals("38436680",ProbeStore.report(context).getJSONObject("shared_track").getString("track_id"))
        assertFalse(ProbeStore.report(context).getJSONObject("shared_track").getBoolean("current_track_verified"))
        assertFalse(ProbeStore.report(context).toString().contains("ref_id=private"))
        assertTrue(ProbeStore.acceptSharedLink(context,"https://music.yandex.ru/track/141103805"))
        assertFalse(ProbeStore.acceptSharedLink(context,"https://music.yandex.ru.evil.test/track/141103805"))
        assertFalse(ProbeStore.acceptSharedLink(context,"https://music.yandex.ru/album/141103805"))
        ProbeStore.clear(context)
    }
    @Test fun separateInstallHasNoEnabledEqualizerOrNotificationListener() {
        assertTrue(context.packageName.endsWith(".shareprobe"))
        val info=context.packageManager.getPackageInfo(context.packageName,PackageManager.GET_ACTIVITIES or PackageManager.GET_SERVICES or PackageManager.GET_RECEIVERS or PackageManager.MATCH_DISABLED_COMPONENTS)
        val activities=requireNotNull(info.activities)
        val services=requireNotNull(info.services)
        assertFalse(activities.any { it.name.endsWith(".MainActivity") })
        assertFalse(activities.any { it.name.endsWith(".EffectPanelActivity") })
        assertFalse(services.any { it.name.endsWith(".AttenuationService") })
        assertFalse(services.any { it.name.endsWith(".MusicListener") })
        val ui=services.first { it.name.endsWith(".ShareUiService") }
        assertEquals("android.permission.BIND_ACCESSIBILITY_SERVICE",ui.permission)
    }
    @Test fun nativeShareUiOpensWithoutLaunchingOtherApps() {
        val instrumentation=InstrumentationRegistry.getInstrumentation()
        val activity=instrumentation.startActivitySync(Intent(context,ShareProbeActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        instrumentation.waitForIdleSync()
        assertNotNull(activity)
        instrumentation.runOnMainSync { activity.finish() }
    }
}
