@echo off
setlocal
cd /d "%~dp0"
title Sollaris Nova - Criar Atalho na Area de Trabalho

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create_desktop_shortcut.ps1"
if errorlevel 1 (
    echo [ERRO] Falha ao criar o atalho.
    pause
    exit /b 1
)

echo.
pause
