package pro.celikom.a1exitwitness;

import pro.celikom.yandex.nativehooklab.NativeGrantContract;
import pro.celikom.yandex.nativehooklab.NativeSourceGate;

import java.io.IOException;
import java.io.InputStream;
import java.lang.ref.WeakReference;
import java.net.URL;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.net.ssl.HttpsURLConnection;

/**
 * Actual alternate encoded-byte transport for ONE original Exo DataSource
 * instance. There is no CELIKOM MediaPlayer, AudioTrack or playback clock.
 *
 * IMPORTANT: no production caller currently issues an approved ALTERNATE
 * native decision. The original publisher source remains the default until
 * exact same-source semantic IDs + a signed user-entitled grant exist.
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
    private WeakReference<Object> originalSource;
    private String signedUrl,expectedMime;
    private long revision=-1;
    private Cursor openedCursor;
    private boolean opening,everCommitted,aborted;
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
                || selectionGeneration<0 || nativeSource==null
                || originalSource!=null || opening || openedCursor!=null
                || !NativeGrantContract.isAcceptable(grant,trackId,albumId,
                    editionId,originalDurationMs,origin,unixNowMs))
            return false;
        revision=selectionGeneration;
        originalSource=new WeakReference<>(nativeSource);
        signedUrl=grant.audioUrl;
        expectedMime=grant.mimeType;
        aborted=false;
        everCommitted=false;
        return true;
    }
    synchronized void cancelForNext() {
        revision=-1;
        aborted=true;
        originalSource=null;
        signedUrl=null;
        expectedMime=null;
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
            if(aborted || opening || source==null || offset<0
                    || originalSource==null || originalSource.get()!=source
                    || signedUrl==null)return null;
            opening=true;
            token=revision;
            cursor=factory.create(signedUrl,expectedMime);
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
                if(revision==token) {
                    aborted=true;
                    signedUrl=null;
                    expectedMime=null;
                    originalSource=null;
                }
                // Once any alternate bytes may have reached Exo, never fall
                // back to original inside the same decoder track.
                if(everCommitted)
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
            if(source==null || openedCursor==null || originalSource==null
                    || originalSource.get()!=source)return null;
            cursor=openedCursor;
        }
        // No additional player or buffer/PCM transformation. Blocking read
        // happens on the original Exo loader thread, not the UI thread.
        return cursor.read(buffer,start,size);
    }
    /** True: alternate owned open, so do NOT close unopened vendor delegate. */
    boolean closeIfApproved(Object source) {
        Cursor cursor;
        synchronized(this) {
            if(originalSource==null || originalSource.get()!=source
                    || openedCursor==null)return false;
            cursor=openedCursor;
            openedCursor=null;
        }
        cursor.close();
        return true;
    }
    synchronized boolean isArmed(Object source) {
        return source!=null && !aborted && originalSource!=null
                && originalSource.get()==source;
    }
}
