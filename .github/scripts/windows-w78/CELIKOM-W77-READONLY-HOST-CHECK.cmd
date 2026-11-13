@echo off
set "CELIKOM_HOST_CHECK_SOURCE=%~f0"
title CELIKOM - READ ONLY YANDEX CHECK
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$s=[IO.File]::ReadAllText($env:CELIKOM_HOST_CHECK_SOURCE,[Text.Encoding]::UTF8); $mark='###CELIKOM_POWERSHELL_START###'; $i=$s.LastIndexOf($mark); if($i -lt 0){throw 'HOST_CHECK_MISSING'}; Invoke-Expression $s.Substring($i+$mark.Length)"
echo.
pause >nul
exit /b 0
###CELIKOM_POWERSHELL_START###
$ErrorActionPreference='Continue'
$lines=New-Object System.Collections.Generic.List[string]
function Add([string]$name,[object]$value) { $repr=if($null -eq $value){'NULL'}else{[string]$value};$script:lines.Add($name+'='+$repr) }
function Hash([string]$path) {
 if(-not (Test-Path -LiteralPath $path -PathType Leaf)){return 'MISSING'}
 try{return (Get-FileHash -LiteralPath $path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()}
 catch{return 'READ_ERROR'}
}
function Tag([string]$hash,[string]$o,[string]$a) {
 if($hash -eq 'MISSING'){return 'MISSING'}
 if($hash -eq 'READ_ERROR'){return 'READ_ERROR'}
 if($hash -eq $o -and $o.Length -eq 64){return 'ORIGINAL'}
 if($hash -eq $a -and $a.Length -eq 64){return 'CELIKOM_APPLIED'}
 return 'CHANGED_OR_UNKNOWN'
}
Add 'CHECK' 'CELIKOM_NATIVE_READ_ONLY_V3'
Add 'UTC' ([DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'))
Add 'COMPUTER_PATHS_INCLUDED' 'NO'
Add 'SESSION_AND_ACCOUNTS_READ' 'NO'
$root=Join-Path $env:LOCALAPPDATA 'Programs\YandexMusic'
$app=Join-Path $env:LOCALAPPDATA 'Programs\CELIKOM'
$backup=Join-Path $env:LOCALAPPDATA 'CELIKOM\Windows\NativeHost\snapshot'
$manifest=Join-Path $backup 'recovery.json'
$exe=Join-Path $root 'Яндекс Музыка.exe'
$asar=Join-Path $root 'resources\app.asar'
$targetApp=Join-Path $app 'CELIKOM.Companion.exe'
Add 'YANDEX_DIR_EXISTS' (Test-Path -LiteralPath $root -PathType Container)
Add 'CELIKOM_DIR_EXISTS' (Test-Path -LiteralPath $app -PathType Container)
Add 'BACKUP_DIR_EXISTS' (Test-Path -LiteralPath $backup -PathType Container)
Add 'YANDEX_PROCESS_RUNNING' ([bool](Get-Process -Name 'Яндекс Музыка' -ErrorAction SilentlyContinue))
try { $appVersion=if(Test-Path -LiteralPath $targetApp){(Get-Item -LiteralPath $targetApp).VersionInfo.FileVersion}else{'MISSING'};Add 'APP_VERSION' $appVersion }catch{Add 'APP_VERSION' 'READ_ERROR'}
try { $exeVersion=if(Test-Path -LiteralPath $exe){(Get-Item -LiteralPath $exe).VersionInfo.FileVersion}else{'MISSING'};Add 'YANDEX_EXE_VERSION' $exeVersion }catch{Add 'YANDEX_EXE_VERSION' 'READ_ERROR'}
$hostModulePath=Join-Path $app 'integration\host.cjs'
try{
 $body=Get-Content -LiteralPath $hostModulePath -Raw -ErrorAction Stop
 $match=[regex]::Match($body,'CELIKOM_NATIVE_VERSION\s*=\s*"([0-9.]+)"')
 $version=if($match.Success){$match.Groups[1].Value}else{'UNKNOWN'};Add 'INTEGRATION_ASSET_VERSION' $version
}catch{Add 'INTEGRATION_ASSET_VERSION' 'MISSING_OR_ERROR'}
$eh=Hash $exe
$ah=Hash $asar
Add 'YANDEX_EXE_EXISTS' ($eh -notin @('MISSING','READ_ERROR'))
Add 'YANDEX_ASAR_EXISTS' ($ah -notin @('MISSING','READ_ERROR'))
Add 'OFFICIAL_51261_ASAR' ($ah -eq '5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215')
if(-not (Test-Path -LiteralPath $manifest -PathType Leaf)){ Add 'MANIFEST' 'MISSING' }
else {
 try {
  $m=Get-Content -LiteralPath $manifest -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
  Add 'MANIFEST' 'READABLE'
  Add 'MANIFEST_SCHEMA' $m.Schema
  Add 'MANIFEST_STATE' $m.State
  Add 'MANIFEST_ROOT_MATCH' ([string]::Equals([IO.Path]::GetFullPath($root).TrimEnd('\'),[IO.Path]::GetFullPath([string]$m.InstallRoot).TrimEnd('\'),[StringComparison]::OrdinalIgnoreCase))
  Add 'ORIGINAL_EXE_BACKUP_HASH_OK' ((Hash (Join-Path $backup 'original.exe')) -eq $m.OriginalExe)
  Add 'ORIGINAL_ASAR_BACKUP_HASH_OK' ((Hash (Join-Path $backup 'original.asar')) -eq $m.OriginalAsar)
  Add 'CURRENT_EXE' (Tag $eh ([string]$m.OriginalExe) ([string]$m.AppliedExe))
  Add 'CURRENT_ASAR' (Tag $ah ([string]$m.OriginalAsar) ([string]$m.AppliedAsar))
  if($m.State -eq 'ACTIVE' -and $eh -eq $m.AppliedExe -and $ah -eq $m.AppliedAsar){Add 'HOST_PAIR_RESULT' 'ACTIVE_RECORDED_HASHES_MATCH'}
  elseif($eh -eq $m.OriginalExe -and $ah -eq $m.OriginalAsar){Add 'HOST_PAIR_RESULT' 'BOTH_ORIGINAL'}
  elseif($eh -in @($m.AppliedExe,$m.OriginalExe) -and $ah -in @($m.AppliedAsar,$m.OriginalAsar)){Add 'HOST_PAIR_RESULT' 'MIXED_OR_INTERRUPTED'}
  else{Add 'HOST_PAIR_RESULT' 'UNRECOGNIZED_CHANGE_NO_AUTOREPAIR'}
 }catch{Add 'MANIFEST' 'PARSE_OR_READ_FAILED'}
}
Add 'ACTION' 'NO_HOST_FILES_CHANGED'
$diagnostics=Join-Path $env:LOCALAPPDATA 'CELIKOM\Windows\companion-events.log'
if(Test-Path -LiteralPath $diagnostics -PathType Leaf){
 try {
  $events=Get-Content -LiteralPath $diagnostics -Tail 1200 -ErrorAction Stop | Where-Object {$_ -match '^20\d\d-[0-9TZ:.-]+\|(APP_UPDATE_|NATIVE_|START_HOST_PREFLIGHT_BLOCKED|GUI_STARTED)'} | Select-Object -Last 80
  Add 'RECENT_SAFE_EVENTS_COUNT' @($events).Count
  foreach($event in $events){$lines.Add($event)}
 }catch{ Add 'RECENT_SAFE_EVENTS' 'READ_ERROR' }
}
$desktop=[Environment]::GetFolderPath('DesktopDirectory')
if(-not (Test-Path -LiteralPath $desktop -PathType Container)){$desktop=Join-Path $env:USERPROFILE 'Downloads'}
$dest=Join-Path $desktop 'CELIKOM-YANDEX-CHECK.txt'
Add 'CHECK_COMPLETED' 'YES'
try{[IO.File]::WriteAllLines($dest,$lines,[Text.UTF8Encoding]::new($true));Write-Host 'ПРОВЕРКА ЗАВЕРШЕНА. Отправь файл CELIKOM-YANDEX-CHECK.txt с рабочего стола сюда.' -ForegroundColor Green}
catch{Write-Host 'Не удалось записать файл на рабочий стол. Результаты ниже:'; $lines | ForEach-Object { Write-Host $_ }}