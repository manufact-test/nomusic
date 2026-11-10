package pro.celikom.nativegate;

import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;

/**
 * Optional platform-granted session-token access only.
 * This service deliberately NEVER reads, stores or relays notifications.
 * No event handling, no network, no disk, no background audio commands.
 */
public final class NativeSessionListener extends NotificationListenerService {
    @Override public void onNotificationPosted(StatusBarNotification ignored) {
        // Intentionally empty. Notification contents are neither parsed nor used.
    }
    @Override public void onNotificationRemoved(StatusBarNotification ignored) {
        // Intentionally empty.
    }
}
