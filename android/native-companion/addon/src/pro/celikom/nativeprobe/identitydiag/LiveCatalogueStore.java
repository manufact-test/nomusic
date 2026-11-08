package pro.celikom.nativeprobe.identitydiag;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;

/**
 * Validated, atomic, on-device metadata-only cache for approved replacements.
 * Never contains private audio, account credentials or playback authorization.
 */
final class LiveCatalogueStore {
 static final int MAX_ROWS=5000,MAX_BYTES=2000000;
 static final long MAX_CACHE_AGE_MS=7L*86400000L;
 private LiveCatalogueStore(){}

 static JSONObject validate(JSONObject data,long nowMs) throws JSONException {
  if(data==null||data.optInt("schema",-1)!=1
    ||!"celikom_owner_catalog_snapshot".equals(data.optString("source"))
    ||!data.optBoolean("complete",false))throw new JSONException("invalid_catalogue_contract");
  long generated=data.optLong("generated_at_ms",0);
  if(generated<=0||generated>nowMs+10*60000L||nowMs-generated>MAX_CACHE_AGE_MS)
   throw new JSONException("stale_catalogue");
  JSONArray entries=data.optJSONArray("tracks");
  int count=data.optInt("total_tracks",-1);
  if(entries==null||count<0||count>MAX_ROWS||entries.length()!=count)
   throw new JSONException("incomplete_catalogue");
  Set<String> ids=new HashSet<>();
  for(int i=0;i<count;i++){
   JSONObject row=entries.optJSONObject(i);
   if(row==null)throw new JSONException("invalid_catalogue_row");
   String id=row.optString("track_id","");
   String title=row.optString("title","").trim(),artist=row.optString("artist","").trim();
   long duration=row.optLong("duration_ms",-1);
   if(!id.matches("[1-9][0-9]{0,19}")||!ids.add(id)
     ||title.isEmpty()||title.length()>512
     ||artist.isEmpty()||artist.length()>512
     ||duration<1000||duration>36000000
     ||!row.optBoolean("replacement_available",false))
    throw new JSONException("invalid_catalogue_row");
  }
  if(data.toString().getBytes(StandardCharsets.UTF_8).length>MAX_BYTES)
   throw new JSONException("catalogue_too_large");
  return data;
 }

 static JSONObject load(File file,long nowMs){
  if(!file.isFile()||file.length()<2||file.length()>MAX_BYTES)return null;
  try(InputStream in=new FileInputStream(file);ByteArrayOutputStream bytes=new ByteArrayOutputStream()){
   byte[] buffer=new byte[8192];int n;
   while((n=in.read(buffer))!=-1){
    if(bytes.size()+n>MAX_BYTES)return null;
    bytes.write(buffer,0,n);
   }
   return validate(new JSONObject(new String(bytes.toByteArray(),StandardCharsets.UTF_8)),nowMs);
  }catch(Exception ignored){return null;}
 }

 static boolean save(File destination,JSONObject data){
  File temporary=new File(destination.getParentFile(),destination.getName()+".tmp");
  try{
   byte[] bytes=data.toString().getBytes(StandardCharsets.UTF_8);
   if(bytes.length>MAX_BYTES)return false;
   try(FileOutputStream out=new FileOutputStream(temporary)){
    out.write(bytes);out.flush();out.getFD().sync();
   }
   if(!temporary.renameTo(destination))return false;
   return true;
  }catch(Exception ignored){return false;}
  finally{if(temporary.exists())temporary.delete();}
 }
}
