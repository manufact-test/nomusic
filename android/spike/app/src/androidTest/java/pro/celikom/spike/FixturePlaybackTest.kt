package pro.celikom.spike

import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.math.abs

@RunWith(AndroidJUnit4::class)
class FixturePlaybackTest {
    @Test fun nativePlayersSeekPauseRestoreAndSuspend() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            lateinit var player: FixturePlayback
            scenario.onActivity { player = FixturePlayback(it); player.start() }
            Thread.sleep(400)
            scenario.onActivity {
                assertTrue(player.policy.replacement)
                assertTrue(player.position > 0)
                assertTrue(abs(player.position - player.replacementPosition) < 250)
                player.seek(3000)
            }
            Thread.sleep(300)
            scenario.onActivity {
                assertTrue(player.position >= 3000)
                assertTrue(abs(player.position - player.replacementPosition) < 250)
                player.pause(); assertFalse(player.policy.playing)
                player.resume(); player.original(); player.failOpen()
                assertFalse(player.policy.replacement); assertTrue(player.policy.manualOriginal)
                player.track("fixture:2"); assertEquals("fixture:2", player.policy.trackId)
                player.suspend(); assertFalse(player.policy.playing); assertFalse(player.policy.replacement)
                player.close()
            }
        }
    }
}
