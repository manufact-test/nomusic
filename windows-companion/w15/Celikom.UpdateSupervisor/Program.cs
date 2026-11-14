using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using Celikom.Companion;
using Celikom.NativeInstaller;
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
        var journal = new DurableSupervisorJournal(root, transaction,
            ProductionSignerCertificateSha256);
        var journalState = journal.Read();
        var runningImage = Environment.ProcessPath;
        if (string.IsNullOrWhiteSpace(runningImage) ||
            !IsTrustedRunningImage(runningImage, journalState.PreviousSupervisorSha256,
                ProductionSignerCertificateSha256))
            return 8;

        var engine = new UpdateSupervisorEngine(transaction, journal,
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
    private static bool IsTrustedRunningImage(
        string path, string expectedSha256, string signerSha256)
    {
        if (!StableUpdatePayloadVerifier.MatchesFile(path, expectedSha256) ||
            !NativeHostSignature.IsValid(path))
            return false;
        try
        {
#pragma warning disable SYSLIB0057
            using var signer = X509Certificate.CreateFromSignedFile(path);
#pragma warning restore SYSLIB0057
            var actual = SHA256.HashData(signer.GetRawCertData());
            var expected = Convert.FromHexString(signerSha256);
            return CryptographicOperations.FixedTimeEquals(actual, expected);
        }
        catch (Exception e) when (e is IOException or CryptographicException or
            ArgumentException or UnauthorizedAccessException)
        {
            return false;
        }
    }
}
