# W155 — one-time CELIKOM P-256 key creation using built-in Windows PowerShell only.
# No Node.js, GitHub CLI, package manager, token or password is required on the owner PC.
# The private key is created locally and is never printed. The owner adds it once as a
# protected GitHub Environment secret through the browser opened by this script.

[CmdletBinding()]
param(
    [string]$KeyDirectory = (Join-Path $env:LOCALAPPDATA "CELIKOM\StableManifestKey"),
    [switch]$NoUi
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") { throw "W155_WINDOWS_REQUIRED" }
if ($PSVersionTable.PSVersion.Major -lt 5) { throw "W155_WINDOWS_POWERSHELL_5_REQUIRED" }
if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) { throw "W155_LOCALAPPDATA_REQUIRED" }

$localRoot = [IO.Path]::GetFullPath($env:LOCALAPPDATA).TrimEnd('\')
$keyRoot = [IO.Path]::GetFullPath($KeyDirectory).TrimEnd('\')
$localPrefix = $localRoot + [IO.Path]::DirectorySeparatorChar
if (!$keyRoot.StartsWith($localPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "W155_KEY_DIRECTORY_MUST_BE_UNDER_LOCALAPPDATA"
}
if ($keyRoot.Contains('"') -or $keyRoot.Contains('&') -or $keyRoot.Contains('|') -or
    $keyRoot.Contains('<') -or $keyRoot.Contains('>') -or $keyRoot.Contains('^') -or
    $keyRoot.Contains('%') -or $keyRoot.Contains('!')) {
    throw "W155_KEY_DIRECTORY_PATH_UNSAFE"
}

function Assert-NoReparseAncestors([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    $drive = [IO.Path]::GetPathRoot($full)
    $current = $drive
    foreach ($segment in ($full.Substring($drive.Length) -split '[\\/]')) {
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
Assert-NoReparseAncestors $keyRoot

if (Test-Path -LiteralPath $keyRoot) {
    $existing = Get-Item -LiteralPath $keyRoot -Force
    if (!$existing.PSIsContainer -or
        ($existing.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "W155_KEY_DIRECTORY_UNSAFE"
    }
    if (@(Get-ChildItem -LiteralPath $keyRoot -Force).Count -gt 0) {
        throw "W155_KEYPAIR_ALREADY_EXISTS_DO_NOT_REGENERATE"
    }
} else {
    New-Item -ItemType Directory -Path $keyRoot -Force | Out-Null
}

# Restrict the key directory to the current Windows user and SYSTEM.
$currentSid = [Security.Principal.WindowsIdentity]::GetCurrent().User
$systemSid = New-Object Security.Principal.SecurityIdentifier("S-1-5-18")
$inherit = [Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
    [Security.AccessControl.InheritanceFlags]::ObjectInherit
$acl = New-Object Security.AccessControl.DirectorySecurity
$acl.SetAccessRuleProtection($true, $false)
$acl.SetOwner($currentSid)
$userRule = [Security.AccessControl.FileSystemAccessRule]::new(
    $currentSid, [Security.AccessControl.FileSystemRights]::FullControl,
    $inherit, [Security.AccessControl.PropagationFlags]::None,
    [Security.AccessControl.AccessControlType]::Allow)
$systemRule = [Security.AccessControl.FileSystemAccessRule]::new(
    $systemSid, [Security.AccessControl.FileSystemRights]::FullControl,
    $inherit, [Security.AccessControl.PropagationFlags]::None,
    [Security.AccessControl.AccessControlType]::Allow)
[void]$acl.AddAccessRule($userRule)
[void]$acl.AddAccessRule($systemRule)
Set-Acl -LiteralPath $keyRoot -AclObject $acl

function Join-Bytes([byte[]]$Left, [byte[]]$Right) {
    $joined = New-Object byte[] ($Left.Length + $Right.Length)
    [Array]::Copy($Left, 0, $joined, 0, $Left.Length)
    [Array]::Copy($Right, 0, $joined, $Left.Length, $Right.Length)
    return ,$joined
}
function New-DerLength([int]$Length) {
    if ($Length -lt 128) { return ,([byte[]]@([byte]$Length)) }
    $octets = New-Object 'System.Collections.Generic.List[byte]'
    $remaining = $Length
    while ($remaining -gt 0) {
        $octets.Insert(0, [byte]($remaining -band 0xff))
        $remaining = [int][Math]::Floor($remaining / 256)
    }
    $result = New-Object byte[] ($octets.Count + 1)
    $result[0] = [byte](0x80 -bor $octets.Count)
    for ($i = 0; $i -lt $octets.Count; $i++) { $result[$i + 1] = $octets[$i] }
    return ,$result
}
function New-DerTlv([byte]$Tag, [byte[]]$Value) {
    $tagBytes = [byte[]]@($Tag)
    $lengthBytes = New-DerLength $Value.Length
    $header = Join-Bytes -Left $tagBytes -Right $lengthBytes
    return ,(Join-Bytes -Left $header -Right $Value)
}

$ecdsa = $null
$parameters = $null
$privatePem = $null
$createdFiles = New-Object 'System.Collections.Generic.List[string]'
$tempFiles = New-Object 'System.Collections.Generic.List[string]'
try {
    $ecdsa = [Security.Cryptography.ECDsaCng]::new(256)
    $parameters = $ecdsa.ExportParameters($true)
    if ($parameters.D.Length -ne 32 -or $parameters.Q.X.Length -ne 32 -or
        $parameters.Q.Y.Length -ne 32) {
        throw "W155_P256_KEY_PARAMETERS_INVALID"
    }

    # DER AlgorithmIdentifier: id-ecPublicKey + prime256v1.
    $oidEcPublicKey = [byte[]]@(0x06,0x07,0x2A,0x86,0x48,0xCE,0x3D,0x02,0x01)
    $oidPrime256v1 = [byte[]]@(0x06,0x08,0x2A,0x86,0x48,0xCE,0x3D,0x03,0x01,0x07)
    $algorithmBody = Join-Bytes -Left $oidEcPublicKey -Right $oidPrime256v1
    $algorithmIdentifier = New-DerTlv -Tag 0x30 -Value $algorithmBody

    # Uncompressed EC point and its DER BIT STRING.
    $point = Join-Bytes -Left ([byte[]]@(0x04)) -Right $parameters.Q.X
    $point = Join-Bytes -Left $point -Right $parameters.Q.Y
    $bitStringBody = Join-Bytes -Left ([byte[]]@(0x00)) -Right $point
    $publicBitString = New-DerTlv -Tag 0x03 -Value $bitStringBody

    # SEC1 ECPrivateKey wrapped in PKCS#8 PrivateKeyInfo (BEGIN PRIVATE KEY).
    $sec1Version = [byte[]]@(0x02,0x01,0x01)
    $privateOctets = New-DerTlv -Tag 0x04 -Value $parameters.D
    $curveParameters = New-DerTlv -Tag 0xA0 -Value $oidPrime256v1
    $publicField = New-DerTlv -Tag 0xA1 -Value $publicBitString
    $sec1Body = Join-Bytes -Left $sec1Version -Right $privateOctets
    $sec1Body = Join-Bytes -Left $sec1Body -Right $curveParameters
    $sec1Body = Join-Bytes -Left $sec1Body -Right $publicField
    $sec1 = New-DerTlv -Tag 0x30 -Value $sec1Body

    $pkcs8Version = [byte[]]@(0x02,0x01,0x00)
    $privateKeyOctets = New-DerTlv -Tag 0x04 -Value $sec1
    $pkcs8Body = Join-Bytes -Left $pkcs8Version -Right $algorithmIdentifier
    $pkcs8Body = Join-Bytes -Left $pkcs8Body -Right $privateKeyOctets
    $pkcs8 = New-DerTlv -Tag 0x30 -Value $pkcs8Body

    $spkiBody = Join-Bytes -Left $algorithmIdentifier -Right $publicBitString
    $spki = New-DerTlv -Tag 0x30 -Value $spkiBody
    $publicBase64 = [Convert]::ToBase64String($spki)
    $base64Private = [Convert]::ToBase64String($pkcs8)
    $newline = [Environment]::NewLine
    $pemLines = New-Object 'System.Collections.Generic.List[string]'
    for ($offset = 0; $offset -lt $base64Private.Length; $offset += 64) {
        $count = [Math]::Min(64, $base64Private.Length - $offset)
        $pemLines.Add($base64Private.Substring($offset, $count))
    }
    $privatePem = "-----BEGIN PRIVATE KEY-----" + $newline +
        ($pemLines -join $newline) + $newline + "-----END PRIVATE KEY-----" + $newline

    $privatePath = Join-Path $keyRoot "manifest-private.pem"
    $publicDerPath = Join-Path $keyRoot "manifest-public.der"
    $publicTextPath = Join-Path $keyRoot "manifest-public-base64.txt"
    $nonce = [Guid]::NewGuid().ToString("N")
    $privateTemp = $privatePath + ".tmp-" + $nonce
    $publicDerTemp = $publicDerPath + ".tmp-" + $nonce
    $publicTextTemp = $publicTextPath + ".tmp-" + $nonce
    foreach ($path in @($privateTemp, $publicDerTemp, $publicTextTemp)) { $tempFiles.Add($path) }

    [IO.File]::WriteAllText($privateTemp, $privatePem, [Text.Encoding]::ASCII)
    [IO.File]::WriteAllBytes($publicDerTemp, $spki)
    [IO.File]::WriteAllText($publicTextTemp, $publicBase64 + $newline, [Text.Encoding]::ASCII)

    [IO.File]::Move($privateTemp, $privatePath); $createdFiles.Add($privatePath)
    [IO.File]::Move($publicDerTemp, $publicDerPath); $createdFiles.Add($publicDerPath)
    [IO.File]::Move($publicTextTemp, $publicTextPath); $createdFiles.Add($publicTextPath)

    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $fingerprint = [BitConverter]::ToString($sha.ComputeHash($spki)).Replace("-", "").ToLowerInvariant()
    } finally { $sha.Dispose() }

    Write-Output "W155_P256_LOCAL_KEYPAIR_CREATED"
    Write-Output "Public key fingerprint: $fingerprint"
    Write-Output "Private key file: $privatePath"
    Write-Output "Public key file: $publicTextPath"
    Write-Output "The private PEM was not printed. Do not send it to ChatGPT or commit it."

    if (!$NoUi) {
        Start-Process "https://github.com/manufact-test/nomusic/settings/environments/windows-stable-owner-build"
        Start-Process -FilePath (Join-Path $env:WINDIR "System32\notepad.exe") -ArgumentList ('"' + $privatePath + '"')
    }
}
catch {
    foreach ($path in $createdFiles) {
        Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
    }
    throw
}
finally {
    foreach ($path in $tempFiles) {
        Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
    }
    if ($null -ne $parameters -and $null -ne $parameters.D) {
        [Array]::Clear($parameters.D, 0, $parameters.D.Length)
    }
    if ($null -ne $privatePem) { $privatePem = $null }
    if ($null -ne $ecdsa) { $ecdsa.Dispose() }
}
