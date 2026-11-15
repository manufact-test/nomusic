[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ReleaseDirectory,
    [Parameter(Mandatory = $true)][string]$Version
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($Version -notmatch '^[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,5}$') {
    throw "W156_OWNER_PACKAGE_VERSION_INVALID"
}
$root = [IO.Path]::GetFullPath($ReleaseDirectory)
if (!(Test-Path -LiteralPath $root -PathType Container)) {
    throw "W156_OWNER_PACKAGE_RELEASE_DIRECTORY_MISSING"
}
$rootInfo = Get-Item -LiteralPath $root -Force
if (($rootInfo.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw "W156_OWNER_PACKAGE_RELEASE_DIRECTORY_UNSAFE"
}

$exeName = "CELIKOM-Windows-$Version.exe"
$versionDirectory = Join-Path $root $Version
$installer = Join-Path $versionDirectory $exeName
$zipName = "CELIKOM-Windows-$Version.zip"
$zipPath = Join-Path $root $zipName
$checksumsPath = Join-Path $root "SHA256SUMS.txt"

if ((Test-Path -LiteralPath $zipPath) -or
    (Test-Path -LiteralPath $checksumsPath)) {
    throw "W156_OWNER_PACKAGE_OUTPUT_ALREADY_EXISTS"
}
if (!(Test-Path -LiteralPath $installer -PathType Leaf)) {
    throw "W156_OWNER_PACKAGE_INSTALLER_MISSING"
}
$installerInfo = Get-Item -LiteralPath $installer -Force
if (($installerInfo.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
    $installerInfo.Length -lt 10000 -or $installerInfo.Length -gt 125000000) {
    throw "W156_OWNER_PACKAGE_INSTALLER_INVALID"
}

$zipCreated = $false
$checksumsCreated = $false
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    Compress-Archive -LiteralPath $installer -DestinationPath $zipPath -CompressionLevel Optimal
    if (!(Test-Path -LiteralPath $zipPath -PathType Leaf)) {
        throw "W156_OWNER_PACKAGE_ZIP_MISSING"
    }
    $zipCreated = $true

    $exeHash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
    $archive = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
    try {
        $entries = @($archive.Entries)
        if ($entries.Count -ne 1 -or $entries[0].FullName -cne $exeName -or
            $entries[0].Length -ne $installerInfo.Length) {
            throw "W156_OWNER_PACKAGE_ZIP_MUST_HAVE_ONE_ROOT_EXE"
        }
        $entryStream = $entries[0].Open()
        $sha = [Security.Cryptography.SHA256]::Create()
        try {
            $entryHash = [Convert]::ToHexString($sha.ComputeHash($entryStream)).ToLowerInvariant()
        }
        finally {
            $sha.Dispose()
            $entryStream.Dispose()
        }
        if ($entryHash -cne $exeHash) {
            throw "W156_OWNER_PACKAGE_ZIP_CONTENT_HASH_MISMATCH"
        }
    }
    finally {
        $archive.Dispose()
    }

    $zipInfo = Get-Item -LiteralPath $zipPath -Force
    if (($zipInfo.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $zipInfo.Length -le 0) {
        throw "W156_OWNER_PACKAGE_ZIP_INVALID"
    }
    $zipHash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $checksumLines = @(
        "$exeHash  $Version/$exeName"
        "$zipHash  $zipName"
    )
    [IO.File]::WriteAllLines($checksumsPath, $checksumLines, [Text.Encoding]::ASCII)
    $checksumsCreated = $true

    Write-Output "W156_OWNER_PACKAGE_EXE_ZIP_PASS"
    Write-Output "EXE_SHA256=$exeHash"
    Write-Output "ZIP_SHA256=$zipHash"
}
catch {
    if ($checksumsCreated) {
        Remove-Item -LiteralPath $checksumsPath -Force -ErrorAction SilentlyContinue
    }
    if ($zipCreated) {
        Remove-Item -LiteralPath $zipPath -Force -ErrorAction SilentlyContinue
    }
    throw
}
