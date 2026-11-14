param(
    [switch]$RequireBuilt
)

$ErrorActionPreference = 'Stop'
$setupPath = Join-Path $PSScriptRoot 'installer/CELIKOM.iss'
$projectPath = Join-Path $PSScriptRoot '../w15/Celikom.Companion/Celikom.Companion.csproj'
if (-not (Test-Path -LiteralPath $setupPath) -or
    -not (Test-Path -LiteralPath $projectPath)) {
    throw 'W136_STAGE_IDENTITY_SOURCE_MISSING'
}

$setup = Get-Content -LiteralPath $setupPath -Raw -Encoding utf8
function SingleSetupValue([string]$pattern, [string]$code) {
    $matches = [regex]::Matches($setup, $pattern)
    if ($matches.Count -ne 1) { throw $code }
    return $matches[0].Groups[1].Value
}

$version = SingleSetupValue '(?m)^AppVersion=([0-9]+\.[0-9]+\.[0-9]+)\s*$' 'W136_INNO_APP_VERSION_INVALID'
$fileVersion = SingleSetupValue '(?m)^VersionInfoVersion=([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\s*$' 'W136_INNO_PE_VERSION_INVALID'
$baseName = SingleSetupValue '(?m)^OutputBaseFilename=([A-Za-z0-9_-]+)\s*$' 'W136_INNO_OUTPUT_NAME_INVALID'
$project = [xml](Get-Content -LiteralPath $projectPath -Raw -Encoding utf8)
$projectVersion = [string]$project.Project.PropertyGroup.Version

if ($version -ne $projectVersion -or $fileVersion -ne "$version.0") {
    throw 'W136_APP_INNO_AND_PE_VERSION_DIVERGED'
}
# The manually selected ZIP upgrade path has a deliberately narrower naming
# contract than the signed production updater. Staging must keep that contract
# until the owner approves a production-signed package.
if ($baseName -cnotmatch '^CELIKOM-W[0-9]{1,3}-[A-Z0-9-]{3,80}-UNSIGNED$') {
    throw 'W136_STAGE_INSTALLER_NOT_ALLOWED_BY_LOCAL_UPDATER'
}
$relativeInstaller = "windows-companion/w20/output/$baseName.exe"
$absoluteInstaller = Join-Path $PSScriptRoot "output/$baseName.exe"
if ($RequireBuilt) {
    if (-not (Test-Path -LiteralPath $absoluteInstaller -PathType Leaf)) {
        throw 'W136_EXACT_COMPILED_INSTALLER_MISSING'
    }
    if ([string]::IsNullOrWhiteSpace($env:GITHUB_ENV)) {
        throw 'W136_GITHUB_STEP_ENVIRONMENT_UNAVAILABLE'
    }
    Add-Content -LiteralPath $env:GITHUB_ENV -Encoding utf8 -Value "CELIKOM_STAGE_INSTALLER=$relativeInstaller"
    Add-Content -LiteralPath $env:GITHUB_ENV -Encoding utf8 -Value "CELIKOM_STAGE_FILE_VERSION=$fileVersion"
}
Write-Output 'W136_CURRENT_APP_INSTALLER_IDENTITY_PASS'
