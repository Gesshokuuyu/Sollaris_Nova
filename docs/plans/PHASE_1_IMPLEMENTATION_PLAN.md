# Plano Detalhado de Implementação e Especificação Visual — Fase 1 (Fundação)

Este documento descreve detalhadamente a especificação visual, os dados exibidos, a hierarquia tipográfica, os cálculos, os limites de alerta e a estrutura exata de cada componente visual da **Fase 1 (Fundação e Métricas de Hardware)**.

---

## 1. Visão Geral do Layout da Janela (Wireframe Visual)

A janela principal (`1180x760 px`) é dividida em uma barra lateral fixa de `220px` à esquerda e uma área de conteúdo responsiva à direita:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ SOLLARIS NOVA — PC OPTIMIZER                                                                   [—] [□] [X] │
├───────────────────────┬─────────────────────────────────────────────────────────────────────────────────────┤
│  [Ícone] SOLLARIS     │  VISÃO GERAL                                       ● Sistema Operacional: Saudável  │
│  Sollaris Nova v0.1.0 │  Última leitura: 11:32:05 | Intervalo: Manual      [ ⟳ Atualizar Agora ]            │
├───────────────────────┼───────────────────────────────────────────────────┬─────────────────────────────────┤
│                       │  CARTÃO CPU                                       │  CARTÃO MEMÓRIA RAM             │
│  [>] Visão Geral      │  42.5%                                    [Normal]│  15.8 GB / 31.7 GB      [Normal]│
│  [ ] Diagnóstico      │  ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │  ███████████████████░░░░░░░░░░░ │
│  [ ] Limpeza          │  • Modelo: AMD Ryzen 5 5600X (6C / 12T)           │  • Usada: 15.8 GB (49.8%)       │
│  [ ] Inicialização    │  • Frequência Base: 3.70 GHz | Atual: 4.15 GHz    │  • Disponível: 15.9 GB          │
│  [ ] Modo Game        │  • Temperatura: 48.0 °C  [Sensor WMI]             │  • Total Instalada: 31.7 GB     │
│  [ ] Histórico        ├───────────────────────────────────────────────────┴─────────────────────────────────┤
│  [ ] Configurações    │  CARTÃO ARMAZENAMENTO (DISCOS LOCAIS)                                               │
│                       │  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│                       │  │ Unidade (C:) [Sistema - NTFS]                           334.2 GB livres de 476 GB│  │
│                       │  │ ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  (29.8% Usado)│  │
│                       │  ├───────────────────────────────────────────────────────────────────────────────┤  │
│                       │  │ Unidade (D:) [Dados - NTFS]                              812.0 GB livres de 931 GB│  │
│                       │  │ ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  (12.8% Usado)│  │
│                       │  └───────────────────────────────────────────────────────────────────────────────┘  │
│                       ├───────────────────────────────────────────────────┬─────────────────────────────────┤
│                       │  CARTÃO GPU & VÍDEO                               │  CARTÃO RESUMO DO SISTEMA       │
│                       │  • GPU: NVIDIA GeForce RTX 3060                   │  • Sistema: Windows 10 Pro 64-bit│
│                       │  • Temperatura GPU: 44.0 °C                       │  • Build: 19045.5487 (AMD64)    │
│                       │  • Driver / WMI: Operante                         │  • Sensores: 2/2 Acessíveis     │
├───────────────────────┴───────────────────────────────────────────────────┴─────────────────────────────────┤
│  Status: Pronto • Python 3.14.3 • Executando sem privilégios elevados                     Sollaris Nova v0.1│
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detalhamento Card a Card

---

### 2.1 Cabeçalho Técnico (Header Bar)
- **Localização:** Topo da área principal (`padding: 24px 24px 16px 24px`).
- **Elementos Visuais:**
  - **Título Principal:** `"Visão Geral"` (Segoe UI, 20px, Bold, cor `#DCE6F1`).
  - **Timestamp da Leitura:** `"Última amostragem: HH:MM:SS"` (Segoe UI, 11px, Regular, cor `#8493A7`).
  - **Badge de Status Global:**
    - Se todas as métricas estiverem normais: chip verde (`#4FBF8A`, texto `"● Sistema Estável"`).
    - Se houver recurso sob carga alta: chip amarelo (`#EAB308`, texto `"▲ Carga Elevada"`).
    - Se houver recurso crítico: chip vermelho (`#EF4444`, texto `"✕ Atenção Requerida"`).
  - **Botão de Atualização Manual:**
    - Botão técnico estilizado com `[ ⟳ Atualizar Agora ]`.
    - Fundo `#16202C`, borda `#263345`, texto `#DCE6F1`, hover `#3B82F6`.
    - Dispara a coleta sob demanda e atualiza imediatamente todos os valores da tela.

---

### 2.2 Cartão 1: Processador (CPU)
- **Superfície:** Fundo `#111923`, borda `#263345` (1px), raio de canto `6px`, padding interno `16px`.
- **Rótulo Superior:** `"PROCESSADOR (CPU)"` (Segoe UI, 12px, Bold, cor `#8493A7`).
- **Badge de Estado:** Chip sutil no canto superior direito:
  - `< 70%`: `"Normal"` (borda e texto `#4FBF8A`)
  - `70% - 85%`: `"Elevado"` (borda e texto `#EAB308`)
  - `> 85%`: `"Crítico"` (borda e texto `#EF4444`)
- **Valor em Destaque:**
  - Exemplo: `42.5 %` (Segoe UI, 28px, Bold, cor `#DCE6F1`).
- **Barra de Progresso Técnica:**
  - Altura: `6px`, fundo da calha: `#1C2736`.
  - Cor do preenchimento dinâmica: verde (`#4FBF8A`) até 70%, amarelo (`#EAB308`) até 85%, vermelho (`#EF4444`) acima de 85%.
- **Grade de Detalhes Técnicos (2 colunas alinhadas):**
  - **Modelo:** Nome comercial do processador (ex.: `AMD Ryzen 5 5600X 6-Core Processor` ou `11th Gen Intel(R) Core(TM) i7-11800H`).
  - **Núcleos:** `X Físicos | Y Lógicos` (ex.: `6 Físicos | 12 Lógicos`).
  - **Frequência:** `Base: X.XX GHz | Atual: Y.YY GHz` (valores arredondados em duas casas decimais).
  - **Temperatura da CPU:**
    - Se disponível: `48.5 °C` (com rótulo atenuado `[Sensor WMI]`).
    - Se indisponível: tag neutra atenuada `"Sensor indisponível"` (cor `#8493A7`), sem exibir `0°C` e sem mascaramento.

---

### 2.3 Cartão 2: Memória RAM
- **Superfície:** Fundo `#111923`, borda `#263345` (1px), raio `6px`, padding `16px`.
- **Rótulo Superior:** `"MEMÓRIA RAM"` (Segoe UI, 12px, Bold, cor `#8493A7`).
- **Badge de Estado:**
  - Memória disponível > 15% ou > 2 GB: `"Normal"` (`#4FBF8A`)
  - Memória disponível entre 10% e 15%: `"Atenção"` (`#EAB308`)
  - Memória disponível < 10% ou < 1.5 GB: `"Crítico"` (`#EF4444`)
- **Valor em Destaque:**
  - Exemplo: `15.8 GB` em uso de `31.7 GB` (`49.8%`) (Segoe UI, 28px / 16px, cor `#DCE6F1`).
- **Barra de Progresso Técnica:**
  - Altura: `6px`, calha `#1C2736`.
  - Cor dinâmica conforme o percentual em uso.
- **Grade de Detalhes Técnicos:**
  - **Em Uso:** `15.8 GB` (`15.823 MB`) — memória residente alocada ativa.
  - **Disponível:** `15.9 GB` (`15.912 MB`) — memória pronta para alocação imediata por novos aplicativos.
  - **Total Instalada:** `31.7 GB` (valor reportado pelo hardware).
  - **Nota Explicativa Discreta:**  
    *(10px, cor `#526071`)*: *"A memória disponível inclui buffers e cache que o Windows reutiliza instantaneamente quando necessário."*

---

### 2.4 Cartão 3: Armazenamento (Partições de Disco)
- **Superfície:** Fundo `#111923`, borda `#263345`, ocupa a largura inteira abaixo da CPU/RAM.
- **Rótulo Superior:** `"ARMAZENAMENTO LOCAL"` (Segoe UI, 12px, Bold, cor `#8493A7`).
- **Lista de Unidades Detectadas:**
  - Cada partição de disco fixa (C:, D:, etc.) ganha uma linha de detalhe completa:
    ```
    Unidade (C:) [Sistema - NTFS]                             334.2 GB livres de 476.0 GB
    ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    29.8% ocupado
    ```
  - **Dados por Partição:**
    - Letra da Unidade e Identificador (ex.: `C:\` ou `D:\`).
    - Tipo de Sistema de Arquivos (ex.: `NTFS`, `FAT32`).
    - Espaço Usado: formatado em `GB` ou `TB` (ex.: `141.8 GB`).
    - Espaço Livre: formatado em `GB` ou `TB` (ex.: `334.2 GB`).
    - Capacidade Total: `476.0 GB`.
    - Percentual de Ocupação: calculado com `(usado / total) * 100`.
    - Barra individual de preenchimento (verde até 80%, amarela de 80% a 90%, vermelha se > 90% ou espaço livre < 15 GB).

---

### 2.5 Cartão 4: GPU & Sensores Térmicos
- **Superfície:** Fundo `#111923`, borda `#263345`, padding `16px`.
- **Rótulo Superior:** `"PLACA DE VÍDEO & SENSORES"` (Segoe UI, 12px, Bold, cor `#8493A7`).
- **Itens de Detalhe:**
  - **Modelo da GPU:** Nome do adaptador de vídeo obtido via `Win32_VideoController` (ex.: `NVIDIA GeForce RTX 3060` ou `Intel(R) UHD Graphics 630`).
  - **Temperatura da GPU:** Exibe valor em `°C` quando suportado pela API de vídeo, ou `"Sensor indisponível"`.
  - **Status de Acesso dos Sensores:**
    - WMI ACPI ThermalZone: `Acessível` ou `Não suportado pela placa-mãe`.
    - Diagnóstico de Permissão: `Leitura autorizada` (sem necessidade de privilégios de Admin).

---

### 2.6 Cartão 5: Resumo da Máquina e Sistema Operacional
- **Superfície:** Fundo `#111923`, borda `#263345`, padding `16px`.
- **Rótulo Superior:** `"SISTEMA & AMBIENTE"` (Segoe UI, 12px, Bold, cor `#8493A7`).
- **Itens de Detalhe:**
  - **Sistema Operacional:** Nome amigável e edição (ex.: `Windows 10 Pro 64-bit`).
  - **Versão / Build do Windows:** Número de compilação exato (ex.: `Build 10.0.19045`).
  - **Arquitetura da CPU:** `AMD64 / x86_64`.
  - **Tempo de Atividade (Uptime):** Dias, horas e minutos desde a última inicialização do Windows (obtido via `psutil.boot_time()`).
  - **Ambiente de Execução:** `Python 3.14.3 (Modo Desktop Nativo)`.

---

## 3. Especificação de Tipagem e Unidades de Dados (`core/hardware.py`)

Todas as unidades são rigorosamente padronizadas:
- **Tamanhos e Capacidades:** Manipuladas internamente como inteiros em **Bytes** (`int`), e formatadas na visualização por função utilitária `format_bytes(bytes_count: int) -> str` (ex.: `1024**3 -> "1.00 GB"`).
- **Frequências de Processador:** Manipuladas em **MHz** (`float`), formatadas na UI em `GHz` quando >= 1000 MHz.
- **Temperaturas:** Manipuladas em graus Celsius (`float`), formatadas com 1 casa decimal (ex.: `48.5 °C`) ou `None`.
- **Porcentagens:** Manipuladas em `float` com 1 casa decimal (ex.: `42.5 %`).

---

## 4. Tratamento de Exceções e Resiliência Técnica na Coleta

| Componente | Possível Falha do Windows | Comportamento e Tratamento |
| :--- | :--- | :--- |
| **CPU Percent** | Primeira chamada do psutil retornando 0.0 | O `HardwareCollector` realiza inicialização prévia no construtor para que a primeira leitura da UI já seja autêntica. |
| **Temperatura WMI** | Placa-mãe desktop sem suporte ACPI ThermalZone ou acesso restrito | Captura `wmi.x_wmi`, registra log de nível `DEBUG` e retorna `SensorReading(is_available=False, value=None)`. UI exibe `"Sensor indisponível"`. |
| **Partições de Disco** | Unidade de CD/DVD vazia, pendrive desmontado ou partição de recuperação bloqueada | O coletor filtra apenas partições com ponto de montagem acessível e captura `PermissionError` / `OSError` individualmente, não quebrando a lista. |
| **Memória RAM** | Falha improvável no psutil | Retorna objeto seguro com fallback e log estruturado. |
| **GPU / Vídeo** | Múltiplas GPUs (ex.: integrada + dedicada em notebook) | Lista os adaptadores detectados e prioriza a GPU dedicada ou exibe ambas em formato compacto. |

---

## 5. Próximos Passos de Execução da Fase 1

1. **Git:** Criar `feature/fase-1-fundacao` a partir de `develop`.
2. **Core:** Implementar `core/hardware.py` com todas as dataclasses e a classe `HardwareCollector`.
3. **UI Components:** Criar `app/components/sidebar.py` e os widgets técnicos.
4. **UI Window:** Implementar `app/window.py` com a montagem exata dos cards descritos acima.
5. **Entrypoint:** Ligar a janela ao `main.py` e testar via `run.bat` / atalho silencioso.
6. **Testes:** Criar `tests/test_hardware.py` com 100% de cobertura dos coletores e mocks de falha.
7. **Gate de Fechamento:** Gerar `docs/phases/PHASE_1_FOUNDATION.md`, atualizar `FUTURE_REQUIREMENTS.md` e `MVP_CRITERIA.md`.
