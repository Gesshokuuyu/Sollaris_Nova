# Guia de Configuração e Execução do Ambiente (Sollaris Nova)

Este documento fornece as instruções para configurar o ambiente de desenvolvimento, instalar as dependências e executar o aplicativo no Windows 10/11.

---

## 1. Pré-requisitos
- **Sistema Operacional:** Windows 10 ou Windows 11 (64-bit).
- **Python:** Versão 3.14 (3.14.3 testada).
  - Verifique com o comando:
    ```powershell
    py -3.14 --version
    ```

---

## 2. Execução Zero-Touch e Atalho na Área de Trabalho (Desktop)

Você **não precisa** abrir terminais nem conviver com janelas pretas de console.

### Opção A (Recomendada): Ícone Oficial no Desktop
1. Dê um duplo clique em `create_desktop_shortcut.bat` (ou execute `.\create_desktop_shortcut.ps1`).
2. Isso cria o atalho oficial com ícone personalizado na sua **Área de Trabalho** (`Sollaris Nova.lnk`) e na raiz do projeto.
3. Ao clicar no ícone, a aplicação abre de forma **100% silenciosa** via `pythonw.exe`, sem abrir nenhuma janela de prompt de comando.

### Opção B: Lançador Silencioso Direto
- Dê um duplo clique em `launch_silent.vbs`.

### Opção C: Lançador Batch no Terminal
- Dê um duplo clique em `run.bat` (ou execute `.\run.ps1` no PowerShell).

---

## 3. Configuração Manual Passo a Passo

Caso prefira executar manualmente:

```powershell
# 1. Criar o ambiente virtual com Python 3.12
py -3.12 -m venv .venv

# 2. Ativar o ambiente virtual
.\.venv\Scripts\Activate.ps1

# 3. Atualizar o pip
python -m pip install --upgrade pip

# 4. Instalar as dependências do projeto
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## 4. Como Executar a Aplicação

Com o ambiente virtual ativado:
```powershell
python main.py
```

Ou através dos atalhos rápidos:
- PowerShell: `.\run.ps1`
- CMD: `run.bat`

---

## 5. Como Executar os Testes Automatizados

Para rodar todos os testes com relatório detalhado:
```powershell
.\.venv\Scripts\pytest -v
```

Para rodar com medição de cobertura:
```powershell
.\.venv\Scripts\pytest --cov=core --cov=app tests/
```

---

## 6. Verificação de Código e Formatação (Ruff)

Para checar linter e regras de código sem modificar arquivos:
```powershell
.\.venv\Scripts\ruff check .
```

Para aplicar correções automáticas de formatação e importações:
```powershell
.\.venv\Scripts\ruff format .
.\.venv\Scripts\ruff check --fix .
```
