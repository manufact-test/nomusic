param(
    [ValidateSet("Stage", "Release")]
    [string]$Mode = "Stage",
    [string]$InstallerScript = (Join-Path $PSScriptRoot "installer\CELIKOM.iss")
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $InstallerScript)) {
    throw "W20_MISSING_INSTALLER_SCRIPT"
}
$text = Get-Content -LiteralPath $InstallerScript -Raw -Encoding utf8
$filesSection = [regex]::Match($text, '(?ms)^\[Files\]\s*$(.*?)(?=^\[|\z)')
if (-not $filesSection.Success) { throw "W20_MISSING_FILES_SECTION" }
$entries = @($filesSection.Groups[1].Value -split "\r?\n" |
    Where-Object { $_ -match '^\s*Source\s*:' })
$allowed = @(
    'Source: "..\publish\{#AppExecutable}"',
    'Source: "..\..\w23\dist\host.cjs"',
    'Source: "..\..\w23\dist\renderer.js"',
    'Source: "..\publish\CELIKOM.UpdateSupervisor.exe"'
)
if ($entries.Count -ne 4) { throw 'W24_UNEXPECTED_INSTALLER_FILE_COUNT' }
foreach ($entry in $allowed) {
    if (@($entries | Where-Object { $_.Trim().StartsWith($entry, [StringComparison]::Ordinal) }).Count -ne 1) {
        throw 'W24_INSTALLER_FILE_NOT_ALLOWED'
    }
}
if ($text -notmatch '(?m)^PrivilegesRequired=lowest\s*$' -or
    $text -notmatch '(?m)^DefaultDirName=\{localappdata\}\\Programs\\CELIKOM\s*$' -or
    $text -match '(?m)^\[(Registry|UninstallDelete)\]') {
    throw "W20_INSTALLER_SECURITY_POLICY_FAILED"
}
if ($Mode -eq "Release") {
    # Consumer release only after audible native playback, controls,
    # recovery, Windows security and signature checks pass.
    throw "W24_RELEASE_BLOCKED_NO_VERIFIED_AUDIO_OR_SIGNING"
}
Write-Output "W24_STAGE_PACKAGE_POLICY_PASS: APP_NATIVE_MODULES_AND_INTERNAL_SUPERVISOR"
