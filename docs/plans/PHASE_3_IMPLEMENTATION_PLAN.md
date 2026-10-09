# Plano de Implementação — Fase 3: Motor de Diagnóstico Explicável, Recomendações Técnicas e Relator de Sessão

Este documento detalha o planejamento arquitetural, modelos de dados, catálogo de regras técnicas, design da interface, relator contínuo de sessão e suíte de testes para a **Fase 3** do Sollaris Nova (PC Optimizer).

> [!NOTE]
> **Status da Fase 3:** Implementada, validada e homologada em `develop` com 40 testes unitários aprovados (100%), eliminando piscamento visual (0ms flicker) e gerando relatórios de voo analíticos em `data/reports/`. Consulte o documento de conclusão em [`docs/phases/PHASE_3_DIAGNOSTICS_AND_RECORDER.md`](file:///d:/GitHub/Sollaris_Nova/docs/phases/PHASE_3_DIAGNOSTICS_AND_RECORDER.md).

---

## 1. Visão Geral e Objetivos da Fase 3

O objetivo central da Fase 3 é transformar dados brutos de telemetria em **diagnósticos técnicos acionáveis, explicáveis e livres de falsos positivos**, além de fornecer um **Relator Técnico Contínuo ("Flight Recorder")** para gravação de sessões de análise e diagnóstico sob demanda.

### Princípios Fundamentais
1. **Sem Pontuações Arbitrárias:** Não utilizar notas cosméticas de 0 a 100 ("Saúde do PC: 72%"). Diagnósticos devem expressar estados de engenharia reais.
2. **Persistência Temporal Obrigatória:** Um pico de CPU de 95% durante 1 segundo ao abrir um navegador é um comportamento esperado do escalonador do Windows, não um problema. Alertas só disparam após confirmação por uma janela de tempo mínima (ex.: 10 amostras consecutivas).
3. **Explicabilidade em 7 Dimensões:** Toda anomalia deve conter: Título, Categoria, Severidade, Evidência Numérica com Tempo, Causa Raiz Técnica, Impacto Provável, Risco e Ação Sugerida Reversível.
4. **Relator Técnico Sob Demanda (Flight Recorder):** Opção ativável por botão na interface que registra em arquivo estruturado (`data/reports/`) todas as atividades segundo a segundo, picos de recursos e anomalias para análise técnica posterior.
5. **Sem Ações Destrutivas Automáticas:** O aplicativo nunca encerra processos ou apaga arquivos sem consentimento explícito e prévia do usuário.
6. **Zero Impacto no Loop da Interface:** O motor avalia o histórico em sub-1.0ms e a gravação de relatórios ocorre via fila thread-safe em thread desacoplada, mantendo 60 FPS ininterruptos.

---

## 2. Requisitos da Fase 3

| ID | Tipo | Descrição | Critério de Aceite |
| :--- | :--- | :--- | :--- |
| **RF-008** | Funcional | Alertas baseados em persistência temporal | Alerta de CPU exige >= 10 amostras acima de 85% no buffer histórico. Picos transitórios (<5s) são ignorados. |
| **RF-008.1** | Funcional | Detecção de pressão persistente de RAM | Dispara quando RAM livre < 1.5 GB ou > 88% por >= 5 amostras consecutivas. |
| **RF-008.2** | Funcional | Detecção de Paginação Excessiva (Swap Thrashing) | Alerta quando alocação de Swap > 75% combinado com RAM > 80%. |
| **RF-008.3** | Funcional | Detecção de Armazenamento Crítico | Alerta de emergência com < 15 GB livres na unidade do sistema (`C:`). |
| **RF-008.4** | Funcional | Identificação de Processo Predador | Aponta no diagnóstico qual processo é o maior responsável pela sobrecarga observada. |
| **RF-008.5** | Funcional | Detecção de Uptime Excessivo | Alerta informativo quando tempo de atividade sem reboot ultrapassar 7 dias. |
| **RF-008.6** | Funcional | Relator Técnico de Sessão (Flight Recorder) | Botão liga/desliga que grava em log técnico contínuo amostras, picos e anomalias com sumário final. |
| **RNF-001** | Não Funcional | Explicabilidade Estruturada | Todo diagnóstico implementa os 7 campos técnicos padronizados. |
| **RNF-002** | Não Funcional | Desempenho de Avaliação | Avaliação completa de todas as regras executada em sub-1.0ms. |
| **RNF-003** | Não Funcional | I/O Assíncrono do Gravador | Gravação do log de sessão em background thread com `queue.Queue` sem bloquear a GUI (0ms). |
| **RNF-004** | Não Funcional | UI Responsiva com Filtros | Filtro rápido por severidade (Todos, Críticos, Atenção, Estáveis) e cartões expansíveis em `DiagnosticsPage`. |

---

## 3. Modelo de Dados da Fase 3

### 3.1 Níveis Semânticos (`FindingLevel`)
```python
class FindingLevel(Enum):
    OPTIMAL = "optimal"    # Sistema dentro dos parâmetros nominais de fábrica
    INFO = "info"          # Fatos técnicos relevantes sem degradação imediata (ex.: uptime longo)
    WARNING = "warning"    # Consumo elevado que pode gerar gargalos futuros (ex.: RAM a 82%)
    CRITICAL = "critical"  # Gargalo sustentado ativo degradando a experiência (ex.: CPU 90% persistente)
```

### 3.2 Estrutura do Apontamento Técnico (`DiagnosticFinding`)
```python
@dataclass(frozen=True)
class DiagnosticFinding:
    category: str                  # "Processador (CPU)", "Memória (RAM)", "Armazenamento", etc.
    level: FindingLevel            # Severidade semântica
    title: str                     # Título técnico direto
    evidence: str                  # Dados numéricos medidos + janela de persistência (ex.: "Média de 89.4% por 15s")
    technical_explanation: str     # O que está acontecendo internamente no subsistema do Windows
    probable_impact: str           # Efeito na máquina (ex.: "Micro-travamentos e atraso de renderização")
    risk: str                      # Consequência caso o usuário não atue (ex.: "Esgotamento de memória e travamento")
    suggested_action: str          # Ação técnica segura e contextual
    is_reversible: bool            # Garantia de reversibilidade da recomendação
    target_route: str | None = None # Rota interna para ação ("cleaner", "startup", "overview")
```

---

## 4. Catálogo de Regras do Motor de Diagnóstico

### Regra 1: Saturação Sustentada de CPU (`CPU_PERSISTENT_HIGH`)
- **Condição:** Pelo menos 10 das últimas 15 amostras no buffer histórico (`deque(maxlen=60)`) com carga global >= 85.0%.
- **Nível:** `CRITICAL`.
- **Evidência:** "CPU operando a XX.X% de carga média nos últimos YY segundos (N amostras consecutivas acima de 85%)."
- **Explicação Técnica:** O agendador de threads do Windows está enfrentando contenção de filas em núcleos lógicos. Processos concorrentes disputam fatias de tempo quântico sem folga térmica.
- **Impacto:** Aumento de latência de entrada (DPC/ISR), queda de taxa de quadros e lentidão na troca de janelas.
- **Ação Sugerida:** Inspecione os processos de maior consumo e suspenda tarefas dispensáveis em segundo plano.

### Regra 2: Carga Transitória de CPU (`CPU_SPIKE_IGNORING`)
- **Condição:** Carga atual > 85%, porém menos de 5 amostras no buffer histórico estão acima de 85%.
- **Resultado:** **Não gera alerta crítico.** Classificado como `OPTIMAL` ou ignorado, preservando o usuário de falsos alarmes decorrentes da abertura de aplicativos ou compilação transitória.

### Regra 3: Pressão Crítica de Memória RAM (`RAM_CRITICAL_EXHAUSTION`)
- **Condição:** Memória disponível < 1.5 GB ou percentual de uso >= 88.0% mantido por pelo menos 5 amostras consecutivas.
- **Nível:** `CRITICAL`.
- **Evidência:** "Apenas X.XX GB disponíveis (YY.Y% em uso) nas últimas N amostras."
- **Explicação Técnica:** A lista de páginas livres e em standby do Memory Manager do Windows está próxima do esgotamento. O subsistema será forçado a recorrer a compressão de memória agressiva e escrita no arquivo de paginação.
- **Impacto:** Stuttering severo em trocas de contexto e lentidão extrema ao alternar navegadores e editores.
- **Ação Sugerida:** Fechar guias ociosas do navegador ou encerrar aplicações em segundo plano que retêm heaps extensos.

### Regra 4: Paginação Excessiva / Thrashing (`SWAP_PRESSURE_HIGH`)
- **Condição:** Uso do arquivo de paginação (Swap) >= 75.0% combinado com RAM global >= 80.0%.
- **Nível:** `WARNING`.
- **Evidência:** "Arquivo de paginação atingiu X.XX GB alocados (YY.Y% de swap) enquanto a RAM opera em ZZ.Z%."
- **Explicação Técnica:** O sistema operacional transferiu blocos de memória virtual secundária para o disco rígido/SSD para evitar estouro de memória física.
- **Impacto:** Degradação de throughput de I/O e desgaste adicional de ciclos de escrita no SSD.
- **Ação Sugerida:** Reiniciar aplicações vazadoras de memória ou aumentar memória RAM física instalada.

### Regra 5: Armazenamento Crítico na Unidade de Sistema (`DISK_SYSTEM_EXHAUSTION`)
- **Condição:** Menos de 15 GB livres ou uso >= 90.0% na partição onde o Windows está instalado (`C:`).
- **Nível:** `CRITICAL`.
- **Evidência:** "Restam apenas X.X GB livres (YY.Y% ocupado) na unidade C:."
- **Explicação Técnica:** O Windows requer espaço mínimo contíguo para alocação dinâmica do `pagefile.sys`, restauração de pontos do sistema (VSS) e arquivos de staging de atualizações cumulativas do Windows Update.
- **Impacto:** Falhas silenciosas em atualizações do Windows, corrupção potencial de dumps de memória e congelamentos de I/O.
- **Ação Sugerida:** Executar varredura na aba de Limpeza Segura para recuperar caches de instaladores e temporários.
- **Target Route:** `cleaner`.

### Regra 6: Processo Predador em Segundo Plano (`PROCESS_HEAVY_CONSUMER`)
- **Condição:** O processo topo consome mais de 25% da memória física total instalada ou retém mais de 4 GB isoladamente.
- **Nível:** `WARNING`.
- **Evidência:** "Processo '[nome]' (PID: [pid]) retém isoladamente X.XX GB de memória RAM."
- **Explicação Técnica:** Aplicação isolada monopolizando a maior fração do working set físico, induzindo compressão forçada nas demais tarefas do usuário.
- **Impacto:** Redução da memória disponível para cache de leitura do sistema operacional.
- **Ação Sugerida:** Avalie reiniciar o processo indicado se seu consumo não corresponder à carga de trabalho esperada.

### Regra 7: Uptime Prolongado Sem Reinicialização (`UPTIME_PROLONGED`)
- **Condição:** Tempo de atividade contínuo do sistema >= 7 dias (604.800 segundos).
- **Nível:** `INFO`.
- **Evidência:** "Sistema operacional em execução contínua há X.X dias."
- **Explicação Técnica:** Pool de memória não-paginada (Non-Paged Pool) do kernel e handles acumulados tendem a fragmentar após longos períodos sem reinício a frio.
- **Impacto:** Pequeno acréscimo na latência de chamadas do subsistema gráfico e de rede.
- **Ação Sugerida:** Reinicie o computador na próxima oportunidade conveniente para limpar pools de kernel.

---

## 5. Relator Técnico de Sessão / Gravador Contínuo (`core/recorder.py`)

O módulo `SessionRecorder` fornece registro sob demanda para técnicos, entusiastas e depuração de estabilidade:

### 5.1 Arquitetura e Concorrência
```
[MonitorService / GUI Tick]
       │ Enqueue snapshot + findings
       ▼
[queue.Queue(maxsize=1000)]
       │
       ▼
[RecorderThread (Daemon)] ──> Escrita em buffer (I/O desacoplado)
       │
       ▼
[Arquivo Local: data/reports/relatorio_sessao_YYYY-MM-DD_HH-MM-SS.log]
```

### 5.2 Estrutura do Arquivo de Relatório (`.log` técnico formatado)
1. **Cabeçalho da Sessão:** Data/hora de início, especificações da máquina (Processador, Cores, RAM instalada, Versão e Build do Windows).
2. **Entradas Periódicas (Ticks de Telemetria):**
   ```
   [16:45:01] CPU: 42.1% (3600 MHz) | RAM: 54.2% (8.6/16.0 GB) | SWAP: 12.0% | DISCO C: 74.2%
              TOP: chrome.exe (PID: 12480, 1.45 GB), code.exe (PID: 8840, 890 MB)
              STATUS: Sistema Estável
   ```
3. **Registro Destacado de Anomalias/Picos:**
   ```
   [16:45:14] >>> ALERTA CRÍTICO: [Processador] Saturação Sustentada de CPU
              EVIDÊNCIA: 92.4% média nos últimos 12s
              PROCESSO RESPONSÁVEL: render_engine.exe (PID: 4320)
   ```
4. **Sumário Executivo Final:**
   - Duração total da gravação e total de amostras colhidas.
   - CPU: Carga média da sessão e pico máximo atingido.
   - RAM: Média de uso e pico máximo atingido.
   - Total de ocorrências de anomalias/alertas por nível de severidade.
   - Caminho do arquivo gerado para compartilhamento ou arquivamento.

### 5.3 Controles na Interface Gráfica
- **Botão de Alternância no Cabeçalho de Diagnóstico:**
  - Inativo: `[ Iniciar Relatório Técnico ]` (`#141E2B`)
  - Ativo: `[ ● Gravando Sessão: 00:03:15 (130 amostras) | Parar ]` com indicador visual destacado (`#EF4444`).
- **Ação ao Encerrar:** Exibe caixa informativa não-intrusiva com resumo e botão `[ Abrir Pasta do Relatório ]` para abrir o Windows Explorer diretamente em `data/reports/`.

---

## 6. Interface Gráfica: `app/pages/diagnostics.py`

A página de Diagnóstico receberá os seguintes elementos:

### 6.1 Barra de Resumo e Filtros Rápidos
- **Contador de Status:**
  - `● N Estáveis` (`#4FBF8A`)
  - `ℹ N Informativos` (`#60A5FA`)
  - `▲ N Atenção` (`#EAB308`)
  - `✕ N Críticos` (`#EF4444`)
- **Filtros Tipo Pílula:** Botões rápidos: `Todos`, `Apenas Críticos`, `Atenção`, `Estáveis`.
- **Botão do Relator:** Botão de gravação posicionado à direita da barra de ferramentas da página.

### 6.2 Cartão Explicativo Estruturado (7 Dimensões)
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [Processador (CPU)] Saturação Sustentada de CPU             [✕ Crítico]      │
├──────────────────────────────────────────────────────────────────────────────┤
│ ┌─ Evidência Numérica Observada ───────────────────────────────────────────┐ │
│ │ • Leitura média: 91.4% de carga nos últimos 15s (12 amostras consecutivas) │ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ Explicação Técnica:                                                          │
│ O escalonador de threads do Windows está enfrentando contenção contínua...   │
│                                                                              │
│ Impacto Provável:                        Risco Técnico:                      │
│ • Micro-travamentos e atraso na UI       • Sobrecarga e throttling térmico   │
│                                                                              │
│ Recomendação:                                                                │
│ Inspecione a lista de processos e feche tarefas em segundo plano redundantes.│
│                                                                              │
│ [Ação Segura & Reversível]                     [Ir para Top Processos ->]    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Integração Arquitetural

```
┌────────────────────────────────────────────────────────┐
│         MonitorService (Thread de Background)          │
│   cpu_history: deque(maxlen=60)                        │
│   ram_history: deque(maxlen=60)                        │
│   latest_snapshot, latest_processes                    │
└───────────────────────────┬────────────────────────────┘
                            │ Thread-safe snapshot
                            ▼
┌────────────────────────────────────────────────────────┐
│          DiagnosticEngine (core/diagnostics.py)        │
│   evaluate_with_history(snapshot, cpu_hist, ram_hist,  │
│                         processes) -> list[Finding]    │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
              ▼                            ▼
┌───────────────────────────┐ ┌──────────────────────────┐
│   DiagnosticsPage (UI)    │ │ SessionRecorder (core)   │
│   Filtros + Cartões 7D    │ │ Gravação contínua em log │
│   Controle de Gravação    │ │ data/reports/            │
└───────────────────────────┘ └──────────────────────────┘
```

---

## 8. Plano de Testes Automatizados (`tests/test_diagnostics.py`)

A suíte será estendida com testes cobrindo todas as regras, persistência e o gravador:

1. **`test_diagnostic_engine_cpu_spike_ignored`:** Injeta buffer com apenas 2 picos de 95% em 60s. Valida que a regra de CPU Crítica **NÃO** é disparada (eliminação de falso positivo).
2. **`test_diagnostic_engine_cpu_persistent_triggered`:** Injeta buffer com 12 amostras consecutivas a 90%. Valida que a regra `CRITICAL` é disparada com evidência numérica de persistência.
3. **`test_diagnostic_engine_ram_exhaustion`:** Injeta snapshot com 1.1 GB de RAM livre mantido por 6 amostras. Valida alerta de esgotamento de memória.
4. **`test_diagnostic_engine_swap_thrashing`:** Injeta swap a 85% e RAM a 85%. Valida disparo do alerta de paginação excessiva.
5. **`test_diagnostic_engine_disk_system_critical`:** Injeta partição `C:` com 10 GB livres. Valida apontamento crítico com target route `"cleaner"`.
6. **`test_diagnostic_engine_predator_process`:** Injeta lista com processo consumindo 6 GB de RAM. Valida recomendação apontando PID e nome do processo.
7. **`test_diagnostic_engine_fields_completeness`:** Valida que 100% dos `DiagnosticFinding` gerados possuem todos os 7 campos técnicos preenchidos sem valores nulos ou vazios.
8. **`test_diagnostics_page_filter_switching`:** Valida na interface gráfica CustomTkinter a filtragem por nível (Críticos, Alertas, Todos).
9. **`test_session_recorder_start_stop_and_flushing`:** Inicia gravação do `SessionRecorder`, despacha 5 ticks e encerra. Valida criação do arquivo em `data/reports/` com cabeçalho e ticks formatados.
10. **`test_session_recorder_summary_generation`:** Valida cálculo correto do sumário executivo final (médias, picos e anomalias).

---

## 9. Cronograma de Execução

1. **Etapa 3.1: Modelos e Motor de Diagnóstico (`core/diagnostics.py`)**
   - Atualizar dataclass `DiagnosticFinding` com os 7 campos técnicos.
   - Implementar método `DiagnosticEngine.evaluate_with_history(...)` com avaliação de persistência temporal e processo predador.
2. **Etapa 3.2: Gravador de Sessão e Relator Técnico (`core/recorder.py`)**
   - Criar `SessionRecorder` com fila thread-safe, worker daemon e formatação de logs e sumário.
3. **Etapa 3.3: Suíte de Testes do Motor e do Gravador (`tests/test_diagnostics.py`)**
   - Criar testes sintéticos para picos transitórios vs persistência sustentada.
   - Criar testes unitários para o ciclo de vida do gravador e sumário final.
4. **Etapa 3.4: Interface Gráfica Explicativa (`app/pages/diagnostics.py`)**
   - Implementar barra de contadores e filtros de severidade no topo.
   - Implementar cartões estruturados com caixas de evidência, explicação, risco/impacto e atalhos de ação segura.
   - Implementar botão de gravação com cronômetro em tempo real e abertura da pasta de relatórios.
5. **Etapa 3.5: Conexão e Roteamento (`app/window.py`)**
   - Passar histórico e processos para a atualização de diagnósticos sem travar o loop de 60 FPS.
   - Conectar navegação rápida (ex.: botão do cartão de disco abrindo a página de limpeza).
6. **Etapa 3.6: Verificação Global de Qualidade e Documentação**
   - Executar `ruff check .` e `pytest -v`.
   - Atualizar `CHANGELOG.md`, `PHASE_3_DIAGNOSTICS.md` e `FUTURE_REQUIREMENTS.md`.
   - Commit e merge formal no branch `develop`.
