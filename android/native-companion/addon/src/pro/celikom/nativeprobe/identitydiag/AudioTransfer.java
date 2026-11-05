package pro.celikom.nativeprobe.identitydiag;
import java.io.*;
import java.net.*;
import java.util.concurrent.*;
import java.util.function.*;
/** Bounded resumable transport. No authentication state or Android dependency. */
final class AudioTransfer {
 static final long MAX_BYTES=31457280, MAX_MS=180000;
 interface Open {HttpURLConnection open() throws Exception;}
 interface Events {void retry(int attempt,long bytes,String reason);}
 interface Progress {void bytes(long received,long expected,long when);}
 static final class Rejected extends IOException {Rejected(String reason){super(reason);}}
 static final class ForegroundYield extends IOException {ForegroundYield(){super("foreground_audio_priority");}}
 static void copy(File file,Open open,BooleanSupplier valid,LongSupplier clock,Events events)throws Exception {
  copy(file,open,valid,()->false,clock,events);
 }
 /** Speculative downloads yield the socket and retain only a validator-pinned
  * prefix while the current decoder needs bandwidth. This is not a revoke:
  * the very same transfer can resume with If-Range when foreground clears. */
 static void copy(File file,Open open,BooleanSupplier valid,BooleanSupplier foregroundBusy,LongSupplier clock,Events events)throws Exception {
  copy(file,open,valid,foregroundBusy,clock,events,(received,expected,when)->{});
 }
 static void copy(File file,Open open,BooleanSupplier valid,BooleanSupplier foregroundBusy,LongSupplier clock,Events events,Progress progress)throws Exception {
  long start=clock.getAsLong(),total=-1;String etag=null;int failures=0;
  ScheduledExecutorService watchdog=Executors.newSingleThreadScheduledExecutor();
  try{
   while(true){
    if(!valid.getAsBoolean())throw new Rejected("download_cancelled");
    if(clock.getAsLong()-start>=MAX_MS)throw new Rejected("download_deadline");
    while(foregroundBusy.getAsBoolean()){
     if(!valid.getAsBoolean())throw new Rejected("download_cancelled");
     if(clock.getAsLong()-start>=MAX_MS)throw new Rejected("download_deadline");
     Thread.sleep(50);
    }
    HttpURLConnection c=open.open();
    ScheduledFuture<?> cancel=watchdog.scheduleAtFixedRate(()->{if(!valid.getAsBoolean()||foregroundBusy.getAsBoolean()||clock.getAsLong()-start>=MAX_MS)c.disconnect();},50,50,TimeUnit.MILLISECONDS);
    long offset=file.length(),expected=-1;
    try{
     c.setConnectTimeout(10000);c.setReadTimeout(12000);c.setInstanceFollowRedirects(false);c.setRequestProperty("Accept-Encoding","identity");
     if(offset>0&&etag!=null){c.setRequestProperty("Range","bytes="+offset+"-");c.setRequestProperty("If-Range",etag);}
     int code=c.getResponseCode();String nextTag=c.getHeaderField("ETag");long length=c.getContentLengthLong();
     if(code==200){offset=0;total=length;etag=strong(nextTag);try(FileOutputStream reset=new FileOutputStream(file)){} }
     else if(code==206&&offset>0&&etag!=null&&etag.equals(nextTag)){
      String range=c.getHeaderField("Content-Range");java.util.regex.Matcher m=java.util.regex.Pattern.compile("bytes ([0-9]+)-([0-9]+)/([0-9]+)").matcher(range==null?"":range);
      if(!m.matches())throw new Rejected("invalid_audio_range");
      long first=Long.parseLong(m.group(1)),last=Long.parseLong(m.group(2)),size=Long.parseLong(m.group(3));
      if(first!=offset||last!=size-1||size<=offset||(total>=0&&size!=total)||(length>=0&&length!=size-offset))throw new Rejected("invalid_audio_range");total=size;
     }else if(code==408||code==429||code>=500&&code<=599)throw new IOException("audio_server_busy");
     else throw new Rejected("audio_access_failed");
     if(total>MAX_BYTES||total==0)throw new Rejected("audio_too_large");expected=total;
     if(expected>0)progress.bytes(offset,expected,clock.getAsLong());
     try(InputStream in=c.getInputStream();FileOutputStream out=new FileOutputStream(file,offset>0)){
      byte[] bytes=new byte[32768];int n;long received=offset;
      while(received!=expected&&(n=in.read(bytes))!=-1){
       if(!valid.getAsBoolean())throw new Rejected("download_cancelled");
       if(foregroundBusy.getAsBoolean())throw new ForegroundYield();
       if(clock.getAsLong()-start>=MAX_MS)throw new Rejected("download_deadline");
       received+=n;if(received>MAX_BYTES||(expected>=0&&received>expected))throw new Rejected("invalid_audio_size");out.write(bytes,0,n);
       if(expected>0)progress.bytes(received,expected,clock.getAsLong());
      }
      if(received==0||expected>=0&&received!=expected)throw new EOFException("incomplete_audio");
     }
     if(!valid.getAsBoolean())throw new Rejected("download_cancelled");return;
    }catch(Rejected e){throw e;}
    catch(IOException e){
     if(!valid.getAsBoolean())throw new Rejected("download_cancelled");
     if(e instanceof ForegroundYield||foregroundBusy.getAsBoolean()){
      events.retry(failures,file.length(),"foreground_yield");
      continue;
     }
     if(++failures>8||clock.getAsLong()-start>=MAX_MS)throw e;
     // Without an immutable validator, never append bytes from another response.
     if(etag==null){try(FileOutputStream out=new FileOutputStream(file)){ }total=-1;}
     events.retry(failures,file.length(),e instanceof SocketTimeoutException?"timeout":"transport_interrupted");
    }finally{cancel.cancel(false);c.disconnect();}
    long until=clock.getAsLong()+Math.min(2000,failures*250);
    while(clock.getAsLong()<until){if(!valid.getAsBoolean())throw new Rejected("download_cancelled");Thread.sleep(50);}
   }
  }finally{watchdog.shutdownNow();}
 }
 static String strong(String tag){return tag!=null&&tag.startsWith("\"")&&tag.endsWith("\"")?tag:null;}
}
