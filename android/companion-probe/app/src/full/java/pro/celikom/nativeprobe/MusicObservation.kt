package pro.celikom.nativeprobe
import android.content.Context
import android.content.ComponentName
import android.service.notification.NotificationListenerService
import androidx.core.app.NotificationManagerCompat
object MusicObservation {
    fun access(c: Context): Boolean = NotificationManagerCompat.getEnabledListenerPackages(c).contains(c.packageName)
    fun rebind(c: Context) = NotificationListenerService.requestRebind(ComponentName(c, MusicListener::class.java))
}
