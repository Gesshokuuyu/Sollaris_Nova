# Critérios de Aceite e Definição de Pronto (DoD) - MVP

Este documento define formalmente os critérios objetivos para considerar o **MVP (Fases 1 a 3)** concluído com sucesso, conforme estabelecido na Seção 15 da especificação.

---

## 1. Definição de Pronto (Definition of Done)

O MVP será considerado concluído quando todos os itens abaixo forem verificados em ambiente Windows:

1. **Execução sem privilégios elevados:**
   - Inicia e roda normalmente no Windows 10/11 sem exigir elevação de UAC (Administrador) para suas funções padrão.
2. **Medições reais e verificáveis:**
   - Exibe CPU, RAM e Armazenamento com valores autênticos obtidos via APIs do sistema operacional (via `psutil` e módulos Win32).
   - Nenhuma métrica é inventada, estimada ou arredondada de forma enganosa.
3. **Sensores de temperatura:**
   - Exibe a temperatura da CPU e GPU caso sensores WMI/OpenHardwareMonitor estejam acessíveis.
   - Quando indisponíveis, exibe explicitamente o status `"Sensor indisponível"`. Jamais mostra `0°C` ou valores simulados.
4. **Gráfico em tempo real:**
   - Exibe histórico de uso de CPU e RAM dos últimos 60 segundos com atualização contínua e estável.
   - O buffer em memória não vaza memória (estrutura de tamanho fixo `deque(maxlen=60)`).
5. **Lista de processos:**
   - Lista os processos que mais consomem memória, exibindo nome, PID, consumo de RAM e uso de CPU.
   - Tratamento adequado de permissões e de processos que terminam durante a leitura.
6. **Diagnóstico explicável:**
   - Detecta gargalos reais com base em múltiplas amostras (ex.: CPU > 85% por mais de 10 segundos).
   - Toda recomendação apresenta justificativa técnica, impacto provável e risco.
   - Não realiza encerramento forçado de processos ou qualquer ação destrutiva automática.
7. **Responsividade da Interface:**
   - A interface CustomTkinter permanece fluida (sem congelamentos / *Not Responding*).
   - As coletas rodam em thread dedicada (`core.monitor.MonitorService`).
8. **Testes automatizados:**
   - A suite de testes em `tests/` roda com sucesso no `pytest`, cobrindo coleta, resiliência a erros e regras de diagnóstico.

---

## 2. Matriz de Verificação dos Requisitos do MVP

| Requisito | Descrição | Status no MVP | Método de Verificação |
| :--- | :--- | :--- | :--- |
| **RF-001** | Uso atual da CPU (%) | Obrigatório | Comparação com Gerenciador de Tarefas |
| **RF-002** | RAM usada, disponível e total | Obrigatório | Comparação com `systeminfo` / Task Manager |
| **RF-003** | Armazenamento por unidade | Obrigatório | Validação com `Get-PSDrive` |
| **RF-004** | Temperatura de CPU/GPU | Obrigatório | Verificação de disponibilidade de sensor |
| **RF-005** | Top processos por RAM | Obrigatório | Validação com lista de processos `psutil` |
| **RF-006** | UI não bloqueante | Obrigatório | Teste de arrasto e interação durante coleta |
| **RF-007** | Gráfico dos últimos 60s | Obrigatório | Verificação visual e teste de deque fixo |
| **RF-008** | Alertas de gargalo persistente | Obrigatório | Teste unitário com dados simulados no `core` |
| **RF-009** | Tratamento de sensores ausentes | Obrigatório | Teste em máquina com/sem sensores |
| **RF-010** | Tratamento de erros sem crash | Obrigatório | Teste com mock de `psutil.NoSuchProcess` |
