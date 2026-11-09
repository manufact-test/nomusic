package pro.celikom.yandexweb;

import android.net.Uri;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;

import java.io.*;
import java.util.*;

/** Only serves private cached CELIKOM MP3s under a nonce-protected same-origin path. */
final class VirtualAudioResource {
  private final CelikomBroker broker;
  private final String nonce;
  VirtualAudioResource(CelikomBroker broker,String nonce){this.broker=broker;this.nonce=nonce;}
  String virtualUrl(String id,String albumId){return "https://music.yandex.ru/__celikom_audio/"+nonce+"/"+id+"/"+albumId+".mp3";}
  WebResourceResponse intercept(WebResourceRequest req){
    Uri url=req.getUrl();
    if(!"https".equals(url.getScheme())||!"music.yandex.ru".equals(url.getHost()))return null;
    String path=url.getEncodedPath();
    String prefix="/__celikom_audio/";
    if(path==null||!path.startsWith(prefix))return null;
    // This path is OUR endpoint; deny unrecognized requests rather than proxying to Yandex.
    if(!"GET".equals(req.getMethod()))return denied(405,"Method Not Allowed",Collections.emptyMap());
    if(url.getEncodedQuery()!=null||url.getEncodedFragment()!=null)return denied(404,"Not Found",Collections.emptyMap());
    String expected=prefix+nonce+"/";
    if(!path.startsWith(expected))return denied(404,"Not Found",Collections.emptyMap());
    String tail=path.substring(expected.length());
    if(!tail.matches("[1-9][0-9]{0,23}/[1-9][0-9]{0,23}\\.mp3"))
        return denied(404,"Not Found",Collections.emptyMap());
    String id=tail.substring(0,tail.indexOf('/'));
    String albumId=tail.substring(tail.indexOf('/')+1,tail.length()-4);
    CelikomBroker.Asset asset=broker.asset(id,albumId);
    if(asset==null||!asset.file.isFile())return denied(404,"Not Found",Collections.emptyMap());
    long total=asset.file.length();
    RangePolicy.Selection range;
    try{
      range=RangePolicy.parse(req.getRequestHeaders().get("Range"),total);
    }catch(IllegalArgumentException e){
      return denied(416,"Range Not Satisfiable",Map.of("Content-Range","bytes */"+total));
    }
    try {
      FileInputStream in=new FileInputStream(asset.file);
      in.getChannel().position(range.start);
      Map<String,String> headers=new HashMap<>();
      headers.put("Content-Type","audio/mpeg");
      headers.put("Accept-Ranges","bytes");
      headers.put("Content-Length",String.valueOf(range.length()));
      headers.put("Cache-Control","private, no-store");
      headers.put("Access-Control-Allow-Origin","https://music.yandex.ru");
      if(range.partial)headers.put("Content-Range",range.contentRange());
      return new WebResourceResponse("audio/mpeg",null,
        range.status(),range.partial?"Partial Content":"OK",
        headers,new BoundedInputStream(in,range.length()));
    }catch(IOException e){return denied(404,"Not Found",Collections.emptyMap());}
  }
  private static WebResourceResponse denied(int code,String reason,Map<String,String> extras){
    Map<String,String> h=new HashMap<>(extras);
    h.put("Cache-Control","no-store");
    return new WebResourceResponse("text/plain","UTF-8",code,reason,h,
      new ByteArrayInputStream(new byte[0]));
  }
  static final class BoundedInputStream extends FilterInputStream {
    long remaining;
    BoundedInputStream(InputStream in,long len){super(in);remaining=len;}
    @Override public int read()throws IOException{
      if(remaining<=0)return -1;
      int v=in.read();
      if(v!=-1)remaining--;
      return v;
    }
    @Override public int read(byte[] b,int off,int len)throws IOException {
      if(remaining<=0)return -1;
      int r=in.read(b,off,(int)Math.min(remaining,len));
      if(r>0)remaining-=r;
      return r;
    }
  }
}
