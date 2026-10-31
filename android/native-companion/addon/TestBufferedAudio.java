package pro.celikom.nativeprobe.identitydiag;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
public class TestBufferedAudio {
 static int checks;static void check(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
 static class Server implements BufferedAudio.Open {
  byte[] data=new byte[BufferedAudio.BLOCK*8+27];AtomicInteger requests=new AtomicInteger(),failBlockTwoRemaining=new AtomicInteger();boolean badRange,changedTag,deny,shortOnce,ignoreRange,blockRead;volatile boolean disconnected;
  final AtomicBoolean stallBlockTwoOnce=new AtomicBoolean();
  final CountDownLatch backgroundReadBlocked=new CountDownLatch(1);
  final AtomicInteger priorityDisconnects=new AtomicInteger();
   final CountDownLatch priorityDisconnected=new CountDownLatch(1);
   final AtomicReference<String> priorityDisconnectThread=new AtomicReference<>();
  Server(){for(int i=0;i<data.length;i++)data[i]=(byte)(i*31);}
  public HttpURLConnection open()throws Exception{return new HttpURLConnection(new URL("https://localhost/audio")){
   int first,last;boolean fail,stalledBackground;volatile boolean closed;
   public int getResponseCode(){requests.incrementAndGet();String[] range=getRequestProperty("Range").substring(6).split("-");first=Integer.parseInt(range[0]);last=Math.min(data.length-1,Integer.parseInt(range[1]));fail=shortOnce;shortOnce=false;return first/BufferedAudio.BLOCK==2&&failBlockTwoRemaining.getAndUpdate(x->Math.max(0,x-1))>0?503:deny?403:ignoreRange?200:206;}
   public String getHeaderField(String key){if(key.equals("ETag"))return changedTag&&first>0?"\"v2\"":"\"v1\"";if(key.equals("Content-Range"))return "bytes "+(badRange?first+1:first)+"-"+last+"/"+data.length;return null;}
   public long getContentLengthLong(){return last-first+1;}
   public InputStream getInputStream(){
    if(first/BufferedAudio.BLOCK==2&&stallBlockTwoOnce.compareAndSet(true,false)){
     stalledBackground=true;
     return new InputStream(){public int read()throws IOException{
      backgroundReadBlocked.countDown();
      while(!closed){try{Thread.sleep(10);}catch(InterruptedException e){throw new IOException(e);}}
      throw new IOException("preempted_background_range");
     }};
    }
    if(blockRead)return new InputStream(){public int read()throws IOException{while(!closed){try{Thread.sleep(10);}catch(InterruptedException e){throw new IOException(e);}}throw new IOException("disconnected");}};
    return new ByteArrayInputStream(data,first,fail?10:last-first+1);
   }
    public synchronized void disconnect(){if(stalledBackground&&!closed){priorityDisconnects.incrementAndGet();priorityDisconnectThread.set(Thread.currentThread().getName());priorityDisconnected.countDown();}closed=true;disconnected=true;}public boolean usingProxy(){return false;}public void connect(){}
  };}
 }
 static BufferedAudio audio(Server s,AtomicBoolean valid,CountDownLatch cached)throws Exception{return new BufferedAudio(File.createTempFile("celikom-range-",".test"),s,valid::get,()->System.nanoTime()/1000000,(event,bytes)->{if(event.equals("replacement_stream_cached"))cached.countDown();});}
 static void rejected(Server s,String reason)throws Exception{BufferedAudio a=audio(s,new AtomicBoolean(true),new CountDownLatch(1));try{a.initialize();throw new AssertionError("accepted "+reason);}catch(IOException e){check(e.getMessage().equals(reason),reason);}finally{a.close();}}
 public static void main(String[] args)throws Exception{
  Server server=new Server();AtomicBoolean valid=new AtomicBoolean(true);CountDownLatch cached=new CountDownLatch(1);BufferedAudio a=audio(server,valid,cached);File file=a.file;
  try{
   a.initialize();check(server.requests.get()==1&&a.cachedBytes()==BufferedAudio.BLOCK&&!a.complete(),"startup publishes one validated block, never waits for full song");
   byte[] buffer=new byte[4096];check(a.readAt(10,buffer,0,buffer.length)==4096,"read initial buffer");for(int i=0;i<buffer.length;i++)check(buffer[i]==server.data[i+10],"exact cached byte "+i);check(server.requests.get()==1,"cached reads do not request network");
   long seek=(long)BufferedAudio.BLOCK*7+5;check(a.readAt(seek,buffer,0,buffer.length)==4096&&server.requests.get()==2,"seek fetches target block directly, skipping unavailable middle");check(buffer[0]==server.data[(int)seek],"seek bytes correct");check(a.nextPrefetchBlock()==8,"late-track start prioritizes the following block before old missing prefix");a.fetch(8);check(a.nextPrefetchBlock()==1,"completed tail returns to fill bounded cache prefix");a.readAt(BufferedAudio.BLOCK*3L,buffer,0,4);check(a.nextPrefetchBlock()==4,"backward seek immediately changes prefetch priority");
   check(a.readAt(a.size,buffer,0,1)==-1&&a.readAt(0,buffer,0,0)==0,"decoder EOF and zero-size semantics");
   a.prefetch();check(cached.await(5,TimeUnit.SECONDS)&&a.complete(),"background fills complete audio");check(Arrays.equals(Files.readAllBytes(file.toPath()),server.data),"sparse cache becomes byte-exact full file");check(a.retainComplete()==file,"only completed file can enter existing cache");
  }finally{a.close();}check(file.exists(),"completed detached file retained");file.delete();
  server=new Server();a=audio(server,new AtomicBoolean(true),new CountDownLatch(1));try{a.initializeForPlayback();check(server.requests.get()==3&&a.present.get(0)&&a.present.get(1)&&a.present.get(a.blocks()-1)&&!a.complete(),"decoder preparation has prefix, read-ahead and tail metadata without full download");int before=server.requests.get();a.readAt(a.size-16,new byte[16],0,16);check(server.requests.get()==before,"decoder tail inspection cannot block on a new network request");}finally{a.close();}
  server=new Server();server.shortOnce=true;a=audio(server,new AtomicBoolean(true),new CountDownLatch(1));try{a.initialize();check(server.requests.get()==2&&a.cachedBytes()==BufferedAudio.BLOCK,"truncated block retries without exposing corrupt prefix");check(a.retainComplete()==null,"partial cache cannot be treated as a complete file");}finally{file=a.file;a.close();}check(!file.exists(),"closing deletes incomplete cache");
  /* HONOR 0.3.67: mobile+VPN lost sparse prefetch after three failed Range
     requests. A later successful decoder miss must re-arm ONE background fill,
     not leave the private song partial forever or spin on cached reads. */
  server=new Server();server.failBlockTwoRemaining.set(3);valid=new AtomicBoolean(true);
  CountDownLatch prefetchFailed=new CountDownLatch(1),releasePrefetchFailure=new CountDownLatch(1),eventuallyCached=new CountDownLatch(1);
  a=new BufferedAudio(File.createTempFile("celikom-range-recovery-",".test"),server,valid::get,
    ()->System.nanoTime()/1000000,(event,bytes)->{
      if(event.equals("replacement_stream_prefetch_wait")){
       prefetchFailed.countDown();
       try{if(!releasePrefetchFailure.await(5,TimeUnit.SECONDS))throw new AssertionError("prefetch failure not released");}
       catch(InterruptedException e){Thread.currentThread().interrupt();throw new AssertionError(e);}
      }
      if(event.equals("replacement_stream_cached"))eventuallyCached.countDown();
    });
  try{
   a.initialize();a.prefetch();
   check(prefetchFailed.await(5,TimeUnit.SECONDS)&&!a.complete(),
     "three failed background Ranges must leave validated partial data, not a corrupt cache");
   int requestsBefore=server.requests.get();
   byte[] recovered=new byte[16];long demanded=BufferedAudio.BLOCK*6L+7;
   check(a.readAt(demanded,recovered,0,recovered.length)==recovered.length
       &&recovered[0]==server.data[(int)demanded],
     "post-failure successful on-demand sparse block is validated and readable");
   check(a.prefetchActive,
     "race reproduction: decoder recovered while old prefetch worker was still failing");
   releasePrefetchFailure.countDown();
   check(eventuallyCached.await(5,TimeUnit.SECONDS)&&a.complete(),
     "RED 0.3.67: demand success before worker cleanup must still restart prefetch");
   check(server.requests.get()>requestsBefore,
     "recovery fills missing blocks, rather than spinning on cached reads");
  }finally{releasePrefetchFailure.countDown();a.close();}
  /* Priority regression: the prefetch worker is blocked forever in HTTP
     block #2, while a real seek demands block #6. A decoder read must not
     wait for that obsolete Range or for its three network retries. After
     yielding, validated background fill still has to complete byte-exact. */
  server=new Server();server.stallBlockTwoOnce.set(true);
  CountDownLatch priorityCached=new CountDownLatch(1),demandDone=new CountDownLatch(1);
  a=new BufferedAudio(File.createTempFile("celikom-priority-",".test"),server,()->true,
   ()->System.nanoTime()/1000000,(event,bytes)->{
    if(event.equals("replacement_stream_cached"))priorityCached.countDown();
   });
  final BufferedAudio prioritized=a;final Server priorityServer=server;
  AtomicReference<Throwable> demandFailure=new AtomicReference<>();
  AtomicInteger demandBytes=new AtomicInteger(-1);
  try{
   prioritized.initializeForPlayback();prioritized.prefetch();
   check(server.backgroundReadBlocked.await(3,TimeUnit.SECONDS),
     "setup: prefetch must be stuck in the old HTTP Range");
   Thread demandThread=new Thread(()->{
    try{
     byte[] bytes=new byte[32];
     long at=BufferedAudio.BLOCK*6L+9;
     demandBytes.set(prioritized.readAt(at,bytes,0,bytes.length));
     if(bytes[0]!=priorityServer.data[(int)at])throw new AssertionError("priority demand byte mismatch");
    }catch(Throwable e){demandFailure.set(e);}
    finally{demandDone.countDown();}
   });
   demandThread.start();
   check(demandDone.await(3,TimeUnit.SECONDS)&&demandFailure.get()==null&&demandBytes.get()==32,
     "a finger seek must finish while an obsolete background Range is stalled: "+demandFailure.get());
    check(server.priorityDisconnected.await(3,TimeUnit.SECONDS)
       &&server.priorityDisconnects.get()==1
       &&!demandThread.getName().equals(server.priorityDisconnectThread.get()),
      "obsolete prefetch connection must disconnect exactly once off the decoder thread");
   check(priorityCached.await(5,TimeUnit.SECONDS)&&prioritized.complete(),
     "prefetch recovers after priority yield without a new seek or timer");
   check(Arrays.equals(Files.readAllBytes(prioritized.file.toPath()),server.data),
     "priority preemption never mixes incomplete or stale bytes");
  }finally{prioritized.close();}
   /* HONOR 0.3.69: rapid finger seeks must NOT start a new speculative
      background Range between validated decoder reads or corrections.
      The whole verified seek/handover owns the foreground transport lease. */
   server=new Server();server.stallBlockTwoOnce.set(true);
   CountDownLatch heldYield=new CountDownLatch(1),heldCached=new CountDownLatch(1);
   AtomicInteger resumedWhileHeld=new AtomicInteger(),yields=new AtomicInteger();
   a=new BufferedAudio(File.createTempFile("celikom-seek-lease-",".test"),server,()->true,
    ()->System.nanoTime()/1000000,(event,bytes)->{
     if(event.equals("replacement_stream_prefetch_yield")){yields.incrementAndGet();heldYield.countDown();}
     if(event.equals("replacement_stream_prefetch_resumed"))resumedWhileHeld.incrementAndGet();
     if(event.equals("replacement_stream_cached"))heldCached.countDown();
    });
   try{
    a.initializeForPlayback();a.prefetch();
    check(server.backgroundReadBlocked.await(3,TimeUnit.SECONDS),
      "setup: speculative Range is blocked before user starts scrubbing");
    a.holdPrefetchForSeek();
    for(int block:new int[]{6,3,5,4}){
     long at=(long)BufferedAudio.BLOCK*block+7;
     byte[] bytes=new byte[32];
     check(a.readAt(at,bytes,0,bytes.length)==bytes.length
       &&bytes[0]==server.data[(int)at],
       "seek correction has priority and byte-exact sparse content for block "+block);
    }
    check(heldYield.await(3,TimeUnit.SECONDS),
      "actual decoder miss must preempt the blocked background transport");
    check(resumedWhileHeld.get()==0&&!a.complete()&&yields.get()==1,
      "background must stay yielded throughout all rapid positions and corrections");
    a.releasePrefetchAfterSeek();
    check(heldCached.await(5,TimeUnit.SECONDS)&&a.complete(),
      "one clock-confirmed handover resumes speculative prefetch");
    check(resumedWhileHeld.get()==1&&yields.get()==1,
      "one yield and one resume per whole seek chain, not per decoder read");
    check(Arrays.equals(Files.readAllBytes(a.file.toPath()),server.data),
      "prefetch recovery after rapid seeks preserves full exact audio bytes");
   }finally{a.close();}
  server=new Server();server.badRange=true;rejected(server,"invalid_audio_range");server=new Server();server.deny=true;rejected(server,"audio_range_unavailable");server=new Server();server.ignoreRange=true;rejected(server,"audio_range_unavailable");
  server=new Server();server.changedTag=true;a=audio(server,new AtomicBoolean(true),new CountDownLatch(1));try{a.initialize();try{a.readAt(BufferedAudio.BLOCK,new byte[4],0,4);throw new AssertionError("mixed version accepted");}catch(IOException e){check(e.getMessage().equals("audio_version_changed"),"changed validator never mixes editions");}}finally{a.close();}
  server=new Server();server.blockRead=true;valid=new AtomicBoolean(true);a=audio(server,valid,new CountDownLatch(1));final BufferedAudio cancelled=a;AtomicReference<Throwable> error=new AtomicReference<>();Thread reader=new Thread(()->{try{cancelled.initialize();}catch(Throwable e){error.set(e);}});reader.start();Thread.sleep(150);valid.set(false);reader.join(2000);check(!reader.isAlive()&&error.get()!=null&&server.disconnected,"Stop/account/track cancellation interrupts blocked network promptly");a.close();
  System.out.println("PASS: "+checks+" progressive startup, byte accuracy, random seek, cache completion, malformed range and cancellation checks");
 }
}
