using Celikom.NativeInstaller;
using System.Text.Json;

// Internal build tool only. The distributed CELIKOM application uses the same
// .NET builder library directly, without Node or command-line setup.
if (args.Length != 7 && !(args.Length == 4 && args[0] == "--install") &&
    !(args.Length == 3 && args[0] == "--restore"))
{
    Console.Error.WriteLine("Usage: <exe> <asar> <host> <renderer> <exe-sha> <asar-sha> <out> | --install <root> <assets> <backup> | --restore <root> <backup>");
    return 2;
}
try
{
    if (args[0] == "--install")
    {
        var state = NativeIntegrationManager.Install(args[1], args[2], args[3]);
        if (state != NativeInstallState.Active) throw new IOException("NOT_ACTIVE_AFTER_INSTALL");
        Console.WriteLine("W24_ACTUAL_HOST_INSTALL_VERIFIED");
        return 0;
    }
    if (args[0] == "--restore")
    {
        var state = NativeIntegrationManager.Restore(args[1], args[2]);
        if (state is not (NativeInstallState.Restored or NativeInstallState.NotInstalled))
            throw new IOException("NOT_RESTORED");
        Console.WriteLine("W24_ACTUAL_HOST_RESTORED");
        return 0;
    }
    var image=NativeAsarImageBuilder.Build(
        File.ReadAllBytes(args[0]), File.ReadAllBytes(args[1]),
        File.ReadAllBytes(args[2]), File.ReadAllBytes(args[3]), args[4], args[5]);
    var folder=Path.GetFullPath(args[6]);
    if (Directory.Exists(folder) || File.Exists(folder))
        throw new IOException("OUTPUT_MUST_NOT_EXIST");
    Directory.CreateDirectory(folder);
    File.WriteAllBytes(Path.Combine(folder, "app.asar"), image.Asar);
    File.WriteAllBytes(Path.Combine(folder, "YandexMusic.patched.exe"), image.Executable);
    var report=new {
        originalExeSha=image.OriginalExeSha256,
        originalAsarSha=image.OriginalAsarSha256,
        modifiedExeSha=image.NewExeSha256,
        modifiedAsarSha=image.NewAsarSha256,
        integrityOccurrences=image.EmbeddedHashesChanged
    };
    File.WriteAllText(Path.Combine(folder,"W24-image-hashes.json"),
        JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true}));
    Console.WriteLine("W24_STAGED_IMAGES_READY");
    return 0;
}
catch (Exception ex) when (ex is IOException or ArgumentException or InvalidOperationException
    or JsonException or OverflowException or OutOfMemoryException)
{
    Console.Error.WriteLine("W24_STAGE_FAILED: "+ex.Message);
    return 1;
}
