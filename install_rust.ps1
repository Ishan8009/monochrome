# ==========================================
# Automated Rust Setup Script for Windows
# ==========================================

$ErrorActionPreference = "Stop"

Write-Host "=== Rust & Cargo Environment Installer ===" -ForegroundColor Cyan

# 1. Check if Rust is already installed
if (Get-Command cargo -ErrorAction SilentlyContinue) {
    $cargoVersion = cargo --version
    Write-Host "Rust is already installed: $cargoVersion" -ForegroundColor Green
    Exit 0
}

# 2. Download rustup-init.exe
$installerUrl = "https://win.rustup.rs/x86_64"
$installerPath = Join-Path $env:TEMP "rustup-init.exe"

Write-Host "[1/3] Downloading Rust installer..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath

# 3. Run rustup-init silently
Write-Host "[2/3] Installing Rust toolchain (please wait)..." -ForegroundColor Yellow
Start-Process -FilePath $installerPath -ArgumentList "-y" -Wait -NoNewWindow

# Clean up installer
Remove-Item -Path $installerPath -Force -ErrorAction SilentlyContinue

# 4. Refresh PATH environment variable for current session
Write-Host "[3/3] Updating PATH environment variables..." -ForegroundColor Yellow
$userCargoPath = "$env:USERPROFILE\.cargo\bin"

if (Test-Path $userCargoPath) {
    $env:PATH = "$userCargoPath;$env:PATH"
}

# 5. Verify installation
if (Get-Command cargo -ErrorAction SilentlyContinue) {
    $installedVersion = cargo --version
    Write-Host "SUCCESS! Installed: $installedVersion" -ForegroundColor Green
    Write-Host "You can now run python build_desktop_app.py to compile your app!" -ForegroundColor Cyan
} else {
    Write-Host "Installation finished. Please close and reopen your terminal window to refresh PATH." -ForegroundColor Yellow
}