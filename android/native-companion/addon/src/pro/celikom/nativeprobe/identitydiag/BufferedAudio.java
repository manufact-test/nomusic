package pro.celikom.nativeprobe.identitydiag;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;
/** Private sparse cache. Only fully validated chunks are ever visible to the decoder. */
class BufferedAudio implements Closeable {
 static final int BLOCK=131072;static final long MAX_BYTES=31457280;
 interface Open {HttpURLConnection open() throws Exception;}
 interface Events {void event(String name,long bytes);}
 final File file;final Open open;final BooleanSupplier valid;final LongSupplier clock;final Events events;
 final BitSet present=new BitSet(),loading=new BitSet();final Set<HttpURLConnection> connections=new HashSet<>();
 final ScheduledExecutorService watcher=Executors.newSingleThreadScheduledExecutor();final ExecutorService background=Executors.newSingleThreadExecutor();
 volatile int playbackBlock;volatile long size=-1,waitingSince=-1;volatile boolean closed;String etag;boolean detached;IOException fatal;
  boolean prefetchActive,prefetchAttempted,prefetchRecoveryPending;
  // A sequence of decoder seeks owns foreground priority until the last
  // verified handover, not merely until one HTTP Range read returns.
  boolean prefetchHeldForSeek,prefetchResumeAfterSeek;
 // Demand reads must not queue behind a background Range over a slow VPN.
 // Background transport is yieldable; foreground seeks retain strict validators.
 int foregroundReads;
 HttpURLConnection prefetchConnection;
 static final class ForegroundPriority extends IOException {
  ForegroundPriority(){super("prefetch_yield_to_decoder");}
 }
 BufferedAudio(File file,Open open,BooleanSupplier valid,LongSupplier clock,Events events){this.file=file;this.open=open;this.valid=valid;this.clock=clock;this.events=events;
  watcher.scheduleAtFixedRate(()->{if(!valid.getAsBoolean())close();},100,100,TimeUnit.MILLISECONDS);
 }
 void initialize()throws IOException{fetch(0);events.event("replacement_stream_ready",cachedBytes());}
 // Cache decoder metadata at the end and a second prefix block before publishing.
 // Android may inspect both ends during prepare; background reads must not race startup.
 void initializeForPlayback()throws IOException{fetch(0);int last=blocks()-1;if(last>0)fetch(last);if(last>1)fetch(1);events.event("replacement_stream_ready",cachedBytes());}
  void holdPrefetchForSeek(){
   synchronized(this){
    if(closed||prefetchHeldForSeek)return;
    prefetchHeldForSeek=true;
    if(prefetchActive)prefetchResumeAfterSeek=true;
    notifyAll();
   }
   // Do not abort a healthy Range for a cached seek. Only an actual decoder
   // cache miss in readAt() preempts the in-flight connection; otherwise let
   // that one block finish, then prevent the next speculative request.
  }
  void releasePrefetchAfterSeek(){
   boolean rearm;
   synchronized(this){
    if(!prefetchHeldForSeek)return;
    prefetchHeldForSeek=false;
    rearm=prefetchResumeAfterSeek&&prefetchAttempted&&!closed&&!complete();
    prefetchResumeAfterSeek=false;
    if(rearm&&prefetchActive){prefetchRecoveryPending=true;rearm=false;}
    notifyAll();
   }
   if(rearm)prefetch();
  }
 void prefetch(){
  final boolean restart;
   synchronized(this){
    if(closed||complete())return;
    if(prefetchHeldForSeek){prefetchAttempted=true;prefetchResumeAfterSeek=true;return;}
    if(prefetchActive)return;
    restart=prefetchAttempted;prefetchAttempted=true;prefetchActive=true;
   }
  if(restart)events.event("replacement_stream_prefetch_resumed",cachedBytes());
  try{background.execute(()->{
   try{
    while(!closed){
     synchronized(BufferedAudio.this){
       if(prefetchHeldForSeek)throw new ForegroundPriority();
       while(!closed&&foregroundReads>0)BufferedAudio.this.wait(100);
      if(closed)break;
       if(prefetchHeldForSeek)throw new ForegroundPriority();
     }
     int b=nextPrefetchBlock();if(b<0)break;
     fetch(b,true);
    }
    if(complete())events.event("replacement_stream_cached",size);
   }
   catch(ForegroundPriority e){events.event("replacement_stream_prefetch_yield",cachedBytes());}
   catch(IOException e){events.event("replacement_stream_prefetch_wait",cachedBytes());}
   catch(InterruptedException e){Thread.currentThread().interrupt();}
   finally{
    boolean rearm;
     synchronized(BufferedAudio.this){
      prefetchActive=false;
      rearm=prefetchRecoveryPending&&!prefetchHeldForSeek;
      if(prefetchRecoveryPending&&prefetchHeldForSeek)prefetchResumeAfterSeek=true;
      prefetchRecoveryPending=false;
     }
    // The decoder may have proved the connection healthy while the worker
    // was still reporting its previous failure. Never lose that one wakeup.
    if(rearm)prefetch();
   }
  });}catch(RejectedExecutionException e){synchronized(this){prefetchActive=false;}if(!closed)throw e;}
 }
 synchronized int nextPrefetchBlock(){int count=blocks();if(count==0)return -1;int cursor=Math.max(0,Math.min(count-1,playbackBlock));for(int b=cursor;b<count;b++)if(!present.get(b))return b;for(int b=0;b<cursor;b++)if(!present.get(b))return b;return -1;}
 int blocks(){return size<0?0:(int)((size+BLOCK-1)/BLOCK);}
 synchronized boolean complete(){return size>0&&present.cardinality()==blocks();}
 synchronized long cachedBytes(){long total=0;for(int b=present.nextSetBit(0);b>=0;b=present.nextSetBit(b+1))total+=Math.min(BLOCK,size-(long)b*BLOCK);return total;}
 synchronized File retainComplete(){if(!complete()||closed)return null;detached=true;return file;}
 boolean stalled(){return waitingSince>=0&&clock.getAsLong()-waitingSince>=250;}
 int readAt(long position,byte[] buffer,int offset,int length)throws IOException{
  if(position<0||offset<0||length<0||offset>buffer.length-length)throw new IOException("invalid_audio_read");if(length==0)return 0;
  synchronized(this){check();if(size<0)throw new IOException("audio_not_initialized");if(position>=size)return -1;}
  int block=(int)(position/BLOCK),count=(int)Math.min(Math.min(length,BLOCK-position%BLOCK),size-position);
  boolean cacheMiss;HttpURLConnection obsoletePrefetch=null;
  synchronized(this){
   playbackBlock=block;cacheMiss=!present.get(block);
   if(cacheMiss){
    if(foregroundReads++==0)waitingSince=clock.getAsLong();
    obsoletePrefetch=prefetchConnection;
   }
  }
  // Never call disconnect() on MediaPlayer's decoder thread: it may block.
  // The validity watcher is a separate executor and can abort the old Range.
  if(obsoletePrefetch!=null)try{final HttpURLConnection old=obsoletePrefetch;watcher.execute(old::disconnect);}
   catch(RejectedExecutionException ignored){}
  try{fetch(block);synchronized(this){check();try(RandomAccessFile in=new RandomAccessFile(file,"r")){in.seek(position);in.readFully(buffer,offset,count);}}
   /* A background HTTP Range failure used to stop prefetch for this whole
      song. A successful ON-DEMAND missing-block fetch is concrete proof that
      transport works again. Restart at most one background worker, using the
      latest demanded block as priority. Cached read-ahead never restarts an
      endlessly failing worker; no timers or unbounded retry queues. */
   // Do not start an extra download during the initial decoder prepare:
   // only re-arm a prefetch that the playback lifecycle already requested.
   boolean rearm=false;
   if(cacheMiss)synchronized(this){
     if(prefetchAttempted&&prefetchHeldForSeek)prefetchResumeAfterSeek=true;
     else if(prefetchAttempted){
     if(prefetchActive)prefetchRecoveryPending=true;
     else rearm=true;
    }
   }
   if(rearm)prefetch();
   return count;}
  finally{if(cacheMiss)synchronized(this){
   if(--foregroundReads==0)waitingSince=-1;
   notifyAll();
  }}
 }
 synchronized void check()throws IOException{if(closed||!valid.getAsBoolean())throw new IOException("audio_cancelled");if(fatal!=null)throw fatal;}
 void fetch(int block)throws IOException{fetch(block,false);}
 void fetch(int block,boolean backgroundRead)throws IOException{
  synchronized(this){
   check();if(backgroundRead&&(foregroundReads>0||prefetchHeldForSeek))throw new ForegroundPriority();
   while(loading.get(block)&&!present.get(block)){
    try{wait(100);}catch(InterruptedException e){Thread.currentThread().interrupt();throw new IOException("audio_interrupted");}
    check();if(backgroundRead&&(foregroundReads>0||prefetchHeldForSeek))throw new ForegroundPriority();
   }
   if(present.get(block))return;loading.set(block);
  }
  try{
   IOException last=null;
   for(int attempt=0;attempt<3;attempt++){
    synchronized(this){check();if(backgroundRead&&(foregroundReads>0||prefetchHeldForSeek))throw new ForegroundPriority();}
    HttpURLConnection c=null;
    try{
     c=open.open();synchronized(this){check();connections.add(c);if(backgroundRead)prefetchConnection=c;}
     c.setConnectTimeout(6000);c.setReadTimeout(5000);c.setInstanceFollowRedirects(false);c.setRequestProperty("Accept-Encoding","identity");
     long first=(long)block*BLOCK,lastByte=size>0?Math.min(size-1,first+BLOCK-1):first+BLOCK-1;
     c.setRequestProperty("Range","bytes="+first+"-"+lastByte);String validator; synchronized(this){validator=etag;}if(validator!=null)c.setRequestProperty("If-Range",validator);
     int code=c.getResponseCode();
     if(code!=206){if(code==408||code==429||code>=500)throw new IOException("audio_network_retry");throw new AudioTransfer.Rejected("audio_range_unavailable");}
     String range=c.getHeaderField("Content-Range"),tag=AudioTransfer.strong(c.getHeaderField("ETag"));
     java.util.regex.Matcher m=java.util.regex.Pattern.compile("bytes ([0-9]+)-([0-9]+)/([0-9]+)").matcher(range==null?"":range);
     if(!m.matches()||tag==null)throw new AudioTransfer.Rejected("invalid_audio_range");
     long from=Long.parseLong(m.group(1)),to=Long.parseLong(m.group(2)),total=Long.parseLong(m.group(3));
     if(total<=0||total>MAX_BYTES||from!=first||to!=Math.min(total-1,first+BLOCK-1))throw new AudioTransfer.Rejected("invalid_audio_range");
     int bytes=(int)(to-from+1);long contentLength=c.getContentLengthLong();if(contentLength>=0&&contentLength!=bytes)throw new AudioTransfer.Rejected("invalid_audio_size");
     synchronized(this){check();if(size<0){size=total;etag=tag;}else if(size!=total||!etag.equals(tag))throw new AudioTransfer.Rejected("audio_version_changed");}
     byte[] data=new byte[bytes];try(InputStream input=c.getInputStream()){int at=0,n;while(at<bytes){synchronized(this){check();}n=input.read(data,at,bytes-at);if(n<0)throw new EOFException("incomplete_audio");if(n==0)continue;at+=n;}}
     synchronized(this){check();try(RandomAccessFile output=new RandomAccessFile(file,"rw")){output.seek(first);output.write(data);}present.set(block);notifyAll();}return;
    }catch(AudioTransfer.Rejected e){synchronized(this){fatal=e;notifyAll();}throw e;}
    catch(Exception e){
     synchronized(this){if(backgroundRead&&(foregroundReads>0||prefetchHeldForSeek))throw new ForegroundPriority();}
     last=e instanceof IOException?(IOException)e:new IOException("audio_transport",e);
     events.event("replacement_stream_retry",cachedBytes());
    }
    finally{if(c!=null){synchronized(this){
     connections.remove(c);
     if(backgroundRead&&prefetchConnection==c)prefetchConnection=null;
    }c.disconnect();}}
   }
   throw last==null?new IOException("audio_transport"):last;
  }finally{synchronized(this){loading.clear(block);notifyAll();}}
 }
 public void close(){List<HttpURLConnection> active;synchronized(this){if(closed)return;closed=true;active=new ArrayList<>(connections);connections.clear();notifyAll();if(!detached)file.delete();}for(HttpURLConnection c:active)c.disconnect();watcher.shutdownNow();background.shutdownNow();}
}
