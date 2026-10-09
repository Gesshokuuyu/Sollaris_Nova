# Plano Detalhado de Implementação e Especificação Técnica — Fase 2 (Dashboard, Gráficos e Medidores Tipo Gauge)

Este documento estabelece o plano formal, a especificação técnica e o detalhamento visual da **Fase 2 (Dashboard, Gráficos Matplotlib em Tempo Real e Medidores Tipo Radial Gauge)** do Sollaris Nova.

---

## 1. Objetivos da Fase 2 e Requisitos Vinculados

A Fase 2 consolida a experiência visual do **Dashboard (Visão Geral)**, substituindo as barras lineares estáticas por medidores radiais analógico-digitais (*Radial Gauges*) de alta precisão técnica e introduzindo a telemetria contínua com histórico dos últimos 60 segundos.

### Requisitos Cobertos
- **RF-007 (Obrigatório / MVP):** Manter gráfico histórico de CPU e RAM dos últimos 60 segundos com atualização contínua e buffer circular fixo (`collections.deque(maxlen=60)`).
- **RF-006 (Obrigatório / MVP):** Atualização assíncrona com renderização do canvas e medidores radiais em sub-3ms, sem travamentos (60 FPS constantes).
- **RF-001, RF-002 e RF-003 (Evolução Visual):** Medidores tipo *Gauge* para CPU, Memória RAM e Discos, proporcionando leitura visual imediata com gradiente de carga e miolo digital.
- **Estatísticas Temporais da Janela:** Exibição da Média Móvel, Pico Máximo e Leitura Mínima dos últimos 60 segundos nos cartões principais.

---

## 2. Wireframe Visual do Dashboard com Medidores Tipo Gauge

A substituição das barras horizontais por medidores tipo Gauge permite um layout em duas colunas internas em cada cartão: o **medidor radial à esquerda** e a **grade de especificações técnicas à direita**:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ SOLLARIS NOVA — PC OPTIMIZER                                                                   [—] [□] [X] │
├───────────────────────┬─────────────────────────────────────────────────────────────────────────────────────┤
│  [Ícone] SOLLARIS     │  VISÃO GERAL                                       ● Sistema Operacional: Estável   │
│  Sollaris Nova v0.1.0 │  Última amostragem: 12:45:10 • Ao Vivo              [ ⟳ Atualizar Agora ]            │
│                       │  ═════════════════════════════════════════════════════════════════════════════════  │
├───────────────────────┼───────────────────────────────────┬─────────────────────────────────────────────────┤
│                       │  CARTÃO CPU (COM RADIAL GAUGE)    │  CARTÃO MEMÓRIA RAM (COM RADIAL GAUGE)          │
│  [>] Visão Geral      │  ┌───────────┐                    │  ┌───────────┐                                  │
│  [ ] Diagnóstico      │  │   ╭───╮   │ • AMD Ryzen 5 5600X│  │   ╭───╮   │ • Em Uso: 15.8 GB (49.8%)        │
│  [ ] Limpeza          │  │  │ 42% │  │ • 6C / 12T • 4.1GHz│  │  │ 50% │  │ • Disponível: 15.9 GB            │
│  [ ] Inicialização    │  │   ╰─ ─╯   │ • Temp: 48.0 °C    │  │   ╰─ ─╯   │ • Total: 31.7 GB                │
│  [ ] Modo Game        │  │   GAUGE   │ • Média 60s: 38.2% │  │   GAUGE   │ • Swap: 2.1 GB / 36.4 GB         │
│  [ ] Histórico        │  └───────────┘ • Pico 60s:  74.0% │  └───────────┘ • Pico 60s: 51.2%                │
│  [ ] Configurações    ├───────────────────────────────────┴─────────────────────────────────────────────────┤
│                       │  GRÁFICO DE TELEMETRIA EM TEMPO REAL (ÚLTIMOS 60 SEGUNDOS)                          │
│                       │  Modo: [ Ambos (CPU + RAM) ] [ Apenas CPU ] [ Apenas RAM ]         Intervalo: 1.5s  │
│                       │  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│                       │  │ 100% ┼─────────────────────────────────────────────────────────────────────── │  │
│                       │  │  80% ┼                                                                       │  │
│                       │  │  60% ┼       ╭───╮             CPU: 42.5% (Azul #3B82F6)                     │  │
│                       │  │  40% ┼───────╯   ╰───────╮     RAM: 49.8% (Verde #4FBF8A)                    │  │
│                       │  │  20% ┼                   ╰────────────────────────────────────────────────── │  │
│                       │  │   0% ┴───────┬───────┬───────┬───────┬───────┬─────────────────────────────── │  │
│                       │  │    -60s     -50s    -40s    -30s    -20s    -10s     Agora                   │  │
│                       │  └───────────────────────────────────────────────────────────────────────────────┘  │
│                       ├─────────────────────────────────────────────────────────────────────────────────────┤
│                       │  ARMAZENAMENTO LOCAL (PARTIÇÕES DETECTADAS)                                         │
│                       │  ┌─────────┐                                                                        │
│                       │  │ ╭─╮ 30% │ Unidade (C:) [Sistema - NTFS]                 334.2 GB livres de 476 GB│
│                       │  └─────────┘ Status: Saudável • Leitura Win32 direta                                │
│                       │  ┌─────────┐                                                                        │
│                       │  │ ╭─╮ 13% │ Unidade (D:) [Dados - NTFS]                   812.0 GB livres de 931 GB│
│                       │  └─────────┘ Status: Saudável • Espaço abundante                                    │
│                       ├───────────────────────────────────┬─────────────────────────────────────────────────┤
│                       │  PLACA DE VÍDEO & DISPLAY         │  SISTEMA & AMBIENTE                             │
│                       │  • GPU: NVIDIA GeForce RTX 3060   │  • SO: Windows 10 Pro 64-bit (Build 19045)      │
│                       │  • Driver: 560.94 | VRAM: 12.0 GB │  • Tempo de Atividade: 3d 14h 22m               │
│                       │  • Temperatura: 44.0 °C           │  • Runtime: Python 3.14 (Desktop Nativo)        │
│                       ├───────────────────────────────────┴─────────────────────────────────────────────────┤
│                       │  PROCESSOS COM MAIOR CONSUMO DE MEMÓRIA (TOP 6)                                     │
│                       │    PID    Nome do Processo                                         Memória RAM      │
│                       │    14820  chrome.exe                                                  942.3 MB      │
│                       │    19204  Code.exe                                                    512.8 MB      │
│                       └─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Especificação Técnica do Componente Radial Gauge (`app/components/radial_gauge.py`)

### 3.1 Geometria e Estilo Visual
O medidor radial segue a estética de instrumentação técnica e aeronáutica moderna:

- **Arco de Varredura (Sweep Angle):** Arco aberto de **240 graus** (início em 210° e término em -30°), deixando uma abertura de 120° na base inferior.
- **Camada 1 — Trilho de Fundo (Track):** Arco passivo em cinza azulado profundo (`#192331`), espessura de 8px, representando o curso total de 0% a 100%.
- **Camada 2 — Arco Ativo de Progresso:** Arco dinâmico proporcional à porcentagem:
  $$\text{extent} = -\left(\frac{\text{valor}}{\text{máximo}}\right) \times 240.0^\circ$$
- **Gradiente Dinâmico por Severidade:**
  - Carga normal (< 70%): `#3B82F6` (CPU) ou `#4FBF8A` (RAM / Discos).
  - Carga elevada (70% - 85%): `#EAB308` (Amarelo técnico).
  - Carga crítica (> 85%): `#EF4444` (Vermelho alerta).
- **Camada 3 — Miolo Numérico Digital (Center Display):**
  - Valor em destaque: `42.5%` ou `15.8 GB` em Segoe UI Bold (`16pt` a `18pt`), cor `#DCE6F1`.
  - Sub-legenda: `"USO"` ou `"CARGA"` em Segoe UI Regular (`8pt`), cor `#8493A7`.

### 3.2 Implementação Nativa em Tkinter Canvas (Zero Overhead)
Para garantir que a animação e atualização dos gauges não consumam CPU e operem a 60 FPS:
- O componente herda de `ctk.CTkFrame` e encapsula um `tk.Canvas` com fundo transparente (`ThemeColors.BG_SURFACE`) e sem bordas adicionais (`highlightthickness=0`).
- Os arcos e textos são desenhados **uma única vez** no `__init__` via `canvas.create_arc()` e `canvas.create_text()`.
- A atualização do valor (`set_value(percent, display_text)`) executa apenas:
  ```python
  canvas.itemconfigure(self._arc_id, extent=calculated_extent, outline=dynamic_color)
  canvas.itemconfigure(self._text_id, text=display_text)
  ```
- **Custo computacional:** Menos de **0.05 milissegundos** por atualização.

### 3.3 Variantes de Tamanho do Gauge
1. **Padrão (Cartões CPU e RAM):** Diâmetro de `120x120 px`, espessura de traço de `8px`.
2. **Compacto (Partições de Disco):** Diâmetro de `60x60 px`, espessura de traço de `5px`, otimizado para listas de unidades.

---

## 4. Especificação do Gráfico Matplotlib (`app/components/performance_chart.py`)

### 4.1 Integração e Tokens
- **Container:** `FigureCanvasTkAgg` embutido em `ctk.CTkFrame`.
- **Altura:** `210px`, largura responsiva (`fill="x"`).
- **Fundo da Figura:** `#111923` (`ThemeColors.BG_SURFACE`).
- **Fundo do Plot:** `#0B0F14` (`ThemeColors.BG_MAIN`).
- **Grid:** Linhas horizontais discretas em `#192331` (`linestyle=":"`, alpha 0.5).
- **Curva CPU:** Linha de 1.8px em `#3B82F6` com área sob a curva preenchida com transparência (`alpha=0.12`).
- **Curva RAM:** Linha de 1.8px em `#4FBF8A` com área sob a curva preenchida com transparência (`alpha=0.08`).
- **Eixo Y:** Fixo de `0.0%` a `100.0%` com marcações a cada 25%.
- **Eixo X:** Escala temporal dos últimos 60 segundos (`-60s`, `-45s`, `-30s`, `-15s`, `Agora`).

### 4.2 Seletores de Modo (Pílulas Técnicas)
- `[ Ambos (CPU + RAM) ]` — Modo unificado com legenda explicativa.
- `[ Apenas CPU ]` — Visualização isolada do processador.
- `[ Apenas RAM ]` — Visualização isolada da memória.

### 4.3 Orçamento de Renderização Sub-3ms
- Instanciação única de `Figure`, `Axes` e `Line2D`.
- Atualização exclusiva via `line.set_data()` e `canvas.draw_idle()`, evitando o custo destrutivo de reconstrução da figura.

---

## 5. Estruturas de Dados e Thread Safety (`core/monitor.py`)

- **Buffers Circulares:** `deque(maxlen=60)` para CPU e RAM protegidos por `threading.Lock`.
- **Snapshot de Histórico:** Método `get_history_snapshot() -> tuple[list[float], list[float]]` retornando cópias estáticas sem risco de corrida de dados.
- **Métricas Agregadas:** Cálculo de `Média Móvel`, `Pico Máximo` e `Mínimo` na janela de 60 segundos.

---

## 6. Arquivos e Módulos Criados / Modificados

```
Sollaris_Nova/
├── app/
│   ├── components/
│   │   ├── radial_gauge.py         # NOVO: Medidor radial circular técnico (Canvas)
│   │   ├── performance_chart.py    # NOVO: Gráfico Matplotlib dos últimos 60 segundos
│   │   └── sidebar.py              # Existente: Menu lateral
│   └── window.py                   # MODIFICADO: Layout com Gauges e Gráfico
├── core/
│   └── monitor.py                  # MODIFICADO: Extração de histórico e estatísticas 60s
├── docs/
│   ├── plans/
│   │   └── PHASE_2_IMPLEMENTATION_PLAN.md # Este plano atualizado
│   ├── phases/
│   │   └── PHASE_2_DASHBOARD_AND_CHARTS.md# Relatório técnico final da fase
│   ├── specs/
│   │   ├── MVP_CRITERIA.md         # Requisito RF-007 atualizado para Validado
│   │   └── FUTURE_REQUIREMENTS.md  # Requisitos futuros identificados
│   └── changelogs/
│       └── CHANGELOG.md            # Registro formal da entrega
└── tests/
    ├── test_charts.py              # NOVO: Testes unitários do gráfico Matplotlib
    └── test_radial_gauge.py        # NOVO: Testes unitários dos medidores radiais
```

---

## 7. Roteiro Passo a Passo de Execução Técnica

1. **Git Flow:**
   - Criar branch `feature/fase-2-graficos-e-gauges` a partir de `develop`.
2. **Medidor Radial (`app/components/radial_gauge.py`):**
   - Construir a classe `RadialGauge` com geometria de arco de 240°, trilho de fundo, cores dinâmicas e miolo digital.
   - Implementar versão compacta (60px) para discos e padrão (120px) para CPU/RAM.
3. **Buffer e Estatísticas (`core/monitor.py`):**
   - Implementar `get_history_snapshot()` e métodos para obter média, pico e mínimo dos últimos 60 segundos.
4. **Gráfico Histórico (`app/components/performance_chart.py`):**
   - Criar o componente Matplotlib com pré-alocação de linhas, tema escuro e seletor de modos.
5. **Integração na Janela Principal (`app/window.py`):**
   - Substituir as barras horizontais simples pelos componentes `RadialGauge` nos cartões de CPU, RAM e Armazenamento.
   - Adicionar o cartão do gráfico entre os medidores principais e o armazenamento.
   - Conectar o loop de 60 FPS com reciclagem direta de propriedades.
6. **Testes Automatizados:**
   - Criar `tests/test_radial_gauge.py` (validação de cálculos de arco e inicialização).
   - Criar `tests/test_charts.py` (validação de renderização headless e buffer de 60 amostras).
7. **Fechamento e Governança:**
   - Validar com `ruff check .` e `pytest -v`.
   - Gerar `docs/phases/PHASE_2_DASHBOARD_AND_CHARTS.md`.
   - Atualizar `MVP_CRITERIA.md`, `FUTURE_REQUIREMENTS.md` e `CHANGELOG.md`.
   - Mesclar a branch na `develop`.
