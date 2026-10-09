# Catálogo Vivo de Requisitos Futuros e Backlog Técnico (Sollaris Nova)

Este documento registra continuamente todas as ideias, novos requisitos funcionais, solicitações do usuário e oportunidades técnicas identificadas durante a execução de cada fase.

> **Regra de Governança:** Conforme a Seção 7 de [CODE_STANDARDS.md](file:///d:/GitHub/Sollaris_Nova/docs/standards/CODE_STANDARDS.md), ao término de cada fase, este documento deve ser revisado e enriquecido com os aprendizados, novas necessidades e requisitos futuros descobertos.

---

## 1. Matriz de Requisitos Futuros Catalogados

| ID | Título | Origem / Fase | Descrição Técnica | Prioridade | Fase Sugerida | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RF-FUT-001** | Suporte a Sensores Proprietários de GPU | Setup Inicial | Suporte avançado para leitura de temperatura e VRAM via NVML (NVIDIA) e ADL (AMD) caso WMI seja insuficiente. | Média | Pós-MVP (Fase 4/5) | Catalogado |
| **RF-FUT-002** | Histórico e Análise de Consumo Energético | Setup Inicial | Exibição de taxas de descarga e saúde de bateria para laptops Windows. | Baixa | Versão 1.x | Ideia |
| **RF-FUT-003** | Modo Escuro / Claro Técnico Alternável | Setup Inicial | Suporte a tema claro técnico de alto contraste para ambientes iluminados. | Baixa | Versão 2.x | Ideia |
| **RF-FUT-004** | Exportação de Diagnósticos em PDF / JSON | Setup Inicial | Possibilidade de exportar o snapshot completo da máquina para diagnóstico técnico externo. | Média | Fase 3 / 4 | Catalogado |
| **RF-FUT-005** | Integração com LibreHardwareMonitor / OpenHardwareMonitor DLL | Setup Inicial | Leitura direta de sensores de placas-mãe de desktops via biblioteca Win32/C# embarcada se WMI não expor ThermalZone. | Alta | Fase 2 / 3 | Investigar |
| **RF-FUT-006** | Monitoramento de NPU (Neural Processing Unit) | Fase 1 | Detecção de consumo de aceleradores neurais em chips modernos (Intel Core Ultra, Snapdragon X, Ryzen AI) no Windows 11. | Baixa | Pós-MVP | Catalogado |
| **RF-FUT-007** | Detecção de Eventos Plug-and-Play de Armazenamento (`WM_DEVICECHANGE`) | Fase 1 | Atualização instantânea dos cartões de disco quando uma unidade USB for inserida ou ejetada, sem depender de refresh manual. | Média | Fase 2 | Planejado |
| **RF-FUT-008** | Driver Opcional de Baixo Nível para Sensores de Desktop (WinRing0) | Fase 1 | Em sistemas desktop onde ACPI ThermalZone requer elevação de privilégios, oferecer serviço opcional transparente para leitura de CPU package temp. | Média | Pós-MVP | Investigar |
| **RF-FUT-009** | Coleta de Processos em Sub-15ms via Win32 Nativo | Fase 1 | Substituição de `psutil.process_iter` (1.1s) por APIs nativas Win32 (`CreateToolhelp32Snapshot` + `GetProcessMemoryInfo`), garantindo leitura sem overhead. | Alta | Concluído (Fase 1) | Entregue |
| **RF-FUT-010** | Loader Visual Não-Bloqueante com Concorrência Atômica | Fase 1 | Eliminação do freeze no botão "Atualizar Agora" com delegação para thread de background e barra de loading indeterminada de 3px. | Alta | Concluído (Fase 1) | Entregue |
| **RF-FUT-011** | Varredura de Temporários Totalmente Assíncrona | Fase 1 | Execução do `CleanerScanner` em worker thread desacoplada da GUI com callback atômico, prevenindo congelamentos em diretórios com >50.000 arquivos. | Média | Fase 1 / 4 | Entregue |
| **RF-FUT-012** | Suporte Dinâmico a CPUs de Alta Densidade (16+ e 24+ Threads) | Fase 1 | Ajuste responsivo ou paginação dos micro-medidores de núcleos lógicos para processadores híbridos (Intel P/E cores e AMD 16C/32T). | Média | Fase 2 | Planejado |
| **RF-FUT-013** | Padronização Anti-Aliasing para Monitores High-DPI | Fase 1 | Padronização de todas as `CTkProgressBar` para altura >= 8px e raio de canto proporcional, prevenindo artefatos visuais de linhas/listras. | Alta | Concluído (Fase 1) | Entregue |
| **RF-FUT-014** | Interpolação e Suavização de Curvas (Filtro Hanning) | Fase 2 | Interpolação densa a 120 pontos com filtro ponderado de Hanning de 5 pontos, eliminando arestas serrilhadas mantendo rigor de 0% a 100%. | Alta | Concluído (Fase 2) | Entregue |
| **RF-FUT-015** | Zoom e Pan Histórico no Canvas | Fase 2 | Ferramenta de inspeção de zoom/pan horizontal no histórico para depurar picos ocorridos há mais de 60 segundos. | Baixa | Backlog v1.x | Aberto |
| **RF-FUT-016** | Agrupamento de Gauges para Servidores com Múltiplos Discos | Fase 2 | Grid compacto responsivo em carrossel caso a máquina possua mais de 6 unidades montadas. | Média | Backlog v1.x | Aberto |
| **RF-FUT-017** | Modos de Acessibilidade de Cores para Daltonismo | Fase 2 | Paleta de cores alternativa para os arcos de gauge para usuários com Deuteranopia ou Protanopia. | Média | Backlog v1.x | Aberto |
| **RF-FUT-018** | Hover Interativo e Cursor com Leitura Temporal no Gráfico | Fase 2 | Rastreamento do mouse via Matplotlib com linha guia vertical, marcadores pontuais e badge temporal dinâmico (`[ -XXs ]`). | Alta | Concluído (Fase 2) | Entregue |
| **RF-FUT-019** | Identificação Visual de Recursos e Sombra sob Curvas | Fase 2 | Preenchimento translúcido sob as curvas (`fill_between`) e badges dedicados coloridos de status (`● CPU: XX%`, `● RAM: YY%`). | Média | Concluído (Fase 2) | Entregue |
| **RF-FUT-020** | Sistema de Dicas Contextuais Flutuantes (`Tooltip`) | Fase 2 | Componente nativo de balão contextual `Tooltip` com posicionamento por cursor (`winfo_pointerxy`) em gauges, núcleos e discos. | Alta | Concluído (Fase 2) | Entregue |
| **RF-FUT-021** | Modularização Arquitetural de Páginas (`app/pages/`) | Fase 2 | Desacoplamento da janela monolítica em 7 páginas modulares com ciclo de vida isolado (`OverviewPage`, `DiagnosticsPage`, etc.). | Alta | Concluído (Fase 2) | Entregue |

---

## 2. Registro de Itens por Fase de Desenvolvimento

### Fase 1 — Fundação e Coleta de Métricas
- **Descoberta WMI ACPI:** A classe `MSAcpi_ThermalZoneTemperature` retorna `wmi.x_access_denied` em execuções de usuário comum no Windows 10/11. O sistema agora exibe `"Sensor indisponível"` com elegância. Foi catalogado o requisito `RF-FUT-008` para investigar soluções de baixo nível caso o usuário deseje telemetria aprofundada de clock/temperatura.
- **Drives Vazios / Leitores de Cartão:** Unidades mapeadas que não possuem mídia física inserida disparam `OSError [WinError 21]`. O filtro implementado via `GetLogicalDriveStringsW` e `GetDiskFreeSpaceExW` reduz o tempo de checagem para 1.5ms e protege a aplicação contra travamentos. Catalogado `RF-FUT-007` para sincronização reativa com mensagens do Windows.
- **Navegação Sem Emojis:** Identificada a necessidade de ícones visuais profissionais vetoriais em PNG monocromático para substituir qualquer elemento com aspecto artificial. Entregue pacote de ícones em `assets/nav_icons/`.
- **Gargalos de CPU/Processos:** O overhead de instanciar objetos `psutil.Process` em loop foi eliminado via Win32 ctypes (`CreateToolhelp32Snapshot`), reduzindo o tempo de 1.118 ms para 13 ms (`RF-FUT-009`).
- **Feedback Visual de Recarregamento:** Implementado o sistema de loader não-bloqueante (`RF-FUT-010`) e erradicação de artefatos de renderização subpixel (`RF-FUT-013`).

### Fase 2 — Dashboard Completo, Gráficos e Radial Gauges
- **Renderização Sub-0.05ms com RadialGauge:** A substituição das barras horizontais por medidores radiais analógico-digitais nativos em `tk.Canvas` com arco de 240° proporcionou leitura técnica instantânea sem qualquer impacto nos 60 FPS da interface.
- **Otimização Matplotlib TkAgg:** Constatado que chamadas a `fig.clf()` e recriação de eixos custavam 50-80ms por ciclo. Com a pré-alocação dos objetos `Line2D`, atualização por `set_data()` e despacho assíncrono via `draw_idle()`, o tempo na thread da UI caiu para menos de 2ms (`RF-007` validado).
- **Fluidez Matemática com Filtro de Hanning:** Implementado `_smooth_data()` com interpolação densa por `np.interp` (120 pontos) e filtro ponderado de Hanning de 5 pontos, garantindo curvas orgânicas sem saltos bruscos (`RF-FUT-014`).
- **Hover Interativo e Cursor no Histórico:** Rastreamento do mouse com linha guia vertical, marcadores circulares sobre as curvas e leitura temporal instantânea do segundo apontado (`RF-FUT-018`).
- **Identificação Visual Diferenciada:** Áreas sombreadas com `fill_between()` e badges dedicados com a cor correspondente de cada curva (`RF-FUT-019`).
- **Tooltips Técnicos em Toda a UI:** Componente nativo [`Tooltip`](file:///d:/GitHub/Sollaris_Nova/app/components/tooltip.py) integrado aos medidores radiais, chips de núcleos lógicos, unidades de disco e badge de status (`RF-FUT-020`).
- **Modularização de Páginas (`app/pages/`):** Arquitetura desacoplada com 7 páginas isoladas, reduzindo `MainWindow` de 1.167 linhas para 328 linhas (`RF-FUT-021`).
- **Estatísticas Temporais da Janela:** Implementação de médias e picos da janela móvel de 60 segundos com `deque(maxlen=60)` sob lock para enriquecer os cartões de CPU e RAM sem vazamentos de memória.

### Fase 3 — Diagnóstico e Recomendações
*(Espaço reservado para descobertas da Fase 3).*

---

## 3. Critérios para Adicionar um Novo Requisito
Todo novo requisito adicionado a este catálogo deve responder:
1. **Qual é a necessidade real do usuário ou do sistema?**
2. **Qual é a evidência técnica ou limitação encontrada?**
3. **Qual é o risco e o impacto para o produto?**
4. **Respeita a filosofia do produto (segurança antes de automação, sem dados falsos, sem telemetria)?**
