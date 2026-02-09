# ============================================
# VirtualCam Studio - OBS Silent Installer
# Downloads and installs OBS Studio silently
# Requires administrator privileges
# ============================================

param(
    [switch]$Unattended = $false
)

$ErrorActionPreference = "Stop"

# Configuration
$OBS_VERSION = "31.0.1"
$OBS_INSTALLER_URL = "https://cdn-fastly.obsproject.com/downloads/OBS-Studio-${OBS_VERSION}-Full-Installer-x64.exe"
$OBS_INSTALLER_FILE = "$env:TEMP\OBS-Studio-Installer.exe"
$OBS_INSTALL_DIR = "C:\Program Files\obs-studio"

function Write-Status($msg) {
    Write-Host "[VirtualCam Studio] $msg" -ForegroundColor Cyan
}

function Write-Success($msg) {
    Write-Host "[OK] $msg" -ForegroundColor Green
}

function Write-Err($msg) {
    Write-Host "[ERRO] $msg" -ForegroundColor Red
}

# Check if OBS is already installed
if (Test-Path "$OBS_INSTALL_DIR\bin\64bit\obs64.exe") {
    Write-Success "OBS Studio ja esta instalado em: $OBS_INSTALL_DIR"
    
    # Register virtual camera
    $vcamDll = "$OBS_INSTALL_DIR\data\obs-plugins\win-dshow\obs-virtualcam-module64.dll"
    if (Test-Path $vcamDll) {
        Write-Status "Registrando camera virtual..."
        Start-Process "regsvr32" -ArgumentList "/s `"$vcamDll`"" -Wait -Verb RunAs
        Write-Success "Camera virtual registrada!"
    }
    exit 0
}

# Check admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Err "Este script precisa ser executado como Administrador."
    if (-not $Unattended) {
        Write-Host "Reiniciando com privilegios elevados..."
        Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    }
    exit 1
}

# Download OBS
Write-Status "Baixando OBS Studio v${OBS_VERSION}..."
Write-Status "URL: $OBS_INSTALLER_URL"

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($OBS_INSTALLER_URL, $OBS_INSTALLER_FILE)
    Write-Success "Download concluido: $OBS_INSTALLER_FILE"
} catch {
    Write-Err "Falha no download: $_"
    Write-Host ""
    Write-Host "Voce pode baixar manualmente de: https://obsproject.com/download"
    if (-not $Unattended) { Read-Host "Pressione Enter para sair" }
    exit 1
}

# Install OBS silently
Write-Status "Instalando OBS Studio silenciosamente..."
try {
    $process = Start-Process -FilePath $OBS_INSTALLER_FILE -ArgumentList "/S" -Wait -PassThru
    if ($process.ExitCode -eq 0) {
        Write-Success "OBS Studio instalado com sucesso!"
    } else {
        Write-Err "Instalacao retornou codigo: $($process.ExitCode)"
    }
} catch {
    Write-Err "Falha na instalacao: $_"
    if (-not $Unattended) { Read-Host "Pressione Enter para sair" }
    exit 1
}

# Register virtual camera
Start-Sleep -Seconds 2
$vcamDll64 = "$OBS_INSTALL_DIR\data\obs-plugins\win-dshow\obs-virtualcam-module64.dll"
$vcamDll32 = "$OBS_INSTALL_DIR\data\obs-plugins\win-dshow\obs-virtualcam-module32.dll"

if (Test-Path $vcamDll64) {
    Write-Status "Registrando camera virtual (64-bit)..."
    Start-Process "regsvr32" -ArgumentList "/s `"$vcamDll64`"" -Wait
    Write-Success "Driver 64-bit registrado!"
}

if (Test-Path $vcamDll32) {
    Write-Status "Registrando camera virtual (32-bit)..."
    Start-Process "regsvr32" -ArgumentList "/s `"$vcamDll32`"" -Wait
    Write-Success "Driver 32-bit registrado!"
}

# Cleanup
Remove-Item $OBS_INSTALLER_FILE -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Success "Instalacao concluida!"
Write-Host "A camera virtual 'OBS Virtual Camera' esta disponivel no sistema."
Write-Host ""

if (-not $Unattended) {
    Read-Host "Pressione Enter para fechar"
}
