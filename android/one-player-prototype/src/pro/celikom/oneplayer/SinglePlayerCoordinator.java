package pro.celikom.oneplayer;

/**
 * Host-facing prototype. Requires an authorized host supplying its true catalog and edition
 * identifiers BEFORE source prepare. Does not hook or read any external process.
 */
public final class SinglePlayerCoordinator {
    public interface HostPlayer {
        /** Must release the prior source; one active source, one player timeline. */
        void prepare(String uri, long generation);
        void play();
        void pause();
        void seekTo(long positionMs);
        void stop();
    }

    public interface CatalogueResolver {
        /** Snapshot only; no network lookup while the host's player is preparing. */
        SourceGate.Candidate cachedCandidate(SourceGate.Track track);
    }

    public interface Telemetry {
        void decision(long generation, String catalogId, SourceGate.Selection selection, String reason);
    }

    private final HostPlayer player;
    private final CatalogueResolver resolver;
    private final Telemetry telemetry;
    private long generation;
    private boolean prepared;
    private boolean hasTrack;

    public SinglePlayerCoordinator(HostPlayer player, CatalogueResolver resolver, Telemetry telemetry) {
        if (player == null || resolver == null || telemetry == null)
            throw new IllegalArgumentException("Host integrations required");
        this.player = player;
        this.resolver = resolver;
        this.telemetry = telemetry;
    }

    /** New track event from the host's own item queue, never external Media3 snapshots. */
    public synchronized long onHostTrack(SourceGate.Track track) {
        generation++;
        prepared = false;
        hasTrack = false;
        player.stop();
        if (track == null) return generation;
        final SourceGate.Candidate candidate = resolver.cachedCandidate(track);
        final SourceGate.Decision decision = SourceGate.select(track, candidate);
        // The host must verify content URI grants/readability and its player capabilities.
        // A failed prepare does not start another player in parallel.
        telemetry.decision(generation, track.catalogId, decision.selection, decision.reason);
        player.prepare(decision.uri, generation);
        prepared = true;
        hasTrack = true;
        return generation;
    }

    /** Native host Play/Pause/Seek remain attached to this same player. */
    public synchronized void play(long itemGeneration) {
        if (prepared && hasTrack && itemGeneration == generation) player.play();
    }

    public synchronized void pause(long itemGeneration) {
        if (prepared && hasTrack && itemGeneration == generation) player.pause();
    }

    public synchronized void seek(long itemGeneration, long positionMs) {
        if (prepared && hasTrack && itemGeneration == generation)
            player.seekTo(Math.max(0, positionMs));
    }

    public synchronized void onStop() {
        generation++;
        player.stop();
        hasTrack = false;
        prepared = false;
    }

    public synchronized long generation() { return generation; }
}
