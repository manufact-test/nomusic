package pro.celikom.nativeprobe.identitydiag;
import android.app.job.JobParameters;
import android.app.job.JobService;
public final class UpdateCheckJob extends JobService {
 public boolean onStartJob(JobParameters params) {
  UpdateCenter.IO.execute(()->{
   try {UpdateCenter.Release r=UpdateCenter.fetch(getApplicationContext());if(r!=null)UpdateCenter.notifyAvailable(getApplicationContext(),r);}
   catch(Exception ignored) { /* Network failure cannot affect playback. */ }
   finally {jobFinished(params,false);}
  });
  return true;
 }
 public boolean onStopJob(JobParameters params){return true;}
}
