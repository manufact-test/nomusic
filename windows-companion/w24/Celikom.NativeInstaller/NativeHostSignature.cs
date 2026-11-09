using System.Runtime.InteropServices;

namespace Celikom.NativeInstaller;

/// <summary>WinVerifyTrust validates the existing original EXE before patching.</summary>
public static class NativeHostSignature
{
    private static readonly Guid ActionId =
        new("00AAC56B-CD44-11d0-8CC2-00C04FC295EE");

    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
    private struct FileInfo
    {
        public uint cbStruct;
        [MarshalAs(UnmanagedType.LPWStr)] public string filePath;
        public IntPtr hFile;
        public IntPtr knownSubject;
    }

    [StructLayout(LayoutKind.Sequential)]
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

    [DllImport("wintrust.dll", ExactSpelling=true, CharSet=CharSet.Unicode)]
    private static extern int WinVerifyTrust(
        IntPtr hwnd, ref Guid action, ref TrustData data);

    public static bool IsValid(string path)
    {
        if (!OperatingSystem.IsWindows() || !File.Exists(path)) return false;
        var native=new FileInfo { cbStruct=(uint)Marshal.SizeOf<FileInfo>(), filePath=path };
        var pointer=Marshal.AllocHGlobal(Marshal.SizeOf<FileInfo>());
        try
        {
            Marshal.StructureToPtr(native,pointer,false);
            var data=new TrustData {
                cbStruct=(uint)Marshal.SizeOf<TrustData>(),
                uiChoice=2, revocationChecks=0, unionChoice=1,
                fileInfo=pointer,stateAction=0,providerFlags=0x1000
            };
            var action=ActionId;
            return WinVerifyTrust(IntPtr.Zero,ref action,ref data)==0;
        }
        finally {
            Marshal.DestroyStructure<FileInfo>(pointer);
            Marshal.FreeHGlobal(pointer);
        }
    }
}
