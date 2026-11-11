using System.Net;
using System.Text.Json;

namespace Celikom.Companion;

/// <summary>
/// A failed network entitlement preview never grants music access. Retry only
/// transport/temporary server failures, suspend when unavailable, resume only
/// after a NEW, explicitly allowed server entitlement for the SAME session.
/// </summary>
public static class EntitlementCheckRecovery
{
    public static bool IsTransient(Exception exception) =>
        exception is HttpRequestException or TaskCanceledException or TimeoutException ||
        exception is ApiFailure failure &&
        (failure.HttpStatus == (int)HttpStatusCode.TooManyRequests ||
         failure.HttpStatus is >= 500 and <= 599);

    public static bool MayResume(bool pendingRecovery, bool loggedIn,
        bool nativeModuleActive, bool nativeModuleMatchesApplication,
        JsonElement freshEntitlement, DateTimeOffset now) =>
        pendingRecovery && loggedIn && nativeModuleActive &&
        nativeModuleMatchesApplication &&
        PlaybackEntitlement.Allowed(freshEntitlement, now);
}
