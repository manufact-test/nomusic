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
         failure.HttpStatus is >= 500 and <= 599 ||
         // Captive portals/VPN gateways sometimes return HTML or redirect
         // instead of the CELIKOM JSON contract. Never authorize from it,
         // but recheck automatically after the route becomes healthy again.
         failure.Category is "INVALID_API_JSON" or "REDIRECT_FORBIDDEN");

    public static string FailureCode(Exception failure) => failure switch
    {
        ApiFailure { HttpStatus: 401 } => "ACTIVE_ENTITLEMENT_DENIED_401",
        ApiFailure { HttpStatus: 403 } => "ACTIVE_ENTITLEMENT_DENIED_403",
        ApiFailure { HttpStatus: 429 } => "ACTIVE_ENTITLEMENT_RATE_LIMITED",
        ApiFailure { HttpStatus: >= 500 and <= 599 } => "ACTIVE_ENTITLEMENT_SERVER_ERROR",
        ApiFailure { Category: "INVALID_API_JSON" } => "ACTIVE_ENTITLEMENT_BAD_RESPONSE",
        ApiFailure { Category: "REDIRECT_FORBIDDEN" } => "ACTIVE_ENTITLEMENT_ROUTE_REDIRECT",
        TaskCanceledException => "ACTIVE_ENTITLEMENT_TIMEOUT",
        TimeoutException => "ACTIVE_ENTITLEMENT_TIMEOUT",
        HttpRequestException => "ACTIVE_ENTITLEMENT_NETWORK_ERROR",
        _ => "ACTIVE_ENTITLEMENT_UNKNOWN_FAILURE"
    };

    public static bool MayResume(bool pendingRecovery, bool loggedIn,
        bool nativeModuleActive, bool nativeModuleMatchesApplication,
        JsonElement freshEntitlement, DateTimeOffset now) =>
        pendingRecovery && loggedIn && nativeModuleActive &&
        nativeModuleMatchesApplication &&
        PlaybackEntitlement.Allowed(freshEntitlement, now);
}
