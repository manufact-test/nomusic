using Celikom.UpdateSupervisor;

internal static class Program
{
    // Deliberately NOT configured. The trusted SHA256 fingerprint of the
    // production CELIKOM signing certificate must be embedded by the signed
    // release pipeline, not passed from CLI, an API response, config or env.
    // Until then this independent helper cannot launch ANY installer.
    private const string ProductionSignerCertificateSha256 = "";

    private static async Task<int> Main(string[] args)
    {
        if (!OperatingSystem.IsWindows() || args.Length != 2 ||
            args[0] != "--supervise" ||
            !Guid.TryParseExact(args[1], "N", out var transaction))
            return 2;
        if (!System.Text.RegularExpressions.Regex.IsMatch(
            ProductionSignerCertificateSha256, "^[a-fA-F0-9]{64}$"))
            return 3; // fail closed: not production-signed / not provisioned

        using var mutex = new Mutex(true,
            "Local\\CELIKOM.Windows.SignedUpdate." + transaction.ToString("N"),
            out bool firstInstance);
        if (!firstInstance) return 4;
        var root = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "CELIKOM", "Windows", "StableRollback");
        var engine = new UpdateSupervisorEngine(transaction,
            new DurableSupervisorJournal(root, transaction,
                ProductionSignerCertificateSha256),
            new WindowsSupervisorHealthProbe(ProductionSignerCertificateSha256),
            new WindowsSignedRollbackLauncher());

        // Independent of the GUI: this process remains alive while the
        // original CELIKOM executable is replaced or crashes.
        using var timeout = new CancellationTokenSource(TimeSpan.FromMinutes(35));
        try
        {
            while (!timeout.Token.IsCancellationRequested)
            {
                var result = await engine.TickAsync(DateTimeOffset.UtcNow, timeout.Token);
                if (result is UpdateSupervisorEngine.Step.Completed or
                    UpdateSupervisorEngine.Step.NewApplicationHealthy or
                    UpdateSupervisorEngine.Step.PreviousVersionRestored)
                    return 0;
                if (result == UpdateSupervisorEngine.Step.ManualRecovery)
                    return 5;
                await Task.Delay(TimeSpan.FromSeconds(2), timeout.Token);
            }
            return 6; // unresolved transaction kept for explicit recovery
        }
        catch (OperationCanceledException) { return 6; }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or
            System.Security.Cryptography.CryptographicException or
            InvalidOperationException or ArgumentException)
        {
            // Fail closed. Never invent a new rollback ticket or run an
            // unverified setup in response to journal/OS errors.
            return 7;
        }
    }
}
