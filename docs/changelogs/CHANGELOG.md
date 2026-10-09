# Changelog — Sollaris Nova (PC Optimizer)

Todas as alterações notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Não Lançado] - Em Desenvolvimento

### Planejado para o MVP (Fases 1 a 3)
- Monitoramento de CPU, memória RAM e armazenamento em tempo real.
- Detecção e leitura de sensores de temperatura (CPU/GPU) com fallback resiliente.
- Gráficos históricos de 60 segundos com Matplotlib integrado ao CustomTkinter.
- Lista ordenada dos processos com maior consumo de RAM e uso de CPU.
- Motor de diagnósticos com persistência de amostras e explicações técnicas.

---

## [0.1.0-setup] - 2026-10-09

### Adicionado
- **Estrutura Base do Repositório:** Criação da árvore de pastas seguindo a especificação técnica (`app/`, `core/`, `database/`, `safety/`, `tests/`, `data/`, `docs/`).
- **Documentação de Contexto e Governança:**
  - `PROJECT_SPEC.md` e `docs/specs/PROJECT_SPEC.md`: Especificação técnica completa de produto, arquitetura, métricas e fases.
  - `docs/specs/MVP_CRITERIA.md`: Critérios de aceitação objetivos e Definição de Pronto (DoD) para o MVP.
  - `docs/architecture/ARCHITECTURE.md`: Detalhamento de camadas, modelo de dados imutável e fluxo de dados assíncrono entre threads.
  - `docs/standards/CODE_STANDARDS.md`: Diretrizes de código PEP 8, tipagem estática, tratamento resiliente de processos e convenções de commit.
  - `docs/standards/DESIGN_SYSTEM.md`: Paleta técnica de cores (#0B0F14 a #EF4444), tipografia Segoe UI, espaçamento e regras visuais.
  - `docs/setup/SETUP_GUIDE.md`: Guia de configuração de ambiente e comandos de execução.
- **Ambiente de Execução e Auto-Bootstrap:**
  - Upgrade do ambiente virtual para **Python 3.14.3** com compilação e wheels validadas (`psutil`, `customtkinter`, `matplotlib`, `WMI`, `pywin32`, `pytest`).
  - Lançador inteligente e transparente (`run.bat` / `run.ps1`): auto-provisionamento em segundo plano sem exigir comandos manuais (Zero-Touch execution).
  - Arquivos `requirements.txt` e `requirements-dev.txt` com dependências congeladas e testadas.
  - Criação do `.gitignore` abrangente para desenvolvimento Python e Windows.
  - Scripts de conveniência de execução e setup (`run.bat`, `run.ps1`, `setup_env.bat`, `setup_env.ps1`).
- **Governança de Ciclo de Vida e CI/CD:**
  - `docs/workflow/DEVELOPMENT_AND_RELEASE_FLOW.md`: Estratégia de branches permanentes (`main`, `lts`, `testing`, `develop`), branches temporárias (`feature/*`, `fix/*`, `hotfix/*`, `release/*`) e tratamento de demandas orientado a issues.
  - `.github/ISSUE_TEMPLATE/`: Formulários estruturados para reporte de bugs gerais, falhas de sensores/hardware e solicitações de novas funcionalidades.
  - `.github/PULL_REQUEST_TEMPLATE.md`: Template com checklist de DoD, vinculação obrigatória de issues e regras de qualidade.
  - `.github/workflows/ci.yml`: Pipeline de CI ativo desde já para testes e linter no Windows com Python 3.14.
  - `.github/workflows/release-build.yml`: Pipeline de empacotamento com PyInstaller (.exe) e publicação de releases preparado para ativação pós-MVP (Fase 6).
- **Tokens de Design e Assets de Identidade:**
  - `assets/icon.ico` e `assets/icon.png`: Criação do ícone técnico multi-resolução do projeto (16x16 até 256x256) com o tema azul e preto minimalista.
  - `launch_silent.vbs`: Inicializador 100% silencioso via `pythonw.exe`, eliminando a exibição de janelas de terminal.
  - `create_desktop_shortcut.bat` e `create_desktop_shortcut.ps1`: Gerador automatizado de atalho do Windows na Área de Trabalho com ícone oficial.
  - `app/theme.py`: Mapeamento centralizado de cores, fontes e dimensões do Design System para CustomTkinter.
- **Qualidade e Testes:**
  - Criação do primeiro teste unitário de ambiente e integridade (`tests/test_environment.py`).
