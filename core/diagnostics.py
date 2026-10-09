"""Motor de Diagnóstico e Detecção de Gargalos — Sollaris Nova.

Analisa snapshots de hardware, métricas de memória e disco para
fornecer diagnósticos técnicos explicáveis sem pontuações arbitrárias.
"""

import logging
from dataclasses import dataclass
from enum import Enum

from core.hardware import SystemSnapshot

logger = logging.getLogger("sollaris_nova.diagnostics")


class FindingLevel(Enum):
    """Nível de severidade do diagnóstico técnico."""

    OPTIMAL = "optimal"
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True)
class DiagnosticFinding:
    """Representa um apontamento técnico de diagnóstico do computador."""

    category: str
    level: FindingLevel
    title: str
    description: str
    recommendation: str


class DiagnosticEngine:
    """Avaliador de saúde técnica do sistema operacional."""

    @staticmethod
    def evaluate(snapshot: SystemSnapshot) -> list[DiagnosticFinding]:
        """Gera a lista de diagnósticos para o snapshot fornecido."""
        findings: list[DiagnosticFinding] = []

        # 1. Avaliação do Processador
        cpu_pct = snapshot.cpu.total_percent
        if cpu_pct > 85.0:
            findings.append(
                DiagnosticFinding(
                    category="Processador (CPU)",
                    level=FindingLevel.CRITICAL,
                    title="Carga Elevada na CPU",
                    description=f"A CPU está operando a {cpu_pct:.1f}% de capacidade global.",
                    recommendation="Verifique na aba de Processos se há tarefas em segundo plano consumindo ciclos excessivos.",
                )
            )
        elif cpu_pct > 70.0:
            findings.append(
                DiagnosticFinding(
                    category="Processador (CPU)",
                    level=FindingLevel.WARNING,
                    title="Uso Moderadamente Alto de CPU",
                    description=f"Uso atual de {cpu_pct:.1f}%.",
                    recommendation="O sistema está sob processamento ativo. Monitorar caso a carga persista.",
                )
            )
        else:
            findings.append(
                DiagnosticFinding(
                    category="Processador (CPU)",
                    level=FindingLevel.OPTIMAL,
                    title="Processador em Nível Estável",
                    description=f"Carga global em {cpu_pct:.1f}%, dentro dos parâmetros operacionais seguros.",
                    recommendation="Nenhuma ação necessária no momento.",
                )
            )

        # 2. Avaliação de Memória RAM
        ram_pct = snapshot.ram.percent
        avail_gb = snapshot.ram.available_bytes / (1024**3)
        if ram_pct > 88.0 or avail_gb < 1.5:
            findings.append(
                DiagnosticFinding(
                    category="Memória (RAM)",
                    level=FindingLevel.CRITICAL,
                    title="Pressão Crítica de Memória",
                    description=f"Uso de {ram_pct:.1f}% ({avail_gb:.2f} GB disponíveis). O Windows pode acionar paginação pesada.",
                    recommendation="Considere fechar guias de navegadores ou aplicações pesadas em segundo plano.",
                )
            )
        elif ram_pct > 75.0 or avail_gb < 2.5:
            findings.append(
                DiagnosticFinding(
                    category="Memória (RAM)",
                    level=FindingLevel.WARNING,
                    title="Uso Elevado de Memória",
                    description=f"Uso de {ram_pct:.1f}% ({avail_gb:.2f} GB livres/cache).",
                    recommendation="Acompanhe a evolução do consumo para evitar lentidão em novos programas.",
                )
            )
        else:
            findings.append(
                DiagnosticFinding(
                    category="Memória (RAM)",
                    level=FindingLevel.OPTIMAL,
                    title="Memória RAM Suficiente",
                    description=f"{avail_gb:.2f} GB de memória disponível para novos processos do usuário.",
                    recommendation="Operação em equilíbrio térmico e de paginação.",
                )
            )

        # 3. Avaliação de Partições de Armazenamento
        for disk in snapshot.disks:
            free_gb = disk.free_bytes / (1024**3)
            if disk.percent > 90.0 or free_gb < 12.0:
                findings.append(
                    DiagnosticFinding(
                        category="Armazenamento",
                        level=FindingLevel.CRITICAL,
                        title=f"Espaço Crítico na Unidade ({disk.device})",
                        description=f"Restam apenas {free_gb:.1f} GB ({disk.percent:.1f}% ocupado).",
                        recommendation="Unidades de sistema com pouco espaço reduzem o desempenho de atualizações e paginação.",
                    )
                )
            elif disk.percent > 80.0 or free_gb < 25.0:
                findings.append(
                    DiagnosticFinding(
                        category="Armazenamento",
                        level=FindingLevel.WARNING,
                        title=f"Espaço Reduzido na Unidade ({disk.device})",
                        description=f"{free_gb:.1f} GB livres ({disk.percent:.1f}% ocupado).",
                        recommendation="Recomendável executar a limpeza de arquivos temporários na aba Limpeza.",
                    )
                )

        # 4. Avaliação de Uptime
        uptime_days = snapshot.uptime_seconds / 86400.0
        if uptime_days > 7.0:
            findings.append(
                DiagnosticFinding(
                    category="Sistema Operacional",
                    level=FindingLevel.INFO,
                    title="Tempo Contínuo Elevado (Uptime)",
                    description=f"O computador está ligado há {uptime_days:.1f} dias sem reinicialização.",
                    recommendation="Reinicializações periódicas liberam buffers de kernel e aplicam atualizações pendentes.",
                )
            )

        return findings
