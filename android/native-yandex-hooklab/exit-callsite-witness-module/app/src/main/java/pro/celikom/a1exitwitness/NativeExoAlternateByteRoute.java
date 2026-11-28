package pro.celikom.a1exitwitness;

import pro.celikom.yandex.nativehooklab.NativeGrantContract;
import pro.celikom.yandex.nativehooklab.NativeSourceGate;

import java.io.IOException;
import java.io.InputStream;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.net.URL;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.net.ssl.HttpsURLConnection;

/**
 * Actual alternate encoded-byte transport for ONE original Exo DataSource
 * instance. There is no CELIKOM MediaPlayer, AudioTrack or playback clock.
 *
 * The owner-consented limited BETA path in NativeEarlySourceLifecycleBridge
 * can issue an ALTERNATE decision for its exact allowlisted source lineage.
 * This route proves byte-source ownership only; it does NOT prove that the
 * armed DataSource is the one consumed by the currently selected renderer.
 *
 * The existing native Exo open/read/close hooks may delegate here only when
 * this precise source has been armed BEFORE its very first open. Never mix
 * original and alternative byte streams within a committed DataSource.
 */
final class NativeExoAlternateByteRoute {
    interface Cursor {
        long open(long start) throws IOException;
        int read(byte[] out,int offset,int length) throws IOException;
        void close();
    }
    interface CursorFactory {
        Cursor create(String url,String expectedMime);
    }
    private static final Pattern CONTENT_RANGE=
        Pattern.compile("bytes ([0-9]+)-([0-9]+)/([0-9]+)");
    static final class HttpsCursor implements Cursor {
        private final String signedUrl,expectedMime;
        private HttpsURLConnection connection;
        private InputStream stream;
        HttpsCursor(String signedUrl,String expectedMime) {
            this.signedUrl=signedUrl;
            this.expectedMime=expectedMime;
        }
        public long open(long start) throws IOException {
            if(start<0)throw new IOException("invalid_range");
            try {
                URL url=new URL(signedUrl);
                HttpsURLConnection c=(HttpsURLConnection)url.openConnection();
                connection=c;
                c.setConnectTimeout(5000);
                c.setReadTimeout(9000);
                c.setInstanceFollowRedirects(false);
                c.setUseCaches(false);
                c.setRequestProperty("Accept",expectedMime);
                c.setRequestProperty("Range","bytes="+start+"-");
                int status=c.getResponseCode();
                if(status!=206)
                    throw new IOException("alternate_range_response_required");
                if(!expectedMime.equals(c.getContentType()))
                    throw new IOException("alternate_mime_mismatch");
                String range=c.getHeaderField("Content-Range");
                Matcher m=CONTENT_RANGE.matcher(range==null?"":range);
                if(!m.matches())throw new IOException("alternate_range_missing");
                long first=Long.parseLong(m.group(1));
                long last=Long.parseLong(m.group(2));
                long total=Long.parseLong(m.group(3));
                if(first!=start || total<=0 || last<first || last>=total
                        || c.getContentLengthLong()!=last-first+1)
                    throw new IOException("alternate_range_inconsistent");
                stream=c.getInputStream();
                return total-start;
            } catch(RuntimeException | IOException ex) {
                close();
                if(ex instanceof IOException)throw (IOException)ex;
                throw new IOException("alternate_response_invalid",ex);
            }
        }
        public int read(byte[] out,int offset,int length) throws IOException {
            if(stream==null)throw new IOException("alternate_not_open");
            return stream.read(out,offset,length);
        }
        public void close() {
            InputStream in=stream;
            stream=null;
            if(in!=null)try {in.close();}catch(IOException ignored) { }
            HttpsURLConnection c=connection;
            connection=null;
            if(c!=null)c.disconnect();
        }
    }

    private final CursorFactory factory;
    // A superseded selection must never authorize an old instance to open
    // again or fall back to vendor bytes. An already committed loader can
    // finish its own cursor until the native player actually closes it.
    private static final class RetiredSource {
        final WeakReference<Object> source;
        Cursor drainingCursor;
        long positiveReads;
        RetiredSource(Object source) {this.source=new WeakReference<>(source);}
    }
    private final ArrayList<RetiredSource> retiredSources=new ArrayList<>();
    private RetiredSource findRetired(Object source) {
        if(source==null)return null;
        RetiredSource found=null;
        for(int i=retiredSources.size()-1;i>=0;i--) {
            RetiredSource retired=retiredSources.get(i);
            Object saved=retired.source.get();
            if(saved==null) {
                if(retired.drainingCursor!=null)retired.drainingCursor.close();
                retiredSources.remove(i);
            } else if(saved==source)found=retired;
        }
        return found;
    }
    private RetiredSource retire(Object source) {
        if(source==null)return null;
        RetiredSource retired=findRetired(source);
        if(retired==null) {
            retired=new RetiredSource(source);
            retiredSources.add(retired);
        }
        return retired;
    }
    private boolean wasRetired(Object source) {
        return findRetired(source)!=null;
    }
    private WeakReference<Object> originalSource;
    private String signedUrl,expectedMime;
    private long revision=-1;
    private long highestAcceptedGeneration=-1;
    private Cursor openedCursor;
    private boolean opening,everCommitted,aborted;
    // Positive alternate reads are scoped to this exact DataSource identity.
    // They are retained after close so a buffered live renderer can be joined
    // to the same source; selection supersession preserves only the exact
    // retired source's own read witness, never a new grant or an open right.
    private long positiveReadCount;
    NativeExoAlternateByteRoute() {
        this((url,mime)->new HttpsCursor(url,mime));
    }
    NativeExoAlternateByteRoute(CursorFactory factory) {
        if(factory==null)throw new IllegalArgumentException("FACTORY_REQUIRED");
        this.factory=factory;
    }

    /**
     * Called only by the trusted exact original-player pre-prepare coordinator
     * after the existing admission model commits ALTERNATE. This class repeats
     * server grant, entitlement, origin and exact triple validation.
     */
    synchronized boolean armApproved(long selectionGeneration,Object nativeSource,
            String trackId,String albumId,String editionId,long originalDurationMs,
            NativeGrantContract.Grant grant,String origin,long unixNowMs,
            NativeSourceGate.Choice nativeDecision) {
        if(nativeDecision!=NativeSourceGate.Choice.ALTERNATE
                || selectionGeneration<=highestAcceptedGeneration || nativeSource==null
                || wasRetired(nativeSource)
                || originalSource!=null || opening || openedCursor!=null
                || !NativeGrantContract.isAcceptable(grant,trackId,albumId,
                    editionId,originalDurationMs,origin,unixNowMs))
            return false;
        revision=selectionGeneration;
        highestAcceptedGeneration=selectionGeneration;
        originalSource=new WeakReference<>(nativeSource);
        signedUrl=grant.audioUrl;
        expectedMime=grant.mimeType;
        aborted=false;
        everCommitted=false;
        positiveReadCount=0;
        return true;
    }
    // Selection callbacks can precede the actual renderer switch. Never
    // truncate an already opened exact stream merely because another
    // selection started. Pending/unopened grants are still invalidated.
    synchronized void supersedeSelection() {
        resetForNext(true);
    }
    synchronized void cancelForNext() {
        resetForNext(false);
        for(RetiredSource retired:retiredSources) {
            if(retired.drainingCursor!=null)retired.drainingCursor.close();
            retired.drainingCursor=null;
            retired.positiveReads=0;
        }
    }
    private void resetForNext(boolean drainCommitted) {
        Object previous=originalSource==null?null:originalSource.get();
        if(everCommitted || opening) {
            RetiredSource retired=retire(previous);
            if(retired!=null && drainCommitted && everCommitted && !opening) {
                retired.drainingCursor=openedCursor;
                retired.positiveReads=positiveReadCount;
                openedCursor=null;
            }
        }
        revision=-1;
        aborted=true;
        originalSource=null;
        signedUrl=null;
        expectedMime=null;
        positiveReadCount=0;
        Cursor open=openedCursor;
        openedCursor=null;
        if(open!=null)open.close();
        // An in-flight open tests revision and closes itself before publish.
    }
    /** Returns null: caller invokes original vendor open once, unchanged. */
    Long openIfApproved(Object source,long offset) throws IOException {
        final Cursor cursor;
        final long token;
        synchronized(this) {
            if(wasRetired(source))throw new IOException("stale_alternate_source");
            if(aborted || source==null || offset<0
                    || originalSource==null || originalSource.get()!=source
                    || signedUrl==null)return null;
            if(opening)throw new IOException("alternate_open_overlap");
            opening=true;
            token=revision;
            try {cursor=factory.create(signedUrl,expectedMime);}
            catch(RuntimeException error) {
                if(everCommitted)retire(source);
                opening=false;
                aborted=true;
                originalSource=null;
                signedUrl=null;
                expectedMime=null;
                if(everCommitted)throw new IOException("alternate_factory_failed",error);
                return null;
            }
            Cursor old=openedCursor;
            openedCursor=null;
            if(old!=null)old.close();
        }
        try {
            long remaining=cursor.open(offset);
            synchronized(this) {
                if(revision!=token || aborted || originalSource==null
                        || originalSource.get()!=source) {
                    cursor.close();
                    throw new IOException("stale_alternate_source");
                }
                openedCursor=cursor;
                everCommitted=true;
                opening=false;
                return remaining;
            }
        } catch(IOException | RuntimeException failure) {
            cursor.close();
            synchronized(this) {
                opening=false;
                boolean stale=(revision!=token);
                if(revision==token) {
                    if(everCommitted)retire(source);
                    aborted=true;
                    signedUrl=null;
                    expectedMime=null;
                    originalSource=null;
                }
                // A Next/close during an in-flight alternate open must
                // never silently fall through to the stale original source.
                // Nor may a previously emitted alternate stream mix with it.
                if(stale || everCommitted)
                    throw failure instanceof IOException
                        ?(IOException)failure:new IOException("alternate_open_failed",failure);
            }
            return null;
        }
    }
    /** Null: no alternate committed, so execute real original read. */
    Integer readIfApproved(Object source,byte[] buffer,int start,int size)
            throws IOException {
        Cursor cursor;
        synchronized(this) {
            RetiredSource retired=findRetired(source);
            if(retired!=null) {
                if(retired.drainingCursor==null)
                    throw new IOException("stale_alternate_source");
                cursor=retired.drainingCursor;
            } else {
                if(source==null || originalSource==null
                        || originalSource.get()!=source)return null;
                if(opening)throw new IOException("alternate_open_in_progress");
                if(openedCursor==null) {
                    if(everCommitted)throw new IOException("alternate_read_without_open");
                    return null;
                }
                cursor=openedCursor;
            }
        }
        // No additional player or buffer/PCM transformation. Blocking read
        // happens on the original Exo loader thread, not the UI thread.
        int count=cursor.read(buffer,start,size);
        if(count>0) synchronized(this) {
            if(!aborted && originalSource!=null
                    && originalSource.get()==source && openedCursor==cursor
                    && positiveReadCount<Long.MAX_VALUE)
                positiveReadCount++;
            else {
                RetiredSource retired=findRetired(source);
                if(retired!=null && retired.drainingCursor==cursor
                        && retired.positiveReads<Long.MAX_VALUE)
                    retired.positiveReads++;
            }
        }
        return count;
    }
    /** True: alternate owned open, so do NOT close unopened vendor delegate. */
    boolean closeIfApproved(Object source) {
        Cursor cursor;
        synchronized(this) {
            RetiredSource retired=findRetired(source);
            if(retired!=null) {
                cursor=retired.drainingCursor;
                retired.drainingCursor=null;
                if(cursor==null)return true; // vendor was never opened
            } else {
                if(originalSource==null || originalSource.get()!=source)
                    return false;
                if(opening) {
                    // A concurrent close invalidates the in-flight alternate
                    // before it can publish a stream for the old DataSource.
                    aborted=true;
                    revision=-1;
                    originalSource=null;
                    signedUrl=null;
                    expectedMime=null;
                    return true;
                }
                if(openedCursor==null)return everCommitted;
                cursor=openedCursor;
                openedCursor=null;
            }
        }
        cursor.close();
        return true;
    }
    synchronized boolean isArmed(Object source) {
        return source!=null && !aborted && originalSource!=null
                && originalSource.get()==source;
    }

    /**
     * Read-only identity witness for the live renderer.
     * 1 = same source has returned positive alternate bytes;
     * 2 = same source is armed but has not returned bytes;
     * -1 = another source owns the active route;
     * 0 = no live route/source is available.
     */
    synchronized int readStatusForSource(Object source) {
        RetiredSource retired=findRetired(source);
        if(retired!=null) {
            if(retired.positiveReads>0)return 1;
            if(retired.drainingCursor!=null)return 2;
        }
        if(source==null || aborted || originalSource==null)return 0;
        Object active=originalSource.get();
        if(active==null)return 0;
        if(active!=source)return -1;
        return positiveReadCount>0?1:2;
    }
}
