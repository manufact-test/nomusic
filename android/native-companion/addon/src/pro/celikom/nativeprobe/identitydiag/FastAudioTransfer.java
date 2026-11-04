package pro.celikom.nativeprobe.identitydiag;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;

/** An optional full-file acceleration: never exposes partial bytes to MediaPlayer. */
final class FastAudioTransfer {
 static final long MIN_BYTES=1048576;
 static final int SHARDS=4;
 interface ModeEvents {void report(String mode,long elapsedMs,long bytes);}
 static final class Probe {
  final long bytes;final String etag;
  Probe(long bytes,String etag){this.bytes=bytes;this.etag=etag;}
 }
 static final class Unsupported extends IOException {
  Unsupported(String why){super(why);}
 }
 static void setup(HttpURLConnection c){
  c.setConnectTimeout(6000);c.setReadTimeout(12000);
  c.setInstanceFollowRedirects(false);
  c.setRequestProperty("Accept-Encoding","identity");
 }
 static long[] range(String header)throws IOException {
  java.util.regex.Matcher m=java.util.regex.Pattern
   .compile("bytes ([0-9]+)-([0-9]+)/([0-9]+)")
   .matcher(header==null?"":header);
  if(!m.matches())throw new Unsupported("invalid_range");
  try{return new long[]{Long.parseLong(m.group(1)),Long.parseLong(m.group(2)),Long.parseLong(m.group(3))};}
  catch(NumberFormatException e){throw new Unsupported("invalid_range");}
 }
 static Probe probe(AudioTransfer.Open open,BooleanSupplier valid)throws Exception{
  if(!valid.getAsBoolean())throw new AudioTransfer.Rejected("download_cancelled");
  HttpURLConnection c=open.open();
  try{
   setup(c);c.setRequestProperty("Range","bytes=0-0");
   if(c.getResponseCode()!=206)throw new Unsupported("range_unavailable");
   long[] r=range(c.getHeaderField("Content-Range"));
   String tag=AudioTransfer.strong(c.getHeaderField("ETag"));
   long length=c.getContentLengthLong();
   if(r[0]!=0||r[1]!=0||r[2]<MIN_BYTES||r[2]>AudioTransfer.MAX_BYTES
       ||tag==null||(length>=0&&length!=1))
    throw new Unsupported("range_validator_unavailable");
   try(InputStream in=c.getInputStream()){
    if(in.read()<0)throw new Unsupported("range_incomplete");
   }
   if(!valid.getAsBoolean())throw new AudioTransfer.Rejected("download_cancelled");
   return new Probe(r[2],tag);
  }finally{c.disconnect();}
 }
 static void fetchShard(File stage,AudioTransfer.Open open,Probe p,int part,
                        BooleanSupplier valid,Set<HttpURLConnection> active)throws Exception{
  if(!valid.getAsBoolean())throw new AudioTransfer.Rejected("download_cancelled");
  long from=p.bytes*part/SHARDS,to=p.bytes*(part+1)/SHARDS-1;
  HttpURLConnection c=open.open();active.add(c);
  try{
   setup(c);c.setRequestProperty("Range","bytes="+from+"-"+to);
   c.setRequestProperty("If-Range",p.etag);
   if(c.getResponseCode()!=206)throw new Unsupported("shard_range_unavailable");
   long[] r=range(c.getHeaderField("Content-Range"));
   long length=c.getContentLengthLong();
   if(r[0]!=from||r[1]!=to||r[2]!=p.bytes||
       !p.etag.equals(AudioTransfer.strong(c.getHeaderField("ETag")))||
       (length>=0&&length!=to-from+1))
     throw new Unsupported("shard_validator_mismatch");
   try(InputStream in=c.getInputStream();RandomAccessFile out=new RandomAccessFile(stage,"rw")){
    out.seek(from);byte[] bytes=new byte[32768];long remaining=to-from+1;
    while(remaining>0){
     if(!valid.getAsBoolean())throw new AudioTransfer.Rejected("download_cancelled");
     int n=in.read(bytes,0,(int)Math.min(bytes.length,remaining));
     if(n<0)throw new Unsupported("shard_incomplete");
     if(n>0){out.write(bytes,0,n);remaining-=n;}
    }
   }
  }finally{active.remove(c);c.disconnect();}
 }
 static void copy(File target,AudioTransfer.Open open,BooleanSupplier valid,LongSupplier clock,
                  AudioTransfer.Events retries,ModeEvents mode)throws Exception{
  long started=clock.getAsLong();
  if(!valid.getAsBoolean())throw new AudioTransfer.Rejected("download_cancelled");
  File stage=null;
  Set<HttpURLConnection> active=Collections.newSetFromMap(new ConcurrentHashMap<HttpURLConnection,Boolean>());
  ExecutorService pool=null;ScheduledExecutorService watcher=null;
  String fallback=null;
  try{
   Probe p=probe(open,valid);
   stage=File.createTempFile("celikom-fast-shards-",".audio",target.getParentFile());
   try(RandomAccessFile file=new RandomAccessFile(stage,"rw")){file.setLength(p.bytes);}
   final File writing=stage;
   pool=Executors.newFixedThreadPool(SHARDS);
   watcher=Executors.newSingleThreadScheduledExecutor();
   watcher.scheduleAtFixedRate(()->{
    if(!valid.getAsBoolean())for(HttpURLConnection c:active)c.disconnect();
   },100,100,TimeUnit.MILLISECONDS);
   CompletionService<Void> completed=new ExecutorCompletionService<>(pool);
   for(int i=0;i<SHARDS;i++){
    final int part=i;
    completed.submit(()->{fetchShard(writing,open,p,part,valid,active);return null;});
   }
   for(int i=0;i<SHARDS;i++)completed.take().get();
   if(!valid.getAsBoolean())throw new AudioTransfer.Rejected("download_cancelled");
   Files.move(stage.toPath(),target.toPath(),StandardCopyOption.REPLACE_EXISTING);
   stage=null;
   mode.report("parallel_verified",clock.getAsLong()-started,p.bytes);
   return;
  }catch(Exception e){
   if(!valid.getAsBoolean())throw new AudioTransfer.Rejected("download_cancelled");
   fallback=e instanceof Unsupported?e.getMessage():"parallel_transport_failed";
  }finally{
   for(HttpURLConnection c:active)c.disconnect();
   if(pool!=null)pool.shutdownNow();
   if(watcher!=null)watcher.shutdownNow();
   if(stage!=null)stage.delete();
  }
  if(!valid.getAsBoolean())throw new AudioTransfer.Rejected("download_cancelled");
  mode.report("serial_fallback_"+fallback,clock.getAsLong()-started,0);
  try(FileOutputStream clear=new FileOutputStream(target)){}
  AudioTransfer.copy(target,open,valid,clock,retries);
 }
}