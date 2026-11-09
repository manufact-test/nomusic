namespace Celikom.Companion;

/// <summary>
/// Ephemeral same-user capability for an explicitly installed native Yandex
/// integration. The Yandex main process can read this narrow bridge token,
/// never CELIKOM access/refresh tokens or the Yandex user profile.
/// The capability exists ONLY while Companion is running.
/// </summary>
public sealed class NativeTokenPublisher : IDisposable
{
    private readonly string _folder;
    private readonly string _path;
    private string _published = "";
    private bool _disposed;

    public NativeTokenPublisher(string? folder = null)
    {
        _folder = folder ?? Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "CELIKOM", "Windows");
        _path = Path.Combine(_folder, "native-bridge.key");
    }

    public string FilePath => _path;

    public void Publish(string token)
    {
        if (_disposed) throw new ObjectDisposedException(nameof(NativeTokenPublisher));
        if (!SessionStore.IsHexToken(token)) throw new ArgumentException("Invalid capability.");
        if (_published == token && File.Exists(_path)) return;
        Directory.CreateDirectory(_folder);
        var temp = Path.Combine(_folder, ".native-bridge-" + Guid.NewGuid().ToString("N"));
        try
        {
            File.WriteAllText(temp, token);
            File.Move(temp, _path, true);
            _published = token;
        }
        finally
        {
            if (File.Exists(temp)) File.Delete(temp);
        }
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        // Never delete a capability published by a newly started other instance.
        try
        {
            if (File.Exists(_path) && File.ReadAllText(_path) == _published)
                File.Delete(_path);
        }
        catch (IOException) { }
        catch (UnauthorizedAccessException) { }
    }
}
