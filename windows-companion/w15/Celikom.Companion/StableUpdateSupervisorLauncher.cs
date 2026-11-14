using System.Diagnostics;
using System.IO.Pipes;
using System.Security.Cryptography;

namespace Celikom.Companion;

/// <summary>
/// Same-user, transaction-scoped readiness handshake between the GUI and the
/// independent rollback Supervisor. The helper signals only after it has read
/// and validated the DPAPI journal, production trust and its own signed image.
/// </summary>
public static class StableUpdateSupervisorHandshake
{
    private const byte ReadyMarker = 0xA7;
    private const string PipePrefix = "celikom-update-supervisor-ready-";

    public static string GetPipeName(Guid transaction)
    {
        if (transaction == Guid.Empty)
            throw new ArgumentException("Supervisor transaction is required.", nameof(transaction));
        return PipePrefix + transaction.ToString("N");
    }

    public static NamedPipeServerStream CreateServer(Guid transaction) =>
        new(GetPipeName(transaction), PipeDirection.In, 1,
            PipeTransmissionMode.Byte,
            PipeOptions.Asynchronous | PipeOptions.CurrentUserOnly,
            1, 1);

    public static async Task<bool> WaitForReadyAsync(
        NamedPipeServerStream server, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(server);
        await server.WaitForConnectionAsync(cancellationToken).ConfigureAwait(false);
        var marker = new byte[1];
        var read = await server.ReadAsync(marker.AsMemory(0, 1), cancellationToken)
            .ConfigureAwait(false);
        return read == 1 && marker[0] == ReadyMarker;
    }

    public static async Task<bool> SignalReadyAsync(
        Guid transaction, CancellationToken cancellationToken)
    {
        if (transaction == Guid.Empty) return false;
        await using var client = new NamedPipeClientStream(
            ".", GetPipeName(transaction), PipeDirection.Out, PipeOptions.Asynchronous);
        await client.ConnectAsync(5000, cancellationToken).ConfigureAwait(false);
        var marker = new[] { ReadyMarker };
        await client.WriteAsync(marker.AsMemory(), cancellationToken).ConfigureAwait(false);
        await client.FlushAsync(cancellationToken).ConfigureAwait(false);
        return true;
    }
}

/// <summary>
/// Launches the previously installed, signed Supervisor from the immutable
/// transaction snapshot so Inno Setup can replace the installed helper file.
/// The update installer must never run unless this process acknowledges READY.
/// </summary>
public static class StableUpdateSupervisorLauncher
{
    private const string SupervisorFileName = "CELIKOM.UpdateSupervisor.exe";

    public static async Task<bool> StartAsync(
        StableUpdateRollbackJournal.Record record,
        CancellationToken cancellationToken = default)
    {
        if (!OperatingSystem.IsWindows() ||
            !StableUpdateTrustConfiguration.TryGetProduction(out var trust) ||
            trust is null ||
            record.Schema != 2 || record.Id == Guid.Empty ||
            record.State != StableUpdateRollbackJournal.Phase.Prepared ||
            record.RollbackAttempts != 0 ||
            !ValidSha(record.PreviousSupervisorSha256) ||
            !ValidSha(record.TargetSupervisorSha256) ||
            !ValidSha(record.SignerSha256) ||
            !string.Equals(record.SignerSha256, trust.SignerCertificateSha256,
                StringComparison.OrdinalIgnoreCase))
            return false;

        Process? process = null;
        try
        {
            var local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            var installRoot = Path.Combine(local, "Programs", "CELIKOM");
            var installedSupervisor = Path.Combine(installRoot, SupervisorFileName);
            if (!StableUpdatePayloadVerifier.MatchesFile(
                    installedSupervisor, record.PreviousSupervisorSha256, 50_000_000))
                return false;

            var snapshotDirectory = StableUpdateRollbackJournal.GetSnapshotDirectory(
                StableUpdateRollbackJournal.DefaultPrivateRoot, record.Id);
            if (!Directory.Exists(snapshotDirectory) ||
                (File.GetAttributes(snapshotDirectory) & FileAttributes.ReparsePoint) != 0)
                return false;

            var snapshotSupervisor = Path.Combine(snapshotDirectory, SupervisorFileName);
            if (File.Exists(snapshotSupervisor))
            {
                if (!StableUpdatePayloadVerifier.MatchesFile(
                        snapshotSupervisor, record.PreviousSupervisorSha256, 50_000_000))
                    return false;
            }
            else
            {
                File.Copy(installedSupervisor, snapshotSupervisor, overwrite: false);
                if (!StableUpdatePayloadVerifier.MatchesFile(
                        snapshotSupervisor, record.PreviousSupervisorSha256, 50_000_000))
                    return false;
            }

            await using var server = StableUpdateSupervisorHandshake.CreateServer(record.Id);
            var startInfo = new ProcessStartInfo(snapshotSupervisor)
            {
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = snapshotDirectory
            };
            startInfo.ArgumentList.Add("--supervise");
            startInfo.ArgumentList.Add(record.Id.ToString("N"));
            process = Process.Start(startInfo);
            if (process is null) return false;

            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            timeout.CancelAfter(TimeSpan.FromSeconds(8));
            var ready = await StableUpdateSupervisorHandshake.WaitForReadyAsync(
                server, timeout.Token).ConfigureAwait(false);
            if (!ready || process.HasExited)
            {
                TryStop(process);
                return false;
            }
            return true;
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            if (process is not null) TryStop(process);
            return false;
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or
            System.ComponentModel.Win32Exception or InvalidOperationException or
            ArgumentException or NotSupportedException or CryptographicException)
        {
            if (process is not null) TryStop(process);
            return false;
        }
        catch
        {
            if (process is not null) TryStop(process);
            if (cancellationToken.IsCancellationRequested) throw;
            return false;
        }
        finally
        {
            process?.Dispose();
        }
    }

    private static bool ValidSha(string? value) =>
        value is { Length: 64 } && value.All(Uri.IsHexDigit);

    private static void TryStop(Process process)
    {
        try
        {
            if (!process.HasExited) process.Kill(entireProcessTree: true);
        }
        catch (Exception e) when (e is InvalidOperationException or
            System.ComponentModel.Win32Exception or NotSupportedException) { }
    }
}
