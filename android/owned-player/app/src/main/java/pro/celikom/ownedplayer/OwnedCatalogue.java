package pro.celikom.ownedplayer;

import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.Collections;
import java.util.Locale;

/** Metadata ONLY, never playback authority or complete Yandex catalogue. */
public final class OwnedCatalogue {
    public static final class Track {
        public final String id,title,artist,album;
        public final long durationMs;
        Track(String id,String title,String artist,String album,long ms) {
            this.id=id;this.title=title;this.artist=artist;this.album=album;durationMs=ms;
        }
        @Override public String toString(){return title+" — "+artist;}
    }
    private final List<Track> tracks;
    private OwnedCatalogue(List<Track> approved) {
        tracks=Collections.unmodifiableList(approved);
    }
    public static OwnedCatalogue parse(JSONObject json,long nowMs)throws Exception {
        if(json==null || json.optInt("schema")!=1 ||
                !"celikom_owner_catalog_snapshot".equals(json.optString("source")) ||
                !json.optBoolean("complete",false))
            throw new Exception("catalogue_contract_invalid");
        long generated=json.optLong("generated_at_ms");
        if(generated<=0 || generated>nowMs+600000 ||
                nowMs-generated>7L*86400000L)
            throw new Exception("catalogue_stale");
        JSONArray items=json.optJSONArray("tracks");
        int count=json.optInt("total_tracks",-1);
        if(items==null || count<0 || count>5000 || items.length()!=count ||
                json.toString().length()>2_000_000)
            throw new Exception("catalogue_incomplete");
        Set<String> seen=new HashSet<>();
        List<Track> approved=new ArrayList<>(count);
        for(int i=0;i<count;i++){
            JSONObject row=items.optJSONObject(i);
            if(row==null)throw new Exception("catalogue_invalid_item");
            String id=row.optString("track_id","");
            String title=row.optString("title","").trim();
            String artist=row.optString("artist","").trim();
            String album=row.optString("album","");
            long ms=row.optLong("duration_ms",-1);
            if(!OwnedPlaybackContract.validTrackId(id)||!seen.add(id) ||
                    title.isEmpty()||title.length()>512 ||
                    artist.isEmpty()||artist.length()>512 ||
                    album.length()>512 ||
                    ms<1000||ms>36000000 ||
                    !row.optBoolean("replacement_available",false))
                throw new Exception("catalogue_invalid_item");
            approved.add(new Track(id,title,artist,album,ms));
        }
        return new OwnedCatalogue(approved);
    }
    public int count(){return tracks.size();}
    public Track get(int index){return tracks.get(index);}
    public int indexOf(String trackId){
        for(int i=0;i<tracks.size();i++)
            if(tracks.get(i).id.equals(trackId))return i;
        return -1;
    }
    public List<Track> search(String query,int limit){
        if(limit<1||limit>250)throw new IllegalArgumentException("limit");
        String value=query==null?"":query.trim().toLowerCase(Locale.ROOT);
        List<Track> found=new ArrayList<>();
        for(Track track:tracks){
            if(!value.isEmpty()&&!track.title.toLowerCase(Locale.ROOT).contains(value)
                    &&!track.artist.toLowerCase(Locale.ROOT).contains(value))continue;
            found.add(track);
            if(found.size()>=limit)break;
        }
        return found;
    }
}
