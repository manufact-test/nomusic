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
   /* The installed package can receive this post-replacement callback. Do not
      clear Recents for an unrelated or unverified install result. Android
      already replaces the running process; users restart CELIKOM manually. */
   int expected=result.getIntExtra("expectedCode",-1);
   int actual=UpdateCenter.installed(context);
   if(!UpdateInstallPolicy.shouldRemoveRecents(true,expected,actual)){
    android.util.Log.w("CELIKOM.Update","Ignoring success without matching installed version");
    return;
   }
   try {
    ActivityManager am=(ActivityManager)context.getSystemService(Context.ACTIVITY_SERVICE);
    if(am!=null)for(ActivityManager.AppTask task:am.getAppTasks()){
     task.finishAndRemoveTask();
    }
   }catch(RuntimeException e){
    android.util.Log.w("CELIKOM.Update","Installed, but Android denied task cleanup",e);
   }
  } else {
   android.util.Log.w("CELIKOM.Update","System installer returned status "+status);
  }
 }
}
