# Developer-owned disposable Windows runner. No customer machine, accounts or audio.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$root = Join-Path $env:RUNNER_TEMP 'celikom-w23-native'
New-Item -ItemType Directory $root -Force | Out-Null
$reportPath = Join-Path $env:GITHUB_WORKSPACE 'windows-companion\w23\W23-report.json'
$report = [ordered]@{
  os = 'Windows Server 2022 disposable'
  defender = 'UNKNOWN'
  genuineYandexSigned = $false
  actualFileVersion = ''
  ownImagesStaged = $false
  managedInstallerActive = $false
  managedRestoreConfirmed = $false
  modifiedExeSignature = 'NOT_CHECKED'
  modifiedAppLaunched = $false
  ownerNativeLogCreated = $false
  ownerNativeLogRedacted = $false
  managedRefreshCycleVerified = $false
  nativeHostLoaded = $false
  rendererInjected = $false
  resourceHookAttached = $false
  companionBridgeStarted = $false
  nativeBridgePreflight = $false
  nativeBridgeStateReached = $false
  mainProcessRelayReached = $false
  rendererStateDelivered = $false
  originalBytesRestored = $false
  originalSignatureRestored = $false
  audio = 'NOT_TESTED_NO_ACCOUNT'
  error = ''
}
function Report { $report | ConvertTo-Json -Depth 5 | Set-Content $reportPath -Encoding utf8 }
$exe = Join-Path $env:LOCALAPPDATA 'Programs\YandexMusic\Яндекс Музыка.exe'
$asar = Join-Path $env:LOCALAPPDATA 'Programs\YandexMusic\resources\app.asar'
$backupExe = Join-Path $root 'original.exe'
$backupAsar = Join-Path $root 'original.asar'
$originalExe = ''
$originalAsar = ''
$backedUp = $false
$failed = $null
$companionProcess = $null
$managedBackup = Join-Path $root "managed-backup"
$cli = "windows-companion/w24/Celikom.NativeInstaller.Cli/Celikom.NativeInstaller.Cli.csproj"
$yandexRoot = Split-Path $exe -Parent
try {
  $mp = Get-MpComputerStatus -ErrorAction Stop
  if ($mp.AntivirusEnabled -and -not $mp.RealTimeProtectionEnabled) {
    try {
      Set-MpPreference -DisableRealtimeMonitoring $false -ErrorAction Stop
      Start-Sleep -Seconds 6
      $mp = Get-MpComputerStatus -ErrorAction Stop
    } catch { }
  }
  $report.defender = "antivirus=$($mp.AntivirusEnabled);realtime=$($mp.RealTimeProtectionEnabled)"
  if (-not $mp.AntivirusEnabled -or -not $mp.RealTimeProtectionEnabled) {
    throw 'DEFENDER_NOT_ACTIVE'
  }
  if (Test-Path $exe) { throw 'YANDEX_ALREADY_INSTALLED_ON_RUNNER' }
  $installer = Join-Path $root 'official.exe'
  Invoke-WebRequest 'https://desktop.app.music.yandex.net/stable/Yandex_Music_x64_5.126.1.exe' -OutFile $installer -UseBasicParsing -TimeoutSec 240
  if ((Get-FileHash $installer -Algorithm SHA256).Hash.ToLowerInvariant() -ne '131fa1d9bc32eee2baadbdd7c1fe7aa8ba4a2f89ec972dd462aa06ee5b170435') {
    throw 'YANDEX_INSTALLER_IDENTITY_MISMATCH'
  }
  $sig = Get-AuthenticodeSignature $installer
  if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch '(?i)Yandex|Яндекс') {
    throw 'YANDEX_INSTALLER_NOT_SIGNED_BY_VENDOR'
  }
  $install = Start-Process $installer -ArgumentList '/S' -PassThru
  if (-not $install.WaitForExit(130000)) {
    try { $install.Kill() } catch {}
    throw 'YANDEX_INSTALL_TIMEOUT'
  }
  if ($install.ExitCode -ne 0 -or -not (Test-Path $exe) -or -not (Test-Path $asar)) {
    throw 'YANDEX_INSTALL_FAILED'
  }
  $originalExe = (Get-FileHash $exe -Algorithm SHA256).Hash.ToLowerInvariant()
  $originalAsar = (Get-FileHash $asar -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($originalAsar -ne '5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215' -or
      (Get-AuthenticodeSignature $exe).Status -ne 'Valid') {
    throw 'YANDEX_ORIGINAL_MISMATCH'
  }
  $report.genuineYandexSigned = $true
  $report.actualFileVersion = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($exe).FileVersion
  Copy-Item $exe $backupExe
  Copy-Item $asar $backupAsar
  $backedUp = $true
  # CI-only: append fixed invalid-token fetch probe to disposable host, NOT owner installer.
  if ($env:CELIKOM_W33_RUNTIME_PROBE -eq '1') {
    $probe = Get-Content 'windows-companion/w23/w33-runtime-probe.cjs' -Raw -Encoding UTF8
    Add-Content 'windows-companion/w23/dist/host.cjs' -Value ([Environment]::NewLine + $probe) -Encoding UTF8
    Write-Output 'W33_DISPOSABLE_RENDERER_PROBE_ATTACHED'
  }
  $out = Join-Path $root 'staged'
  $args = @('windows-companion/w23/asar-images.mjs','--asar',$asar,'--exe',$exe,'--host','windows-companion/w23/dist/host.cjs','--renderer','windows-companion/w23/dist/renderer.js','--asar-sha',$originalAsar,'--exe-sha',$originalExe,'--out',$out)
  & node @args
  if ($LASTEXITCODE -ne 0) { throw 'STAGE_IMAGES_FAILED' }
  $manifest = Get-Content (Join-Path $out 'W23-image-hashes.json') -Raw | ConvertFrom-Json
  if ($manifest.originalAsarSha -ne $originalAsar -or $manifest.originalExeSha -ne $originalExe) {
    throw 'STAGED_IMAGES_WRONG_SOURCE'
  }
  $report.ownImagesStaged = $true
  # Actual same .NET integration transaction used by the CELIKOM desktop app:
  # signed preflight -> exact backup -> two-phase apply -> post-write verification.
  & dotnet run --project $cli -c Release -- --install $yandexRoot 'windows-companion/w23/dist' $managedBackup
  if ($LASTEXITCODE -ne 0) { throw 'W24_NATIVE_MANAGER_INSTALL_FAILED' }
  $installedRecord = Get-Content (Join-Path $managedBackup 'recovery.json') -Raw | ConvertFrom-Json
  if ($installedRecord.State -ne 'ACTIVE' -or
      (Get-FileHash $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $installedRecord.AppliedExe -or
      (Get-FileHash $asar -Algorithm SHA256).Hash.ToLowerInvariant() -ne $installedRecord.AppliedAsar) {
    throw 'W24_INSTALLED_PAIR_MISMATCH'
  }
  $report.managedInstallerActive = $true
  $report.modifiedExeSignature = (Get-AuthenticodeSignature $exe).Status.ToString()
  $data = Join-Path $env:LOCALAPPDATA 'CELIKOM\Windows'
  $capability = Join-Path $data 'native-bridge.key'
  $diagnostics = Join-Path $root 'host-events.txt'
  $bridgeDiagnostic = Join-Path $root 'bridge-events.txt'
  $env:CELIKOM_W23_DEV_DIAG = $diagnostics
  $env:CELIKOM_W23_DEV_BRIDGE_DIAG = $bridgeDiagnostic
  $companionExe = Join-Path $env:GITHUB_WORKSPACE 'windows-companion\w23\companion\CELIKOM.Companion.exe'
  if (-not (Test-Path $companionExe)) { throw 'COMPANION_BINARY_MISSING' }
  $companionProcess = Start-Process $companionExe -PassThru
  $keyReady = $false
  for ($i=0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 500
    if (Test-Path $capability) {
      $key = (Get-Content $capability -Raw).Trim()
      if ($key.Length -eq 64 -and $key -match '\A[0-9a-f]{64}\z') { $keyReady=$true; break }
    }
  }
  if (-not $keyReady) { throw 'COMPANION_BRIDGE_NOT_STARTED' }
  $report.companionBridgeStarted = $true
  $proc = Start-Process $exe -PassThru
  Start-Sleep -Seconds 20
  if (Test-Path $bridgeDiagnostic) {
    $bridgeEvents = @(Get-Content $bridgeDiagnostic)
    $report.nativeBridgePreflight = 'NATIVE_PREFLIGHT' -in $bridgeEvents
    $report.nativeBridgeStateReached = 'NATIVE_STATE_REQUEST' -in $bridgeEvents
  }
  $report.modifiedAppLaunched = @(Get-Process -Id $proc.Id -ErrorAction SilentlyContinue).Count -gt 0
  if (Test-Path $diagnostics) {
    $events = @(Get-Content $diagnostics)
    $report.observedEvents = @($events | Sort-Object -Unique)
    if ($env:CELIKOM_W33_RUNTIME_PROBE -eq '1') {
      $report.w33RuntimeProbe = @($events | Where-Object { $_.StartsWith('W33_RT_') } | Sort-Object -Unique)
      if ($report.w33RuntimeProbe.Count -eq 0) { throw 'W33_NATIVE_RENDERER_PROBE_NOT_OBSERVED' }
    }
    $report.nativeHostLoaded = 'HOST_LOADED' -in $events
    $report.rendererInjected = 'RENDERER_INJECTED' -in $events
    $report.resourceHookAttached = 'RESOURCE_ATTACHED' -in $events
    $report.mainProcessRelayReached = 'LOCAL_STATE_OK' -in $events
    $report.rendererStateDelivered = 'RENDERER_STATE_DELIVERED' -in $events
  }
  if (-not $report.modifiedAppLaunched) { throw 'MODIFIED_YANDEX_NOT_RUNNING' }
  if (-not $report.nativeHostLoaded) { throw 'NATIVE_HOST_BOOTSTRAP_NOT_EXECUTED' }
  if (-not $report.rendererInjected -or -not $report.resourceHookAttached)
    { throw 'NATIVE_RESOURCE_NOT_ATTACHED' }
  # Requests are made by the trusted Electron main process: no renderer
  # CORS preflight is required, and neither CSP nor PNA is altered.
  if (-not $report.nativeBridgeStateReached -or
      -not $report.mainProcessRelayReached -or -not $report.rendererStateDelivered)
    { throw 'NATIVE_MAIN_PROCESS_RELAY_CANNOT_REACH_COMPANION' }
  # Owner diagnostics are automatically created without developer environment flags.
  $ownerLog = Join-Path $data 'native-events.log'
  if (-not (Test-Path $ownerLog)) { throw 'W28_NATIVE_OWNER_LOG_NOT_CREATED' }
  $ownerLines = @(Get-Content $ownerLog -TotalCount 2500)
  if ($ownerLines.Count -lt 1 -or
      @($ownerLines | Where-Object { $_ -match '\|HOST_LOADED$' }).Count -eq 0) {
    throw 'W28_NATIVE_OWNER_LOG_MISSING_HOST_EVENT'
  }
  foreach ($line in $ownerLines) {
    if ($line -notmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\|[A-Z_]{3,48}(\|track=[1-9][0-9]{0,17})?$') {
      throw 'W28_NATIVE_OWNER_LOG_UNSAFE'
    }
  }
  $report.ownerNativeLogCreated = $true
  $report.ownerNativeLogRedacted = $true
  # W24 -> W28 refresh in disposable CI: verified restore + install again.
  Get-Process -Name 'Яндекс Музыка' -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 2
  & dotnet run --project $cli -c Release -- --restore $yandexRoot $managedBackup
  if ($LASTEXITCODE -ne 0) { throw 'W28_REFRESH_RESTORE_FAILED' }
  & dotnet run --project $cli -c Release -- --install $yandexRoot 'windows-companion/w23/dist' $managedBackup
  if ($LASTEXITCODE -ne 0) { throw 'W28_REFRESH_INSTALL_FAILED' }
  $refreshed = Get-Content (Join-Path $managedBackup 'recovery.json') -Raw | ConvertFrom-Json
  if ($refreshed.State -ne 'ACTIVE' -or
      (Get-FileHash $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $refreshed.AppliedExe -or
      (Get-FileHash $asar -Algorithm SHA256).Hash.ToLowerInvariant() -ne $refreshed.AppliedAsar) {
    throw 'W28_REFRESH_APPLIED_HASH_MISMATCH'
  }
  $report.managedRefreshCycleVerified = $true

} catch {
  $failed = $_.Exception.Message
  $report.error = $failed
} finally {
  try {
    Get-Process -Name 'Яндекс Музыка' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    if ($companionProcess) {
      Stop-Process -Id $companionProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 3
    if ($backedUp) {
      if (Test-Path (Join-Path $managedBackup 'recovery.json')) {
        & dotnet run --project $cli -c Release -- --restore $yandexRoot $managedBackup
        if ($LASTEXITCODE -eq 0) {
          $report.managedRestoreConfirmed = $true
        } else {
          $failed = 'W24_RECOVERY_MANAGER_FAILED'
          $report.error = $failed
        }
      }
      # Last-resort cleanup is only for this disposable CI machine.
      if (-not $report.managedRestoreConfirmed) {
        Copy-Item $backupExe $exe -Force -ErrorAction Stop
        Copy-Item $backupAsar $asar -Force -ErrorAction Stop
      }
      $report.originalBytesRestored =
        ((Get-FileHash $exe -Algorithm SHA256).Hash.ToLowerInvariant() -eq $originalExe) -and
        ((Get-FileHash $asar -Algorithm SHA256).Hash.ToLowerInvariant() -eq $originalAsar)
      $report.originalSignatureRestored = (Get-AuthenticodeSignature $exe).Status -eq 'Valid'
    }
    Remove-Item (Join-Path $env:LOCALAPPDATA 'CELIKOM\Windows\native-bridge.key') -Force -ErrorAction SilentlyContinue
    Remove-Item Env:\CELIKOM_W23_DEV_DIAG -ErrorAction SilentlyContinue
    Remove-Item Env:\CELIKOM_W23_DEV_BRIDGE_DIAG -ErrorAction SilentlyContinue
  } catch {
    $failed = 'RESTORE_FAILED'
    $report.error = $failed
  }
  Report
  $report | ConvertTo-Json -Depth 5 | Write-Output
}
if ($backedUp -and (-not $report.originalBytesRestored -or -not $report.originalSignatureRestored)) {
  throw 'RESTORE_NOT_VERIFIED'
}
if ($failed) { throw $failed }
