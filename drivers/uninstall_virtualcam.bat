@echo off
:: ============================================
:: VirtualCam Studio - Desinstalação do Driver
:: Remove o registro do driver de câmera virtual
:: Requer privilégios de administrador
:: ============================================

net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ============================================
echo   VirtualCam Studio - Driver Uninstaller
echo ============================================
echo.

set "OBS_DIR="
if exist "C:\Program Files\obs-studio\data\obs-plugins\win-dshow" (
    set "OBS_DIR=C:\Program Files\obs-studio\data\obs-plugins\win-dshow"
)
if exist "C:\Program Files (x86)\obs-studio\data\obs-plugins\win-dshow" (
    set "OBS_DIR=C:\Program Files (x86)\obs-studio\data\obs-plugins\win-dshow"
)

if defined OBS_DIR (
    echo Removendo registro do driver de camera virtual...
    
    if exist "%OBS_DIR%\obs-virtualcam-module64.dll" (
        regsvr32 /s /u "%OBS_DIR%\obs-virtualcam-module64.dll"
        echo [OK] Driver 64-bit removido.
    )
    
    if exist "%OBS_DIR%\obs-virtualcam-module32.dll" (
        regsvr32 /s /u "%OBS_DIR%\obs-virtualcam-module32.dll"
        echo [OK] Driver 32-bit removido.
    )
    
    echo.
    echo Driver de camera virtual removido com sucesso.
) else (
    echo Nenhum driver encontrado para remover.
)

echo.
pause
