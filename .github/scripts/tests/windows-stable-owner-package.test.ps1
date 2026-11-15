$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $PSScriptRoot
$helper = Join-Path $scriptRoot "windows-stable-owner-package.ps1"
if (!(Test-Path -LiteralPath $helper -PathType Leaf)) {
    throw "W156_OWNER_PACKAGE_HELPER_MISSING"
}
$root = Join-Path $env:TEMP ("celikom-owner-package-" + [Guid]::NewGuid().ToString("N"))
$version = "0.24.99"
$versionDirectory = Join-Path $root $version
New-Item -ItemType Directory -Path $versionDirectory -Force | Out-Null
try {
    $exeName = "CELIKOM-Windows-$version.exe"
    $installer = Join-Path $versionDirectory $exeName
    $bytes = [byte[]]::new(32768)
    for ($i = 0; $i -lt $bytes.Length; $i++) { $bytes[$i] = [byte]($i % 251) }
    [IO.File]::WriteAllBytes($installer, $bytes)

    & $helper -ReleaseDirectory $root -Version $version
    $zipPath = Join-Path $root "CELIKOM-Windows-$version.zip"
    $sumsPath = Join-Path $root "SHA256SUMS.txt"
    if (!(Test-Path -LiteralPath $zipPath) -or !(Test-Path -LiteralPath $sumsPath)) {
        throw "W156_OWNER_PACKAGE_OUTPUT_MISSING"
    }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
    try {
        $entries = @($archive.Entries)
        if ($entries.Count -ne 1 -or $entries[0].FullName -cne $exeName) {
            throw "W156_OWNER_PACKAGE_FIXTURE_ENTRY_INVALID"
        }
        $stream = $entries[0].Open()
        try {
            $sha = [Security.Cryptography.SHA256]::Create()
            try {
                $entryHash = [Convert]::ToHexString($sha.ComputeHash($stream)).ToLowerInvariant()
            } finally { $sha.Dispose() }
        } finally { $stream.Dispose() }
    } finally { $archive.Dispose() }

    $exeHash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
    $zipHash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($entryHash -cne $exeHash) { throw "W156_OWNER_PACKAGE_FIXTURE_CONTENT_MISMATCH" }
    $sums = Get-Content -LiteralPath $sumsPath -Raw
    if (!$sums.Contains("$exeHash  $version/$exeName") -or
        !$sums.Contains("$zipHash  CELIKOM-Windows-$version.zip")) {
        throw "W156_OWNER_PACKAGE_FIXTURE_CHECKSUM_MISMATCH"
    }

    $overwriteRejected = $false
    try { & $helper -ReleaseDirectory $root -Version $version }
    catch { $overwriteRejected = $_.Exception.Message -match "W156_OWNER_PACKAGE_OUTPUT_ALREADY_EXISTS" }
    if (!$overwriteRejected) { throw "W156_OWNER_PACKAGE_OVERWRITE_NOT_REFUSED" }

    Write-Output "W156_OWNER_PACKAGE_FIXTURE_PASS"
}
finally {
    Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
