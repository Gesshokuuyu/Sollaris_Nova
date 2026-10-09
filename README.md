# Sollaris Nova — PC Optimizer

Aplicativo desktop em Python para monitoramento técnico de hardware, diagnóstico explicável de gargalos e manutenção preventiva no Windows 10 e 11.

---

## 1. Visão Geral e Princípios

O Sollaris Nova é um utilitário focado em transparência, estabilidade e respeito ao sistema operacional:

- **Medições Autênticas:** Métricas reais de CPU, RAM, Armazenamento e Sensores térmicos obtidas via chamadas diretas ao Windows (Kernel32, Psapi, Registro e WMI). Não utiliza estimativas arbitrárias ou pontuações de saúde fictícias.
- **Arquitetura Não-Bloqueante:** O loop visual da interface (CustomTkinter) opera a 60 FPS constantes. Toda a coleta de hardware roda em thread desacoplada em segundo plano (`MonitorService`), consumindo dados via filas atômicas sem travar a interface (*zero-freeze*).
- **Execução Segura:** Opera sem necessidade de privilégios de Administrador (sem janelas de UAC). Tratamento resiliente de permissões de processos e discos removíveis sem mídia.
- **Privacidade Total:** 100% offline, sem envio de telemetria ou comunicação de rede externa.

---

## 2. Como o Aplicativo Funciona

```
[Hardware / SO Windows]
   │  (Kernel32, Psapi, Winreg, psutil)
   ▼
[MonitorService (Thread em Background)]  ──>  Coleta de snapshot em sub-15ms
   │  (Fila thread-safe atômica / queue.Queue)
   ▼
[MainWindow (GUI CustomTkinter)]         ──>  Reciclagem de widgets em sub-0.5ms (60 FPS)
   ├── Visão Geral (CPU, RAM, Swap, Discos, GPU, Top Processos)
   ├── Diagnóstico Explicável (Regras técnicas com severidade)
   ├── Limpeza Segura (Varredura não-destrutiva de temporários)
   ├── Inicialização (Programas no Registro HKCU/HKLM)
   ├── Modo Game (Perfis de energia e prioridade)
   └── Histórico da Sessão (Médias e picos)
```

---

## 3. Pré-requisitos

- **Sistema Operacional:** Windows 10 ou Windows 11 (64-bit).
- **Python:** Versão 3.14 ou superior instalada e acessível no PATH do Windows.

---

## 4. Instalação e Configuração

### Opção 1: Setup Automático via Script
Na raiz do repositório, execute o script correspondente ao seu terminal para criar o ambiente virtual `.venv` e instalar todas as dependências:

- **Via Prompt de Comando (CMD):**
  ```cmd
  scripts\setup_env.bat
  ```

- **Via PowerShell:**
  ```powershell
  .\scripts\setup_env.ps1
  ```

### Opção 2: Instalação Manual via Pip
```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## 5. Como Executar

### 5.1 Atalho na Área de Trabalho (Recomendado)
Para criar o atalho oficial com ícone personalizado na Área de Trabalho e na raiz do projeto:

- Dê um duplo clique em `scripts\create_desktop_shortcut.bat`, ou rode no PowerShell:
  ```powershell
  .\scripts\create_desktop_shortcut.ps1
  ```
- O atalho executa a aplicação de forma silenciosa via `scripts\launch_silent.vbs`, sem abrir janelas de terminal.

### 5.2 Execução via Linha de Comando ou Scripts
- **CMD:** `scripts\run.bat`
- **PowerShell:** `.\scripts\run.ps1`
- **Direto pelo Python:**
  ```powershell
  .\.venv\Scripts\python.exe main.py
  ```

### 5.3 Diagnóstico do Ambiente via CLI
Para verificar as bibliotecas e a detecção de hardware diretamente pelo terminal:
```powershell
.\.venv\Scripts\python.exe main.py --check-env
```

---

## 6. Testes Automatizados e Qualidade de Código

### Executar a Suíte de Testes
```powershell
.\.venv\Scripts\pytest -v
```

### Checagem de Linter e Padrões (Ruff)
```powershell
.\.venv\Scripts\ruff check .
```

---

## 7. Estrutura do Projeto

```
Sollaris_Nova/
├── app/                        # Camada de Interface Gráfica (CustomTkinter)
│   ├── components/             # Sidebar técnica e componentes reutilizáveis
│   ├── theme.py                # Tokens de cores e tipografia Segoe UI
│   └── window.py               # Janela principal e reciclagem de widgets
├── core/                       # Núcleo de Coleta e Lógica de Negócio
│   ├── hardware.py             # Coletor de hardware (Kernel32, psutil, WMI)
│   ├── monitor.py              # Thread assíncrona de monitoramento
│   ├── processes.py            # Coleta de processos em sub-15ms (Win32)
│   ├── diagnostics.py          # Motor de diagnóstico explicável
│   ├── cleaner.py              # Varredura não-destrutiva de temporários
│   └── startup.py              # Enumeração de inicialização (Registro)
├── scripts/                    # Scripts utilitários de execução e atalhos
│   ├── run.bat / run.ps1       # Executores rápidos da aplicação
│   ├── setup_env.bat / .ps1    # Provisionamento do ambiente virtual
│   ├── launch_silent.vbs       # Lançador sem janela de console
│   └── create_desktop_shortcut # Gerador de atalho oficial no Desktop
├── assets/                     # Ícones monocromáticos e identidade visual
├── docs/                       # Documentação técnica e governança
│   ├── architecture/           # Detalhes de concorrência e camadas
│   ├── changelogs/             # Registro formal de alterações
│   ├── phases/                 # Relatórios de conclusão de fases
│   ├── setup/                  # Guia estendido de configuração
│   ├── specs/                  # Critérios de aceite e requisitos futuros
│   └── standards/              # Normas de código e Design System
├── tests/                      # Testes automatizados (pytest)
├── main.py                     # Ponto de entrada da aplicação
├── requirements.txt            # Dependências de produção
├── requirements-dev.txt        # Dependências de desenvolvimento e testes
└── LICENSE                     # Licença MIT
```

---

## 8. Licença

Este projeto é distribuído sob a licença [MIT](LICENSE). Consulte o arquivo [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) para atribuições de bibliotecas de terceiros.
