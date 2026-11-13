package pro.celikom.spike

/** Only controls audio owned by this diagnostic app. Never grants library access. */
class PlaybackPolicy {
    var trackId = "fixture:1"; private set
    var replacement = false; private set
    var playing = false; private set
    var manualOriginal = false; private set
    fun start() { manualOriginal = false; playing = true; replacement = true }
    fun original() { manualOriginal = true; replacement = false }
    fun failure() { replacement = false }
    fun pause() { playing = false }
    fun resume() { playing = true } // Does not undo Original or recover into replacement.
    fun suspend() { playing = false; replacement = false }
    fun changeTrack(id: String) {
        require(id in setOf("fixture:1", "fixture:2"))
        trackId = id
        replacement = false // New exact state requires an explicit Start in this spike.
    }
}
