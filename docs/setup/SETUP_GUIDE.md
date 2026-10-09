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

## 2. Execução Zero-Touch (Automática com 1 Clique)

Você **não precisa** rodar comandos manuais de criação de ambiente ou ativação.

Basta dar **duplo clique no arquivo `run.bat`** (ou executar `.\run.ps1` no PowerShell):
1. O launcher detecta se o ambiente `.venv` já existe com Python 3.14.
2. Se não existir, ele cria a `.venv` e instala todas as dependências automaticamente em segundo plano.
3. Inicia o aplicativo diretamente.

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
