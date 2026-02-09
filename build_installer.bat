@echo off
echo ============================================================
echo   VirtualCam Studio - Build Otimizado do Instalador
echo   Gera um instalador compacto para distribuicao
echo ============================================================
echo.

REM ---- Pre-requisitos ----
echo [VERIFICANDO] Pre-requisitos...

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale Python 3.11+
    pause
    exit /b 1
)
echo   [OK] Python encontrado

pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando PyInstaller...
    pip install pyinstaller
)
echo   [OK] PyInstaller disponivel

where iscc >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Inno Setup (iscc) nao encontrado no PATH.
    echo         O instalador nao sera gerado automaticamente.
    echo         Instale de: https://jrsoftware.org/isinfo.php
    set "SKIP_INNO=1"
) else (
    echo   [OK] Inno Setup encontrado
    set "SKIP_INNO=0"
)

REM ---- Verificar UPX ----
where upx >nul 2>&1
if errorlevel 1 (
    echo [AVISO] UPX nao encontrado. Binarios nao serao comprimidos.
    echo         Instale UPX para reduzir o tamanho em ~30%%:
    echo         https://github.com/upx/upx/releases
    set "HAS_UPX=0"
) else (
    echo   [OK] UPX encontrado - binarios serao comprimidos
    set "HAS_UPX=1"
)

echo.

REM ---- Etapa 1: Instalar dependencias (otimizadas) ----
echo [1/5] Instalando dependencias Python (otimizadas)...
echo        opencv-python-headless (em vez de opencv-python)
echo        customtkinter (em vez de PyQt5)
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)
REM Garantir que PyQt5 nao esta instalado (economia de ~80 MB)
pip uninstall PyQt5 PyQt5-sip PyQt5-Qt5 -y >nul 2>&1
REM Garantir que opencv-python full nao esta (economia de ~45 MB)
pip uninstall opencv-python -y >nul 2>&1
echo   [OK] Dependencias otimizadas instaladas

echo.

REM ---- Etapa 2: Gerar templates ----
echo [2/5] Gerando templates de overlay...
python src\template_generator.py
echo   [OK] Templates gerados

echo.

REM ---- Etapa 3: Compilar com PyInstaller ----
echo [3/5] Compilando executavel com PyInstaller...
echo         (isso pode levar alguns minutos)
echo         Usando: strip=True, upx=True, exclusoes agressivas
pyinstaller virtualcam_studio.spec --noconfirm --clean
if errorlevel 1 (
    echo [ERRO] Falha na compilacao PyInstaller.
    pause
    exit /b 1
)

REM ---- Mostrar tamanho do build ----
echo   [OK] Executavel compilado em dist\VirtualCamStudio\
for /f "tokens=3" %%a in ('dir dist\VirtualCamStudio /s /-c ^| findstr "bytes"') do set SIZE=%%a
echo   Tamanho total: %SIZE% bytes

echo.

REM ---- Etapa 4: Verificar OBS Installer ----
echo [4/5] Verificando OBS Installer para bundle...
if not exist "installer\OBS-Studio-Full-Installer-x64.exe" (
    echo   [INFO] OBS Installer nao encontrado em installer\
    echo   Para incluir o OBS no instalador, baixe de:
    echo     https://obsproject.com/download
    echo   E coloque como: installer\OBS-Studio-Full-Installer-x64.exe
    echo.
    echo   SEM o OBS: instalador fica ~30-40 MB (compacto!)
    echo   COM o OBS: instalador fica ~230 MB (all-in-one)
) else (
    echo   [OK] OBS Installer encontrado - sera incluido no bundle
)

echo.

REM ---- Etapa 5: Gerar instalador Inno Setup ----
if "%SKIP_INNO%"=="1" (
    echo [5/5] Pulando geracao do instalador (Inno Setup nao disponivel)
    echo.
    echo ============================================================
    echo   BUILD PARCIAL CONCLUIDO!
    echo.
    echo   Executavel: dist\VirtualCamStudio\VirtualCamStudio.exe
    echo.
    echo   Para gerar o instalador, instale o Inno Setup e execute:
    echo     iscc installer\setup_allinone.iss
    echo ============================================================
) else (
    echo [5/5] Gerando instalador com Inno Setup...
    mkdir dist\installer 2>nul
    iscc installer\setup_allinone.iss
    if errorlevel 1 (
        echo [ERRO] Falha ao gerar instalador.
        pause
        exit /b 1
    )
    echo.
    echo ============================================================
    echo   BUILD COMPLETO - VERSAO OTIMIZADA!
    echo.
    echo   Executavel: dist\VirtualCamStudio\VirtualCamStudio.exe
    echo   Instalador: dist\installer\VirtualCamStudio_Setup_v1.0.0.exe
    echo.
    echo   Comparativo de tamanho:
    echo     Versao anterior: ~720 MB instalado, ~230 MB download
    echo     Versao otimizada: ~60-70 MB instalado, ~30-40 MB download
    echo.
    echo   O instalador pode ser distribuido para os usuarios.
    echo ============================================================
)

echo.
pause
