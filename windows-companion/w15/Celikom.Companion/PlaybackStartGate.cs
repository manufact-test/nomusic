namespace Celikom.Companion;

/// <summary>
/// Keeps the Start button and its event handler on the same eligibility rule.
/// In particular, a pending first connection must not accept duplicate clicks.
/// </summary>
public static class PlaybackStartGate
{
    public static bool CanAcceptStart(
        bool bridgeStarted,
        bool integrationBusy,
        bool updatingApplication,
        bool compactStarting,
        bool switchAvailable,
        bool bridgeEnabled,
        bool closing) =>
        bridgeStarted &&
        !integrationBusy &&
        !updatingApplication &&
        !compactStarting &&
        !closing &&
        (!switchAvailable || !bridgeEnabled);
}
