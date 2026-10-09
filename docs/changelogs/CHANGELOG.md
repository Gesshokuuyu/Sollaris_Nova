# Changelog — Sollaris Nova (PC Optimizer)

Todas as alterações notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Não Lançado] - Em Desenvolvimento

### Planejado para a Fase 2 (Dashboard Completo)
- Thread assíncrona de coleta com fila thread-safe (`core.monitor.MonitorService`).
- Buffer circular de 60 segundos com `collections.deque(maxlen=60)`.
- Gráfico histórico duplo de CPU e RAM em tempo real com Matplotlib.
- Monitor de processos (Top 5 por uso de memória RAM) com tratamento de permissões.

---

## [0.1.0-alpha] - 2026-10-09 (Fase 1: Fundação & Hardware)

### Adicionado
- **Núcleo de Métricas Autênticas (`core/hardware.py`):**
  - Dataclasses imutáveis tipadas: `SensorReading`, `CpuMetrics`, `RamMetrics`, `DiskPartitionMetrics`, `GpuMetrics` e `SystemSnapshot`.
  - Coletor de hardware (`HardwareCollector`) via `psutil`, `platform` e WMI (`Win32_VideoController`).
  - Tratamento resiliente de sensores ACPI: captura limpa de `wmi.x_access_denied` sem crash ou zeros artificiais.
  - Filtro protetor de partições: supressão de exceções em unidades de cartão de memória ou discos vazios.
  - Formatadores de precisão: `format_bytes`, `format_frequency` e `format_uptime`.
- **Design System & Navegação Sem Emojis (`app/components/sidebar.py`):**
  - Barra lateral de 220px com navegação técnica.
  - Conjunto de 14 ícones monocromáticos em PNG (`assets/nav_icons/`) para estados normal e ativo das rotas.
- **Painel Técnico de Hardware (`app/window.py`):**
  - Header bar com timestamp da amostragem, badge de estabilidade e botão "Atualizar Agora".
  - Cartão de CPU com destaque percentual, progresso colorido, modelo, núcleos, frequências e temperatura.
  - Cartão de RAM com proporção em uso / total, barra de progresso e nota técnica sobre cache reaproveitável.
  - Cartão de Armazenamento multi-partição dinâmico com alertas para unidades abaixo de 15 GB livres.
  - Cartão de GPU & Sensores com nome da placa, versão do driver e status de interface WMI.
  - Cartão do Sistema com versão do Windows, compilação, arquitetura e uptime formatado.
  - Barra de rodapé técnica com status operacional.
- **Ponto de Entrada Integrado (`main.py`):**
  - Conexão nativa com `MainWindow`.
  - CLI com flags `--check-env` e `--verbose`.
- **Suíte de Testes Automatizados (`tests/`):**
  - 15 testes automatizados aprovados no `pytest` cobrindo o ambiente, a camada de hardware e a interface gráfica.
- **Artefatos e Governança:**
  - Criação de `docs/phases/PHASE_1_FOUNDATION.md`.
  - Atualização do catálogo vivo `docs/specs/FUTURE_REQUIREMENTS.md`.
  - Atualização dos critérios de aceite em `docs/specs/MVP_CRITERIA.md`.

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
