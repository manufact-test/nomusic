package pro.celikom.nativeprobe.identitydiag;
import java.util.*;
public class TestPure {
 static void check(boolean ok,String m){if(!ok)throw new AssertionError(m);}
 public static void main(String[] a) throws Exception {
  check(LogStore.clean("https://x.test/?token=EXAMPLE123&trackId=456").equals("https://x.test/?token=[REDACTED]&trackId=456"),"URL token redaction");
  check(LogStore.clean("Bearer EXAMPLE_ABC.123").equals("Bearer [REDACTED]"),"Bearer redaction");
  check(LogStore.secret("accessToken")&&LogStore.secret("AUTHORIZATION")&&LogStore.secret("password"),"sensitive keys");
  check(!LogStore.secret("mediaId")&&!LogStore.secret("android.mediaSession")&&!LogStore.secret("catalogueTrackId"),"track fields preserved");
  String j=String.valueOf(LogStore.json(LogStore.map("nested",LogStore.map("password","EXAMPLE_PASSWORD","trackId",456)),0));
  check(!j.contains("EXAMPLE_PASSWORD")&&j.contains("456")&&j.contains("REDACTED"),"nested redaction");
  List<Object> refs=ShareLinks.parse("Исполнитель — песня https://music.yandex.ru/album/123/track/456?utm_source=share&token=EXAMPLE");
  check(refs.size()==1,"single shared link");Map<?,?> ref=(Map<?,?>)refs.get(0);check("456".equals(ref.get("catalogueTrackId"))&&"123".equals(ref.get("albumId")),"exact catalogue IDs");check(!String.valueOf(ref).contains("EXAMPLE"),"share query excluded");
  check(ShareLinks.parse("https://music.yandex.ru.evil.test/album/123/track/456").isEmpty(),"host validation");
  check(ShareLinks.parse("unrelated text").isEmpty(),"unrelated share ignored");
  check("456".equals(((Map<?,?>)ShareLinks.parse("https://music.yandex.com/track/456").get(0)).get("catalogueTrackId")),"track-only link");
  String cover="https://avatars.yandex.net/get-music-content/20622967/bb5ddb97.a.43573492-1/700x700";
  check("43573492".equals(AlbumMatch.albumId(cover)),"album ID from observed cover URI");
  check(AlbumMatch.albumId(cover.replace("avatars.yandex.net","avatars.yandex.net.evil.test"))==null,"cover host validation");
  check(AlbumMatch.albumId(cover.replace("https:","http:"))==null,"HTTPS cover requirement");
  org.json.JSONObject album=new org.json.JSONObject("{\"id\":43573492,\"volumes\":[[{\"id\":154872274,\"title\":\"Alone 2\",\"durationMs\":178380,\"artists\":[{\"name\":\"Edgars Bukovskis\"}]}]]}");
  List<Map<String,Object>> tracks=AlbumMatch.tracks(album,"43573492");
  Map<String,Object> match=AlbumMatch.match("Alone 2","Edgars Bukovskis",178380,tracks);
  check("UNIQUE_CANDIDATE".equals(match.get("status"))&&"154872274".equals(match.get("catalogueTrackId")),"unique album candidate");
  check("NO_MATCH".equals(AlbumMatch.match("Alone 2","Other artist",178380,tracks).get("status")),"artist mismatch rejected");
  check("NO_MATCH".equals(AlbumMatch.match("Alone 2","Edgars Bukovskis",180000,tracks).get("status")),"duration mismatch rejected");
  check("MISSING_DURATION".equals(AlbumMatch.match("Alone 2","Edgars Bukovskis",0,tracks).get("status")),"missing duration rejected");
  tracks.add(new LinkedHashMap<>(tracks.get(0)));tracks.get(1).put("catalogueTrackId","999");
  match=AlbumMatch.match("Alone 2","Edgars Bukovskis",178380,tracks);
  check("AMBIGUOUS".equals(match.get("status"))&&!match.containsKey("catalogueTrackId"),"ambiguity never produces a selected ID");
  boolean rejected=false;try{AlbumMatch.tracks(album,"1");}catch(IllegalArgumentException expected){rejected=true;}check(rejected,"wrong album response rejected");
  album=new org.json.JSONObject("{\"id\":43573492,\"volumes\":[[{\"id\":123,\"title\":\"Alone 2\",\"version\":\"Live\",\"durationMs\":178380,\"artists\":[{\"name\":\"Edgars Bukovskis\"}]}]]}");
  tracks=AlbumMatch.tracks(album,"43573492");check("NO_MATCH".equals(AlbumMatch.match("Alone 2","Edgars Bukovskis",178380,tracks).get("status")),"version mismatch rejected");
  check("UNIQUE_CANDIDATE".equals(AlbumMatch.match("Alone 2 (Live)","Edgars Bukovskis",178380,tracks).get("status")),"explicit matching version accepted");
  /* Execute against the actual compiled Android addon, including a disk-cache round trip. */
  java.io.File cacheFile=java.io.File.createTempFile("artist-cache-", ".json");cacheFile.delete();
  try{IdentityCache cache=new IdentityCache(cacheFile);List<Map<String,Object>> recorded=new ArrayList<>();recorded.add(LogStore.map("catalogueTrackId","89285816","displayTitle","Он рядом","title","Он рядом","version","","artist","Quest Pistols","durationMs",224520L));cache.save("17497301",recorded);List<Map<String,Object>> cached=new IdentityCache(cacheFile).load().get("17497301");check("89285816".equals(AlbumMatch.match("Он рядом","Quest Pistols Show, Quest Pistols",224520,cached).get("catalogueTrackId")),"installed-cache path resolves the recorded artist pair");}finally{cacheFile.delete();}
  System.out.println("PASS: redaction, shared links, album URI parsing, strict matching, ambiguity, duration, album response and version validation");
 }
}
