namespace Celikom.Companion.Core;

/// <summary>
/// An isolated source-decision contract, NOT a hook, player, decoder or installer.
/// It may only select a prevalidated source for the exact current Yandex track.
/// </summary>
public sealed record SourceTicket(
    string TrackId,
    Uri AudioUrl,
    DateTimeOffset ExpiresAt,
    bool Approved,
    bool Entitled,
    bool DurationMatched,
    bool AudioValidated);

public sealed record SourceChoice(bool UseReplacement, Uri? Url);

public sealed class SourceSwapGate
{
    private readonly Uri _apiOrigin;
    private string? _currentTrack;
    private long _generation;
    private bool _enabled;
    private bool _preferOriginal;

    public SourceSwapGate(Uri apiOrigin)
    {
        if (apiOrigin.Scheme != Uri.UriSchemeHttps || !apiOrigin.IsAbsoluteUri ||
            !string.IsNullOrEmpty(apiOrigin.UserInfo) || apiOrigin.AbsolutePath != "/" ||
            !string.IsNullOrEmpty(apiOrigin.Query) || !string.IsNullOrEmpty(apiOrigin.Fragment))
            throw new ArgumentException("Expected HTTPS origin only.", nameof(apiOrigin));
        _apiOrigin = apiOrigin;
    }

    public long StartTrack(string exactYandexId)
    {
        if (string.IsNullOrWhiteSpace(exactYandexId))
            throw new ArgumentException("An exact track ID is required.", nameof(exactYandexId));
        _currentTrack = exactYandexId;
        _preferOriginal = false;
        return ++_generation;
    }

    public void Enable() { _enabled = true; ++_generation; }
    public void Stop() { _enabled = false; ++_generation; }
    public void Original() { _preferOriginal = true; ++_generation; }

    public long CurrentGeneration => _generation;

    public SourceChoice Choose(long capturedGeneration, SourceTicket? ticket, DateTimeOffset now)
    {
        if (!_enabled || _preferOriginal || capturedGeneration != _generation ||
            _currentTrack is null || ticket is null ||
            !string.Equals(ticket.TrackId, _currentTrack, StringComparison.Ordinal) ||
            !ticket.Approved || !ticket.Entitled || !ticket.DurationMatched ||
            !ticket.AudioValidated || ticket.ExpiresAt <= now.AddSeconds(30))
            return new(false, null);

        Uri url = ticket.AudioUrl;
        if (!url.IsAbsoluteUri || url.Scheme != Uri.UriSchemeHttps ||
            !string.IsNullOrEmpty(url.UserInfo) ||
            url.Host != _apiOrigin.Host || url.Port != _apiOrigin.Port ||
            !url.AbsolutePath.StartsWith("/api/v1/audio/", StringComparison.Ordinal))
            return new(false, null);
        return new(true, url);
    }
}
