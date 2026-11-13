namespace Celikom.Companion;

/// <summary>
/// Rate limits client-triggered Yandex compatibility feed refresh after a
/// native host/start failure. Does not change playback or trust policy.
/// </summary>
public sealed class YandexFailureRecheckGate
{
    private DateTimeOffset _nextAllowed = DateTimeOffset.MinValue;
    private bool _running;

    public static bool IsNativeHostFailure(string? status) =>
        string.Equals(status, "HOST_ERROR", StringComparison.Ordinal);

    public static bool IsMissingStartupHandshake(string? status) =>
        status is "NOT_CONNECTED" or "UNAVAILABLE" or "HOST_ERROR";

    public bool TryStart(DateTimeOffset now)
    {
        if (_running || now < _nextAllowed) return false;
        _running = true;
        _nextAllowed = now.AddMinutes(2);
        return true;
    }

    public void Finish() => _running = false;
}
