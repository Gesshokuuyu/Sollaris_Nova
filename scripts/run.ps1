# Launcher automatico transparente para Sollaris Nova (PowerShell)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

# 1. Auto-provisionamento caso .venv nao exista
if (-not (Test-Path $PythonExe)) {
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host "  Sollaris Nova - Inicializacao Automatica (Python 3.14)" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host "[*] Ambiente virtual nao encontrado. Configurando automaticamente..." -ForegroundColor Yellow
    
    try {
        & py -3.14 -m venv .venv
    } catch {
        try {
            & py -m venv .venv
        } catch {
            & python -m venv .venv
        }
    }

    if (-not (Test-Path $PythonExe)) {
        Write-Host "[ERRO] Nao foi possivel criar o ambiente virtual com Python 3.14." -ForegroundColor Red
        exit 1
    }

    Write-Host "[*] Instalando dependencias do projeto..." -ForegroundColor Yellow
    & $PythonExe -m pip install --upgrade pip | Out-Null
    & $PythonExe -m pip install -r requirements-dev.txt
    Write-Host "[*] Ambiente preparado com sucesso!" -ForegroundColor Green
    Write-Host ""
}

# 2. Execucao da aplicacao
& $PythonExe (Join-Path $ProjectRoot "main.py") @args
