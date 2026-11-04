package pro.celikom.nativeprobe.identitydiag;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;
/** Private sparse cache. Only fully validated chunks are ever visible to the decoder. */
class BufferedAudio implements Closeable {
 static final int BLOCK=131072;static final long MAX_BYTES=31457280;
 // Test.29 owner rejection: a wide speculative Range reserved four blocks
 // while a finger scrub needed one. Revert to independently preemptible 128-KiB
 // foreground/background reads; no batch can hold a future seek block hostage.
 static final int PREFETCH_RUN_BLOCKS=1;
 interface Open {HttpURLConnection open() throws Exception;}
 interface Events {void event(String name,long bytes);}
 final File file;final Open open;final BooleanSupplier valid;final LongSupplier clock;final Events events;
 final BitSet present=new BitSet(),loading=new BitSet();final Set<HttpURLConnection> connections=new HashSet<>();
 final ScheduledExecutorService watcher=Executors.newSingleThreadScheduledExecutor();final ExecutorService background=Executors.newSingleThreadExecutor();
 volatile int playbackBlock;volatile long size=-1,waitingSince=-1;volatile boolean closed;String etag;boolean detached;IOException fatal;
 volatile boolean backgroundBatchUnsupported;
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
 static final class BatchUnsupported extends IOException {
  BatchUnsupported(){super("prefetch_batch_unsupported");}
 }
 BufferedAudio(File file,Open open,BooleanSupplier valid,LongSupplier clock,Events events){this.file=file;this.open=open;this.valid=valid;this.clock=clock;this.events=events;
  watcher.scheduleAtFixedRate(()->{if(!valid.getAsBoolean())close();},100,100,TimeUnit.MILLISECONDS);
 }
 void initialize()throws IOException{fetch(0);events.event("replacement_stream_ready",cachedBytes());}
 // Cache decoder metadata at the end and a second prefix block before publishing.
 // Android may inspect both ends during prepare; background reads must not race startup.
 void initializeForPlayback()throws IOException{fetch(0);int last=blocks()-1;if(last>0)fetch(last);if(last>1)fetch(1);events.event("replacement_stream_ready",cachedBytes());}
 // The single decoder can be joining a song already several seconds in.
 // The first validated prefix is sufficient to publish an on-demand sparse
 // source. Tail, next prefix and source-position hint are *opportunistic*:
 // waiting for all three on a congested connection made Test.26 fail its
 // entire 1.8s startup probe and then download the whole song for 10-22s.
 // No unvalidated bytes are exposed; missing blocks are fetched on demand.
 void initializeForCurrentPosition(long sourcePositionMs,long durationMs)throws IOException{
  fetch(0); // Establish authoritative length and strong ETag before parallel reads.
  int last=blocks()-1;
  LinkedHashSet<Integer> needed=new LinkedHashSet<>();
  if(last>0)needed.add(last);
  if(last>1)needed.add(1);
  int hint=hintedBlock(sourcePositionMs,durationMs);
  if(hint>0&&hint<last)needed.add(hint);
  if(needed.isEmpty()){events.event("replacement_stream_ready",cachedBytes());return;}
  ExecutorService warm=Executors.newFixedThreadPool(Math.min(3,needed.size()),r->{Thread t=new Thread(r,"celikom-cold-range");t.setDaemon(true);return t;});
  ArrayList<Future<?>> reads=new ArrayList<>();
  try{
   for(int block:needed)reads.add(warm.submit(()->{fetch(block);return null;}));
   long deadline=System.nanoTime()+TimeUnit.MILLISECONDS.toNanos(900);
   for(Future<?> read:reads){
    long remaining=deadline-System.nanoTime();
    if(remaining<=0){events.event("replacement_stream_cold_warm_pending",cachedBytes());break;}
    try{read.get(remaining,TimeUnit.NANOSECONDS);}
    catch(TimeoutException e){events.event("replacement_stream_cold_warm_pending",cachedBytes());break;}
    catch(InterruptedException e){Thread.currentThread().interrupt();throw new IOException("audio_interrupted",e);}
    catch(ExecutionException e){Throwable cause=e.getCause();if(cause instanceof AudioTransfer.Rejected)throw (IOException)cause;
     events.event("replacement_stream_cold_warm_deferred",cachedBytes());}
   }
   check();
   events.event("replacement_stream_ready",cachedBytes());
  }finally{
   // Already-started validated Range fetches may complete into this source;
   // they must not be canceled or lose their buffered bytes at publication.
   warm.shutdown();
  }
 }
 int hintedBlock(long positionMs,long durationMs){
  if(durationMs<=0||positionMs<=0||size<=0)return -1;
  long ahead=Math.min(durationMs,positionMs+1600);
  long estimated=(long)((double)size*((double)ahead/durationMs));
  int last=blocks()-1;
  return last>1?Math.max(1,Math.min(last-1,(int)(estimated/BLOCK))):-1;
 }
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
     try{fetch(b,true);}catch(BatchUnsupported unsupported){
      // A compliant CDN can reject wider Range spans while accepting one
      // block. Retry this block through the original proven transport path.
      continue;
     }
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
 /** Conservative evidence for a native, still-audible MediaPlayer seek.
  * Sparse files are laid out by BYTE, not by time; MP3 may be VBR. This is
  * only an eligibility hint (not proof of decoder data readiness): require
  * several fully verified adjacent blocks, including metadata head/tail.
  * A bounded hot-seek watchdog must still fail open if the player stalls. */
 synchronized boolean hasVerifiedSeekNeighborhood(long positionMs,long durationMs){
  if(closed||size<=0||positionMs<0||durationMs<=0||positionMs>=durationMs)return false;
  if(complete())return true;
  int last=blocks()-1;
  if(last<3||!present.get(0)||!present.get(last))return false;
  long estimated=Math.min(size-1,(long)((double)size*positionMs/durationMs));
  int b=(int)(estimated/BLOCK);
  return b>0&&b<last&&present.get(b-1)&&present.get(b)&&present.get(b+1);
 }
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
  if(cacheMiss)events.event("replacement_stream_decoder_demand_begin",cachedBytes());
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
  finally{if(cacheMiss){
   synchronized(this){if(--foregroundReads==0)waitingSince=-1;notifyAll();}
   events.event("replacement_stream_decoder_demand_end",cachedBytes());
  }}
 }
 synchronized void check()throws IOException{if(closed||!valid.getAsBoolean())throw new IOException("audio_cancelled");if(fatal!=null)throw fatal;}
 void fetch(int block)throws IOException{fetch(block,false);}
 void fetch(int block,boolean backgroundRead)throws IOException{
  final int runBlocks;
  synchronized(this){
   check();if(backgroundRead&&(foregroundReads>0||prefetchHeldForSeek))throw new ForegroundPriority();
   while(loading.get(block)&&!present.get(block)){
    try{wait(100);}catch(InterruptedException e){Thread.currentThread().interrupt();throw new IOException("audio_interrupted");}
    check();if(backgroundRead&&(foregroundReads>0||prefetchHeldForSeek))throw new ForegroundPriority();
   }
   if(present.get(block))return;
   int count=1;
   if(backgroundRead&&!backgroundBatchUnsupported){
    int limit=Math.min(blocks(),block+PREFETCH_RUN_BLOCKS);
    while(block+count<limit&&!present.get(block+count)&&!loading.get(block+count))count++;
   }
   runBlocks=count;
   loading.set(block,block+runBlocks);
  }
  try{
   IOException last=null;
   for(int attempt=0;attempt<3;attempt++){
    synchronized(this){check();if(backgroundRead&&(foregroundReads>0||prefetchHeldForSeek))throw new ForegroundPriority();}
    HttpURLConnection c=null;
    try{
     c=open.open();synchronized(this){check();connections.add(c);if(backgroundRead)prefetchConnection=c;}
     c.setConnectTimeout(6000);c.setReadTimeout(5000);c.setInstanceFollowRedirects(false);c.setRequestProperty("Accept-Encoding","identity");
     long first=(long)block*BLOCK,lastByte=size>0?Math.min(size-1,first+(long)runBlocks*BLOCK-1):first+BLOCK-1;
     c.setRequestProperty("Range","bytes="+first+"-"+lastByte);String validator; synchronized(this){validator=etag;}if(validator!=null)c.setRequestProperty("If-Range",validator);
     int code=c.getResponseCode();
     if(code!=206){
      if(backgroundRead&&runBlocks>1&&(code==200||code==416)){
       backgroundBatchUnsupported=true;
       events.event("replacement_stream_prefetch_batch_fallback",cachedBytes());
       throw new BatchUnsupported();
      }
      if(code==408||code==429||code>=500)throw new IOException("audio_network_retry");
      throw new AudioTransfer.Rejected("audio_range_unavailable");
     }
     String range=c.getHeaderField("Content-Range"),tag=AudioTransfer.strong(c.getHeaderField("ETag"));
     java.util.regex.Matcher m=java.util.regex.Pattern.compile("bytes ([0-9]+)-([0-9]+)/([0-9]+)").matcher(range==null?"":range);
     if(!m.matches()||tag==null)throw new AudioTransfer.Rejected("invalid_audio_range");
     long from=Long.parseLong(m.group(1)),to=Long.parseLong(m.group(2)),total=Long.parseLong(m.group(3));
     if(total<=0||total>MAX_BYTES||from!=first||to!=Math.min(total-1,first+(long)runBlocks*BLOCK-1))throw new AudioTransfer.Rejected("invalid_audio_range");
     int bytes=(int)(to-from+1);long contentLength=c.getContentLengthLong();if(contentLength>=0&&contentLength!=bytes)throw new AudioTransfer.Rejected("invalid_audio_size");
     synchronized(this){check();if(size<0){size=total;etag=tag;}else if(size!=total||!etag.equals(tag))throw new AudioTransfer.Rejected("audio_version_changed");}
     byte[] data=new byte[bytes];try(InputStream input=c.getInputStream()){int at=0,n;while(at<bytes){synchronized(this){check();}n=input.read(data,at,bytes-at);if(n<0)throw new EOFException("incomplete_audio");if(n==0)continue;at+=n;}}
     // No block becomes visible before the entire validated response has
     // reached the private file. A canceled background run cannot expose a
     // partially written block to a foreground seek.
     synchronized(this){check();try(RandomAccessFile output=new RandomAccessFile(file,"rw")){output.seek(first);output.write(data);}present.set(block,block+runBlocks);notifyAll();}
     if(backgroundRead&&runBlocks>1)events.event("replacement_stream_prefetch_batch",cachedBytes());
     return;
    }catch(BatchUnsupported unsupported){throw unsupported;
    }catch(AudioTransfer.Rejected e){synchronized(this){fatal=e;notifyAll();}throw e;}
    catch(Exception e){
     synchronized(this){if(backgroundRead&&(foregroundReads>0||prefetchHeldForSeek))throw new ForegroundPriority();}
     if(backgroundRead&&runBlocks>1
         &&(e instanceof SocketTimeoutException||attempt>=1)){
      backgroundBatchUnsupported=true;
      events.event("replacement_stream_prefetch_batch_fallback",cachedBytes());
      throw new BatchUnsupported();
     }
     last=e instanceof IOException?(IOException)e:new IOException("audio_transport",e);
     events.event("replacement_stream_retry",cachedBytes());
    }
    finally{if(c!=null){synchronized(this){
     connections.remove(c);
     if(backgroundRead&&prefetchConnection==c)prefetchConnection=null;
    }c.disconnect();}}
   }
   throw last==null?new IOException("audio_transport"):last;
  }finally{synchronized(this){loading.clear(block,block+runBlocks);notifyAll();}}
 }
 public void close(){List<HttpURLConnection> active;synchronized(this){if(closed)return;closed=true;active=new ArrayList<>(connections);connections.clear();notifyAll();if(!detached)file.delete();}for(HttpURLConnection c:active)c.disconnect();watcher.shutdownNow();background.shutdownNow();}
}
