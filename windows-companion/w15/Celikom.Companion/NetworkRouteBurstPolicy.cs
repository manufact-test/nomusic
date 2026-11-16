namespace Celikom.Companion;

/// <summary>
/// A VPN switch can emit delayed address notifications while Windows settles
/// several adapters. Keep one native source-hold marker across that burst,
/// while the last notification still owns the entitlement recheck.
/// </summary>
public static class NetworkRouteBurstPolicy
{
    public static readonly TimeSpan RouteBurstWindow = TimeSpan.FromSeconds(8);
    public static readonly TimeSpan RecheckQuietPeriod = TimeSpan.FromSeconds(3);

    public static int NextEpoch(int previous) =>
        previous == int.MaxValue ? 1 : previous + 1;

    public static bool Latest(int scheduledEpoch, int currentEpoch) =>
        scheduledEpoch == currentEpoch;

    public static bool SameBurst(DateTimeOffset now, DateTimeOffset previousRouteAt) =>
        previousRouteAt != DateTimeOffset.MinValue && now >= previousRouteAt &&
        now - previousRouteAt < RouteBurstWindow;

    public static bool LogDue(DateTimeOffset now, DateTimeOffset previousLoggedAt) =>
        previousLoggedAt == DateTimeOffset.MinValue ||
        now - previousLoggedAt >= TimeSpan.FromMilliseconds(1400);
}
