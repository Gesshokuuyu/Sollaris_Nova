# Changelog — Sollaris Nova (PC Optimizer)

Todas as alterações notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Não Lançado] - Em Desenvolvimento

### Planejado para a Fase 4 (Limpeza Segura e Otimização do Windows)
- Varredura de arquivos temporários do usuário e do sistema com verificação de segurança (whitelist).
- Gerenciamento de programas de inicialização via registro do Windows com confirmação prévia.
- Ponto de Restauração do Sistema (VSS) via WMI antes de modificações.
- Exclusão segura e reversível para a lixeira do Windows.

---

## [0.3.0-alpha] - 2026-10-09 (Fase 3: Diagnóstico Explicável & Gravador de Voo / Flight Recorder)

### Adicionado
- **Motor de Diagnóstico em 7 Dimensões (`core/diagnostics.py`):**
  - Implementação completa do `DiagnosticEngine` com o método `evaluate_with_history()`.
  - Estrutura de dados `DiagnosticFinding` enriquecida em 7 dimensões explicáveis: categoria, nível (`OPTIMAL`, `INFO`, `WARNING`, `CRITICAL`), título, evidência numérica observada, diagnóstico técnico profundo, impacto provável, risco da intervenção, reversibilidade e ação recomendada com rota de navegação contextual.
  - Eliminação de falsos positivos via persistência temporal: picos instantâneos transitórios de CPU (< 5s) são avaliados como normais (`OPTIMAL`). Alertas críticos exigem saturação sustentada comprovada (mínimo de 10 amostras consecutivas >= 85%).
  - Detecção especializada de gargalos: saturação de CPU, pressão de memória RAM, contenção de memória virtual (Swap Thrashing), esgotamento de espaço na unidade de sistema (`C:`) e identificação de processos predadores monopolizando recursos.
  - Preservação retroativa de propriedades `.description` e `.recommendation` para total compatibilidade com interfaces e testes existentes.
- **Relator Técnico de Sessão / Gravador de Voo Expandido (`core/recorder.py`):**
  - Gravação contínua e assíncrona de telemetria ("Flight Recorder") em arquivo de log estruturado sob demanda em `data/reports/`.
  - Arquitetura de I/O em segundo plano totalmente não-bloqueante (0ms de impacto na thread da interface gráfica) via `queue.Queue(maxsize=2000)` e thread trabalhadora daemon `SessionRecorderWriter`.
  - Cabeçalho técnico altamente detalhado com inventário de hardware, contagem de processos e threads ativos no SO, clock base e inicial, temperatura (WMI), VRAM de GPU e tabela completa de partições montadas (`C:`, `D:`, etc.) com ocupação e tipo de sistema de arquivos.
  - Amostragem cronológica a cada tick registrando CPU, clock atual, temperatura térmica, RAM física livre e utilizada, swap, top 5 processos detalhados (PID, nome, memória retida) e bloco analítico de cada anomalia ativa (evidência, causa raiz e recomendação técnica).
  - Sumário executivo analítico consolidando duração, cadência de amostragem, mínimos, médias e picos máximos de CPU/RAM, variação de working set ($\Delta$ RAM), discriminação de anomalias por categoria, ranking dos processos mais demandantes da sessão e parecer técnico conclusivo.
- **Interface de Diagnóstico Fluida e Sem Flickering (`app/pages/diagnostics.py`):**
  - Eliminação completa de piscamento de tela através do padrão de Card Pooling (`FindingCardWidget`): os cards são reciclados e atualizados *in-place* via `.configure()`, impedindo o colapso e reconstrução de geometria da GUI.
  - Memoização de assinatura de estado (`current_fingerprint`) evitando repinturas redundantes quando não há transição de severidade.
  - Estabilização de métricas estáveis em `core/diagnostics.py` para evitar oscilações cosméticas de texto em estado nominal (`OPTIMAL`).
  - Banner superior com botão interativo de controle do Gravador de Voo (`Gravar Relatório Técnico` / `REC: MM:SS (N amostras) | Parar`).
  - Notificação pós-gravação com botão rápido para abrir o diretório `data/reports/` no Explorador de Arquivos do Windows via `os.startfile()`.
  - Pílulas de filtro por severidade com contadores dinâmicos em tempo real: `Todos (N)`, `Críticos (N)`, `Atenção (N)` e `Estáveis (N)`.
  - Cards explicativos estruturados com caixa de evidência técnica (`#141E2B`), badges de severidade e reversibilidade da ação recomendada.
  - Botões de ação contextual permitindo navegação instantânea para Visão Geral (`overview`), Limpeza Segura (`cleaner`) ou Inicialização (`startup`).
- **Testes Automatizados de Diagnóstico e Gravação:**
  - Adicionado `tests/test_diagnostics.py` com 8 testes unitários cobrindo integridade das 7 dimensões, persistência temporal de CPU e RAM, detecção de thrashing, esgotamento de partição `C:`, processos predadores e ciclo de vida do `SessionRecorder`.
  - Atualizado `tests/test_pages.py` validando os filtros interativos da `DiagnosticsPage`, alternância de gravação e navegação contextual.
  - Suíte completa de testes expandida para **40 testes automatizados**, todos aprovados com 100% de sucesso.

---

## [0.2.0-alpha] - 2026-10-09 (Fase 2: Dashboard, Gráficos & Medidores Tipo Gauge)

### Refatorado
- **Modularização Arquitetural de Páginas (`app/pages/`):**
  - Desacoplamento da janela monolítica `MainWindow` (reduzida de 1.167 linhas para 328 linhas).
  - Criação de componentes dedicados com responsabilidade única:
    - [`OverviewPage`](file:///d:/GitHub/Sollaris_Nova/app/pages/overview.py): telemetria, medidores radiais, gráfico e top processos (448 linhas).
    - [`DiagnosticsPage`](file:///d:/GitHub/Sollaris_Nova/app/pages/diagnostics.py): motor explicável e cartões de avaliação (65 linhas).
    - [`CleanerPage`](file:///d:/GitHub/Sollaris_Nova/app/pages/cleaner.py): varredura não-destrutiva de temporários e thread assíncrona (93 linhas).
    - [`StartupPage`](file:///d:/GitHub/Sollaris_Nova/app/pages/startup.py): mapeamento de inicialização no Registro do Windows (68 linhas).
    - [`GameModePage`](file:///d:/GitHub/Sollaris_Nova/app/pages/game_mode.py): perfis operacionais e planos de energia (74 linhas).
    - [`HistoryPage`](file:///d:/GitHub/Sollaris_Nova/app/pages/history.py): métricas acumuladas, médias e picos da sessão (82 linhas).
    - [`SettingsPage`](file:///d:/GitHub/Sollaris_Nova/app/pages/settings.py): configuração de cadência de telemetria e metadados (78 linhas).
  - Adicionado `tests/test_pages.py` expandindo a suíte para 31 testes automatizados (100% de sucesso).

### Adicionado
- **Medidores Radiais Analógico-Digitais (`app/components/radial_gauge.py`):**
  - Componente técnico `RadialGauge` construído sobre `tk.Canvas` puro com atualização em sub-0.05ms.
  - Arco aberto de 240° de varredura, trilho passivo (#192331) e arco ativo colorido por carga (Azul/Verde até 70%, Amarelo até 85%, Vermelho acima de 85%).
  - Miolo digital com tipografia Segoe UI Bold em tempo real.
  - Variante padrão (116px) para cartões de CPU e Memória RAM.
  - Variante compacta (56px) para cada partição detectada no cartão de discos locais.
- **Curvas Fluidas & Interpolação de Alta Densidade (`app/components/performance_chart.py`):**
  - Implementação de `_smooth_data()` com interpolação densa por `np.interp` (120 pontos) e filtro de suavização Hanning de 5 pontos com atenuação de bordas.
  - Eliminação de arestas serrilhadas e saltos bruscos no histórico de 60 segundos mantendo rigor matemático (0% a 100%).
- **Identificação Visual de Recursos e Área Sombreada:**
  - Preenchimento translúcido sob as curvas (`fill_between` com alfa 0.14 para CPU azul e 0.08 para RAM verde).
  - Badges dedicados coloridos de status no cabeçalho do gráfico com valores instantâneos (`● CPU: XX.X%` em `#60A5FA` e `● RAM: YY.Y%` in `#4FBF8A`).
- **Cursor Interativo de Hover no Gráfico de Telemetria:**
  - Rastreamento contínuo do mouse via eventos `motion_notify_event` e `axes_leave_event` do Matplotlib.
  - Linha guia vertical tracejada sincronizada com marcadores circulares pontuais sobre as curvas ativas.
  - Pílula temporal dinâmica no cabeçalho exibindo a leitura exata do segundo apontado pelo cursor (ex.: `[ -24s ] ● CPU: 42.1% ● RAM: 48.9%`).
- **Sistema de Tooltips Técnicos Flutuantes (`app/components/tooltip.py`):**
  - Componente nativo de balão contextual `Tooltip` com posicionamento dinâmico pelo ponteiro do mouse (`winfo_pointerxy()`) e atraso de disparo configurável.
  - Integração em todos os indicadores da Visão Geral:
    - Gauge principal de CPU (modelo, frequência atual, carga total e contagem de núcleos físicos/lógicos).
    - Gauge principal de RAM (uso percentual, bytes utilizados, disponíveis e arquivo de paginação swap).
    - Micro-chips de núcleos lógicos individuais (`N1` a `N12+`).
    - Medidores compactos de partição de disco (espaço ocupado, livre, sistema de arquivos e caminho de montagem).
    - Badge superior de integridade e estabilidade do sistema.
- **Testes Automatizados:**
  - `tests/test_radial_gauge.py`: 3 testes validando geometria de arcos, clamping de valores (0-100%) e limites cromáticos.
  - `tests/test_charts.py`: 4 testes cobrindo inicialização de figura, alternância de modos, atualização com interpolação (120 pontos) e cálculos de janela.
  - `tests/test_tooltip.py`: 2 testes cobrindo ciclo de vida do popup, funções dinâmicas de texto e destruição segura.
  - Suíte total expandida para 29 testes automatizados (100% de aprovação).

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
