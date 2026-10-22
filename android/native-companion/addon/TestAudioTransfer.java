package pro.celikom.nativeprobe.identitydiag;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.atomic.*;
public class TestAudioTransfer {
 static int checks;static void check(boolean b,String s){checks++;if(!b)throw new AssertionError(s);}
 static class Response extends HttpURLConnection {
  int code,failAt=-1;byte[] bytes;Map<String,String> headers=new HashMap<>();volatile boolean disconnected;long jump;AtomicLong extra;
  Response(int c,String body)throws Exception{super(new URL("https://localhost/audio"));code=c;bytes=body.getBytes("UTF-8");headers.put("ETag","\"v1\"");}
  public int getResponseCode(){return code;}public String getHeaderField(String n){return headers.get(n);}public long getContentLengthLong(){return bytes.length;}
  public InputStream getInputStream(){return new InputStream(){int at;public int read()throws IOException{if(extra!=null)extra.addAndGet(jump);if(disconnected)throw new IOException("disconnected");if(failAt>=0&&at>=failAt)throw new SocketTimeoutException();return at<bytes.length?bytes[at++]:-1;} public int read(byte[] b,int o,int n)throws IOException{int x=read();if(x<0)return -1;b[o]=(byte)x;return 1;}};}
  public void disconnect(){disconnected=true;}public boolean usingProxy(){return false;}public void connect(){}
 }
 static void transfer(File f,AtomicBoolean valid,AtomicLong extra,Response...responses)throws Exception{
  AtomicInteger index=new AtomicInteger();AudioTransfer.copy(f,()->{int i=index.getAndIncrement();check(i<responses.length,"bounded expected request count");return responses[i];},valid::get,()->System.nanoTime()/1000000+extra.get(),(a,b,c)->{});
 }
 static void rejected(File f,Response response,String code)throws Exception{try{transfer(f,new AtomicBoolean(true),new AtomicLong(),response);throw new AssertionError("accepted "+code);}catch(AudioTransfer.Rejected e){check(e.getMessage().equals(code),"reject "+code);}}
 public static void main(String[] args)throws Exception{
  File f=File.createTempFile("celikom-transfer-",".test");AtomicBoolean valid=new AtomicBoolean(true);AtomicLong extra=new AtomicLong();
  try{
   Response first=new Response(200,"abcdef");first.failAt=3;Response rest=new Response(206,"def");rest.headers.put("Content-Range","bytes 3-5/6");transfer(f,valid,extra,first,rest);check(new String(Files.readAllBytes(f.toPath()),"UTF-8").equals("abcdef"),"timeout retains exact prefix");check("bytes=3-".equals(rest.getRequestProperty("Range"))&&"\"v1\"".equals(rest.getRequestProperty("If-Range")),"range pinned to immutable validator");
   Files.write(f.toPath(),new byte[0]);first=new Response(200,"abcdef");first.failAt=2;rest=new Response(200,"UVWXYZ");rest.headers.put("ETag","\"v2\"");transfer(f,valid,extra,first,rest);check(new String(Files.readAllBytes(f.toPath()),"UTF-8").equals("UVWXYZ"),"ignored range or changed object restarts safely");
   Files.write(f.toPath(),new byte[0]);first=new Response(200,"abcdef");first.failAt=2;first.headers.clear();rest=new Response(200,"abcdef");transfer(f,valid,extra,first,rest);check(rest.getRequestProperty("Range")==null&&f.length()==6,"no validator cannot append");
   Files.write(f.toPath(),new byte[0]);first=new Response(200,"abcdef");first.failAt=3;rest=new Response(206,"def");rest.headers.put("Content-Range","bytes 2-4/6");try{transfer(f,valid,extra,first,rest);throw new AssertionError("bad range accepted");}catch(AudioTransfer.Rejected e){check(e.getMessage().equals("invalid_audio_range"),"wrong range cannot corrupt audio");}
   Files.write(f.toPath(),new byte[0]);first=new Response(200,"abcd");first.extra=extra;first.jump=9000;transfer(f,valid,extra,first);check(f.length()==4&&extra.get()>30000,"advancing transfer beyond thirty seconds completes");
   Files.write(f.toPath(),new byte[0]);rejected(f,new Response(403,"denied"),"audio_access_failed");
   Response huge=new Response(200,"x"){public long getContentLengthLong(){return AudioTransfer.MAX_BYTES+1;}};rejected(f,huge,"audio_too_large");
   valid.set(false);try{transfer(f,valid,new AtomicLong(),new Response(200,"abc"));throw new AssertionError("cancel ignored");}catch(AudioTransfer.Rejected e){check(e.getMessage().equals("download_cancelled"),"stale track or account cannot download");}
   valid.set(true);Files.write(f.toPath(),new byte[0]);Response blocked=new Response(200,"abc"){public InputStream getInputStream(){return new InputStream(){public int read()throws IOException{while(!disconnected){try{Thread.sleep(10);}catch(InterruptedException e){throw new IOException(e);}}throw new IOException("cancelled socket");}};}};
   Thread cancel=new Thread(()->{try{Thread.sleep(200);}catch(Exception e){}valid.set(false);});cancel.start();long start=System.nanoTime();try{transfer(f,valid,new AtomicLong(),blocked);throw new AssertionError("blocked transfer survived cancellation");}catch(AudioTransfer.Rejected e){check(blocked.disconnected&&(System.nanoTime()-start)/1000000<2000,"watchdog releases obsolete blocked socket promptly");}cancel.join();
  }finally{f.delete();}
  System.out.println("PASS: "+checks+" actual transport range, retry, slow transfer, validation and cancellation checks");
 }
}
