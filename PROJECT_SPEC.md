# PC Optimizer — Especificação do Projeto (Sollaris Nova)

**Versão do documento:** 1.0  
**Plataforma inicial:** Windows 10 (futuramente Windows 11)  
**Linguagem:** Python (>= 3.14)  
**Interface:** Desktop (CustomTkinter)  
**Estilo visual:** Minimalista, técnico, azul e preto  
**Objetivo:** Monitoramento, diagnóstico e otimização segura do computador.

---

## 1. Visão Geral

O **PC Optimizer** (codinome do projeto: *Sollaris Nova*) é um aplicativo desktop desenvolvido em Python para monitorar o desempenho do computador, identificar possíveis causas de lentidão e oferecer ferramentas seguras para gerenciamento de recursos.

O aplicativo prioriza:
- **Informações reais:** medições verdadeiras fornecidas pelo sistema operacional e hardware.
- **Diagnósticos explicáveis:** qualquer alerta ou recomendação é sustentado por evidências claras.
- **Ações reversíveis e seguras:** nenhuma alteração destrutiva ou não autorizada.

> O aplicativo **não** deve ser apenas uma ferramenta de limpeza de arquivos nem prometer aumentos mágicos de desempenho sem medições comprovadas.

### 1.1 Objetivos Principais
1. Monitorar CPU, RAM, armazenamento e processos em tempo real.
2. Exibir temperaturas quando houver sensores acessíveis e compatíveis.
3. Identificar consumo elevado e persistente de recursos.
4. Apresentar recomendações com justificativas técnicas, impacto e risco.
5. Permitir limpeza controlada de arquivos temporários com prévia e confirmação.
6. Ajudar a gerenciar programas de inicialização.
7. Oferecer perfis para uso cotidiano e jogos.
8. Registrar métricas e comparar resultados.
9. Funcionar 100% localmente, sem depender de serviços externos.

### 1.2 Público-alvo
Usuários de Windows 10/11 que desejam compreender melhor o desempenho do computador e administrar recursos sem precisar navegar por diversas ferramentas dispersas do sistema.

### 1.3 Princípios do Produto
- **Segurança antes da automação:** O sistema nunca altera o ambiente sem prévia e confirmação do usuário.
- **Dados reais antes de recomendações:** Sem dados fictícios, estimativas sem fundamento ou scores arbitrários.
- **Transparência sobre limitações do hardware:** Sensores indisponíveis são explicitamente sinalizados como tais.
- **Interface discreta e objetiva:** Foco na produtividade técnica, sem poluição visual.
- **Nenhuma promessa sem evidências:** Desempenho é medido antes e depois.
- **Nenhuma coleta remota:** Privacidade total por padrão; telemetria zero.
- **Ações reversíveis:** Onde tecnicamente possível, o estado anterior é preservado para rollback.

---

## 2. Escopo do MVP

O MVP é a primeira versão utilizável do produto, focada em monitoramento funcional e diagnóstico básico.

### 2.1 Funcionalidades Obrigatórias (MVP)
- **Dashboard:**
  - Uso atual da CPU em porcentagem.
  - Memória RAM usada, disponível e total.
  - Uso e espaço livre do armazenamento (por unidade).
  - Temperatura da CPU quando disponível.
  - Temperatura da GPU quando disponível.
  - Nome do processador, memória total e informações básicas do sistema.
  - Gráfico de CPU e RAM dos últimos 60 segundos.
  - Lista dos processos que mais consomem memória.
  - Horário da última atualização.
  - Estado explícito dos sensores indisponíveis.
- **Monitoramento:**
  - Atualização configurável (padrão: 1 segundo).
  - Execução assíncrona do monitoramento em thread dedicada sem bloquear a UI.
  - Tratamento resiliente de processos encerrados durante a coleta (`NoSuchProcess`, `AccessDenied`).
  - Tratamento resiliente de erros de permissão.
  - Histórico temporário das amostras em memória (buffer circular/deque de 60s).
- **Diagnóstico Básico:**
  - Aviso de consumo persistentemente alto de CPU (múltiplas amostras).
  - Aviso de pouca memória disponível.
  - Aviso de armazenamento quase cheio.
  - Identificação dos processos que mais consomem memória.
  - Recomendações com motivo, impacto provável e risco.
  - Limites configuráveis, sem alertas por picos pontuais isolados.
- **Interface:**
  - Menu lateral de navegação.
  - Dashboard como página inicial padrão.
  - Tema escuro azul e preto.
  - Layout responsivo e redimensionável.
  - Indicadores claros de carregamento, erro e indisponibilidade de sensores.
  - Sem tela de login, sem contas, sem chamadas externas.

### 2.2 Funcionalidades Fora do MVP (Versões 1.x e Futuras)
- Limpeza automatizada avançada (fora do MVP; entra na v1.x com confirmação).
- Gerenciamento completo de serviços do Windows.
- Alterações automáticas no registro.
- Aplicação automática de planos de energia.
- Monitoramento avançado de sensores proprietários específicos do fabricante.
- Captura de FPS / overlay em jogos.
- Inteligência artificial ou modelos LLM locais integrados.
- Otimização automática sem confirmação (proibido pela filosofia do produto).
- Execução como serviço de segundo plano do Windows.

---

## 3. Requisitos Funcionais

| ID | Requisito | Prioridade | Fase |
| :--- | :--- | :--- | :--- |
| **RF-001** | Exibir uso de CPU em porcentagem | Obrigatório | MVP (Fase 1-2) |
| **RF-002** | Exibir memória RAM usada, disponível e total | Obrigatório | MVP (Fase 1-2) |
| **RF-003** | Exibir espaço usado e livre por unidade de armazenamento | Obrigatório | MVP (Fase 1-2) |
| **RF-004** | Exibir temperatura de CPU e GPU quando disponível | Obrigatório | MVP (Fase 2) |
| **RF-005** | Exibir processos ordenados por consumo de RAM | Obrigatório | MVP (Fase 2) |
| **RF-006** | Atualizar métricas sem travar a interface gráfica | Obrigatório | MVP (Fase 1-2) |
| **RF-007** | Manter gráfico histórico de CPU e RAM (últimos 60s) | Obrigatório | MVP (Fase 2) |
| **RF-008** | Gerar alertas de possíveis gargalos baseados em persistência | Obrigatório | MVP (Fase 3) |
| **RF-009** | Tratar sensores indisponíveis de forma transparente | Obrigatório | MVP (Fase 2) |
| **RF-010** | Registrar erros sem encerrar o aplicativo | Obrigatório | MVP (Fase 1-3) |
| **RF-011** | Limpar arquivos temporários com prévia e confirmação | Alta | Versão 1.x (Fase 4) |
| **RF-012** | Gerenciar itens selecionados de inicialização | Alta | Versão 1.x (Fase 4) |
| **RF-013** | Salvar histórico de métricas no SQLite com retenção | Média | Versão 1.x (Fase 5) |
| **RF-014** | Criar perfis de uso cotidiano e jogos | Média | Versão 1.x (Fase 5) |
| **RF-015** | Empacotar como executável independente (.exe) | Final | Distribuição (Fase 6) |

---

## 4. Requisitos Não Funcionais

### 4.1 Desempenho
- O intervalo de atualização padrão deve ser de aproximadamente 1 segundo.
- Operações de I/O, medições de hardware e varreduras de processos nunca executam na thread da GUI (Tkinter loop).
- Histórico em memória utiliza estruturas com tamanho máximo fixo (`collections.deque(maxlen=60)`).
- O próprio monitoramento deve ser leve, consumindo menos de 1% a 2% de CPU em regime estável.

### 4.2 Confiabilidade
- Falhas na leitura de sensores nunca devem provocar crash ou encerrar o programa.
- Processos que terminam durante o ciclo de coleta são ignorados silenciosa e seguramente.
- Dados indisponíveis nunca são mascarados com zeros fictícios ou estimativas inventadas.
- Falha em um módulo secundário (ex.: WMI de temperatura) mantém o restante do monitor operacional.

### 4.3 Segurança
- Execução sem necessidade de privilégios de Administrador para o monitoramento padrão.
- Nunca encerrar processos de forma automática no MVP.
- Nunca apagar arquivos sem prévia detalhada, seleção e confirmação expressa.
- Não desativar serviços essenciais do Windows nem aplicar rotinas cegas de "debloat".
- Não executar comandos de sistema montados a partir de strings arbitrárias.

### 4.4 Privacidade
- Coleta 100% local.
- Zero telemetria, zero requisições para servidores externos.
- Nomes de processos ou dados da máquina nunca saem do computador do usuário.
- O usuário tem a faculdade de limpar o histórico local armazenado a qualquer momento.

---

## 5. Arquitetura Técnica

```
pc-optimizer/ (Sollaris Nova)
├── main.py                     # Ponto de entrada da aplicação
├── requirements.txt            # Dependências de produção
├── requirements-dev.txt        # Dependências de desenvolvimento e testes
├── README.md                   # Apresentação do projeto e guia rápido
├── PROJECT_SPEC.md             # Especificação completa do projeto
├── LICENSE                     # Licença de código aberto (MIT)
├── THIRD_PARTY_NOTICES.md      # Avisos e licenças de dependências de terceiros
├── docs/                       # Documentação viva do projeto
│   ├── specs/                  # Especificações técnicas e funcionais
│   ├── architecture/           # Detalhes de arquitetura, fluxo e camadas
│   ├── standards/              # Padrões de código, design tokens e convenções
│   └── changelogs/             # Histórico de alterações e releases
├── app/                        # Camada de Apresentação (CustomTkinter UI)
│   ├── __init__.py
│   ├── window.py               # Janela principal e ciclo de eventos da UI
│   ├── theme.py                # Paleta de cores, tipografia e estilos
│   ├── components/             # Componentes visuais reutilizáveis
│   │   ├── __init__.py
│   │   ├── metric_card.py      # Cartão de métrica técnica
│   │   ├── sidebar.py          # Menu lateral de navegação
│   │   └── performance_chart.py# Gráfico Matplotlib embarcado no Tkinter
│   └── pages/                  # Telas/visões da aplicação
│       ├── __init__.py
│       ├── dashboard.py        # Dashboard principal (MVP)
│       ├── diagnostics.py      # Tela de diagnóstico e alertas (Fase 3)
│       ├── cleaner.py          # Limpeza com prévia (Fase 4)
│       ├── startup.py          # Gerenciamento de inicialização (Fase 4)
│       ├── game_mode.py        # Perfis de desempenho (Fase 5)
│       └── history.py          # Histórico SQLite (Fase 5)
├── core/                       # Camada de Negócio e Coleta (Sem dependência de UI)
│   ├── __init__.py
│   ├── monitor.py              # Orquestrador do ciclo de monitoramento e buffer
│   ├── processes.py            # Coleta e ordenação segura de processos
│   ├── diagnostics.py          # Regras de detecção e análise de gargalos
│   ├── recommendations.py      # Estrutura e geração de recomendações
│   ├── hardware.py             # Informações de hardware e sensores (CPU/RAM/Disco/Temp)
│   ├── cleanup.py              # Varredura e exclusão segura de temporários
│   ├── startup_manager.py      # Itens de inicialização do Windows
│   └── game_profiles.py        # Gestão de perfis
├── database/                   # Camada de Persistência Local
│   ├── __init__.py
│   ├── db.py                   # Conexão SQLite e migrações
│   └── history.py              # DAO de métricas e eventos com retenção
├── safety/                     # Camada de Segurança e Auditoria
│   ├── __init__.py
│   ├── permissions.py          # Checagem de privilégios e UAC
│   ├── restore.py              # Registro de alterações reversíveis
│   └── audit_log.py            # Log de ações locais autorizadas
├── tests/                      # Testes Automatizados
│   ├── __init__.py
│   ├── test_monitor.py
│   ├── test_hardware.py
│   ├── test_diagnostics.py
│   └── test_cleanup.py
└── data/                       # Diretório local para banco SQLite e logs
    └── .gitkeep
```

---

## 6. Bibliotecas e Dependências

### Dependências Iniciais
- `psutil` (>= 6.0.0): Coleta de CPU, RAM, discos e processos.
- `customtkinter` (>= 5.2.0): Interface desktop moderna com tema escuro.
- `matplotlib` (>= 3.9.0): Gráficos históricos de desempenho integrados ao Tkinter.
- `pytest` (>= 8.0.0): Suite de testes automatizados.

### Dependências Opcionais / Específicas do Windows
- `WMI`: Consultas de hardware, fabricante e temperaturas no Windows.
- `pywin32`: APIs Win32 para permissões e registro.
- `pyinstaller`: Empacotamento em executável único `.exe`.

---

## 7. Especificação Visual e Design System

### 7.1 Identidade Visual
- Minimalista, técnico, sóbrio.
- Sem gradientes espalhafatosos, sem neons, sem emojis como ícones estruturais.
- Tipografia: **Segoe UI** (nativa no Windows 10/11) com hierarquia limpa.
- Bordas sutis de 1px (`#263345`).

### 7.2 Paleta de Cores
| Token | Valor Hex | Finalidade |
| :--- | :--- | :--- |
| `BG_MAIN` | `#0B0F14` | Fundo principal da aplicação |
| `BG_SIDEBAR` | `#0E141C` | Fundo do menu lateral |
| `BG_SURFACE` | `#111923` | Superfície de cartões e painéis |
| `BORDER_COLOR`| `#263345` | Bordas e divisores discretos (1px) |
| `ACCENT_BLUE` | `#3B82F6` | Ações primárias, itens ativos, foco |
| `ACCENT_LIGHT`| `#60A5FA` | Hover, destaque sutil |
| `TEXT_PRIMARY`| `#DCE6F1` | Títulos e valores numéricos em evidência |
| `TEXT_MUTED`  | `#8493A7` | Rótulos secundários, unidades, legendas |
| `STATUS_OK`   | `#4FBF8A` | Estado normal / saudável (verde discreto) |
| `STATUS_WARN` | `#EAB308` | Alerta / atenção (amarelo) |
| `STATUS_ERROR`| `#EF4444` | Falha / erro / sobrecarga (vermelho) |

### 7.3 Dimensões da Janela
- Largura padrão: 1180 px | Altura padrão: 760 px
- Largura mínima: 960 px | Altura mínima: 640 px
- Menu lateral: ~220 px de largura fixa

---

## 8. Definição das Métricas

- **CPU:** Percentual global de uso, frequência atual/base, total de núcleos físicos e lógicos. Uso por processo.
- **RAM:** Total, utilizada, livre, disponível em cache e porcentagem. Top processos consumidores.
- **Armazenamento:** Capacidade total, espaço usado, espaço livre e percentual de ocupação por ponto de montagem (C:, D:, etc.).
- **Temperatura:** Sensor de CPU e GPU. Caso indisponível, sinalização explícita `"Sensor indisponível"`.
- **GPU Integrada vs Dedicada:** Distinção clara entre memória RAM do sistema compartilhada e VRAM dedicada.

---

## 9. Regras de Diagnóstico

Diagnósticos são disparados com base em janelas de tempo, não leituras isoladas:
1. **CPU Elevada:** Média móvel superior a 85% por mais de 10 amostras consecutivas.
2. **Memória Baixa:** Menos de 10% ou 1.5 GB disponíveis de forma persistente.
3. **Armazenamento Crítico:** Menos de 10% ou 15 GB livres na unidade do sistema.

Cada recomendação deve conter:
- **Título**
- **Evidência observada** (dados numéricos que motivaram o alerta)
- **Explicação técnica**
- **Impacto provável**
- **Risco**
- **Ação sugerida**
- **Possibilidade de reversão**

---

## 10. Plano de Desenvolvimento (Fases)

1. **Fase 1 — Fundação:** Ambiente virtual, dependências, janela principal, tema e hardware básico.
2. **Fase 2 — Dashboard:** Cartões de métricas, gráficos Matplotlib em tempo real, lista de processos, thread assíncrona.
3. **Fase 3 — Diagnóstico:** Motor de regras com histórico, recomendações explicáveis, testes automatizados.
4. **Fase 4 — Limpeza e Inicialização:** Prévia segura de temporários, confirmação, itens de startup do Windows.
5. **Fase 5 — Histórico e Perfis:** SQLite, retenção de dados, perfis para jogos e produtividade.
6. **Fase 6 — Distribuição:** Validação no Windows 10/11, verificação de licenças e build PyInstaller.
