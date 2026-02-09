@echo off
echo Iniciando VirtualCam Studio...
cd /d "%~dp0"
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
python src\main.py
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao iniciar. Verifique se as dependencias estao instaladas:
    echo   pip install -r requirements.txt
    pause
)
