package pro.celikom.nativeprobe.identitydiag;
public class TestPresencePreview {
 static int checks;static void check(boolean ok){checks++;if(!ok)throw new AssertionError("preview check "+checks);}
 public static void main(String[] args){PresencePreview p=new PresencePreview();p.put("song","pending",7,1000);check("pending".equals(p.get("song",7,1001)));check(p.get("other",7,1001).isEmpty());check(p.get("song",8,1001).isEmpty());check(p.get("song",7,301000).isEmpty());check(p.get("song",7,999).isEmpty());p.put("song","none",7,2000);check("none".equals(p.get("song",7,2001)));p.put("song","unknown",7,2002);check("none".equals(p.get("song",7,2003)));for(int i=0;i<100;i++)p.put("id"+i,"approved",7,3000+i);check(p.entries.size()<=32);p.clear();check(p.entries.isEmpty());System.out.println("PASS: "+checks+" account/song-scoped presentation preview checks");}
}
