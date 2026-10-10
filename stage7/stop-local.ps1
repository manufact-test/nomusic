param([switch]$Reset)
$ErrorActionPreference = "Stop"
$compose = Join-Path $PSScriptRoot "compose.yaml"
$runtime = Join-Path $PSScriptRoot ".runtime"
$envFile = Join-Path $runtime "local.env"
if (!(Test-Path $envFile)) {
    Write-Host "No local CELIKOM Stage 7 sandbox has been initialized."
    exit 0
}
$args = @("compose", "-p", "celikom-stage7-local", "--env-file", $envFile, "-f", $compose, "down")
if ($Reset) { $args += "--volumes" }
& docker @args
if ($LASTEXITCODE -ne 0) { throw "Docker Compose shutdown failed." }
if ($Reset) {
    Remove-Item -LiteralPath $envFile -Force
    Write-Host "Private local MySQL/audio volumes and test credentials cleared."
} else {
    Write-Host "Sandbox stopped. Local test data was kept; use -Reset to delete it."
}
