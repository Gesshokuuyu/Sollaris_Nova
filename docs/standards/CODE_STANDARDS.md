# Padrões de Código e Diretrizes de Engenharia (Sollaris Nova)

Este documento estabelece as convenções de código, diretrizes de arquitetura, tratamento de exceções e boas práticas obrigatórias para o desenvolvimento do **PC Optimizer (Sollaris Nova)**.

---

## 1. Princípios Gerais de Código
1. **Clareza e Simplicidade:** Código explícito é preferível a truques excessivamente inteligentes.
2. **Tipagem Estática Obrigatória:** Todas as funções, métodos e atributos de classes públicas devem conter Type Hints (`typing`).
3. **Imutabilidade em DTOs:** Dados trafegados entre camadas devem utilizar `@dataclass(frozen=True)` ou tipos primitivos imutáveis.
4. **Resiliência a Falhas:** Falhas de sensores ou encerramento de processos nunca podem derrubar o aplicativo.

---

## 2. Padrões de Estilo Python
- Versão mínima suportada: **Python 3.14+**.
- Conformidade com a **PEP 8**.
- Tamanho máximo de linha: **100 caracteres**.
- Aspas duplas (`"`) ou simples (`'`) consistentes no mesmo módulo.
- Nomenclatura:
  - Módulos e pacotes: `snake_case` (ex.: `metric_card.py`, `hardware.py`)
  - Classes: `PascalCase` (ex.: `HardwareCollector`, `MonitorService`)
  - Funções e métodos: `snake_case` (ex.: `get_cpu_metrics()`, `refresh_data()`)
  - Constantes e Design Tokens: `UPPER_SNAKE_CASE` (ex.: `BG_MAIN`, `REFRESH_INTERVAL_MS`)
  - Variáveis privadas / protegidas: prefixadas com `_` (ex.: `_running`, `_history`)

---

## 3. Tratamento de Erros e Exceções

### 3.1 Regra Proibitiva: Proibido `except:` genérico sem tratamento
Nunca utilize blocos `except:` sem especificar a classe de erro ou capturar apenas para silenciar falhas sem log.

### 3.2 Exceções de Sistema (`psutil` e Windows)
Ao iterar sobre processos do sistema, é mandatório capturar individualmente:
```python
try:
    proc_info = proc.as_dict(attrs=["pid", "name", "memory_info", "cpu_percent"])
except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
    continue
```

### 3.3 Sensores Ausentes ou Falhos
Se um sensor WMI ou térmico falhar, retorne um objeto `SensorReading(value=None, unit="°C", is_available=False)` com o motivo logado. **Nunca retorne `0.0` como se fosse uma medição real.**

---

## 4. Threads e Interface Gráfica (CustomTkinter)

1. **Thread Principal (GUI):**
   - Responsável exclusiva por instanciar, renderizar, animar e destruir widgets Tkinter.
   - Nenhuma chamada de I/O em disco, rede ou varredura de processos pode ser executada nesta thread.
2. **Threads Secundárias (Background Workers):**
   - Coletam dados do sistema em loop ou sob demanda.
   - Para enviar dados ou invocar callbacks na UI, utilize sempre `widget.after(0, callback, *args)` ou coloque eventos em uma `queue.Queue`.
3. **Encerramento Seguro:**
   - Todas as threads de suporte devem ser marcadas como `daemon=True` ou monitorar um evento de encerramento (`threading.Event`).
   - O fechamento da janela (`WM_DELETE_WINDOW`) deve sinalizar o encerramento gracioso das threads antes de `destroy()`.

---

## 5. Estrutura de Testes Automatizados (`pytest`)
- Todos os testes residem no diretório `tests/`.
- Os testes do `core` não devem exigir privilégios de administrador nem alterar arquivos do usuário.
- Utilize mocks (`unittest.mock`) para simular cenários de falhas de sensores, ausência de permissões e desaparecimento de processos.
- Nomenclatura de arquivos de teste: `test_<modulo>.py`.
- Nomenclatura de funções de teste: `test_<comportamento_esperado>()`.

---

## 6. Convenção de Commits
Utilize o padrão **Conventional Commits**:
- `feat:` Nova funcionalidade para o usuário.
- `fix:` Correção de bug.
- `docs:` Alterações na documentação ou specs.
- `refactor:` Alteração no código que não muda comportamento nem adiciona feature.
- `test:` Adição ou correção de testes.
- `chore:` Manutenção de build, dependências ou ferramentas de desenvolvimento.
- `perf:` Melhoria de desempenho.

---

## 7. Protocolo Obrigatório de Fechamento de Fase (Gate de Qualidade)

Ao término de qualquer fase do roadmap (Fase 1 a 6), **antes de mesclar o código ou iniciar a próxima fase**, é obrigatório cumprir o checklist de artefatos e governança:

1. **Auditoria de Integridade Técnica:**
   - `pytest -v` com 100% de aprovação.
   - `ruff check .` limpo, sem erros de linter ou formatação.
2. **Geração do Documento da Fase (`docs/phases/PHASE_<N>_<NOME>.md`):**
   - Resumo detalhado do que foi construído vs escopo planejado.
   - Decisões de arquitetura adotadas e desafios superados.
   - Métricas e validações no Windows 10/11.
3. **Catalogação de Novos Requisitos Futuros (`docs/specs/FUTURE_REQUIREMENTS.md`):**
   - Toda oportunidade de melhoria, novo sensor desejado, nova ideia de recurso ou detalhe técnico descoberto durante a fase deve ser registrado formalmente neste arquivo para não haver desvio de escopo nem perda de contexto.
4. **Atualização dos Critérios de Aceite e DoD (`docs/specs/MVP_CRITERIA.md`):**
   - Atualização do status dos requisitos funcionais entregues na fase.
5. **Registro de Mudanças (`docs/changelogs/CHANGELOG.md`):**
   - Atualização do changelog consolidado e geração do registro do marco.
6. **Apresentação ao Usuário:**
   - Geração de artefato estruturado no brain para validação e transparência.
