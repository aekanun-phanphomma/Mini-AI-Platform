#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Phase 0 / Windows side: install WSL2 + Ubuntu and write %USERPROFILE%\.wslconfig.
  See docs/adr/0003-wsl2-linux-filesystem.md

.NOTES
  Comments are in English on purpose: Windows PowerShell 5.1 reads BOM-less
  UTF-8 files as ANSI, so Thai text would be garbled or break parsing.
  Safe to re-run (idempotent).
#>
param(
    [string]$Distro = "Ubuntu-24.04",
    [int]$MemoryGB = 12,
    [int]$Processors = 6,
    [int]$SwapGB = 8
)
$ErrorActionPreference = "Stop"

# --- 1. Sanity check: leave headroom for Windows itself -----------------------
$totalGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
if ($MemoryGB -gt ($totalGB - 4)) {
    $MemoryGB = [math]::Max(4, $totalGB - 4)
    Write-Warning "Host has ${totalGB}GB RAM; capping WSL memory at ${MemoryGB}GB"
}

# --- 2. Install WSL + distro if missing ---------------------------------------
$distros = @()
try {
    # wsl.exe prints UTF-16; strip NUL chars before comparing
    $distros = (wsl.exe --list --quiet) -replace "`0", "" | Where-Object { $_ -ne "" }
} catch {
    Write-Host "WSL not installed yet."
}

if ($distros -contains $Distro) {
    Write-Host "==> $Distro already installed"
} else {
    Write-Host "==> Installing WSL2 + $Distro (a reboot may be required)"
    wsl.exe --install -d $Distro
    Write-Host "After reboot, open '$Distro' from the Start menu once to create your Linux user."
}

wsl.exe --update
wsl.exe --set-default-version 2

# --- 3. .wslconfig: resource limits for the WSL VM ----------------------------
# Without limits WSL may take up to 50% of RAM and never give it back.
$wslconfig = Join-Path $env:USERPROFILE ".wslconfig"
$content = @"
# Managed by Mini-AI-Platform/bootstrap/windows/setup-wsl.ps1
[wsl2]
memory=${MemoryGB}GB
processors=$Processors
swap=${SwapGB}GB
localhostForwarding=true

[experimental]
autoMemoryReclaim=gradual
sparseVhd=true
"@

if (Test-Path $wslconfig) {
    $old = Get-Content $wslconfig -Raw
    if ($old -ne $content) {
        Copy-Item $wslconfig "$wslconfig.bak" -Force
        Write-Host "==> Backed up existing .wslconfig to .wslconfig.bak"
    }
}
Set-Content -Path $wslconfig -Value $content -Encoding ascii
Write-Host "==> Wrote $wslconfig (memory=${MemoryGB}GB, processors=$Processors)"

Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. wsl --shutdown          (apply .wslconfig)"
Write-Host "  2. Open $Distro, clone the repo into ~/code (NOT /mnt/c), run ./bootstrap/bootstrap.sh"
