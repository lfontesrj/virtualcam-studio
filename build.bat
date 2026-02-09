@echo off
echo ============================================
echo   VirtualCam Studio - Build Script
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale Python 3.11+
    pause
    exit /b 1
)

echo [1/4] Instalando dependencias...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [2/4] Gerando templates...
python src/template_generator.py

echo.
echo [3/4] Compilando executavel com PyInstaller...
pyinstaller virtualcam_studio.spec --noconfirm

echo.
echo [4/4] Build concluido!
echo.
echo O executavel esta em: dist\VirtualCamStudio\VirtualCamStudio.exe
echo.
pause
