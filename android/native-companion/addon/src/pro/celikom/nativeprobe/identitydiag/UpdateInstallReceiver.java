package pro.celikom.nativeprobe.identitydiag;
import android.app.*;
import android.content.*;
import android.content.pm.PackageInstaller;
public final class UpdateInstallReceiver extends BroadcastReceiver {
 @Override public void onReceive(Context context,Intent result){
  int status=result.getIntExtra(PackageInstaller.EXTRA_STATUS,PackageInstaller.STATUS_FAILURE);
  if(status==PackageInstaller.STATUS_PENDING_USER_ACTION){
   Intent confirmation=result.getParcelableExtra(Intent.EXTRA_INTENT);
   if(confirmation!=null){confirmation.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);context.startActivity(confirmation);}
  } else if(status==PackageInstaller.STATUS_SUCCESS){
   /* Android replaces this process on successful installation. Verify on next launch. */
  } else {
   android.util.Log.w("CELIKOM.Update","System installer returned status "+status);
  }
 }
}
