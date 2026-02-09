@echo off
echo ============================================
echo   VirtualCam Studio - Instalacao Dev
echo   (Versao Otimizada - ~50 MB total)
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Instale Python 3.11+ de https://python.org
    pause
    exit /b 1
)

echo [1/4] Criando ambiente virtual...
python -m venv venv
call venv\Scripts\activate.bat

echo.
echo [2/4] Instalando dependencias otimizadas...
echo        opencv-python-headless (sem GUI Qt)
echo        customtkinter (em vez de PyQt5)
pip install -r requirements.txt

echo.
echo [3/4] Removendo dependencias pesadas (se existirem)...
pip uninstall PyQt5 PyQt5-sip PyQt5-Qt5 opencv-python -y >nul 2>&1

echo.
echo [4/4] Gerando templates...
python src\template_generator.py

echo.
echo ============================================
echo   Instalacao concluida!
echo.
echo   Para executar:
echo     run.bat
echo   Ou:
echo     venv\Scripts\activate.bat
echo     python src\main.py
echo ============================================
pause
