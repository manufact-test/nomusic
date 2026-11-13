namespace Celikom.Companion;

/// <summary>
/// Rate limits client-triggered Yandex compatibility feed refresh after a
/// native host/start failure. Does not change playback or trust policy.
/// </summary>
public sealed class YandexFailureRecheckGate
{
    private DateTimeOffset _nextAllowed = DateTimeOffset.MinValue;
    private bool _running;
    private int _consecutiveTriggers;

    public static bool IsNativeHandshakePresent(string? status) =>
        status is "ORIGINAL" or "NATIVE_CONNECTED" or "NATIVE_MAPPING_ACCEPTED" or
            "NATIVE_SOURCE_VERIFIED" or "NATIVE_RECOVERING" or "NATIVE_SOURCE_FAILED";

    public static bool IsNativeHostFailure(string? status) =>
        string.Equals(status, "HOST_ERROR", StringComparison.Ordinal);

    public static bool IsMissingStartupHandshake(string? status) =>
        status is "NOT_CONNECTED" or "UNAVAILABLE" or "HOST_ERROR";

    public bool TryStart(DateTimeOffset now)
    {
        if (_running || now < _nextAllowed) return false;
        _running = true;
        // Repeated native failures back off 2, 4, 8 then 15 minutes.
        _consecutiveTriggers = Math.Min(4, _consecutiveTriggers + 1);
        _nextAllowed = now.AddMinutes(Math.Min(15, 1 << _consecutiveTriggers));
        return true;
    }

    public void ConfirmNativeHealthy()
    {
        if (_running) return;
        _consecutiveTriggers = 0;
        _nextAllowed = DateTimeOffset.MinValue;
    }

    public void Finish() => _running = false;
}
