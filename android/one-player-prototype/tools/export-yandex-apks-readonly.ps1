# CELIKOM Android feasibility — authorized owner's offline APK-only export.
# Requires adb in PATH + user-approved USB debugging. DOES NOT install/uninstall/modify anything.
# Output is PRIVATE and may contain proprietary third-party code; do not publish to GitHub.
$ErrorActionPreference = 'Stop'
$package = 'ru.yandex.music'
if (-not (Get-Command adb -ErrorAction SilentlyContinue)) {
  throw 'adb not found. Install official Android Platform Tools first.'
}
$serial = (& adb devices | Select-String '^[^\s]+\s+device$' | ForEach-Object {
    ($_.Line -split '\s+')[0]
})
if (@($serial).Count -ne 1) {
  throw 'Connect exactly one authorized Android device with USB debugging approved.'
}
$serial = @($serial)[0]
$paths = @(& adb -s $serial shell pm path $package |
  ForEach-Object { $_.Trim().Replace([char]13,'') } |
  Where-Object { $_ -match '^package:/' } |
  ForEach-Object { $_.Substring(8) })
if ($paths.Count -eq 0) { throw 'Package not found. No changes made.' }
$root = Join-Path (Get-Location) ('CELIKOM-private-yandex-apk-inventory-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $root | Out-Null
$rows = @()
for ($i = 0; $i -lt $paths.Count; $i++) {
  $localName = ('apk-part-{0:D2}.apk' -f ($i + 1))
  $dest = Join-Path $root $localName
  & adb -s $serial pull $paths[$i] $dest | Out-Null
  if ($LASTEXITCODE -ne 0 -or !(Test-Path $dest)) {
    throw 'Copy failed. Phone remains unchanged.'
  }
  $hash = (Get-FileHash -Algorithm SHA256 $dest).Hash.ToLowerInvariant()
  $rows += [pscustomobject]@{file=$localName; sha256=$hash; bytes=(Get-Item $dest).Length}
}
$rows | ConvertTo-Json -Depth 3 | Set-Content -Encoding UTF8 (Join-Path $root 'checksums.json')
$zip = $root + '.zip'
Compress-Archive -LiteralPath (Join-Path $root '*') -DestinationPath $zip -CompressionLevel Optimal
Write-Output ('PRIVATE APK snapshot: ' + $zip)
Write-Output ('Extracted APK parts: ' + $rows.Count)
Write-Output 'NO user data, OAuth/session files, app databases, or music cache copied.'
Write-Output 'Do not upload this proprietary APK archive to a public repository.'
