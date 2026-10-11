package pro.celikom.spike

import android.view.ViewGroup
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import org.json.JSONObject
import android.os.SystemClock
import android.view.MotionEvent
import android.content.ContentValues
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import android.graphics.Bitmap

@RunWith(AndroidJUnit4::class)
class YandexSurfaceProbeTest {
    @Test fun reportRealServiceCapabilitiesWithoutClaimingPlayback() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            lateinit var probe: YandexSurfaceProbe
            scenario.onActivity {
                probe = YandexSurfaceProbe(it)
                it.addContentView(probe.view, ViewGroup.LayoutParams(-1, -1))
                probe.load("https://music.yandex.ru/track/144530503")
            }
            try {
                Thread.sleep(25000) // Network/page deadline, not owner action.
                val controlDone=CountDownLatch(1)
                var point: FloatArray? = null
                scenario.onActivity { probe.playControl { point=it; controlDone.countDown() } }
                assertTrue(controlDone.await(5,TimeUnit.SECONDS))
                point?.let {
                    val automation=InstrumentationRegistry.getInstrumentation().uiAutomation
                    val now=SystemClock.uptimeMillis()
                    val down=MotionEvent.obtain(now,now,MotionEvent.ACTION_DOWN,it[0],it[1],0)
                    val up=MotionEvent.obtain(now,now+100,MotionEvent.ACTION_UP,it[0],it[1],0)
                    try { automation.injectInputEvent(down,true); automation.injectInputEvent(up,true) }
                    finally { down.recycle(); up.recycle() }
                    Thread.sleep(10000)
                }
                val done = CountDownLatch(1)
                var report = JSONObject()
                scenario.onActivity { probe.report { report = it; done.countDown() } }
                assertTrue("Bounded service report returned", done.await(10, TimeUnit.SECONDS))
                assertFalse("Passive probe never claims playback", report.getBoolean("playback_confirmed"))
                val context = InstrumentationRegistry.getInstrumentation().targetContext
                report.put("explicit_play_control_tapped",point!=null)
                check(Build.VERSION.SDK_INT >= 29) // CI probe targets API 35.
                fun output(name: String, mime: String, write: (java.io.OutputStream) -> Unit) {
                    val values=ContentValues().apply {
                        put(MediaStore.MediaColumns.DISPLAY_NAME,name)
                        put(MediaStore.MediaColumns.MIME_TYPE,mime)
                        put(MediaStore.MediaColumns.RELATIVE_PATH,Environment.DIRECTORY_DOWNLOADS)
                    }
                    val uri=checkNotNull(context.contentResolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,values))
                    checkNotNull(context.contentResolver.openOutputStream(uri)).use(write)
                }
                output("celikom-surface-report.json","application/json") { it.write(report.toString().toByteArray()) }
                val screenshot=InstrumentationRegistry.getInstrumentation().uiAutomation.takeScreenshot()
                checkNotNull(screenshot)
                output("celikom-surface.png","image/png") { screenshot.compress(Bitmap.CompressFormat.PNG,100,it) }
                screenshot.recycle()
            } finally { scenario.onActivity { probe.close() } }
        }
    }
}
