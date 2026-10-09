"""Motor de Diagnóstico e Detecção de Gargalos Técnicos — Sollaris Nova.

Analisa telemetria contínua, histórico temporal e consumo de processos
para fornecer diagnósticos explicáveis e auditáveis em 7 dimensões,
sem pontuações arbitrárias e com eliminação rigorosa de falsos positivos.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.hardware import SystemSnapshot
    from core.processes import ProcessItem

logger = logging.getLogger("sollaris_nova.diagnostics")


class FindingLevel(Enum):
    """Nível de severidade semântica do diagnóstico técnico."""

    OPTIMAL = "optimal"
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True)
class DiagnosticFinding:
    """Representa um apontamento técnico de diagnóstico em 7 dimensões explicáveis."""

    category: str
    level: FindingLevel
    title: str
    evidence: str
    technical_explanation: str
    probable_impact: str
    risk: str
    suggested_action: str
    is_reversible: bool = True
    target_route: str | None = None

    @property
    def description(self) -> str:
        """Alias de compatibilidade com interfaces e testes existentes."""
        return self.technical_explanation

    @property
    def recommendation(self) -> str:
        """Alias de compatibilidade com interfaces e testes existentes."""
        return self.suggested_action


class DiagnosticEngine:
    """Motor de diagnóstico explicável com verificação de persistência temporal."""

    @staticmethod
    def evaluate(snapshot: SystemSnapshot) -> list[DiagnosticFinding]:
        """Avaliação direta para compatibilidade retroativa (amostra única)."""
        return DiagnosticEngine.evaluate_with_history(
            snapshot=snapshot,
            cpu_history=[snapshot.cpu.total_percent],
            ram_history=[snapshot.ram.percent],
            processes=[],
        )

    @staticmethod
    def evaluate_with_history(
        snapshot: SystemSnapshot,
        cpu_history: list[float] | None = None,
        ram_history: list[float] | None = None,
        processes: list[ProcessItem] | None = None,
    ) -> list[DiagnosticFinding]:
        """Avalia a saúde técnica do sistema cruzando telemetria atual e histórico temporal."""
        findings: list[DiagnosticFinding] = []

        # 1. Avaliação de CPU com persistência temporal
        cpu_finding = DiagnosticEngine._check_cpu_persistence(
            cpu_history=cpu_history or [snapshot.cpu.total_percent],
            current_pct=snapshot.cpu.total_percent,
        )
        findings.append(cpu_finding)

        # 2. Avaliação de Memória RAM com persistência
        ram_finding = DiagnosticEngine._check_ram_pressure(
            snapshot=snapshot,
            ram_history=ram_history or [snapshot.ram.percent],
        )
        findings.append(ram_finding)

        # 3. Avaliação de Arquivo de Paginação (Swap Thrashing)
        swap_finding = DiagnosticEngine._check_swap_thrashing(snapshot)
        if swap_finding:
            findings.append(swap_finding)

        # 4. Avaliação de Armazenamento Local
        disk_findings = DiagnosticEngine._check_disk_exhaustion(snapshot)
        findings.extend(disk_findings)

        # 5. Avaliação de Processos Predadores
        if processes:
            predator_finding = DiagnosticEngine._check_predator_process(processes, snapshot)
            if predator_finding:
                findings.append(predator_finding)

        # 6. Avaliação de Uptime do Sistema
        uptime_finding = DiagnosticEngine._check_system_uptime(snapshot)
        if uptime_finding:
            findings.append(uptime_finding)

        return findings

    @staticmethod
    def _check_cpu_persistence(cpu_history: list[float], current_pct: float) -> DiagnosticFinding:
        """Analisa o histórico de CPU eliminando picos transitórios (<5s)."""
        n_samples = len(cpu_history)

        if n_samples >= 10:
            recent_window = cpu_history[-15:] if n_samples >= 15 else cpu_history
            count_critical = sum(1 for v in recent_window if v >= 85.0)
            count_warning = sum(1 for v in recent_window if v >= 70.0)
            avg_window = sum(recent_window) / len(recent_window)
            elapsed_sec = len(recent_window) * 1.5

            if count_critical >= 10:
                return DiagnosticFinding(
                    category="Processador (CPU)",
                    level=FindingLevel.CRITICAL,
                    title="Saturação Sustentada de CPU",
                    evidence=f"Carga média de {avg_window:.1f}% nos últimos {elapsed_sec:.0f}s ({count_critical} de {len(recent_window)} amostras acima de 85%).",
                    technical_explanation="O agendador de threads do Windows está enfrentando contenção contínua em múltiplos núcleos lógicos. Processos concorrentes disputam fatias quânticas de tempo sem folga ociosa.",
                    probable_impact="Aumento de latência de entrada (DPC/ISR), queda perceptível de taxa de quadros e atraso na troca de janelas.",
                    risk="Elevação térmica sustentada e possível acionamento de estrangulamento térmico (thermal throttling) pelo hardware.",
                    suggested_action="Inspecione os processos de maior consumo e encerre tarefas secundárias dispensáveis em segundo plano.",
                    is_reversible=True,
                    target_route="overview",
                )

            if count_warning >= 8 or avg_window >= 75.0:
                return DiagnosticFinding(
                    category="Processador (CPU)",
                    level=FindingLevel.WARNING,
                    title="Carga Moderadamente Alta de CPU",
                    evidence=f"Carga média de {avg_window:.1f}% nos últimos {elapsed_sec:.0f}s sob processamento ativo contínuo.",
                    technical_explanation="A CPU opera com alta utilização contínua, porém sem saturação completa de todos os núcleos lógicos.",
                    probable_impact="Pequeno aumento no tempo de resposta para novas tarefas iniciadas pelo usuário.",
                    risk="Se a demanda aumentar, o sistema poderá entrar em contenção crônica de CPU.",
                    suggested_action="Monitore a evolução do processamento para confirmar se decorre de trabalho esperado do usuário.",
                    is_reversible=True,
                    target_route="overview",
                )

        # Caso tenha menos de 10 amostras (amostragem inicial)
        elif current_pct >= 85.0:
            return DiagnosticFinding(
                category="Processador (CPU)",
                level=FindingLevel.WARNING,
                title="Pico Elevado de CPU em Observação",
                evidence=f"Carga instantânea em {current_pct:.1f}%. Coletando amostras para confirmar se há persistência temporal.",
                technical_explanation="O processador registrou um pico de demanda que pode ser transitório (ex.: carregamento de software ou compilação pontual).",
                probable_impact="Possível breve oscilação de resposta durante o carregamento de novas instruções.",
                risk="Baixo caso seja transitório; torna-se crítico apenas se mantido continuamente.",
                suggested_action="Aguarde alguns ciclos de telemetria para validação da estabilização da curva.",
                is_reversible=True,
                target_route="overview",
            )

        # Carga em parâmetros normais (ou pico transitório ignorado com segurança)
        return DiagnosticFinding(
            category="Processador (CPU)",
            level=FindingLevel.OPTIMAL,
            title="Processador em Nível Estável",
            evidence="Operando com folga térmica e de ciclos dentro dos parâmetros nominais de carga.",
            technical_explanation="As filas de espera de threads do Windows operam fluidas, com tempo ocioso suficiente em todos os núcleos lógicos.",
            probable_impact="Nenhum. Responsividade e alternância de aplicativos em velocidade nominal.",
            risk="Nenhum risco detectado para o hardware ou estabilidade do sistema.",
            suggested_action="Nenhuma intervenção necessária no momento.",
            is_reversible=True,
            target_route=None,
        )

    @staticmethod
    def _check_ram_pressure(snapshot: SystemSnapshot, ram_history: list[float]) -> DiagnosticFinding:
        """Analisa a pressão de memória RAM física e risco de paginação."""
        ram_pct = snapshot.ram.percent
        avail_gb = snapshot.ram.available_bytes / (1024**3)
        total_gb = snapshot.ram.total_bytes / (1024**3)

        count_exhaustion = sum(1 for v in ram_history[-10:] if v >= 88.0)

        if (ram_pct >= 88.0 or avail_gb < 1.5) and (count_exhaustion >= 4 or len(ram_history) < 5):
            return DiagnosticFinding(
                category="Memória (RAM)",
                level=FindingLevel.CRITICAL,
                title="Pressão Crítica de Memória RAM",
                evidence=f"Apenas {avail_gb:.2f} GB disponíveis de {total_gb:.1f} GB ({ram_pct:.1f}% em uso contínuo).",
                technical_explanation="A lista de páginas livres e em standby do Memory Manager do Windows está próxima do esgotamento. O subsistema recorrerá a compressão forçada de working set e despejo no disco.",
                probable_impact="Travamentos abruptos de taxa de quadros (stuttering) e lentidão intensa ao alternar entre aplicativos.",
                risk="Esgotamento da memória física, falhas em alocações de novos processos ou encerramento anômalo por falta de memória.",
                suggested_action="Feche guias de navegadores ociosas ou encerre aplicações em segundo plano que retêm heaps volumosos.",
                is_reversible=True,
                target_route="overview",
            )

        if ram_pct >= 78.0 or avail_gb < 2.5:
            return DiagnosticFinding(
                category="Memória (RAM)",
                level=FindingLevel.WARNING,
                title="Consumo Elevado de Memória RAM",
                evidence=f"{ram_pct:.1f}% da capacidade física em uso ({avail_gb:.2f} GB disponíveis).",
                technical_explanation="O working set dos processos ativos consome a maior parte da memória física, reduzindo o cache em standby reservado para arquivos de disco.",
                probable_impact="Tempo adicional para carregamento inicial de novos softwares pesados.",
                risk="Abertura de novos aplicativos simultâneos pode forçar compressão de memória.",
                suggested_action="Monitore os principais processos consumidores na lista de processos para evitar saturação.",
                is_reversible=True,
                target_route="overview",
            )

        return DiagnosticFinding(
            category="Memória (RAM)",
            level=FindingLevel.OPTIMAL,
            title="Memória RAM em Parâmetros Seguros",
            evidence=f"Margem física segura para alocação de processos e cache do Windows ({total_gb:.0f} GB instalados).",
            technical_explanation="Existe margem física suficiente tanto para a execução fluida dos processos atuais quanto para o cache de arquivos do kernel do Windows.",
            probable_impact="Nenhum. Ausência de contenção ou paginação secundária.",
            risk="Nenhum risco detectado.",
            suggested_action="Operação equilibrada sem necessidade de ajustes.",
            is_reversible=True,
            target_route=None,
        )

    @staticmethod
    def _check_swap_thrashing(snapshot: SystemSnapshot) -> DiagnosticFinding | None:
        """Verifica se há pressão combinada entre memória RAM e paginação de disco."""
        if snapshot.ram.swap_total_bytes <= 0:
            return None

        swap_pct = snapshot.ram.swap_percent
        ram_pct = snapshot.ram.percent
        swap_used_gb = snapshot.ram.swap_used_bytes / (1024**3)

        if swap_pct >= 75.0 and ram_pct >= 80.0:
            return DiagnosticFinding(
                category="Memória Virtual",
                level=FindingLevel.WARNING,
                title="Alocação Excessiva de Arquivo de Paginação (Swap)",
                evidence=f"Arquivo de paginação atingiu {swap_pct:.1f}% ({swap_used_gb:.2f} GB alocados) com RAM em {ram_pct:.1f}%.",
                technical_explanation="O Windows está transferindo blocos de memória primária para o arquivo pagefile.sys no disco para evitar pane de memória física (thrashing).",
                probable_impact="Atraso perceptível ao restaurar janelas minimizadas e aumento do tráfego de leitura/escrita no disco.",
                risk="Degradação cumulativa da responsividade do sistema durante multitarefa e desgaste adicional em SSDs.",
                suggested_action="Reinicie aplicações ativas há muito tempo ou considere expandir a memória RAM física instalada.",
                is_reversible=True,
                target_route="overview",
            )

        return None

    @staticmethod
    def _check_disk_exhaustion(snapshot: SystemSnapshot) -> list[DiagnosticFinding]:
        """Avalia partições locais com foco de emergência na unidade do sistema."""
        findings: list[DiagnosticFinding] = []

        for disk in snapshot.disks:
            free_gb = disk.free_bytes / (1024**3)
            is_system_drive = "c:" in disk.mountpoint.lower() or "c:" in disk.device.lower()

            if is_system_drive and (free_gb < 15.0 or disk.percent >= 90.0):
                findings.append(
                    DiagnosticFinding(
                        category="Armazenamento",
                        level=FindingLevel.CRITICAL,
                        title=f"Espaço Crítico na Unidade de Sistema ({disk.device})",
                        evidence=f"Restam apenas {free_gb:.1f} GB livres ({disk.percent:.1f}% ocupado) na partição principal do Windows.",
                        technical_explanation="O Windows necessita de espaço contíguo para o arquivo de paginação dinâmica, pontos de restauração (VSS) e pacotes cumulativos de atualização do Windows Update.",
                        probable_impact="Falhas silenciosas em atualizações do sistema, corrupção potencial de dumps de crash e perda de desempenho em I/O.",
                        risk="Impossibilidade de instalar correções de segurança essenciais e risco de falhas de inicialização.",
                        suggested_action="Execute a varredura na aba Limpeza Segura para remover caches de instaladores e temporários antigos.",
                        is_reversible=True,
                        target_route="cleaner",
                    )
                )
            elif free_gb < 25.0 or disk.percent >= 85.0:
                findings.append(
                    DiagnosticFinding(
                        category="Armazenamento",
                        level=FindingLevel.WARNING,
                        title=f"Espaço Reduzido na Unidade ({disk.device})",
                        evidence=f"{free_gb:.1f} GB livres ({disk.percent:.1f}% de ocupação) no ponto de montagem {disk.mountpoint}.",
                        technical_explanation="A unidade está se aproximando do limite operacional recomendado de folga de 15% para desfragmentação e alocação de blocos.",
                        probable_impact="Redução na velocidade de gravação de arquivos grandes e gravações fragmentadas.",
                        risk="Esgotamento iminente de armazenamento caso novos downloads ou softwares sejam instalados.",
                        suggested_action="Analise pastas temporárias na aba Limpeza ou mova arquivos estáticos para unidades secundárias.",
                        is_reversible=True,
                        target_route="cleaner",
                    )
                )

        return findings

    @staticmethod
    def _check_predator_process(procs: list[ProcessItem], snapshot: SystemSnapshot) -> DiagnosticFinding | None:
        """Detecta se uma aplicação individual está monopolizando excessivamente o working set."""
        if not procs or snapshot.ram.total_bytes <= 0:
            return None

        top_p = procs[0]
        p_bytes = top_p.memory_rss_bytes
        total_ram = snapshot.ram.total_bytes
        p_pct = (p_bytes / total_ram) * 100.0
        p_gb = p_bytes / (1024**3)

        if p_pct >= 25.0 or p_gb >= 4.0:
            return DiagnosticFinding(
                category="Processos",
                level=FindingLevel.WARNING,
                title=f"Processo com Grande Retenção de Memória: {top_p.name}",
                evidence=f"O processo '{top_p.name}' (PID: {top_p.pid}) retém isoladamente {p_gb:.2f} GB ({p_pct:.1f}% da RAM total instalada).",
                technical_explanation="Uma única tarefa está concentrando a maior fatia do working set físico do sistema operacional, induzindo compressão forçada nas tarefas concorrentes.",
                probable_impact="Menor quantidade de memória livre disponível para caches de leitura e para novos processos do usuário.",
                risk="Se o processo continuar expandindo o consumo, o sistema poderá entrar em saturação crítica de memória.",
                suggested_action=f"Avalie reiniciar ou fechar abas/tarefas desnecessárias no aplicativo '{top_p.name}'.",
                is_reversible=True,
                target_route="overview",
            )

        return None

    @staticmethod
    def _check_system_uptime(snapshot: SystemSnapshot) -> DiagnosticFinding | None:
        """Verifica se o computador está em operação ininterrupta por períodos excessivos."""
        uptime_days = snapshot.uptime_seconds / 86400.0
        if uptime_days >= 7.0:
            return DiagnosticFinding(
                category="Sistema Operacional",
                level=FindingLevel.INFO,
                title="Tempo de Atividade Prolongado (Uptime)",
                evidence=f"O sistema operacional está em execução contínua há {uptime_days:.1f} dias sem reinicialização a frio.",
                technical_explanation="Os pools de memória não-paginada (Non-Paged Pool) do kernel e tabelas de handles do Windows acumulam fragmentação com uptime prolongado.",
                probable_impact="Possível aumento sutil de latência em operações de socket de rede e drivers gráficos.",
                risk="Baixo a médio; atualizações de kernel do Windows podem estar aguardando reinício para serem aplicadas.",
                suggested_action="Recomenda-se reiniciar o computador na próxima oportunidade conveniente para renovar pools do kernel.",
                is_reversible=True,
                target_route=None,
            )

        return None
