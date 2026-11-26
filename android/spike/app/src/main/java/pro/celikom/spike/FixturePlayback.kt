package pro.celikom.spike

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.media.MediaPlayer

/** Both audio sources are generated fixture WAVs; no remote service is opened. */
class FixturePlayback(context: Context) {
    val policy = PlaybackPolicy()
    private val audio = context.getSystemService(AudioManager::class.java)
    private val original = MediaPlayer.create(context, R.raw.original)
    private val alternate = MediaPlayer.create(context, R.raw.alternate)
    private var closed = false
    private val focus = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN)
        .setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).build())
        .setOnAudioFocusChangeListener { if (it != AudioManager.AUDIOFOCUS_GAIN) suspend() }
        .build()
    init {
        original.isLooping = true; alternate.isLooping = true
        alternate.setVolume(0f, 0f)
        alternate.setOnErrorListener { _, _, _ -> failOpen(); true }
    }
    val position: Int get() = if (closed) 0 else original.currentPosition
    val replacementPosition: Int get() = if (closed) 0 else alternate.currentPosition
    val duration: Int get() = if (closed) 8000 else original.duration
    fun start() {
        if (closed || audio.requestAudioFocus(focus) != AudioManager.AUDIOFOCUS_REQUEST_GRANTED) return
        try {
            alternate.seekTo(original.currentPosition.toLong(), MediaPlayer.SEEK_CLOSEST)
            // Keep original audible until alternate has successfully started.
            alternate.setVolume(1f, 1f); alternate.start()
            original.start(); original.setVolume(0f, 0f)
            policy.start()
        } catch (_: IllegalStateException) { failOpen() }
    }
    fun original() {
        if (closed) return
        original.setVolume(1f, 1f); alternate.setVolume(0f, 0f)
        if (alternate.isPlaying) alternate.pause()
        policy.original()
    }
    fun failOpen() {
        if (closed) return
        original.setVolume(1f, 1f)
        runCatching { alternate.setVolume(0f, 0f); if (alternate.isPlaying) alternate.pause() }
        policy.failure()
    }
    fun pause() {
        if (closed) return
        if (original.isPlaying) original.pause()
        runCatching { if (alternate.isPlaying) alternate.pause() }
        policy.pause()
    }
    fun resume() {
        if (closed || audio.requestAudioFocus(focus) != AudioManager.AUDIOFOCUS_REQUEST_GRANTED) return
        original.start()
        if (policy.replacement) alternate.start()
        policy.resume()
    }
    fun seek(ms: Int) {
        if (closed) return
        val target = ms.coerceIn(0, duration - 1)
        original.seekTo(target.toLong(), MediaPlayer.SEEK_CLOSEST)
        runCatching { alternate.seekTo(target.toLong(), MediaPlayer.SEEK_CLOSEST) }.onFailure { failOpen() }
    }
    fun track(id: String) { original(); policy.changeTrack(id); seek(0) }
    fun suspend() {
        if (closed) return
        failOpen()
        if (original.isPlaying) original.pause()
        policy.suspend(); audio.abandonAudioFocusRequest(focus)
    }
    fun close() {
        if (closed) return
        suspend(); original.release(); alternate.release(); closed = true
    }
}
