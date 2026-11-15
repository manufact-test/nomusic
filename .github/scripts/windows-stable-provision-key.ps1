# W155 — one-time CELIKOM stable manifest key provisioning
# Run from the repository root on the owner's trusted Windows PC.
# Requires PowerShell 7+, Node.js 24, GitHub CLI (gh), and access to the
# windows-stable-production environment in manufact-test/nomusic.

[CmdletBinding()]
param(
    [string]$Repository = "manufact-test/nomusic",
    [string]$EnvironmentName = "windows-stable-production",
    [string]$KeyDirectory = (Join-Path $env:LOCALAPPDATA "CELIKOM\StableManifestKey")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw "W155_POWERSHELL_7_REQUIRED"
}
if ($Repository -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$' -or
    $EnvironmentName -notmatch '^[A-Za-z0-9_.-]+$') {
    throw "W155_REPOSITORY_OR_ENVIRONMENT_INVALID"
}

function Invoke-GhSecretFromFile([string]$Name, [string]$FilePath) {
    # cmd.exe redirects the protected local PEM file to gh stdin. The PEM is
    # never placed in process arguments, terminal output, or a temporary copy.
    $command = 'gh secret set ' + $Name + ' --repo ' + $Repository +
        ' --env ' + $EnvironmentName + ' < "' + $FilePath + '"'
    & cmd.exe /d /c $command *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "W155_GH_SECRET_UPLOAD_FAILED"
    }
}

if (!(Get-Command node -ErrorAction SilentlyContinue) -or
    !(Get-Command gh -ErrorAction SilentlyContinue) -or
    !(Get-Command icacls.exe -ErrorAction SilentlyContinue)) {
    throw "W155_NODE_GH_OR_ICACLS_MISSING"
}
gh auth status *> $null
if ($LASTEXITCODE -ne 0) { throw "W155_GH_AUTH_REQUIRED" }
gh api "repos/$Repository/environments/$EnvironmentName" *> $null
if ($LASTEXITCODE -ne 0) { throw "W155_GITHUB_ENVIRONMENT_MUST_EXIST_FIRST" }
if (Test-Path -LiteralPath $KeyDirectory) {
    throw "W155_KEY_DIRECTORY_ALREADY_EXISTS_REFUSE_OVERWRITE"
}

$scriptPath = Join-Path (Get-Location) ".github/scripts/windows-stable-keygen.mjs"
if (!(Test-Path -LiteralPath $scriptPath)) { throw "W155_RUN_FROM_REPOSITORY_ROOT" }
$parent = Split-Path -Parent $KeyDirectory
New-Item -ItemType Directory -Path $parent -Force | Out-Null
node $scriptPath $KeyDirectory
if ($LASTEXITCODE -ne 0) { throw "W155_P256_KEY_GENERATION_FAILED" }

$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls.exe $KeyDirectory /inheritance:r /grant:r "$($currentUser):(OI)(CI)F" "SYSTEM:(OI)(CI)F" /T /C *> $null
if ($LASTEXITCODE -ne 0) { throw "W155_PRIVATE_KEY_ACL_HARDENING_FAILED" }

$privatePath = Join-Path $KeyDirectory "manifest-private.pem"
$publicPath = Join-Path $KeyDirectory "manifest-public-base64.txt"
if (!(Test-Path -LiteralPath $privatePath) -or !(Test-Path -LiteralPath $publicPath)) {
    throw "W155_KEYPAIR_OUTPUT_MISSING"
}

Invoke-GhSecretFromFile "CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM" $privatePath
gh variable set CELIKOM_STABLE_ORIGIN --repo $Repository --env $EnvironmentName --body "https://celikom.com" *> $null
if ($LASTEXITCODE -ne 0) { throw "W155_GH_ORIGIN_VARIABLE_SET_FAILED" }
$publicKeyBase64 = (Get-Content -LiteralPath $publicPath -Raw).Trim()
gh variable set CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64 --repo $Repository --env $EnvironmentName --body $publicKeyBase64 *> $null
if ($LASTEXITCODE -ne 0) { throw "W155_GH_PUBLIC_KEY_VARIABLE_SET_FAILED" }

$secretNames = gh secret list --repo $Repository --env $EnvironmentName
if ($LASTEXITCODE -ne 0 -or $secretNames -notmatch "CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM") {
    throw "W155_GH_SECRET_CONFIRMATION_FAILED"
}
$origin = gh variable get CELIKOM_STABLE_ORIGIN --repo $Repository --env $EnvironmentName
if ($LASTEXITCODE -ne 0 -or $origin.Trim() -ne "https://celikom.com") {
    throw "W155_GH_ORIGIN_CONFIRMATION_FAILED"
}
$der = [Convert]::FromBase64String($publicKeyBase64)
$fingerprint = [Convert]::ToHexString(
    [Security.Cryptography.SHA256]::HashData($der)).ToLowerInvariant()
Write-Output "W155_P256_PRODUCTION_KEY_PROVISIONED"
Write-Output "Public key fingerprint: $fingerprint"
Write-Output "Private key remains in protected GitHub environment and at: $KeyDirectory"
Write-Output "Keep an encrypted offline backup. Never paste or upload the PEM into chat, issues, or commits."
