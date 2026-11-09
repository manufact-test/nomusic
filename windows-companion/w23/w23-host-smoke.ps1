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
  ownImagesStaged = $false
  modifiedExeSignature = 'NOT_CHECKED'
  modifiedAppLaunched = $false
  nativeHostLoaded = $false
  rendererInjected = $false
  resourceHookAttached = $false
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
  Copy-Item $exe $backupExe
  Copy-Item $asar $backupAsar
  $backedUp = $true
  $out = Join-Path $root 'staged'
  $args = @('windows-companion/w23/asar-images.mjs','--asar',$asar,'--exe',$exe,'--host','windows-companion/w23/dist/host.cjs','--renderer','windows-companion/w23/dist/renderer.js','--asar-sha',$originalAsar,'--exe-sha',$originalExe,'--out',$out)
  & node @args
  if ($LASTEXITCODE -ne 0) { throw 'STAGE_IMAGES_FAILED' }
  $manifest = Get-Content (Join-Path $out 'W23-image-hashes.json') -Raw | ConvertFrom-Json
  if ($manifest.originalAsarSha -ne $originalAsar -or $manifest.originalExeSha -ne $originalExe) {
    throw 'STAGED_IMAGES_WRONG_SOURCE'
  }
  $report.ownImagesStaged = $true
  Copy-Item (Join-Path $out 'app.asar') $asar -Force
  Copy-Item (Join-Path $out 'YandexMusic.patched.exe') $exe -Force
  if ((Get-FileHash $asar -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.modifiedAsarSha -or
      (Get-FileHash $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.modifiedExeSha) {
    throw 'HOST_FILES_CHANGED_DURING_APPLY'
  }
  $report.modifiedExeSignature = (Get-AuthenticodeSignature $exe).Status.ToString()
  $data = Join-Path $env:LOCALAPPDATA 'CELIKOM\Windows'
  New-Item -ItemType Directory $data -Force | Out-Null
  ('a'*64) | Set-Content (Join-Path $data 'native-bridge.key') -NoNewline
  $diagnostics = Join-Path $root 'host-events.txt'
  $env:CELIKOM_W23_DEV_DIAG = $diagnostics
  $proc = Start-Process $exe -PassThru
  Start-Sleep -Seconds 20
  $report.modifiedAppLaunched = @(Get-Process -Id $proc.Id -ErrorAction SilentlyContinue).Count -gt 0
  if (Test-Path $diagnostics) {
    $events = @(Get-Content $diagnostics)
    $report.nativeHostLoaded = 'HOST_LOADED' -in $events
    $report.rendererInjected = 'RENDERER_INJECTED' -in $events
    $report.resourceHookAttached = 'RESOURCE_ATTACHED' -in $events
  }
  if (-not $report.modifiedAppLaunched) { throw 'MODIFIED_YANDEX_NOT_RUNNING' }
  if (-not $report.nativeHostLoaded) { throw 'NATIVE_HOST_BOOTSTRAP_NOT_EXECUTED' }
} catch {
  $failed = $_.Exception.Message
  $report.error = $failed
} finally {
  try {
    Get-Process -Name 'Яндекс Музыка' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    if ($backedUp) {
      Copy-Item $backupExe $exe -Force -ErrorAction Stop
      Copy-Item $backupAsar $asar -Force -ErrorAction Stop
      $report.originalBytesRestored =
        ((Get-FileHash $exe -Algorithm SHA256).Hash.ToLowerInvariant() -eq $originalExe) -and
        ((Get-FileHash $asar -Algorithm SHA256).Hash.ToLowerInvariant() -eq $originalAsar)
      $report.originalSignatureRestored = (Get-AuthenticodeSignature $exe).Status -eq 'Valid'
    }
    Remove-Item (Join-Path $env:LOCALAPPDATA 'CELIKOM\Windows\native-bridge.key') -Force -ErrorAction SilentlyContinue
    Remove-Item Env:\CELIKOM_W23_DEV_DIAG -ErrorAction SilentlyContinue
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
