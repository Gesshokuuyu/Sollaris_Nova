# Arquitetura Técnica — PC Optimizer (Sollaris Nova)

Este documento descreve a arquitetura de software, a separação em camadas, o fluxo de dados assíncrono e as decisões de design para o projeto Sollaris Nova.

---

## 1. Visão Geral das Camadas

A arquitetura adota uma separação estrita de responsabilidades em camadas desacopladas:

```
┌────────────────────────────────────────────────────────┐
│               Interface (Camada app/)                 │
│  CustomTkinter UI • Janela • Páginas • Componentes     │
└───────────────────────────▲────────────────────────────┘
                            │ Thread-safe Queue / after()
                            │ (Apenas leitura de Dataclasses)
┌───────────────────────────▼────────────────────────────┐
│               Serviços (Camada core/)                  │
│  MonitorService (Thread de Coleta em Background)       │
│  HardwareCollector • ProcessManager • DiagnosticEngine │
└─────────────▲────────────────────────────▲─────────────┘
              │                            │
┌─────────────▼─────────────┐ ┌────────────▼─────────────┐
│   Segurança (safety/)     │ │  Persistência (database/)│
│   Permissões • Auditoria  │ │  SQLite • Histórico       │
└───────────────────────────┘ └──────────────────────────┘
              │
┌─────────────▼─────────────┐
│    Sistema Operacional    │
│    psutil • WMI • Win32   │
└───────────────────────────┘
```

---

## 2. Descrição das Camadas

### 2.1 Camada de Apresentação (`app/`)
- **Tecnologia:** CustomTkinter + Matplotlib (FigureCanvasTkAgg).
- **Arquitetura Modular:**
  - `app/window.py`: Orquestrador central que gerencia o shell da janela, barra lateral e despacho de eventos (reduzido a ~300 linhas).
  - `app/pages/`: 7 telas com ciclo de vida desacoplado (`OverviewPage`, `DiagnosticsPage`, `CleanerPage`, `StartupPage`, `GameModePage`, `HistoryPage`, `SettingsPage`).
  - `app/components/`: Componentes técnicos reutilizáveis (`RadialGauge`, `PerformanceChart`, `Tooltip`, `Sidebar`).
- **Regra de Ouro:** A interface **nunca** faz chamadas bloqueantes ao sistema operacional (`psutil`, `wmi`, etc.).
- Toda atualização visual é orientada a eventos. A interface consome objetos de dados puros (`dataclasses`) emitidos pelo `MonitorService`.
- Todas as mutações da árvore de widgets do Tkinter ocorrem obrigatoriamente na thread principal via mecanismo `root.after(0, ...)`.

### 2.2 Camada de Coleta e Diagnóstico (`core/`)
- **Independência total de UI:** Não importa nenhuma biblioteca gráfica (`tkinter`, `customtkinter`). Pode ser testada em modo headless no `pytest`.
- **Monitoramento Assíncrono (`core/monitor.py`):**
  - Executa uma thread daemon de amostragem periódica (intervalo padrão de 1.0s).
  - Mantém um histórico em memória com tamanho delimitado (`collections.deque(maxlen=60)`).
  - Trata exceções em tempo de coleta: se a leitura de um sensor falhar, retorna `SensorStatus.UNAVAILABLE` sem interromper a thread.
- **Hardware (`core/hardware.py`):**
  - Normaliza os dados brutos de CPU, RAM, partições de armazenamento e sensores de temperatura.
- **Processos (`core/processes.py`):**
  - Trata exceções esperadas no ciclo de vida de processos: `psutil.NoSuchProcess`, `psutil.AccessDenied` e `psutil.ZombieProcess`.
  - Ordena e limita a lista (ex.: top 10 maiores consumidores de memória).
- **Diagnóstico (`core/diagnostics.py`):**
  - Analisa amostras temporais acumuladas para detectar anomalias sustentadas.
  - Produz objetos `Recommendation` estruturados e explicáveis.

### 2.3 Camada de Segurança (`safety/`)
- Valida privilégios de execução (usuário padrão vs administrador).
- Implementa o padrão **Preview-Before-Action** (qualquer ação de limpeza gera um relatório de prévia com arquivos elegíveis, tamanho liberável e riscos antes de qualquer deleção).
- Registra todas as ações autorizadas em log local de auditoria (`safety/audit_log.py`).

### 2.4 Camada de Persistência (`database/`)
- Banco de dados embutido SQLite armazenado em `data/optimizer.db`.
- Foco em retenção controlada (ex.: expiração de dados mais antigos que 7 dias).
- Desacoplado da thread de UI: escritas são agendadas em lote ou disparadas por eventos periódicos.

---

## 3. Modelo de Dados Unificado (Dataclasses)

Para garantir desacoplamento, todas as trocas de dados entre `core` e `app` utilizam dataclasses tipadas e imutáveis:

```python
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass(frozen=True)
class SensorReading:
    value: Optional[float]
    unit: str
    is_available: bool
    sensor_name: Optional[str] = None

@dataclass(frozen=True)
class CpuMetrics:
    total_percent: float
    core_count_logical: int
    core_count_physical: int
    frequency_current_mhz: Optional[float]
    temperature: SensorReading

@dataclass(frozen=True)
class RamMetrics:
    total_bytes: int
    used_bytes: int
    available_bytes: int
    percent: float

@dataclass(frozen=True)
class DiskPartitionMetrics:
    device: str
    mountpoint: str
    fstype: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float

@dataclass(frozen=True)
class ProcessSnapshot:
    pid: int
    name: str
    memory_bytes: int
    memory_percent: float
    cpu_percent: Optional[float]

@dataclass(frozen=True)
class SystemSnapshot:
    timestamp: datetime
    cpu: CpuMetrics
    ram: RamMetrics
    disks: List[DiskPartitionMetrics]
    gpu_temperature: SensorReading
    top_processes: List[ProcessSnapshot]
```

---

## 4. Comunicação entre Threads e Concorrência

1. O `MonitorService` opera em loop contínuo:
   ```
   [Início do Tick] ──> [HardwareCollector.collect()] ──> [ProcessManager.collect_top()]
         │
         ├──> [Armazenar em Deque(maxlen=60)]
         │
         ├──> [DiagnosticEngine.evaluate(history)]
         │
         └──> [Despachar SystemSnapshot via Callback / UI Thread Queue]
   ```
2. A UI recebe o snapshot no método thread-safe e invoca as atualizações dos widgets sem recomputar métricas pesadas.
3. Se a janela for fechada pelo usuário, o `MonitorService.stop()` sinaliza um `threading.Event` para encerramento gracioso e imediato do loop de background.
