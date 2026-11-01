package pro.celikom.researchsource

import android.app.Activity
import android.content.Intent
import android.media.MediaPlayer
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.Process
import android.widget.TextView

/** Only an owned CI fixture. No service credentials, networking or third-party app. */
class SourceActivity : Activity() {
    private var player: MediaPlayer? = null
    private val handler = Handler(Looper.getMainLooper())
    private val report = object : Runnable {
        override fun run() {
            player?.let {
                sendBroadcast(Intent("pro.celikom.research.SNAPSHOT")
                    .setPackage("pro.celikom.researchcontroller")
                    .putExtra("uid", Process.myUid())
                    .putExtra("session", it.audioSessionId)
                    .putExtra("position", it.currentPosition)
                    .putExtra("playing", it.isPlaying))
            }
            handler.postDelayed(this, 100)
        }
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(TextView(this).apply { text = "Owned cross-app audio fixture" })
        player = MediaPlayer.create(this, R.raw.original).apply { isLooping = true; start() }
        handler.post(report)
    }
    override fun onDestroy() {
        handler.removeCallbacks(report)
        player?.release()
        player = null
        super.onDestroy()
    }
}
