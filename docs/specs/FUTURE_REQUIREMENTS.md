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

---

## 2. Registro de Itens por Fase de Desenvolvimento

### Fase 1 — Fundação e Coleta de Métricas
- **Descoberta WMI ACPI:** A classe `MSAcpi_ThermalZoneTemperature` retorna `wmi.x_access_denied` em execuções de usuário comum no Windows 10/11. O sistema agora exibe `"Sensor indisponível"` com elegância. Foi catalogado o requisito `RF-FUT-008` para investigar soluções de baixo nível caso o usuário deseje telemetria aprofundada de clock/temperatura.
- **Drives Vazios / Leitores de Cartão:** Unidades mapeadas que não possuem mídia física inserida disparam `OSError [WinError 21]`. O filtro implementado em `HardwareCollector` protege a aplicação contra travamentos. Catalogado `RF-FUT-007` para sincronização reativa com mensagens do Windows.
- **Navegação Sem Emojis:** Identificada a necessidade de ícones visuais profissionais vetoriais em PNG monocromático para substituir qualquer elemento com aspecto artificial. Entregue pacote de ícones em `assets/nav_icons/`.

### Fase 2 — Dashboard Completo
*(Espaço reservado para descobertas da Fase 2).*

### Fase 3 — Diagnóstico e Recomendações
*(Espaço reservado para descobertas da Fase 3).*

---

## 3. Critérios para Adicionar um Novo Requisito
Todo novo requisito adicionado a este catálogo deve responder:
1. **Qual é a necessidade real do usuário ou do sistema?**
2. **Qual é a evidência técnica ou limitação encontrada?**
3. **Qual é o risco e o impacto para o produto?**
4. **Respeita a filosofia do produto (segurança antes de automação, sem dados falsos, sem telemetria)?**
