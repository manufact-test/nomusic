package pro.celikom.nativeprobe.identitydiag;

import android.app.ActivityManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageInstaller;
import android.os.Build;
import android.util.Log;
import java.util.List;

/**
 * Handles the Android PackageInstaller result.
 *
 * A successful in-place update intentionally leaves CELIKOM closed and removes
 * its tasks from Recents. The owner can launch the newly installed version
 * manually. Cancellation/failure leaves the existing task alone.
 */
public final class UpdateInstallReceiver extends BroadcastReceiver {
    private static final String TAG = "CELIKOM.Update";

    @Override public void onReceive(Context context, Intent result) {
        int status = result.getIntExtra(
            PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE
        );

        if (status == PackageInstaller.STATUS_PENDING_USER_ACTION) {
            Intent confirmation = result.getParcelableExtra(Intent.EXTRA_INTENT);
            if (confirmation != null) {
                confirmation.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                context.startActivity(confirmation);
            }
        } else if (status == PackageInstaller.STATUS_SUCCESS) {
            int expectedCode = result.getIntExtra("expectedCode", -1);
            closeTasksAfterVerifiedInstall(context, expectedCode);
        } else {
            Log.w(TAG, "System installer returned status " + status);
        }
    }

    private static void closeTasksAfterVerifiedInstall(Context context, int expectedCode) {
        if (expectedCode <= 0 || installedVersionCode(context) < expectedCode) {
            Log.w(TAG, "Update callback received, but expected version is not installed; keeping task");
            return;
        }

        ActivityManager manager =
            (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
        if (manager == null) {
            Log.w(TAG, "ActivityManager unavailable; cannot remove CELIKOM task");
            return;
        }

        try {
            List<ActivityManager.AppTask> tasks = manager.getAppTasks();
            for (ActivityManager.AppTask task : tasks) {
                try {
                    task.finishAndRemoveTask();
                } catch (RuntimeException error) {
                    Log.w(TAG, "Could not remove one CELIKOM recent task", error);
                }
            }
        } catch (RuntimeException error) {
            Log.w(TAG, "Could not enumerate CELIKOM recent tasks", error);
        }
    }

    private static long installedVersionCode(Context context) {
        try {
            PackageInfo info = context.getPackageManager().getPackageInfo(
                context.getPackageName(), 0
            );
            return Build.VERSION.SDK_INT >= 28
                ? info.getLongVersionCode()
                : info.versionCode;
        } catch (Exception error) {
            Log.w(TAG, "Could not verify installed CELIKOM version", error);
            return -1L;
        }
    }
}
