namespace Celikom.Companion;

/// <summary>
/// Every Windows network signal invalidates a prior scheduled VPN check.
/// The 1.4s coalesce window only limits diagnostic logging; it must NEVER
/// drop the last VPN route change. No entitlement is granted by a signal.
/// </summary>
public static class NetworkRouteBurstPolicy
{
    public static int NextEpoch(int previous) =>
        previous == int.MaxValue ? 1 : previous + 1;

    public static bool Latest(int scheduledEpoch, int currentEpoch) =>
        scheduledEpoch == currentEpoch;

    public static bool LogDue(DateTimeOffset now, DateTimeOffset previousLoggedAt) =>
        previousLoggedAt == DateTimeOffset.MinValue ||
        now - previousLoggedAt >= TimeSpan.FromMilliseconds(1400);
}
