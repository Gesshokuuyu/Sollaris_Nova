# Changelog — Sollaris Nova (PC Optimizer)

Todas as alterações notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Não Lançado] - Em Desenvolvimento

### Planejado para a Fase 3 (Diagnóstico Explicável e Recomendações)
- Motor avançado de regras técnicas com janelas de persistência temporal (detecção de gargalos estáveis).
- Cartões explicativos com título, evidência numérica observada, explicação técnica, impacto, risco e reversibilidade.
- Notificações de alerta no badge de status e limites de tolerância configuráveis.

---

## [0.2.0-alpha] - 2026-10-09 (Fase 2: Dashboard, Gráficos & Medidores Tipo Gauge)

### Adicionado
- **Medidores Radiais Analógico-Digitais (`app/components/radial_gauge.py`):**
  - Componente técnico `RadialGauge` construído sobre `tk.Canvas` puro com atualização em sub-0.05ms.
  - Arco aberto de 240° de varredura, trilho passivo (#192331) e arco ativo colorido por carga (Azul/Verde até 70%, Amarelo até 85%, Vermelho acima de 85%).
  - Miolo digital com tipografia Segoe UI Bold em tempo real.
  - Variante padrão (116px) para cartões de CPU e Memória RAM.
  - Variante compacta (56px) para cada partição detectada no cartão de discos locais.
- **Gráfico Histórico dos Últimos 60 Segundos (`app/components/performance_chart.py`):**
  - Gráfico em tempo real embarcado no CustomTkinter via `FigureCanvasTkAgg`.
  - Estética Dark Minimalist combinando com os tokens do tema (`#111923`, `#0B0F14`, `#263345`).
  - Atualização por substituição de vetores via `set_data()` e despacho assíncrono não-bloqueante com `draw_idle()`, garantindo renderização em sub-2ms.
  - Seletores interativos em estilo pílula: `Ambos (CPU + RAM)`, `Apenas CPU` e `Apenas RAM`.
- **Estatísticas Temporais da Janela Móvel (`core/monitor.py`):**
  - Extração atômica e thread-safe de dados históricos com `get_history_snapshot()`.
  - Cálculo de média móvel, leitura máxima (pico) e leitura mínima dos últimos 60 segundos com `get_window_statistics()`.
  - Exibição de média e pico da janela diretamente nos cartões de CPU e RAM.
- **Testes Automatizados:**
  - `tests/test_radial_gauge.py`: 3 novos testes validando geometria de arcos, clamping de valores (0-100%) e limites cromáticos.
  - `tests/test_charts.py`: 4 novos testes cobrindo inicialização de figura, alternância de modos, atualização de amostras (0 a 60 pontos) e cálculos matemáticos de janela.
  - Suíte total expandida para 27 testes automatizados (100% de aprovação).

## [0.1.0-alpha] - 2026-10-09 (Fase 1: Fundação & Hardware)

### Adicionado
- **Núcleo de Métricas Autênticas & Baixo Nível (`core/hardware.py`):**
  - Dataclasses imutáveis tipadas: `SensorReading`, `CpuMetrics`, `RamMetrics`, `DiskPartitionMetrics`, `GpuMetrics` e `SystemSnapshot`.
  - Coletor de hardware (`HardwareCollector`) via `psutil`, `platform` e APIs nativas do Windows (`Kernel32`, `Psapi`, `Winreg`).
  - Coleta direta de partições em 1.5ms via `GetLogicalDriveStringsW` e `GetDiskFreeSpaceExW`, evitando timeouts em drives vazios.
  - Leitura instantânea de nome de processador via Registro do Windows (0.03ms).
  - Tratamento resiliente de sensores ACPI: captura limpa de `wmi.x_access_denied` sem crash ou zeros artificiais.
  - Formatadores de precisão: `format_bytes`, `format_frequency` e `format_uptime`.
- **Top Processos de Altíssima Velocidade (`core/processes.py`):**
  - Varredura em 13ms via `CreateToolhelp32Snapshot` e `GetProcessMemoryInfo`, eliminando overhead de 1.1s do `psutil`.
- **Serviço de Monitoramento Assíncrono (`core/monitor.py`):**
  - Daemon thread desacoplada com inicialização de COM (`CoInitialize`), fila atômica (`queue.Queue`) e evento de wake imediato (`threading.Event`).
- **Módulos de Sistema e Diagnóstico Inicial:**
  - `core/diagnostics.py`: Motor de diagnóstico explicável baseado em regras e persistência temporal.
  - `core/cleaner.py`: Varredura não-destrutiva de temporários e caches em background thread.
  - `core/startup.py`: Mapeamento de entradas de inicialização no Registro do Windows (HKCU/HKLM).
- **Design System, UI Fluida & Loader Não-Bloqueante (`app/`):**
  - Barra lateral de 220px com navegação técnica e 14 ícones monocromáticos vetoriais em PNG (`assets/nav_icons/`), sem emojis.
  - Sistema de loader visual: barra de progresso indeterminada de 3px e botões com transição de estado reativo (*"Atualizando..."* em 1.15ms).
  - Resolução de artefatos visuais: barras de progresso com 8px de altura sólida sem distorções de canvas, e pré-carregamento imediato de discos.
  - Cartões técnicos para CPU (com chips por núcleo lógico), RAM física e paginação, Discos, GPU/Display, Sistema e Top Processos.
- **Ponto de Entrada Integrado (`main.py`):**
  - Lançador desktop 100% silencioso (`launch_silent.vbs`) e atalho com ícone oficial `sollaris_nova.ico`.
- **Suíte de Testes Automatizados (`tests/`):**
  - 20 testes automatizados aprovados no `pytest` com 100% de sucesso.
- **Artefatos e Governança:**
  - Criação de `docs/phases/PHASE_1_FOUNDATION.md`.
  - Relatório técnico de desempenho e loader em `phase_1_performance_and_loader_report.md`.
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
