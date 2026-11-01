package pro.celikom.nativeprobe.identitydiag;
import android.app.job.JobParameters;
import android.app.job.JobService;
public final class UpdateCheckJob extends JobService {
 public boolean onStartJob(JobParameters params) {
  UpdateCenter.IO.execute(()->{
   try {
    android.content.Context context=getApplicationContext();
    UpdateCenter.Release r=UpdateCenter.fetch(context);
    UpdateCenter.recordSuccessfulCheck(context,r);
    if(r!=null)UpdateCenter.notifyAvailable(context,r);
   }
   catch(Exception ignored) { /* Network failure cannot affect playback. */ }
   finally {jobFinished(params,false);}
  });
  return true;
 }
 public boolean onStopJob(JobParameters params){return true;}
}
