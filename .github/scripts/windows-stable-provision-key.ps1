# W155 — one-time CELIKOM stable manifest key provisioning
# Run from the repository root on the owner's trusted Windows PC.
# Requires PowerShell 7+, Node.js 24, GitHub CLI (gh), and admin access to
# the protected windows-stable-production environment in manufact-test/nomusic.
# Refuses an unprotected environment and never replaces an existing signing key.

[CmdletBinding()]
param(
    [string]$Repository = "manufact-test/nomusic",
    [string]$EnvironmentName = "windows-stable-production",
    [string]$KeyDirectory = (Join-Path $env:LOCALAPPDATA "CELIKOM\StableManifestKey")
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ExpectedOrigin = "https://celikom.com"
$ExpectedDeployRoot = "/home/u235811320/domains/celikom.com/public_html"
$PrivateSecretName = "CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM"
$PublicVariableName = "CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64"

if ($PSVersionTable.PSVersion.Major -lt 7) { throw "W155_POWERSHELL_7_REQUIRED" }
if ($Repository -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$' -or
    $EnvironmentName -notmatch '^[A-Za-z0-9_.-]+$') {
    throw "W155_REPOSITORY_OR_ENVIRONMENT_INVALID"
}
foreach ($tool in @("node", "gh", "icacls.exe")) {
    if (!(Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "W155_REQUIRED_TOOL_MISSING"
    }
}
$nodeVersion = (& node --version).Trim()
if ($LASTEXITCODE -ne 0 -or $nodeVersion -notmatch '^v24\.') {
    throw "W155_NODE_24_REQUIRED"
}
gh auth status *> $null
if ($LASTEXITCODE -ne 0) { throw "W155_GH_AUTH_REQUIRED" }

$repoRoot = [IO.Path]::GetFullPath((Get-Location).Path).TrimEnd('\')
$keyRoot = [IO.Path]::GetFullPath($KeyDirectory)
function Assert-NoReparseAncestors([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    $root = [IO.Path]::GetPathRoot($full)
    if ([string]::IsNullOrWhiteSpace($root)) {
        throw "W155_KEY_DIRECTORY_PATH_UNSAFE"
    }
    $current = $root
    foreach ($segment in ($full.Substring($root.Length) -split '[\\/]')) {
        if ([string]::IsNullOrWhiteSpace($segment)) { continue }
        $current = [IO.Path]::Combine($current, $segment)
        if (Test-Path -LiteralPath $current) {
            $entry = Get-Item -LiteralPath $current -Force
            if (($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "W155_KEY_DIRECTORY_REPARSE_ANCESTOR"
            }
        }
    }
}
Assert-NoReparseAncestors $repoRoot
Assert-NoReparseAncestors $keyRoot
if ($keyRoot.Equals($repoRoot, [StringComparison]::OrdinalIgnoreCase) -or
    $keyRoot.StartsWith($repoRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase) -or $keyRoot.StartsWith('\\') -or
    $keyRoot.Contains('"') -or $keyRoot.Contains('&') -or $keyRoot.Contains('|') -or
    $keyRoot.Contains('<') -or $keyRoot.Contains('>') -or $keyRoot.Contains('^') -or
    $keyRoot.Contains('%') -or $keyRoot.Contains('!')) {
    throw "W155_KEY_DIRECTORY_PATH_UNSAFE"
}

# Verify an actual required-reviewer rule and a custom deployment policy
# containing exactly the main branch. Environment existence alone is not enough.
$envJson = gh api "repos/$Repository/environments/$EnvironmentName"
if ($LASTEXITCODE -ne 0) { throw "W155_PROTECTED_ENVIRONMENT_REQUIRED" }
$envConfig = ($envJson -join [Environment]::NewLine) | ConvertFrom-Json -ErrorAction Stop
$reviewRules = @($envConfig.protection_rules | Where-Object {
    $_.type -eq "required_reviewers" -and @($_.reviewers).Count -gt 0
})
if ($reviewRules.Count -lt 1) { throw "W155_REQUIRED_REVIEWER_MISSING" }
$policy = $envConfig.deployment_branch_policy
if ($null -eq $policy -or $policy.protected_branches -ne $false -or
    $policy.custom_branch_policies -ne $true) {
    throw "W155_MAIN_ONLY_DEPLOYMENT_POLICY_REQUIRED"
}
$branchJson = gh api "repos/$Repository/environments/$EnvironmentName/deployment-branch-policies"
if ($LASTEXITCODE -ne 0) { throw "W155_DEPLOYMENT_BRANCH_POLICY_UNREADABLE" }
$branchConfig = ($branchJson -join [Environment]::NewLine) | ConvertFrom-Json -ErrorAction Stop
$branches = @($branchConfig.branch_policies)
if ($branches.Count -ne 1 -or $branches[0].type -ne "branch" -or
    $branches[0].name -ne "main") {
    throw "W155_ENVIRONMENT_MUST_ALLOW_ONLY_MAIN"
}

$secretJson = gh secret list --repo $Repository --env $EnvironmentName --json name
if ($LASTEXITCODE -ne 0) { throw "W155_SECRET_LIST_FAILED" }
$secretNames = @()
if (-not [string]::IsNullOrWhiteSpace(($secretJson -join ""))) {
    $secretNames = @(($secretJson -join [Environment]::NewLine) |
        ConvertFrom-Json -ErrorAction Stop | ForEach-Object { $_.name })
}
$secretExists = $secretNames -contains $PrivateSecretName
$varsJson = gh variable list --repo $Repository --env $EnvironmentName --json name,value
if ($LASTEXITCODE -ne 0) { throw "W155_VARIABLE_LIST_FAILED" }
$vars = @()
if (-not [string]::IsNullOrWhiteSpace(($varsJson -join ""))) {
    $vars = @(($varsJson -join [Environment]::NewLine) | ConvertFrom-Json -ErrorAction Stop)
}
function Get-Var([string]$Name) {
    $found = @($vars | Where-Object { $_.name -eq $Name } | Select-Object -First 1)
    if ($found.Count -eq 0) { return $null }
    return [string]$found[0].value
}
$originVar = Get-Var "CELIKOM_STABLE_ORIGIN"
$publicVar = Get-Var $PublicVariableName
$rootVar = Get-Var "CELIKOM_STABLE_DEPLOY_ROOT"
if (($null -ne $originVar -and $originVar -cne $ExpectedOrigin) -or
    ($null -ne $rootVar -and $rootVar -cne $ExpectedDeployRoot)) {
    throw "W155_EXISTING_PRODUCTION_VARIABLE_MISMATCH"
}

$scriptPath = Join-Path $repoRoot ".github/scripts/windows-stable-keygen.mjs"
if (!(Test-Path -LiteralPath $scriptPath)) { throw "W155_RUN_FROM_REPOSITORY_ROOT" }
$dirExists = Test-Path -LiteralPath $keyRoot
if (($secretExists -or $null -ne $publicVar) -and !$dirExists) {
    throw "W155_EXISTING_PRODUCTION_KEYPAIR_REQUIRED_NO_ROTATION"
}
if (!$dirExists) {
    New-Item -ItemType Directory -Path (Split-Path -Parent $keyRoot) -Force | Out-Null
    New-Item -ItemType Directory -Path $keyRoot | Out-Null
}
$dirInfo = Get-Item -LiteralPath $keyRoot -Force
if (!$dirInfo.PSIsContainer -or
    ($dirInfo.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw "W155_KEY_DIRECTORY_UNSAFE"
}
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls.exe $keyRoot /inheritance:r /grant:r "$($currentUser):(OI)(CI)F" "SYSTEM:(OI)(CI)F" /T /C *> $null
if ($LASTEXITCODE -ne 0) { throw "W155_PRIVATE_KEY_ACL_HARDENING_FAILED" }

$privatePath = Join-Path $keyRoot "manifest-private.pem"
$derPath = Join-Path $keyRoot "manifest-public.der"
$publicPath = Join-Path $keyRoot "manifest-public-base64.txt"
$items = @(Get-ChildItem -LiteralPath $keyRoot -Force)
if ($items.Count -eq 0) {
    if ($secretExists -or $null -ne $publicVar) {
        throw "W155_EXISTING_PRODUCTION_KEY_MUST_NOT_BE_REGENERATED"
    }
    node $scriptPath $keyRoot
    if ($LASTEXITCODE -ne 0) { throw "W155_P256_KEY_GENERATION_FAILED" }
    $items = @(Get-ChildItem -LiteralPath $keyRoot -Force)
}
$expected = @("manifest-private.pem", "manifest-public.der", "manifest-public-base64.txt")
if ($items.Count -ne 3 -or @($items | Where-Object { $_.Name -notin $expected }).Count -ne 0) {
    throw "W155_KEYPAIR_DIRECTORY_CONTENTS_INVALID"
}
foreach ($filePath in @($privatePath, $derPath, $publicPath)) {
    $fileInfo = Get-Item -LiteralPath $filePath -Force
    if (($fileInfo.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "W155_KEYPAIR_FILE_UNSAFE"
    }
}
$publicDer = [IO.File]::ReadAllBytes($derPath)
$publicBase64 = [Convert]::ToBase64String($publicDer)
if (([IO.File]::ReadAllText($publicPath)).Trim() -cne $publicBase64) {
    throw "W155_PUBLIC_KEY_FILES_DISAGREE"
}
$privatePem = [IO.File]::ReadAllText($privatePath)
$ecdsa = [Security.Cryptography.ECDsa]::Create()
try {
    $ecdsa.ImportFromPem($privatePem)
    if ($ecdsa.ExportParameters($false).Curve.Oid.Value -ne "1.2.840.10045.3.1.7" -or
        [Convert]::ToBase64String($ecdsa.ExportSubjectPublicKeyInfo()) -cne $publicBase64) {
        throw "W155_PRIVATE_PUBLIC_KEYPAIR_MISMATCH"
    }
}
finally { $ecdsa.Dispose() }
$privatePem = $null

if ($null -ne $publicVar -and $publicVar -cne $publicBase64) {
    throw "W155_EXISTING_PUBLIC_PIN_MISMATCH_REFUSE_KEY_ROTATION"
}
if ($secretExists -and $publicVar -cne $publicBase64) {
    throw "W155_EXISTING_PRIVATE_SECRET_DO_NOT_OVERWRITE"
}

function Set-OrConfirmVar([string]$Name, [string]$Value, [AllowNull()][object]$Existing) {
    if ($null -ne $Existing) {
        if ([string]$Existing -cne $Value) {
            throw ("W155_VARIABLE_MISMATCH_" + $Name)
        }
        return
    }
    gh variable set $Name --repo $Repository --env $EnvironmentName --body $Value *> $null
    if ($LASTEXITCODE -ne 0) { throw ("W155_VARIABLE_SET_FAILED_" + $Name) }
}

# Publish the non-secret trust tuple first. This makes a partial first run
# safely resumable; the private key is uploaded only after all public pins exist.
Set-OrConfirmVar "CELIKOM_STABLE_ORIGIN" $ExpectedOrigin $originVar
Set-OrConfirmVar $PublicVariableName $publicBase64 $publicVar
Set-OrConfirmVar "CELIKOM_STABLE_DEPLOY_ROOT" $ExpectedDeployRoot $rootVar

if (!$secretExists) {
    $command = 'gh secret set ' + $PrivateSecretName + ' --repo ' + $Repository +
        ' --env ' + $EnvironmentName + ' < "' + $privatePath + '"'
    & cmd.exe /d /c $command *> $null
    if ($LASTEXITCODE -ne 0) { throw "W155_GH_SECRET_UPLOAD_FAILED" }
}

$verifiedSecrets = gh secret list --repo $Repository --env $EnvironmentName --json name
if ($LASTEXITCODE -ne 0) { throw "W155_SECRET_CONFIRMATION_FAILED" }
$verifiedSecretNames = @(($verifiedSecrets -join [Environment]::NewLine) |
    ConvertFrom-Json -ErrorAction Stop | ForEach-Object { $_.name })
if ($verifiedSecretNames -notcontains $PrivateSecretName) {
    throw "W155_SECRET_CONFIRMATION_FAILED"
}
$verifiedVarsJson = gh variable list --repo $Repository --env $EnvironmentName --json name,value
if ($LASTEXITCODE -ne 0) { throw "W155_VARIABLE_CONFIRMATION_FAILED" }
$verifiedVars = @(($verifiedVarsJson -join [Environment]::NewLine) | ConvertFrom-Json -ErrorAction Stop)
$verifiedOrigin = @($verifiedVars | Where-Object { $_.name -eq "CELIKOM_STABLE_ORIGIN" })[0].value
$verifiedPublic = @($verifiedVars | Where-Object { $_.name -eq $PublicVariableName })[0].value
$verifiedRoot = @($verifiedVars | Where-Object { $_.name -eq "CELIKOM_STABLE_DEPLOY_ROOT" })[0].value
if ($verifiedOrigin -cne $ExpectedOrigin -or $verifiedPublic -cne $publicBase64 -or
    $verifiedRoot -cne $ExpectedDeployRoot) {
    throw "W155_VARIABLE_CONFIRMATION_FAILED"
}
$fingerprint = [Convert]::ToHexString(
    [Security.Cryptography.SHA256]::HashData($publicDer)).ToLowerInvariant()
Write-Output "W155_P256_PRODUCTION_KEY_PROVISIONED_OR_VERIFIED"
Write-Output "Public key fingerprint: $fingerprint"
Write-Output "Environment: $EnvironmentName (required reviewer and main-only policy verified)"
Write-Output "Private key remains in the protected GitHub secret and at: $keyRoot"
Write-Output "Keep an encrypted offline backup. Never paste the PEM into chat, issues or commits."
