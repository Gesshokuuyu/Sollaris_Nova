@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo  Configuracao de Ambiente: Sollaris Nova (Python 3.14)
echo ========================================================

where py >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] O inicializador Python 'py' nao foi localizado no PATH.
    echo Instale o Python 3.14 antes de prosseguir.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [*] Criando ambiente virtual com Python 3.14...
    py -3.14 -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao criar .venv com py -3.14. Tentando python padrao...
        python -m venv .venv
        if %errorlevel% neq 0 (
            echo [ERRO] Nao foi possivel criar o ambiente virtual.
            pause
            exit /b 1
        )
    )
) else (
    echo [*] Ambiente virtual .venv ja existe.
)

echo [*] Atualizando pip e instalando dependencias...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

if %errorlevel% equ 0 (
    echo.
    echo [SUCESSO] Ambiente preparado com sucesso no Python 3.14!
    echo Para iniciar o aplicativo com um clique duplo: run.bat
) else (
    echo.
    echo [ERRO] Falha ao instalar dependencias.
)
pause
