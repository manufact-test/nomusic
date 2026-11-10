package pro.celikom.ownedplayer;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import org.json.JSONObject;
import java.security.KeyStore;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Own CELIKOM tokens ONLY; never accepts or stores a Yandex account token. */
final class OwnedSessionStore {
    private static final String KEY="celikom.owned.session.v1";
    private final SharedPreferences prefs;
    private JSONObject cached;
    private boolean loaded;
    private long accountEpoch;
    OwnedSessionStore(Context context){
        prefs=context.getApplicationContext().getSharedPreferences("owned-account",Context.MODE_PRIVATE);
    }
    synchronized String installation(){
        String id=prefs.getString("install",null);
        if(id==null){
            id=UUID.randomUUID().toString();
            if(!prefs.edit().putString("install",id).commit())
                throw new IllegalStateException("install_persist_failed");
        }
        return id;
    }
    private SecretKey key()throws Exception{
        KeyStore store=KeyStore.getInstance("AndroidKeyStore");store.load(null);
        if(store.containsAlias(KEY))return (SecretKey)store.getKey(KEY,null);
        KeyGenerator gen=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
        gen.init(new KeyGenParameterSpec.Builder(KEY,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());
        return gen.generateKey();
    }
    synchronized JSONObject current(){
        if(loaded)return cached;
        loaded=true;
        try {
            String data=prefs.getString("secret",null);
            if(data==null)return null;
            byte[] bytes=Base64.decode(data,Base64.NO_WRAP);
            if(bytes.length<29||bytes.length>8192)throw new Exception("session_size");
            Cipher c=Cipher.getInstance("AES/GCM/NoPadding");
            c.init(Cipher.DECRYPT_MODE,key(),new GCMParameterSpec(128,bytes,0,12));
            JSONObject j=new JSONObject(new String(c.doFinal(bytes,12,bytes.length-12),StandardCharsets.UTF_8));
            if(!valid(j))throw new Exception("session_invalid");
            return cached=j;
        }catch(Exception ignored){
            prefs.edit().remove("secret").commit();
            return cached=null;
        }
    }
    private static boolean valid(JSONObject j){
        return j!=null && j.optString("access_token").matches("[0-9a-f]{64}")
                &&j.optString("refresh_token").matches("[0-9a-f]{64}");
    }
    synchronized long epoch(){return accountEpoch;}
    synchronized void save(JSONObject json,boolean newAccount)throws Exception{
        if(!valid(json))throw new Exception("invalid_celikom_session");
        long ttl=Math.max(1,Math.min(900,json.optLong("expires_in",900)));
        json.put("_access_until_ms",System.currentTimeMillis()+ttl*1000L);
        byte[] data=json.toString().getBytes(StandardCharsets.UTF_8);
        if(data.length>8000)throw new Exception("session_too_large");
        Cipher c=Cipher.getInstance("AES/GCM/NoPadding");
        c.init(Cipher.ENCRYPT_MODE,key());
        byte[] iv=c.getIV(),ciphertext=c.doFinal(data);
        byte[] combined=new byte[iv.length+ciphertext.length];
        System.arraycopy(iv,0,combined,0,iv.length);
        System.arraycopy(ciphertext,0,combined,iv.length,ciphertext.length);
        if(!prefs.edit().putString("secret",Base64.encodeToString(combined,Base64.NO_WRAP)).commit())
            throw new Exception("session_persist_failed");
        cached=json;loaded=true;
        if(newAccount)accountEpoch++;
    }
    synchronized void clear(){
        prefs.edit().remove("secret").commit();
        cached=null;loaded=true;accountEpoch++;
    }
}
