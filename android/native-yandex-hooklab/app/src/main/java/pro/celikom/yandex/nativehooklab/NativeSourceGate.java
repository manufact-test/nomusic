package pro.celikom.yandex.nativehooklab;

/**
 * Pure-Java admission model for a future SINGLE-Yandex-player source swap.
 * Not installed as an active hook. No private Yandex reads or audio mutation.
 * Exact identity is the triple track + album + edition.
 */
public final class NativeSourceGate {
    public enum Choice { UNDECIDED, ORIGINAL, ALTERNATE }
    public enum Stage { BEFORE_PREPARE, PREPARED, PLAYING, PAUSED, FAILED, ENDED }
    public enum Reason { ACCEPTED, WRONG_TRACK, STALE_REVISION, TOO_LATE,
        NOT_READY, ALREADY_COMMITTED, NONE }

    public static final class Candidate {
        public final String track, album, edition;
        public final boolean rightsConfirmed, decoderCompatible, durationMatches,
                contiguousStartupReady, byteRangeSeekable, cryptoCompatible;
        public Candidate(String track, String album, String edition,
                boolean rightsConfirmed, boolean decoderCompatible, boolean durationMatches,
                boolean contiguousStartupReady, boolean byteRangeSeekable, boolean cryptoCompatible) {
            this.track=track; this.album=album; this.edition=edition;
            this.rightsConfirmed=rightsConfirmed;
            this.decoderCompatible=decoderCompatible;
            this.durationMatches=durationMatches;
            this.contiguousStartupReady=contiguousStartupReady;
            this.byteRangeSeekable=byteRangeSeekable;
            this.cryptoCompatible=cryptoCompatible;
        }
        boolean ready() {
            return rightsConfirmed && decoderCompatible && durationMatches
                && contiguousStartupReady && byteRangeSeekable && cryptoCompatible;
        }
    }

    public static final class Result {
        public final Choice choice;
        public final Reason reason;
        Result(Choice choice, Reason reason) { this.choice=choice; this.reason=reason; }
    }

    private long revision;
    private String activeTrack, activeAlbum, activeEdition;
    private Choice choice=Choice.UNDECIDED;
    private Stage stage=Stage.ENDED;
    private long startedAtMs;
    private final long resolveBudgetMs;
    private int committedSources;

    public NativeSourceGate(long resolveBudgetMs) {
        if(resolveBudgetMs<1 || resolveBudgetMs>10000)
            throw new IllegalArgumentException("RESOLVE_BUDGET_OUT_OF_RANGE");
        this.resolveBudgetMs=resolveBudgetMs;
    }

    /** Caller must provide all three exact identities from the same native item. */
    public synchronized long beginTrack(String track,String album,String edition,long nowMs) {
        if(track==null||track.isEmpty()||album==null||album.isEmpty()
                ||edition==null||edition.isEmpty())
            throw new IllegalArgumentException("EXACT_TRACK_ALBUM_EDITION_REQUIRED");
        revision++;
        activeTrack=track;
        activeAlbum=album;
        activeEdition=edition;
        startedAtMs=nowMs;
        choice=Choice.UNDECIDED;
        stage=Stage.BEFORE_PREPARE;
        committedSources=0;
        return revision;
    }

    /** Exact track+album+edition only; network responses after Next cannot apply. */
    public synchronized Result propose(long rev,Candidate candidate,long nowMs) {
        if(rev!=revision)return new Result(Choice.UNDECIDED,Reason.STALE_REVISION);
        if(stage!=Stage.BEFORE_PREPARE||choice!=Choice.UNDECIDED)
            return new Result(Choice.UNDECIDED,Reason.ALREADY_COMMITTED);
        if(nowMs<startedAtMs||nowMs-startedAtMs>resolveBudgetMs)
            return new Result(Choice.UNDECIDED,Reason.TOO_LATE);
        if(candidate==null||!activeTrack.equals(candidate.track)
                ||!activeAlbum.equals(candidate.album)||!activeEdition.equals(candidate.edition))
            return new Result(Choice.UNDECIDED,Reason.WRONG_TRACK);
        if(!candidate.ready())return new Result(Choice.UNDECIDED,Reason.NOT_READY);
        choice=Choice.ALTERNATE;
        return new Result(Choice.ALTERNATE,Reason.ACCEPTED);
    }

    /** Exactly one source is chosen. An undecided/expired track selects original. */
    public synchronized Choice prepare(long rev,long nowMs) {
        if(rev!=revision||stage!=Stage.BEFORE_PREPARE)
            throw new IllegalStateException("STALE_OR_DUPLICATE_PREPARE");
        if(choice==Choice.UNDECIDED
                ||nowMs<startedAtMs||nowMs-startedAtMs>resolveBudgetMs)
            choice=Choice.ORIGINAL;
        stage=Stage.PREPARED;
        if(++committedSources!=1)throw new IllegalStateException("DUAL_SOURCE_COMMIT");
        return choice;
    }

    /** No second player; native Yandex alone will process UI transport. */
    public synchronized void onPlay(long rev) {
        if(rev==revision && (stage==Stage.PREPARED||stage==Stage.PAUSED))
            stage=Stage.PLAYING;
    }
    public synchronized void onPause(long rev) {
        if(rev==revision && stage==Stage.PLAYING)stage=Stage.PAUSED;
    }
    public synchronized void onSeek(long rev) {
        if(rev!=revision)return; // seek never creates a new source commit
    }
    public synchronized boolean rejectBeforePrepare(long rev) {
        if(rev!=revision||stage!=Stage.BEFORE_PREPARE)return false;
        choice=Choice.ORIGINAL;
        return true;
    }
    public synchronized void onDecoderFailure(long rev) {
        if(rev==revision)stage=Stage.FAILED;
    }
    public synchronized void end(long rev) {
        if(rev==revision)stage=Stage.ENDED;
    }
    public synchronized Choice choice(){return choice;}
    public synchronized Stage stage(){return stage;}
    public synchronized long revision(){return revision;}
    public synchronized int commits(){return committedSources;}
}
