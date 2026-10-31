package pro.celikom.nativeprobe.identitydiag;
import org.json.JSONObject;
public class TestDiagnosticAccess {
 static int checks;static void check(boolean ok){checks++;if(!ok)throw new AssertionError("diagnostic rights check "+checks);}
 public static void main(String[] args)throws Exception{
  check(!DiagnosticAccess.user(null));check(!DiagnosticAccess.user(new JSONObject()));
  check(!DiagnosticAccess.user(new JSONObject("{\"user\":{\"id\":1,\"status\":\"active\",\"email\":\"ordinary@example.test\",\"role\":\"owner\",\"promo\":\"forever\"}}")));
  check(DiagnosticAccess.digest("18e9af33bc55e691582e0495d6f9024611649a3342742ec7569cd565e28af572"));
  check(DiagnosticAccess.digest("50bc7e488885f21b0af751f8e2ed3bc622d3bc097c6541817c9ef742cdf7777e"));check(!DiagnosticAccess.digest(""));
  check(DiagnosticAccess.lease(true,7,7,1000,2000));check(!DiagnosticAccess.lease(false,7,7,1000,2000));check(!DiagnosticAccess.lease(true,7,8,1000,2000));check(!DiagnosticAccess.lease(true,7,7,2000,2000));check(!DiagnosticAccess.lease(true,7,7,2001,2000));
  check(DiagnosticAccess.offlineIncidentHint(true,17,17));
  check(!DiagnosticAccess.offlineIncidentHint(false,17,17));
  check(!DiagnosticAccess.offlineIncidentHint(true,17,18));
  check(!DiagnosticAccess.offlineIncidentHint(true,0,17));
  check(!DiagnosticAccess.offlineIncidentHint(true,17,0));
  System.out.println("PASS: "+checks+" diagnostic identity, offline incident UI and expiry checks");
 }
}
