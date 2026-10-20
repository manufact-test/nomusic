package pro.celikom.nativeprobe.identitydiag;
import java.util.*;
import java.util.regex.*;
final class ShareLinks {
 static List<Object> parse(String raw){List<Object> refs=new ArrayList<>();Matcher links=Pattern.compile("https?://(?:music\\.yandex\\.(?:ru|com|by|kz|uz)|ya\\.ru)/[^\\s<>\"?]*").matcher(raw==null?"":raw);while(links.find()&&refs.size()<5){String u=links.group();Map<String,Object> ref=LogStore.map("url",u);Matcher track=Pattern.compile("/(?:album/(\\d+)/)?track/(\\d+)(?:/|$)").matcher(u);if(track.find()){ref.put("albumId",track.group(1));ref.put("catalogueTrackId",track.group(2));}refs.add(ref);}return refs;}
}
