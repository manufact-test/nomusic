package pro.celikom.nativeprobe

import androidx.media3.common.MediaItem
import androidx.media3.common.MediaMetadata
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.session.MediaLibraryService
import androidx.media3.session.MediaSession

/** Debug-only local service: first admission refused, then metadata changes. Never shipped. */
@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
class ProbeLibraryFixture : MediaLibraryService() {
    companion object {
        @Volatile var admissions = 0
        @Volatile var instance: ProbeLibraryFixture? = null
    }
    private lateinit var player: ExoPlayer
    private lateinit var session: MediaLibrarySession
    override fun onCreate() {
        super.onCreate();instance=this
        player=ExoPlayer.Builder(this).build()
        change("Probe one","1")
        session=MediaLibrarySession.Builder(this,player,object : MediaLibrarySession.Callback {
            override fun onGetItem(session: MediaLibrarySession, browser: MediaSession.ControllerInfo, mediaId: String): com.google.common.util.concurrent.ListenableFuture<androidx.media3.session.LibraryResult<MediaItem>> {
                val item=MediaItem.Builder().setMediaId(mediaId)
                    .setMediaMetadata(player.mediaMetadata.buildUpon().setIsBrowsable(false).setIsPlayable(true).build())
                    .setRequestMetadata(MediaItem.RequestMetadata.Builder()
                        .setMediaUri(android.net.Uri.parse("https://music.yandex.ru/album/38763902/track/142820338?token=private-test")).build()).build()
                return com.google.common.util.concurrent.Futures.immediateFuture(androidx.media3.session.LibraryResult.ofItem(item,null))
            }
        }).setSessionExtras(android.os.Bundle().apply { putString("com.example.track_id","141103805");putString("password","private-fixture") }).build()
    }
    fun change(title: String, id: String) {
        player.setMediaItem(MediaItem.Builder().setMediaId(id).setUri("asset:///unused-test-only")
            .setMediaMetadata(MediaMetadata.Builder().setTitle(title).build()).build())
    }
    override fun onGetSession(controllerInfo: MediaSession.ControllerInfo): MediaLibrarySession? {
        admissions++
        return if (admissions==1) null else session
    }
    override fun onDestroy() { instance=null;session.release();player.release();super.onDestroy() }
}
