# Especificação Técnica do PC Optimizer (Sollaris Nova)

> Arquivo espelhado para referência contínua da documentação técnica. O arquivo de especificação mestre na raiz do repositório é [PROJECT_SPEC.md](file:///d:/GitHub/Sollaris_Nova/PROJECT_SPEC.md).

Consulte [PROJECT_SPEC.md](file:///d:/GitHub/Sollaris_Nova/PROJECT_SPEC.md) para a íntegra dos requisitos funcionais, não funcionais e plano das 6 fases de desenvolvimento.

## Resumo dos Requisitos do MVP
- **RF-001:** Monitorar uso global da CPU em porcentagem.
- **RF-002:** Monitorar RAM (usada, disponível, total e percentual).
- **RF-003:** Monitorar armazenamento por unidade (total, usado, livre, percentual).
- **RF-004:** Identificar e exibir temperatura de CPU/GPU quando sensores existirem.
- **RF-005:** Listar processos ordenados por consumo de memória com PID e CPU.
- **RF-006:** Thread de coleta em segundo plano, sem travar o loop de renderização da UI.
- **RF-007:** Gráfico histórico com buffer circular dos últimos 60 segundos.
- **RF-008:** Alertas de gargalo baseados em persistência temporal (sem falsos positivos por pico único).
- **RF-009:** Indicação explícita "Sensor indisponível" quando não houver hardware compatível.
- **RF-010:** Tratamento de erros (`NoSuchProcess`, `AccessDenied`, WMI) com log estruturado sem crash.
