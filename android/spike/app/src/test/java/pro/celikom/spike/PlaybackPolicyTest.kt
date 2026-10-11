package pro.celikom.spike

import org.junit.Assert.*
import org.junit.Test

class PlaybackPolicyTest {
    @Test fun manualOriginalSurvivesResumeAndFailure() {
        val p = PlaybackPolicy(); p.start(); p.original(); p.pause(); p.resume(); p.failure()
        assertTrue(p.manualOriginal); assertFalse(p.replacement); assertTrue(p.playing)
    }
    @Test fun networkLossRestoresOriginalWithoutStoppingTimeline() {
        val p = PlaybackPolicy(); p.start(); p.failure()
        assertFalse(p.replacement); assertTrue(p.playing)
    }
    @Test fun backgroundAndFocusNeverAutomaticallyRestart() {
        val p = PlaybackPolicy(); p.start(); p.suspend()
        assertFalse(p.playing); assertFalse(p.replacement)
    }
    @Test fun processRestartStartsUnmutedAndStopped() {
        val p = PlaybackPolicy()
        assertFalse(p.replacement); assertFalse(p.playing)
    }
    @Test fun exactNextPreviousStateRejectsUnknownTrack() {
        val p = PlaybackPolicy(); p.start(); p.changeTrack("fixture:2")
        assertEquals("fixture:2", p.trackId); assertFalse(p.replacement)
        p.changeTrack("fixture:1"); assertEquals("fixture:1", p.trackId)
        assertThrows(IllegalArgumentException::class.java) { p.changeTrack("144530503") }
    }
}
