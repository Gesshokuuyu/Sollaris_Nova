# Setup automatizado do ambiente de desenvolvimento no PowerShell (Python 3.14)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Configuracao de Ambiente: Sollaris Nova (Python 3.14)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[*] Criando ambiente virtual Python 3.14..." -ForegroundColor Yellow
    py -3.14 -m venv .venv
} else {
    Write-Host "[*] Ambiente virtual .venv ja existe." -ForegroundColor Green
}

Write-Host "[*] Atualizando pip..." -ForegroundColor Yellow
& $VenvPython -m pip install --upgrade pip

Write-Host "[*] Instalando dependencias de desenvolvimento e producao..." -ForegroundColor Yellow
& $VenvPython -m pip install -r requirements-dev.txt

Write-Host ""
Write-Host "[SUCESSO] Ambiente preparado com sucesso no Python 3.14!" -ForegroundColor Green
Write-Host "Para rodar a aplicacao: .\scripts\run.ps1 ou clique duplo em scripts\run.bat" -ForegroundColor Cyan
Write-Host "Para rodar os testes:   .\.venv\Scripts\pytest -v" -ForegroundColor Cyan
