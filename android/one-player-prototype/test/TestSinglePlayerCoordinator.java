import java.util.ArrayList;
import java.util.List;
import pro.celikom.oneplayer.*;
import pro.celikom.oneplayer.SourceGate.*;

public final class TestSinglePlayerCoordinator {
    private static int cases;
    private static final class FakeHost implements SinglePlayerCoordinator.HostPlayer {
        final List<String> events = new ArrayList<>();
        String preparedUri;
        @Override public void prepare(String uri, long generation) {
            preparedUri = uri;
            events.add("prepare:" + generation);
        }
        @Override public void play() { events.add("play"); }
        @Override public void pause() { events.add("pause"); }
        @Override public void seekTo(long positionMs) { events.add("seek:" + positionMs); }
        @Override public void stop() { events.add("stop"); }
    }
    private static void check(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
        cases++;
    }
    public static void main(String[] args) {
        FakeHost host = new FakeHost();
        final String original = "content://lab/original";
        final String alternate = "content://lab/alternate";
        final List<String> reasons = new ArrayList<>();
        SinglePlayerCoordinator ctl = new SinglePlayerCoordinator(host, track ->
            new Candidate(track.catalogId, track.editionId, alternate, 150000, true, true, true, true),
            (generation, id, selection, reason) -> reasons.add(reason));
        Track a = new Track("42884423", "album-raskol", original, 150000, Evidence.INTERNAL_CATALOG);
        long first = ctl.onHostTrack(a);
        check(host.preparedUri.equals(alternate), "authorized alternate should be selected before prepare");
        ctl.play(first);
        ctl.seek(first, 33000);
        ctl.pause(first);
        check(host.events.contains("play") && host.events.contains("seek:33000") &&
              host.events.contains("pause"), "native host controls must be forwarded");
        long second = ctl.onHostTrack(new Track("1944599","album-other",
            original,150000,Evidence.EXTERNAL_ALIAS));
        check(host.preparedUri.equals(original), "unverified identity must fall back before prepare");
        int oldCount = host.events.size();
        ctl.play(first);
        ctl.pause(first);
        ctl.seek(first,5000);
        check(host.events.size() == oldCount, "outdated item cannot control current playback");
        check(second > first, "item generation must strictly increase");
        ctl.onStop();
        int afterStop = host.events.size();
        ctl.play(second);
        check(host.events.size() == afterStop, "stopped player cannot be restarted by stale callback");
        check(reasons.contains("catalog_identity_unverified"), "reason must be auditable");
        System.out.println("PASS: " + cases + " single-player host coordination scenarios");
    }
}
