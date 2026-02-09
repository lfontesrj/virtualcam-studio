@echo off
:: ============================================
:: VirtualCam Studio - Instalação do Driver
:: Registra o driver de câmera virtual no sistema
:: Requer privilégios de administrador
:: ============================================

:: Check for admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Solicitando privilegios de administrador...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ============================================
echo   VirtualCam Studio - Driver Installer
echo ============================================
echo.

:: Determine script directory
set "SCRIPT_DIR=%~dp0"

:: Try to register OBS virtual camera if OBS is installed
set "OBS_DIR="
if exist "C:\Program Files\obs-studio\data\obs-plugins\win-dshow" (
    set "OBS_DIR=C:\Program Files\obs-studio\data\obs-plugins\win-dshow"
)
if exist "C:\Program Files (x86)\obs-studio\data\obs-plugins\win-dshow" (
    set "OBS_DIR=C:\Program Files (x86)\obs-studio\data\obs-plugins\win-dshow"
)

if defined OBS_DIR (
    echo [INFO] OBS Studio detectado.
    echo [INFO] Registrando camera virtual do OBS...
    
    if exist "%OBS_DIR%\obs-virtualcam-module64.dll" (
        regsvr32 /s "%OBS_DIR%\obs-virtualcam-module64.dll"
        if %errorlevel% equ 0 (
            echo [OK] Driver 64-bit registrado com sucesso!
        ) else (
            echo [ERRO] Falha ao registrar driver 64-bit.
        )
    )
    
    if exist "%OBS_DIR%\obs-virtualcam-module32.dll" (
        regsvr32 /s "%OBS_DIR%\obs-virtualcam-module32.dll"
        if %errorlevel% equ 0 (
            echo [OK] Driver 32-bit registrado com sucesso!
        ) else (
            echo [ERRO] Falha ao registrar driver 32-bit.
        )
    )
    
    echo.
    echo [SUCESSO] Camera virtual instalada!
    echo Agora voce pode selecionar "OBS Virtual Camera" no Teams, Zoom, etc.
    goto :done
)

:: OBS not found - show instructions
echo [AVISO] OBS Studio nao foi encontrado no sistema.
echo.
echo Para usar o VirtualCam Studio, voce precisa do driver de camera virtual.
echo.
echo Opcao 1 (Recomendada):
echo   Instale o OBS Studio de: https://obsproject.com/download
echo   Depois execute este script novamente.
echo.
echo Opcao 2:
echo   Se voce ja tem o OBS instalado em outro local,
echo   abra o OBS e clique em "Iniciar Camera Virtual" uma vez.
echo.

:done
echo.
pause
