using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using Celikom.NativeInstaller;

namespace Celikom.Companion;

public enum YandexHostStatus
{
    NotInstalled,
    IncompleteInstallation,
    UnsupportedVersion,
    UntrustedExecutable,
    UnknownAsar,
    OfficialBaselineVerified,
    InspectionUnavailable
}

public sealed record YandexHostResult(YandexHostStatus Status, string Version);

/// <summary>
/// Read-only detection of the exact owner-tested Yandex build.
/// A verified official installation is NOT proof of a working CELIKOM integration.
/// No launch, patch, network request, account access or elevation.
/// </summary>
public static class YandexHostProbe
{
    public const string VerifiedVersion = "5.126.1.0";
    public const string VerifiedAsarSha256 =
        "5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215";

    public static string DefaultInstallationRoot => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "Programs", "YandexMusic");

    public static YandexHostResult Inspect(string? installationRoot = null)
    {
        try
        {
            var root = installationRoot ?? DefaultInstallationRoot;
            var executable = Path.Combine(root, "Яндекс Музыка.exe");
            var asar = Path.Combine(root, "resources", "app.asar");
            if (!File.Exists(executable))
                return new(YandexHostStatus.NotInstalled, "");
            if (!File.Exists(asar))
                return new(YandexHostStatus.IncompleteInstallation, "");

            var version = FileVersionInfo.GetVersionInfo(executable).FileVersion ?? "";
            var pinnedVendor = OfficialYandexCatalog.TryGet(version, out var approved);
            if (!pinnedVendor &&
                version is not ("5.126.1" or "5.126.1.0" or "5.126.1.56270518164a6ebd4b974971490df41224a69d68"))
                return new(YandexHostStatus.UnsupportedVersion, version);

            // Check the executable itself, not merely whether it carries a certificate.
            // A modified, formerly signed EXE must fail the WinVerifyTrust hash check.
            if (!AuthenticodeVerifier.IsTrusted(executable))
                return new(YandexHostStatus.UntrustedExecutable, version);

            // For 5.127 require the signed EXE's exact independent official
            // package hash as well as its ASAR, not merely a claimed version.
            if (pinnedVendor)
            {
                // An approved feed entry never bypasses actual Windows signature
                // and pinned Yandex publisher verification.
                if (!OfficialYandexCatalog.IsExactTrustedVendorPair(executable, asar))
                    return new(YandexHostStatus.UntrustedExecutable, version);
            }
            using var stream = new FileStream(asar, FileMode.Open, FileAccess.Read, FileShare.Read);
            var sha = Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
            var expectedSha = pinnedVendor ? approved.AsarSha256 : VerifiedAsarSha256;
            if (sha != expectedSha)
                return new(YandexHostStatus.UnknownAsar, version);

            return new(YandexHostStatus.OfficialBaselineVerified, version);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException
            or CryptographicException or ArgumentException or System.ComponentModel.Win32Exception)
        {
            return new(YandexHostStatus.InspectionUnavailable, "");
        }
    }
}

internal static class AuthenticodeVerifier
{
    private static readonly Guid VerifyAction =
        new("00AAC56B-CD44-11d0-8CC2-00C04FC295EE");

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct FileInfo
    {
        public uint cbStruct;
        [MarshalAs(UnmanagedType.LPWStr)] public string filePath;
        public IntPtr hFile;
        public IntPtr knownSubject;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct TrustData
    {
        public uint cbStruct;
        public IntPtr policyCallbackData;
        public IntPtr sipClientData;
        public uint uiChoice;
        public uint revocationChecks;
        public uint unionChoice;
        public IntPtr fileInfo;
        public uint stateAction;
        public IntPtr stateData;
        public IntPtr urlReference;
        public uint providerFlags;
        public uint uiContext;
        public IntPtr signatureSettings;
    }

    [DllImport("wintrust.dll", ExactSpelling = true, CharSet = CharSet.Unicode)]
    private static extern int WinVerifyTrust(
        IntPtr hwnd, ref Guid action, ref TrustData data);

    public static bool IsTrusted(string executable)
    {
        if (!OperatingSystem.IsWindows()) return false;
        var native = new FileInfo
        {
            cbStruct = (uint)Marshal.SizeOf<FileInfo>(),
            filePath = executable
        };
        var ptr = Marshal.AllocHGlobal(Marshal.SizeOf<FileInfo>());
        try
        {
            Marshal.StructureToPtr(native, ptr, false);
            var data = new TrustData
            {
                cbStruct = (uint)Marshal.SizeOf<TrustData>(),
                uiChoice = 2,           // WTD_UI_NONE
                revocationChecks = 0,   // WTD_REVOKE_NONE
                unionChoice = 1,        // WTD_CHOICE_FILE
                fileInfo = ptr,
                stateAction = 0,        // WTD_STATEACTION_IGNORE
                providerFlags = 0x1000 // WTD_CACHE_ONLY_URL_RETRIEVAL
            };
            var action = VerifyAction;
            return WinVerifyTrust(IntPtr.Zero, ref action, ref data) == 0;
        }
        finally
        {
            Marshal.DestroyStructure<FileInfo>(ptr);
            Marshal.FreeHGlobal(ptr);
        }
    }
}
