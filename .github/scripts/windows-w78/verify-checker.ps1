$ErrorActionPreference = 'Stop'
$env:LOCALAPPDATA = Join-Path $env:TEMP 'CELIKOM-W78-READONLY-CI'
$root = Join-Path $env:LOCALAPPDATA 'Programs\YandexMusic'
$app = Join-Path $env:LOCALAPPDATA 'Programs\CELIKOM'
$backup = Join-Path $env:LOCALAPPDATA 'CELIKOM\Windows\NativeHost\snapshot'
$exe = Join-Path $root 'Яндекс Музыка.exe'
$asar = Join-Path $root 'resources\app.asar'
$module = Join-Path $app 'integration\host.cjs'
foreach ($path in @((Split-Path $asar), (Split-Path $module), $backup)) {
  New-Item -ItemType Directory -Force -Path $path | Out-Null
}
[IO.File]::WriteAllBytes($exe, [Text.Encoding]::UTF8.GetBytes('CI: patched app executable; synthetic only'))
[IO.File]::WriteAllBytes($asar, [Text.Encoding]::UTF8.GetBytes('CI: patched app asar; synthetic only'))
[IO.File]::WriteAllBytes((Join-Path $backup 'original.exe'),[Text.Encoding]::UTF8.GetBytes('CI: original EXE'))
[IO.File]::WriteAllBytes((Join-Path $backup 'original.asar'),[Text.Encoding]::UTF8.GetBytes('CI: original ASAR'))
[IO.File]::WriteAllText($module, 'const CELIKOM_NATIVE_VERSION = "0.24.24";', [Text.Encoding]::UTF8)
$sha = { param([string]$p) (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() }
$record = @{
  Schema = 1
  InstallRoot = $root
  OriginalExe = (& $sha (Join-Path $backup 'original.exe'))
  OriginalAsar = (& $sha (Join-Path $backup 'original.asar'))
  AppliedExe = (& $sha $exe)
  AppliedAsar = (& $sha $asar)
  State = 'ACTIVE'
}
$record | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backup 'recovery.json') -Encoding UTF8
$parsedFixture = Get-Content -LiteralPath (Join-Path $backup 'recovery.json') -Raw | ConvertFrom-Json
$expected = [IO.Path]::GetFullPath($root).TrimEnd('\')
Write-Output ('W78_SYNTHETIC_ROOT_NORM_LENGTHS '+$expected.Length+' '+$parsedFixture.InstallRoot.Length)
Write-Output ('W78_SYNTHETIC_ROOT_A='+$expected)
Write-Output ('W78_SYNTHETIC_ROOT_B='+$parsedFixture.InstallRoot)
Write-Output ('W78_SYNTHETIC_ROOT_EQ='+[string]::Equals($expected,[string]$parsedFixture.InstallRoot,[StringComparison]::OrdinalIgnoreCase))
$eventsDir = Join-Path $env:LOCALAPPDATA 'CELIKOM\Windows'
[IO.File]::WriteAllText((Join-Path $eventsDir 'companion-events.log'),
  ((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.fffZ') + '|NATIVE_INSTALL_OK' + [Environment]::NewLine))
$desktop = [Environment]::GetFolderPath('DesktopDirectory')
if ([string]::IsNullOrWhiteSpace($desktop)) { throw 'W78_NO_DESKTOP_FOR_REPORT' }
New-Item -ItemType Directory -Force -Path $desktop | Out-Null
$report = Join-Path $desktop 'CELIKOM-YANDEX-CHECK.txt'
if (Test-Path -LiteralPath $report) { Remove-Item -LiteralPath $report -Force }
$scriptPath = Join-Path (Get-Location) '.github\scripts\windows-w78\CELIKOM-W77-READONLY-HOST-CHECK.cmd'
$cmd = [IO.File]::ReadAllText($scriptPath,[Text.Encoding]::UTF8)
$marker = '###CELIKOM_POWERSHELL_START###'
$index = $cmd.LastIndexOf($marker)
if ($index -lt 0) { throw 'W78_NO_EMBEDDED_SCRIPT' }
$ps = $cmd.Substring($index + $marker.Length)
[ScriptBlock]::Create($ps) | Out-Null
# The fixture harness runs in PowerShell 7 (native UTF-8), while the exact
# embedded diagnostic runs in the Windows PowerShell 5.1 executable used by
# the user's double-click CMD launcher. Encode as UTF-16LE to prevent the
# legacy host from misreading the Cyrillic Yandex exe file name.
$encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($ps))
& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand $encoded
if ($LASTEXITCODE -ne 0) { throw 'W78_CHECKER_5_1_RUNTIME_ERROR' }
if (!(Test-Path -LiteralPath $report)) { throw 'W78_REPORT_NOT_CREATED' }
$out = [IO.File]::ReadAllText($report)
Write-Output 'W78_SYNTHETIC_REPORT_START'
Write-Output $out
Write-Output 'W78_SYNTHETIC_REPORT_END'
foreach ($claim in @('CHECK=CELIKOM_NATIVE_READ_ONLY_V2',
   'CHECK_COMPLETED=YES', 'INTEGRATION_ASSET_VERSION=0.24.24',
   'CURRENT_EXE=CELIKOM_APPLIED', 'CURRENT_ASAR=CELIKOM_APPLIED',
   'HOST_PAIR_RESULT=ACTIVE_RECORDED_HASHES_MATCH',
   'ORIGINAL_EXE_BACKUP_HASH_OK=True','ORIGINAL_ASAR_BACKUP_HASH_OK=True',
   'ACTION=NO_HOST_FILES_CHANGED', 'RECENT_SAFE_EVENTS_COUNT=1')) {
   if (!$out.Contains($claim)) { throw ('W78_MISSING_EXPECTED_'+$claim) }
}
if ((& $sha $exe) -ne $record.AppliedExe -or
    (& $sha $asar) -ne $record.AppliedAsar) {throw 'W78_CHECKER_MUTATED_HOST'}
Write-Output 'W78_WINDOWS_POWERSHELL_5_1_READONLY_HOST_CHECK_V2_PASS'
