@echo off
setlocal
cd /d "%~dp0.."
set "ROOT_DIR=%cd%"
title Sollaris Nova - PC Optimizer

set "VENV_PYTHON=%ROOT_DIR%\.venv\Scripts\python.exe"

REM Se o ambiente virtual ja existe, inicia diretamente
if exist "%VENV_PYTHON%" goto :LAUNCH

echo ========================================================
echo  Sollaris Nova - Auto-Provisionamento (Python 3.14)
echo ========================================================
echo [*] Preparando ambiente isolado pela primeira vez...

where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3.14 -m venv "%ROOT_DIR%\.venv" 2>nul
    if errorlevel 1 (
        py -m venv "%ROOT_DIR%\.venv"
    )
) else (
    python -m venv "%ROOT_DIR%\.venv"
)

if not exist "%VENV_PYTHON%" (
    echo [ERRO] Nao foi possivel criar o ambiente virtual com Python 3.14.
    echo Certifique-se de que o Python 3.14 esta instalado no Windows.
    pause
    exit /b 1
)

echo [*] Instalando dependencias do projeto...
"%VENV_PYTHON%" -m pip install --upgrade pip >nul 2>&1
"%VENV_PYTHON%" -m pip install -r "%ROOT_DIR%\requirements-dev.txt"
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias no ambiente virtual.
    pause
    exit /b 1
)
echo [*] Ambiente preparado com sucesso!
echo.

:LAUNCH
"%VENV_PYTHON%" "%ROOT_DIR%\main.py" %*
if errorlevel 1 (
    echo.
    echo [AVISO] Aplicativo encerrado com codigo de erro %errorlevel%.
    pause
)
