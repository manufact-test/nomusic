package pro.celikom.nativeprobe.identitydiag;
import org.json.*;
import java.net.URI;
import java.text.Normalizer;
import java.util.*;
import java.util.regex.*;
final class AlbumMatch {
 static String albumId(String cover){try{URI u=new URI(cover);if(!"https".equalsIgnoreCase(u.getScheme())||!"avatars.yandex.net".equalsIgnoreCase(u.getHost())||!u.getPath().startsWith("/get-music-content/"))return null;Matcher m=Pattern.compile("\\.a\\.(\\d{1,15})(?:-|/)").matcher(u.getPath());return m.find()?m.group(1):null;}catch(Exception e){return null;}}
 static String norm(String s){return Normalizer.normalize(s==null?"":s,Normalizer.Form.NFKC).toLowerCase(Locale.ROOT).replaceAll("\\s+"," ").trim();}
 /* Only collapse the duplicated pair seen in Yandex's display metadata.
    Other additional artists remain part of the exact identity. */
 static String artistKey(String value){SortedSet<String> names=new TreeSet<>();for(String part:norm(value).split(",")){String name=part.trim();if(!name.isEmpty())names.add(name);}if(names.contains("quest pistols")&&names.contains("quest pistols show"))names.remove("quest pistols show");return String.join(", ",names);}
 static List<Map<String,Object>> tracks(JSONObject result,String expected)throws Exception{
  if(!expected.equals(String.valueOf(result.opt("id"))))throw new IllegalArgumentException("Response album ID does not match request");
  JSONArray volumes=result.optJSONArray("volumes");if(volumes==null)throw new IllegalArgumentException("No album volumes in response");
  LinkedHashMap<String,Map<String,Object>> tracks=new LinkedHashMap<>();
  for(int v=0;v<volumes.length();v++){JSONArray volume=volumes.optJSONArray(v);if(volume==null)continue;for(int i=0;i<volume.length();i++){JSONObject t=volume.optJSONObject(i);if(t==null)continue;String id=String.valueOf(t.opt("id"));if(!id.matches("\\d{1,20}"))continue;String title=t.optString("title","");String version=t.optString("version","");String display=title;if(!version.isEmpty()&&!norm(title).contains(norm(version)))display=title+" ("+version+")";JSONArray artists=t.optJSONArray("artists");List<String> names=new ArrayList<>();if(artists!=null)for(int k=0;k<artists.length();k++){JSONObject a=artists.optJSONObject(k);if(a!=null&&!a.optString("name","").isEmpty())names.add(a.optString("name"));}tracks.put(id,LogStore.map("catalogueTrackId",id,"title",title,"version",version,"displayTitle",display,"artist",String.join(", ",names),"durationMs",t.optLong("durationMs",-1)));if(tracks.size()>1000)throw new IllegalArgumentException("Album track limit exceeded");}}
  return new ArrayList<>(tracks.values());
 }
 static Map<String,Object> match(String title,String artist,long duration,List<Map<String,Object>> tracks){
  List<Object> sameTitleArtist=new ArrayList<>();List<Object> candidates=new ArrayList<>();
  for(Map<String,Object> t:tracks){if(norm(title).isEmpty()||norm(artist).isEmpty())continue;if(!norm(title).equals(norm(String.valueOf(t.get("displayTitle"))))||!artistKey(artist).equals(artistKey(String.valueOf(t.get("artist")))))continue;long td=((Number)t.get("durationMs")).longValue();sameTitleArtist.add(t);if(duration>0&&td>0&&Math.abs(td-duration)<=1000)candidates.add(t);}
  String status=duration<=0?"MISSING_DURATION":candidates.size()==1?"UNIQUE_CANDIDATE":candidates.isEmpty()?"NO_MATCH":"AMBIGUOUS";
  Map<String,Object> out=LogStore.map("status",status,"method","album ID from cover URI + strict title/artist + duration within 1000 ms","candidates",candidates,"titleArtistMatches",sameTitleArtist);
  if(candidates.size()==1)out.put("catalogueTrackId",((Map<?,?>)candidates.get(0)).get("catalogueTrackId"));return out;
 }
}
