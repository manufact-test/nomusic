param([switch]$Quiet)
# Windows PowerShell 5.1+/7. All operations are local-only; Hostinger is untouched.
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$compose = Join-Path $PSScriptRoot "compose.yaml"
$runtime = Join-Path $PSScriptRoot ".runtime"
$envFile = Join-Path $runtime "local.env"

function New-LocalSecret {
    $bytes = New-Object byte[] 48
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return [BitConverter]::ToString($bytes).Replace("-", "").ToLowerInvariant()
}

if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker Desktop is required for an isolated local CELIKOM test. Install and start Docker Desktop first."
}
& docker compose version
if ($LASTEXITCODE -ne 0) { throw "Docker Compose is not available." }
if (!(Test-Path $runtime)) { New-Item -ItemType Directory -Path $runtime -Force | Out-Null }
if (!(Test-Path $envFile)) {
    $values = @(
        "STAGE7_DB_PASSWORD=$(New-LocalSecret)",
        "STAGE7_ROOT_PASSWORD=$(New-LocalSecret)",
        "STAGE7_API_TOKEN=$(New-LocalSecret)",
        "STAGE7_UPLOAD_TOKEN=$(New-LocalSecret)",
        "STAGE7_SIGNING_KEY=$(New-LocalSecret)"
    )
    [System.IO.File]::WriteAllText($envFile, (($values -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding($false)))
}
& docker compose -p celikom-stage7-local --env-file $envFile -f $compose up -d --build
if ($LASTEXITCODE -ne 0) { throw "Isolated sandbox failed to start." }
& docker compose -p celikom-stage7-local --env-file $envFile -f $compose exec -T api php bin/migrate.php
if ($LASTEXITCODE -ne 0) { throw "Isolated sandbox schema migration failed." }

$health = $false
for ($i=0; $i -lt 30; $i++) {
    try {
        $response = Invoke-RestMethod "http://127.0.0.1:8787/api/v1/health" -TimeoutSec 3
        if ($response.status -eq "ok") { $health = $true; break }
    } catch { Start-Sleep -Seconds 1 }
}
if (!$health) { throw "Local CELIKOM API did not become healthy." }

Write-Host "Building a separate unpacked Chrome extension for local staging..."
$mount = "type=bind,source=$root,target=/workspace"
& docker run --rm --mount $mount -w /workspace -e "CELIKOM_API_BASE_URL=http://127.0.0.1:8787" node:24 sh -lc "npm ci && npm run build:extension"
if ($LASTEXITCODE -ne 0) { throw "Local Chrome extension build failed." }

$configFile = Join-Path $root "extension/dist/unpacked/api/config.json"
$config = Get-Content $configFile -Raw | ConvertFrom-Json
if ($config.baseUrl -ne "http://127.0.0.1:8787") { throw "Incorrect sandbox API origin in Chrome build." }

$settings = @{}
Get-Content $envFile | ForEach-Object {
    $pair = $_ -split "=", 2
    if ($pair.Length -eq 2) { $settings[$pair[0]] = $pair[1] }
}
Write-Host ""
Write-Host "CELIKOM Stage 7 ISOLATED local sandbox is ready." -ForegroundColor Green
Write-Host "API: http://127.0.0.1:8787"
Write-Host "Chrome unpacked directory: $root/extension/dist/unpacked"
Write-Host "Open chrome://extensions, turn on Developer mode and choose Load unpacked."
Write-Host "Disable the previously installed CELIKOM extension while using this sandbox."
if (!$Quiet) {
    Write-Host "Add version -> owner-only upload code: $($settings['STAGE7_UPLOAD_TOKEN'])"
    Write-Host "Developer access code (optional): $($settings['STAGE7_API_TOKEN'])"
}
Write-Host "Keep both codes private and never share screenshots that contain them."
Write-Host "After testing: .\stage7\stop-local.ps1 -Reset removes all isolated data and tokens."
