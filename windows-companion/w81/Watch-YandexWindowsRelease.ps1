# PowerShell 7 on Windows runner. Portable between GitHub Actions and private Windows CI.
# Downloads vendor packages into RUNNER_TEMP ONLY. Never runs vendor installer or
# publishes untested compatibility entries. Outputs a small JSON report.
[CmdletBinding()]
param(
    [string]$CatalogPath = 'windows-companion/w24/compatibility/official-yandex-builds-v1.json',
    [string]$ReportPath = 'windows-w81-vendor-watch-report.json',
    [string]$ForceVersion = '',
    [switch]$ValidateCandidate
)
$ErrorActionPreference = 'Stop'
$base = 'https://music-desktop-application.s3.yandex.net/stable'
$origin = "$base/latest.yml"
$report = [ordered]@{
    schema = 1; status = 'failed'; vendorVersion = ''; exeVersion = ''
    installerSha256 = ''; exeSha256 = ''; asarSha256 = ''
    checks = @(); releaseFeed = $origin; candidateRequiresReview = $false
}
function Save-Report {
    $parent = Split-Path -Parent $ReportPath
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $report | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 -Path $ReportPath
}
try {
    if (!(Test-Path -LiteralPath $CatalogPath)) { throw 'REVIEWED_CATALOG_NOT_FOUND' }
    $catalog = Get-Content -LiteralPath $CatalogPath -Raw | ConvertFrom-Json
    if ($catalog.schema -ne 1 -or $catalog.purpose -ne 'celikom-windows-yandex-official-baselines') {
        throw 'INVALID_REVIEWED_CATALOG'
    }
    $response = Invoke-WebRequest -Uri $origin -TimeoutSec 20 -MaximumRedirection 0
    if ([int]$response.StatusCode -ne 200 -or $response.RawContentLength -gt 16384) {
        throw 'OFFICIAL_WINDOWS_UPDATE_MANIFEST_UNAVAILABLE'
    }
    # Some Yandex S3 manifests come as application/octet-stream: IWR returns
    # byte[] Content rather than string on Windows PowerShell 7.
    $yaml = if ($response.Content -is [byte[]]) {
        [Text.Encoding]::UTF8.GetString($response.Content)
    } else { [string]$response.Content }
    if ($yaml.Length -gt 16384) { throw 'OFFICIAL_WINDOWS_FEED_TOO_LARGE' }
    $versionMatch = [regex]::Match($yaml, '(?m)^version:\s*(5\.[0-9]{1,4}\.[0-9]{1,3})\s*$')
    if (!$versionMatch.Success) { throw 'OFFICIAL_WINDOWS_FEED_VERSION_NOT_FOUND' }
    $latest = $versionMatch.Groups[1].Value
    $version = if ($ForceVersion) { $ForceVersion } else { $latest }
    if ($version -notmatch '^5\.[0-9]{1,4}\.[0-9]{1,3}$') {
        throw 'OFFICIAL_WINDOWS_VERSION_INVALID'
    }
    $report.vendorVersion = $version
    $report.checks += "official-windows-feed:$latest"

    $reviewed = @($catalog.builds | Where-Object {
        $_.status -eq 'verified' -and
        $_.version.StartsWith(($version + '.'), [StringComparison]::Ordinal)
    })
    if (!$ForceVersion -and $reviewed.Count -eq 1) {
        $report.status = 'already_supported'
        $report.checks += 'reviewed-version-retained'
        Write-Host "W81_VENDOR_VERSION_ALREADY_SUPPORTED $version"
        Save-Report
        exit 0
    }

    if (!$ValidateCandidate) {
        $report.status = 'new_release_detected'
        $report.candidateRequiresReview = $true
        Write-Host "W81_NEW_WINDOWS_YANDEX_RELEASE $version"
        Save-Report
        exit 0
    }

    $setupName = "Yandex_Music_x64_$version.exe"
    $url = "$base/$setupName"
    $dir = Join-Path ([IO.Path]::GetTempPath()) ("celikom-w81-official-"+[Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $dir | Out-Null
    try {
        $file = Join-Path $dir $setupName
        # HEAD checks avoid pulling unbounded third-party binaries.
        $head = Invoke-WebRequest -Uri $url -Method Head -TimeoutSec 20 -MaximumRedirection 0
        $size = [long](@($head.Headers['Content-Length'])[0])
        if ($size -lt 50000000 -or $size -gt 220000000) {
            throw 'OFFICIAL_SETUP_SIZE_NOT_EXPECTED'
        }
        Invoke-WebRequest -Uri $url -OutFile $file -TimeoutSec 240 -MaximumRedirection 0
        if ((Get-Item $file).Length -ne $size) { throw 'OFFICIAL_SETUP_DOWNLOAD_TRUNCATED' }
        $installerSig = Get-AuthenticodeSignature -FilePath $file
        if ($installerSig.Status -ne 'Valid' -or
            $installerSig.SignerCertificate.Subject -notmatch 'YANDEX LLC') {
            throw 'OFFICIAL_SETUP_SIGNATURE_OR_PUBLISHER_INVALID'
        }
        $report.installerSha256 = (Get-FileHash $file -Algorithm SHA256).Hash.ToLowerInvariant()
        $out = Join-Path $dir 'extracted'
        New-Item -ItemType Directory -Path $out | Out-Null
        & 'C:\Program Files\7-Zip\7z.exe' x -y "-o$out" $file | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'OFFICIAL_SETUP_EXTRACT_FAILED' }
        $nested = @(Get-ChildItem -Path $out -Recurse -File -Filter 'app-64.7z')
        if ($nested.Count -ne 1) { throw 'OFFICIAL_INTERNAL_ARCHIVE_UNKNOWN' }
        $inner = Join-Path $out 'inner'
        New-Item -ItemType Directory -Path $inner | Out-Null
        & 'C:\Program Files\7-Zip\7z.exe' x -y "-o$inner" $nested[0].FullName | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'OFFICIAL_INNER_EXTRACT_FAILED' }
        $executables = @(Get-ChildItem $inner -Recurse -File | Where-Object Name -eq 'Яндекс Музыка.exe')
        $archives = @(Get-ChildItem $inner -Recurse -File | Where-Object Name -eq 'app.asar')
        if ($executables.Count -ne 1 -or $archives.Count -ne 1) {
            throw 'OFFICIAL_HOST_PAIR_NOT_UNIQUE'
        }
        $exe = $executables[0].FullName
        $asar = $archives[0].FullName
        $exeSig = Get-AuthenticodeSignature -FilePath $exe
        if ($exeSig.Status -ne 'Valid' -or
            $exeSig.SignerCertificate.Subject -notmatch 'YANDEX LLC') {
            throw 'OFFICIAL_INNER_EXE_NOT_TRUSTED'
        }
        $exeVersion = [Diagnostics.FileVersionInfo]::GetVersionInfo($exe).FileVersion
        if (!$exeVersion.StartsWith("$version.",[StringComparison]::Ordinal)) {
            throw 'OFFICIAL_INNER_EXE_VERSION_MISMATCH'
        }
        $report.exeVersion = $exeVersion
        $report.exeSha256 = (Get-FileHash $exe -Algorithm SHA256).Hash.ToLowerInvariant()
        $report.asarSha256 = (Get-FileHash $asar -Algorithm SHA256).Hash.ToLowerInvariant()
        $report.checks += 'vendor-installer-signature'
        $report.checks += 'inner-executable-signature-and-version'
        $assets = 'windows-companion/w23/dist'
        if (!(Test-Path "$assets/host.cjs") -or !(Test-Path "$assets/renderer.js")) {
            throw 'CELIKOM_NATIVE_MODULE_ASSETS_NOT_BUILT'
        }
        $stage = Join-Path $dir 'staged-images'
        dotnet run --project 'windows-companion/w24/Celikom.NativeInstaller.Cli/Celikom.NativeInstaller.Cli.csproj' -c Release -- $exe $asar "$assets/host.cjs" "$assets/renderer.js" $report.exeSha256 $report.asarSha256 $stage
        if ($LASTEXITCODE -ne 0) { throw 'W81_VENDOR_IMAGE_BUILD_FAILED' }
        $image = Get-Content (Join-Path $stage 'W24-image-hashes.json') -Raw | ConvertFrom-Json
        if ($image.integrityOccurrences -lt 1) { throw 'W81_NO_INTEGRITY_CHECK_REPLACED' }
        $report.checks += 'native-image-builder-staged'
        $report.status = 'candidate_requires_runtime_review'
        $report.candidateRequiresReview = $true
        Write-Host "W81_OFFICIAL_YANDEX_CANDIDATE_STAGED $version exactEXE=$($report.exeSha256)"
    }
    finally {
        if (Test-Path $dir) { Remove-Item -Path $dir -Recurse -Force }
    }
}
catch {
    $report.status = 'failed'
    $report.checks += ([string]$_.Exception.Message -replace '[^A-Z0-9_]','_')
    Save-Report
    throw
}
Save-Report
