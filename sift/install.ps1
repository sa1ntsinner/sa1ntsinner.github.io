# sift installer for Windows: puts the latest release into %LOCALAPPDATA%\Programs\sift and adds it to PATH.
#   irm https://sa1ntsinner.github.io/sift/install.ps1 | iex
# $env:SIFT_INSTALL_DIR picks another folder.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$dir = if ($env:SIFT_INSTALL_DIR) { $env:SIFT_INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA 'Programs\sift' }
$url = 'https://github.com/sa1ntsinner/sift/releases/latest/download/sift-windows-x64.exe'

New-Item -ItemType Directory -Force $dir | Out-Null
Write-Host "Downloading $url"
Invoke-WebRequest $url -OutFile "$dir\sift.exe.part" -UseBasicParsing
Move-Item -Force "$dir\sift.exe.part" "$dir\sift.exe"
& "$dir\sift.exe" --version

# User PATH lives in the registry as REG_EXPAND_SZ; keep it that way (SetEnvironmentVariable would flatten it).
$key = Get-Item 'HKCU:\Environment'
$path = $key.GetValue('Path', '', 'DoNotExpandEnvironmentNames')
if (($path -split ';') -notcontains $dir) {
    Set-ItemProperty 'HKCU:\Environment' Path (($path.TrimEnd(';') + ";$dir").TrimStart(';')) -Type ExpandString
    # Tell Explorer that PATH changed, so new terminals see it without signing out.
    [Environment]::SetEnvironmentVariable('SIFT_INSTALLING', '1', 'User')
    [Environment]::SetEnvironmentVariable('SIFT_INSTALLING', $null, 'User')
    $env:Path = "$env:Path;$dir"
    Write-Host 'Done. Run: sift (in a new terminal window)'
} else {
    Write-Host 'Done. Run: sift'
}
