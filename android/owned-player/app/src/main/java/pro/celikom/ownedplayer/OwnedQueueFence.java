package pro.celikom.ownedplayer;

/** Rejects late asynchronous grants/metadata after Next, Stop or logout. */
public final class OwnedQueueFence {
    private long revision;
    private String currentId;
    public synchronized long begin(String id) {
        if(!OwnedPlaybackContract.validTrackId(id))
            throw new IllegalArgumentException("invalid_track_id");
        if(revision==Long.MAX_VALUE)throw new IllegalStateException("revision_overflow");
        revision++;
        currentId=id;
        return revision;
    }
    public synchronized boolean current(long at,String id) {
        return at==revision && id!=null && id.equals(currentId);
    }
    public synchronized void clear() {
        if(revision==Long.MAX_VALUE)throw new IllegalStateException("revision_overflow");
        revision++;
        currentId=null;
    }
}
