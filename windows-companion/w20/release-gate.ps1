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
if ($entries.Count -ne 1 -or
    $entries[0] -notmatch 'Source:\s*"\.\.\\publish\\\{#AppExecutable\}"') {
    throw "W20_THIRD_PARTY_OR_UNKNOWN_BINARY_IN_INSTALLER"
}
if ($text -notmatch '(?m)^PrivilegesRequired=lowest\s*$' -or
    $text -notmatch '(?m)^DefaultDirName=\{localappdata\}\\Programs\\CELIKOM\s*$' -or
    $text -match '(?m)^\[(Registry|UninstallDelete)\]') {
    throw "W20_INSTALLER_SECURITY_POLICY_FAILED"
}
if ($Mode -eq "Release") {
    # This must remain fail-closed until independent written Yandex/PulseSync
    # permissions (as applicable), audio E2E, rollback, Win10/11 security and
    # trusted code signing are verified in an approved release record.
    throw "W20_RELEASE_BLOCKED_NO_LICENSED_NATIVE_AUDIO_OR_SIGNED_RELEASE"
}
Write-Output "W20_STAGE_PACKAGE_POLICY_PASS: OWN_EXECUTABLE_ONLY"
