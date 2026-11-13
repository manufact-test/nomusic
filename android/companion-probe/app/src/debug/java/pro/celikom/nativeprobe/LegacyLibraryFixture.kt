package pro.celikom.nativeprobe

/** Local debug-only public framework session; never included in the distributed APK. */
class LegacyLibraryFixture : android.service.media.MediaBrowserService() {
    private lateinit var session: android.media.session.MediaSession
    override fun onCreate() {
        super.onCreate()
        session = android.media.session.MediaSession(this, "legacy-identity-fixture")
        session.setMetadata(android.media.MediaMetadata.Builder()
            .putString(android.media.MediaMetadata.METADATA_KEY_MEDIA_ID, "141103805")
            .putString(android.media.MediaMetadata.METADATA_KEY_TITLE, "Fixture exact ID")
            .putString(android.media.MediaMetadata.METADATA_KEY_MEDIA_URI, "https://music.yandex.ru/album/37458189/track/141103805?token=private-fixture").build())
        session.setQueue(listOf(android.media.session.MediaSession.QueueItem(android.media.MediaDescription.Builder()
            .setMediaId("141103805").setMediaUri(android.net.Uri.parse("https://music.yandex.ru/album/37458189/track/141103805?token=private-fixture")).build(), 7)))
        session.setPlaybackState(android.media.session.PlaybackState.Builder().setState(android.media.session.PlaybackState.STATE_PLAYING, 2000, 1f)
            .setActiveQueueItemId(7).build())
        sessionToken = session.sessionToken
    }
    override fun onGetRoot(clientPackageName: String, clientUid: Int, rootHints: android.os.Bundle?): BrowserRoot? =
        if (clientPackageName == packageName) BrowserRoot("fixture-root", null) else null
    override fun onLoadChildren(parentId: String, result: Result<MutableList<android.media.browse.MediaBrowser.MediaItem>>) { result.sendResult(mutableListOf()) }
    override fun onDestroy() { session.release(); super.onDestroy() }
}
