package pro.celikom.nativeprobe.identitydiag;

import java.util.Objects;

/**
 * Test.72: prevents Media3 cross-item snapshots from authorizing a wrong
 * replacement. Yandex can briefly publish old item metadata together with
 * another item's duration while the UI already moved to that next song.
 *
 * No audio or transport commands, no timers, no second controller.
 * This protects identity only; it cannot verify which PCM Yandex produces.
 */
final class SourceSnapshotConsistency {
 static final long MAX_DURATION_DIFFERENCE_MS = 4000L;

 enum Status { ACCEPT, CONFLICT, HOLD, RECOVERED }
 static final class Verdict {
  final Status status;
  final String reason;
  final long previousDurationMs;
  final boolean usedMetadataDuration;
  Verdict(Status status,String reason,long previous,boolean metadata){
   this.status=status;this.reason=reason;previousDurationMs=previous;
   usedMetadataDuration=metadata;
  }
  boolean allowed(){return status==Status.ACCEPT||status==Status.RECOVERED;}
  boolean firstConflict(){return status==Status.CONFLICT;}
 }
 private String acceptedIdentity,blockedIdentity;
 private long acceptedDuration=-1L;
 private boolean blocked,requireNewIdentity;
 private static String identity(String alias,String title,String artist,String cover){
  return String.valueOf(alias)+"\u001f"+String.valueOf(title)+"\u001f"
   +String.valueOf(artist)+"\u001f"+String.valueOf(cover);
 }
 static boolean validMetadataDuration(long duration){
  // Only millisecond-scale track lengths qualify. Unknown extras are ignored.
  return duration>=10000L&&duration<=28800000L;
 }
 static boolean mismatched(long a,long b){
  return a>0&&b>0&&Math.abs(a-b)>MAX_DURATION_DIFFERENCE_MS;
 }
 Verdict observe(String alias,String title,String artist,String cover,
                 long controllerDurationMs,long metadataDurationMs){
  if(alias==null||alias.isEmpty()||title==null||title.trim().isEmpty()
      ||controllerDurationMs<=0)
   return new Verdict(Status.HOLD,"incomplete_current_item",acceptedDuration,false);
  String key=identity(alias,title,artist,cover);
  boolean metadataProvided=validMetadataDuration(metadataDurationMs);
  boolean disagreesWithMetadata=metadataProvided&&mismatched(controllerDurationMs,metadataDurationMs);
  boolean sameAccepted=Objects.equals(acceptedIdentity,key);
  boolean disagreesWithAccepted=sameAccepted&&mismatched(controllerDurationMs,acceptedDuration);
  if(blocked){
   // An old media item with a new duration cannot become trusted again just
   // because the duration flips back: Yandex's UI may already show another item.
   if(requireNewIdentity&&Objects.equals(blockedIdentity,key))
    return new Verdict(Status.HOLD,"stale_item_wait_new_identity",acceptedDuration,metadataProvided);
   if(disagreesWithMetadata)
    return new Verdict(Status.HOLD,"duration_metadata_conflict",acceptedDuration,metadataProvided);
   // For an unanchored *new* item, a fully coherent future sample is sufficient.
   // For a known-old item, require a different media item identity.
   blocked=false;requireNewIdentity=false;blockedIdentity=null;
   acceptedIdentity=key;acceptedDuration=controllerDurationMs;
   return new Verdict(Status.RECOVERED,"coherent_new_item",acceptedDuration,metadataProvided);
  }
  if(disagreesWithAccepted||disagreesWithMetadata){
   blocked=true;blockedIdentity=key;
   requireNewIdentity=sameAccepted; // a verified old alias requires item turnover
   return new Verdict(Status.CONFLICT,
     disagreesWithAccepted?"unchanged_item_changed_duration":"item_vs_metadata_duration",
     acceptedDuration,metadataProvided);
  }
  if(!sameAccepted){
   acceptedIdentity=key;
   acceptedDuration=controllerDurationMs;
  }
  return new Verdict(Status.ACCEPT,"coherent",acceptedDuration,metadataProvided);
 }
 void clear(){
  acceptedIdentity=null;blockedIdentity=null;acceptedDuration=-1L;
  blocked=false;requireNewIdentity=false;
 }
}
