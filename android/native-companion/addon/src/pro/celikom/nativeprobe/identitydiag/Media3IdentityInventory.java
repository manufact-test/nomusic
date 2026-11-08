package pro.celikom.nativeprobe.identitydiag;
import android.os.Bundle;
import android.net.Uri;
import androidx.media3.common.*;
import androidx.media3.session.MediaController;
import java.util.*;

/** Passive public-session field inventory. Never logs raw URI, raw extra value,
 * signed URLs, tokens, or anything that could be mistaken for verified track ID.
 * Numeric candidates are diagnostic only; the existing album/edition safety
 * gate remains the sole authority until the phone supplies corroboration. */
final class Media3IdentityInventory {
 private Media3IdentityInventory(){}
 static Map<String,Object> extras(Bundle b){
  Map<String,Object> summary=new LinkedHashMap<>();
  if(b==null){summary.put("present",false);return summary;}
  summary.put("present",true);
  ArrayList<String> fields=new ArrayList<>(),numericCandidates=new ArrayList<>();
  try {
   ArrayList<String> names=new ArrayList<>(b.keySet());Collections.sort(names);
   for(String key:names){
    if(fields.size()>=24)break;
    if(key==null||!key.matches("[A-Za-z0-9_.-]{1,80}"))continue;
    Object value;
    try{value=b.get(key);}catch(RuntimeException unreadable){fields.add(key+":unreadable");continue;}
    String type=value==null?"null":value.getClass().getSimpleName();
    fields.add(key+":"+type);
    if(key.toLowerCase(Locale.ROOT).matches(".*(track[_\\.-]?id|music[_\\.-]?id).*")
       &&value!=null){
     String id=String.valueOf(value);
     if(id.matches("[1-9][0-9]{5,15}"))numericCandidates.add(key+"="+id);
    }
   }
  }catch(RuntimeException bad){summary.put("unreadable",true);}
  summary.put("keysAndTypes",fields);
  summary.put("unverifiedNumericCandidateFields",numericCandidates);
  return summary;
 }
 static String uriKind(Uri u){return u==null?"absent":(u.getScheme()==null?"no_scheme":u.getScheme());}
 static void capture(MediaController c,MediaItem item,String scope){
  if(!LogStore.active||item==null)return;
  try{
   MediaMetadata m=item.mediaMetadata;
   MediaItem.RequestMetadata r=item.requestMetadata;
   boolean local=item.localConfiguration!=null;
   Map<String,Object> evidence=LogStore.map(
    "scope",scope,"mediaAlias",item.mediaId,
    "mediaIdIsVerifiedYandexTrackId",false,
    "mediaMetadataExtras",extras(m==null?null:m.extras),
    "requestMetadataExtras",extras(r==null?null:r.extras),
    "requestMediaUriScheme",r==null?"absent":uriKind(r.mediaUri),
    "localConfigurationPresent",local,
    "localUriScheme",local?uriKind(item.localConfiguration.uri):"absent",
    "sourcePositionIsInterpolated",true,
    "fieldCollectionReadOnly",true
   );
   if(c!=null&&c.isConnected()){
    evidence.put("sessionExtras",extras(c.getSessionExtras()));
    evidence.put("playerCanReadTimeline",c.isCommandAvailable(Player.COMMAND_GET_TIMELINE));
    evidence.put("playerCanReadCurrentItem",c.isCommandAvailable(Player.COMMAND_GET_CURRENT_MEDIA_ITEM));
    if(c.isCommandAvailable(Player.COMMAND_GET_TIMELINE)){
     Timeline timeline=c.getCurrentTimeline();int index=c.getCurrentMediaItemIndex();
     if(index>=0&&index<timeline.getWindowCount()){
      Timeline.Window window=new Timeline.Window();timeline.getWindow(index,window);
      evidence.put("windowPlaceholder",window.isPlaceholder);
      evidence.put("windowHasMediaItem",window.mediaItem!=null);
      evidence.put("windowItemAlias",window.mediaItem==null?null:window.mediaItem.mediaId);
      evidence.put("windowDurationMs",window.getDurationMs());
     }
    }
   }
   LogStore.log("media3_identity_fields_readonly",evidence);
  }catch(RuntimeException e){LogStore.log("media3_identity_fields_unavailable",
    LogStore.map("scope",scope,"errorType",e.getClass().getSimpleName(),"commandsSent",false));}
 }
}
