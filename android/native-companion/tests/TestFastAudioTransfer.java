package pro.celikom.nativeprobe.identitydiag;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.atomic.*;

/** Deterministic HTTP contract; real speed remains a device/network measurement. */
public final class TestFastAudioTransfer {
 static int checks;
 static void check(boolean yes,String message){checks++;if(!yes)throw new AssertionError(message);}
 static final class Fake implements AudioTransfer.Open {
  final byte[] contents;final boolean rangeSupport,badShardTag;
  final AtomicInteger requests=new AtomicInteger(),partials=new AtomicInteger(),serials=new AtomicInteger();
  final java.util.concurrent.atomic.AtomicBoolean allowed=new java.util.concurrent.atomic.AtomicBoolean(true);
  volatile boolean revokeOnShard;
  Fake(byte[] contents,boolean rangeSupport,boolean badShardTag){this.contents=contents;this.rangeSupport=rangeSupport;this.badShardTag=badShardTag;}
  public HttpURLConnection open(){requests.incrementAndGet();return new Connection(this);}
 }
 static final class Connection extends HttpURLConnection {
  final Fake owner;long from,to;boolean partial;
  Connection(Fake owner){super(url());this.owner=owner;}
  static URL url(){try{return new URL("https://example.invalid/celikom.mp3");}catch(Exception ex){throw new RuntimeException(ex);}}
  void inspect(){
   String header=getRequestProperty("Range");
   partial=header!=null&&owner.rangeSupport;
   from=0;to=owner.contents.length-1;
   if(partial){
    java.util.regex.Matcher m=java.util.regex.Pattern.compile("bytes=([0-9]+)-([0-9]+)").matcher(header);
    if(!m.matches())throw new IllegalArgumentException("bad fixture range: "+header);
    from=Long.parseLong(m.group(1));to=Math.min(owner.contents.length-1,Long.parseLong(m.group(2)));
   }
  }
  public void connect(){}
  public boolean usingProxy(){return false;}
  public void disconnect(){}
  public int getResponseCode(){inspect();if(partial)owner.partials.incrementAndGet();else owner.serials.incrementAndGet();return partial?206:200;}
  public String getHeaderField(String header){
   if("ETag".equalsIgnoreCase(header))return owner.badShardTag&&partial&&from>0?"\"changed\"":"\"original\"";
   if("Content-Range".equalsIgnoreCase(header)&&partial)return "bytes "+from+"-"+to+"/"+owner.contents.length;
   return null;
  }
  public long getContentLengthLong(){return to-from+1;}
  public InputStream getInputStream(){
   if(owner.revokeOnShard&&partial&&from>0)owner.allowed.set(false);
   return new ByteArrayInputStream(owner.contents,(int)from,(int)(to-from+1));
  }
 }
 static byte[] audio(int length){byte[] data=new byte[length];new Random(0xC311C0).nextBytes(data);return data;}
 static void caseRun(int size,boolean supportsRange,boolean invalidTag,String expected)throws Exception{
  byte[] data=audio(size);
  Fake transport=new Fake(data,supportsRange,invalidTag);
  File out=File.createTempFile("fast-audio-verified-",".test");
  List<String> modes=new ArrayList<>();
  try{
   FastAudioTransfer.copy(out,transport,()->true,System::currentTimeMillis,(a,b,c)->{},
     (mode,ms,bytes)->modes.add(mode));
   check(Arrays.equals(data,Files.readAllBytes(out.toPath())),"full local bytes must match source exactly "+expected);
   check(modes.size()==1&&modes.get(0).startsWith(expected),"expected download mode "+expected+": "+modes);
   if("parallel_verified".equals(expected)){
    check(transport.partials.get()==FastAudioTransfer.SHARDS+1&&transport.serials.get()==0,
       "verified four-byte-range shards plus one metadata probe");
   }else check(transport.serials.get()==(supportsRange?1:2),
     "unsupported/mismatched Range falls back to proven serial download");
  }finally{out.delete();}
 }
 static void cancellation()throws Exception{
  File out=File.createTempFile("fast-audio-cancel-",".test");
  Fake t=new Fake(audio(3*1024*1024),true,false);
  try{
   boolean blocked=false;
   try{FastAudioTransfer.copy(out,t,()->false,System::currentTimeMillis,(a,b,c)->{},(a,b,c)->{});}
   catch(AudioTransfer.Rejected ex){blocked="download_cancelled".equals(ex.getMessage());}
   check(blocked&&t.requests.get()==0&&out.length()==0,"revoked foreground lease cannot start any HTTP read");
  }finally{out.delete();}
 }
 static void midDownloadRevocation()throws Exception{
  File out=File.createTempFile("fast-audio-mid-cancel-",".test");
  Fake t=new Fake(audio(5*1024*1024),true,false);t.revokeOnShard=true;
  try{
   boolean rejected=false;
   try{FastAudioTransfer.copy(out,t,t.allowed::get,System::currentTimeMillis,(a,b,c)->{},(a,b,c)->{});}
   catch(AudioTransfer.Rejected ex){rejected="download_cancelled".equals(ex.getMessage());}
   check(rejected&&out.length()==0,"revoked in-flight shards cannot publish incomplete local MP3");
  }finally{out.delete();}
 }
 public static void main(String[] args)throws Exception{
  caseRun(4*1024*1024+253,true,false,"parallel_verified");
  caseRun(4*1024*1024+253,false,false,"serial_fallback_");
  caseRun(4*1024*1024+253,true,true,"serial_fallback_");
  caseRun(450000,true,false,"serial_fallback_");
  cancellation();
  midDownloadRevocation();
  System.out.println("PASS: "+checks+" validated four-range full-file transport and serial fallback checks");
 }
}