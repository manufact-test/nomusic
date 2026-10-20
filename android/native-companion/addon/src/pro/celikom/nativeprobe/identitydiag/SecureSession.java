package pro.celikom.nativeprobe.identitydiag;
import android.content.*;
import android.security.keystore.*;
import android.util.Base64;
import org.json.*;
import java.security.*;
import javax.crypto.*;
import javax.crypto.spec.GCMParameterSpec;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
/** App-private encrypted session; passwords are never persisted. */
final class SecureSession {
 JSONObject cached;final Context context;static final String ALIAS="celikom.native.session.v1";
 SecureSession(Context c){context=c.getApplicationContext();}
 String installation(){SharedPreferences p=context.getSharedPreferences("native-session",0);String id=p.getString("installation","");if(id.isEmpty()){id=UUID.randomUUID().toString();p.edit().putString("installation",id).commit();}return id;}
 javax.crypto.SecretKey key()throws Exception {KeyStore k=KeyStore.getInstance("AndroidKeyStore");k.load(null);if(!k.containsAlias(ALIAS)){KeyGenerator g=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");g.init(new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());g.generateKey();}return (javax.crypto.SecretKey)k.getKey(ALIAS,null);}
 synchronized JSONObject read(){if(cached!=null)return cached;try{String s=context.getSharedPreferences("native-session",0).getString("encrypted","");if(s.isEmpty())return cached=new JSONObject();String[] a=s.split(":");Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.DECRYPT_MODE,key(),new GCMParameterSpec(128,Base64.decode(a[0],Base64.NO_WRAP)));return cached=new JSONObject(new String(c.doFinal(Base64.decode(a[1],Base64.NO_WRAP)),StandardCharsets.UTF_8));}catch(Exception e){return cached=new JSONObject();}}
 synchronized void save(JSONObject j)throws Exception {if(!j.optString("access_token").matches("[a-f0-9]{64}")||!j.optString("refresh_token").matches("[a-f0-9]{64}"))throw new Exception("invalid_session_response");j.put("access_until_ms",System.currentTimeMillis()+Math.min(900,j.optInt("expires_in",900))*1000L);Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.ENCRYPT_MODE,key());String s=Base64.encodeToString(c.getIV(),Base64.NO_WRAP)+":"+Base64.encodeToString(c.doFinal(j.toString().getBytes(StandardCharsets.UTF_8)),Base64.NO_WRAP);if(!context.getSharedPreferences("native-session",0).edit().putString("encrypted",s).commit())throw new Exception("session_storage_failed");cached=j;}
 synchronized void clear(){cached=new JSONObject();context.getSharedPreferences("native-session",0).edit().remove("encrypted").commit();}
}
