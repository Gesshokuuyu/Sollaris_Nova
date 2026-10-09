"""Testes unitários para o Motor de Diagnóstico Explicável e Gravador de Sessão.

Valida as 7 dimensões explicáveis, eliminação de falsos positivos por persistência temporal,
detecção de processos predadores, esgotamento de disco e ciclo de vida do SessionRecorder.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from core.diagnostics import DiagnosticEngine, DiagnosticFinding, FindingLevel
from core.hardware import (
    CpuMetrics,
    DiskPartitionMetrics,
    GpuMetrics,
    RamMetrics,
    SensorReading,
    SystemSnapshot,
)
from core.processes import ProcessItem
from core.recorder import SessionRecorder


def _create_snapshot(
    cpu_percent: float = 20.0,
    ram_percent: float = 40.0,
    ram_available_bytes: int = 8 * 1024**3,
    swap_percent: float = 10.0,
    c_drive_free_bytes: int = 100 * 1024**3,
    uptime_seconds: float = 3600.0,
) -> SystemSnapshot:
    """Cria um snapshot customizado para testes sintéticos determinísticos."""
    return SystemSnapshot(
        timestamp=datetime.now().astimezone(),
        os_name="Windows 11 Pro",
        os_release="11",
        os_build="22631.3000",
        architecture="AMD64",
        uptime_seconds=uptime_seconds,
        cpu=CpuMetrics(
            total_percent=cpu_percent,
            core_count_logical=8,
            core_count_physical=4,
            frequency_current_mhz=3200.0,
            frequency_base_mhz=3200.0,
            model_name="Test CPU Multi-Core",
            temperature=SensorReading(is_available=True, value=45.0, unit="°C"),
            per_cpu_percent=(cpu_percent,) * 8,
            process_count=120,
            thread_count=1800,
        ),
        ram=RamMetrics(
            total_bytes=16 * 1024**3,
            used_bytes=int(16 * 1024**3 * (ram_percent / 100.0)),
            available_bytes=ram_available_bytes,
            free_bytes=ram_available_bytes,
            percent=ram_percent,
            swap_total_bytes=4 * 1024**3,
            swap_used_bytes=int(4 * 1024**3 * (swap_percent / 100.0)),
            swap_percent=swap_percent,
        ),
        disks=[
            DiskPartitionMetrics(
                device="C:\\",
                mountpoint="C:\\",
                fstype="NTFS",
                total_bytes=256 * 1024**3,
                used_bytes=256 * 1024**3 - c_drive_free_bytes,
                free_bytes=c_drive_free_bytes,
                percent=100.0 - (c_drive_free_bytes / (256 * 1024**3) * 100.0),
            )
        ],
        gpu=GpuMetrics(
            name="Test GPU",
            driver_version="550.00",
            temperature=SensorReading(is_available=True, value=50.0, unit="°C"),
        ),
    )


def test_diagnostic_finding_7_dimensions_integrity() -> None:
    """Valida se DiagnosticFinding possui as 7 dimensões explicáveis e compatibilidade retroativa."""
    finding = DiagnosticFinding(
        category="Armazenamento",
        level=FindingLevel.WARNING,
        title="Espaço Reduzido",
        evidence="12 GB livres no volume C:",
        technical_explanation="O espaço livre está abaixo do limiar de segurança.",
        probable_impact="Falhas em atualizações do Windows Update.",
        risk="Baixo — limpeza não remove arquivos de usuário.",
        suggested_action="Executar limpeza segura.",
        is_reversible=True,
        target_route="cleaner",
    )

    assert finding.category == "Armazenamento"
    assert finding.level == FindingLevel.WARNING
    assert finding.title == "Espaço Reduzido"
    assert finding.evidence == "12 GB livres no volume C:"
    assert finding.technical_explanation == "O espaço livre está abaixo do limiar de segurança."
    assert finding.probable_impact == "Falhas em atualizações do Windows Update."
    assert finding.risk == "Baixo — limpeza não remove arquivos de usuário."
    assert finding.suggested_action == "Executar limpeza segura."
    assert finding.is_reversible is True
    assert finding.target_route == "cleaner"

    # Aliases de compatibilidade retroativa
    assert finding.description == finding.technical_explanation
    assert finding.recommendation == finding.suggested_action


def test_cpu_transient_spike_ignored() -> None:
    """Garante que picos transitórios (<5s) em janela com histórico sejam ignorados e avaliados como OPTIMAL."""
    snap = _create_snapshot(cpu_percent=95.0)
    # 12 amostras normais (~20%) seguidas de 3 amostras altas transitórias
    cpu_history = [20.0] * 12 + [95.0, 92.0, 96.0]

    findings = DiagnosticEngine.evaluate_with_history(
        snapshot=snap,
        cpu_history=cpu_history,
    )

    cpu_finding = next(f for f in findings if f.category == "Processador (CPU)")
    assert cpu_finding.level == FindingLevel.OPTIMAL
    assert "estável" in cpu_finding.title.lower() or "dentro dos parâmetros" in cpu_finding.evidence.lower()


def test_cpu_sustained_saturation_triggered() -> None:
    """Garante que saturação sustentada (>=10 amostras >=85%) dispare nível CRITICAL."""
    snap = _create_snapshot(cpu_percent=94.0)
    # 12 amostras consecutivas >= 85%
    cpu_history = [88.0, 92.0, 95.0, 90.0, 89.0, 94.0, 91.0, 93.0, 95.0, 96.0, 88.0, 94.0]

    findings = DiagnosticEngine.evaluate_with_history(
        snapshot=snap,
        cpu_history=cpu_history,
    )

    cpu_finding = next(f for f in findings if f.category == "Processador (CPU)")
    assert cpu_finding.level == FindingLevel.CRITICAL
    assert "Saturação Sustentada" in cpu_finding.title
    assert "12 de 12 amostras" in cpu_finding.evidence
    assert cpu_finding.target_route == "overview"


def test_ram_pressure_detection() -> None:
    """Verifica detecção de pressão moderada e severa de RAM com persistência temporal."""
    # Pressão moderada (82%, < 2GB livre)
    snap_warn = _create_snapshot(ram_percent=82.0, ram_available_bytes=1500 * 1024**2)
    ram_hist_warn = [81.0, 82.0, 82.5, 83.0, 82.0, 81.5, 82.0, 82.0]
    findings_warn = DiagnosticEngine.evaluate_with_history(snapshot=snap_warn, ram_history=ram_hist_warn)
    ram_finding_warn = next(f for f in findings_warn if f.category == "Memória (RAM)")
    assert ram_finding_warn.level == FindingLevel.WARNING

    # Pressão crítica sustentada (92%, < 800MB livre, com persistência)
    snap_crit = _create_snapshot(ram_percent=92.0, ram_available_bytes=600 * 1024**2)
    ram_hist_crit = [90.0, 91.0, 92.0, 91.5, 92.5, 93.0, 92.0, 91.0]
    findings_crit = DiagnosticEngine.evaluate_with_history(snapshot=snap_crit, ram_history=ram_hist_crit)
    ram_finding_crit = next(f for f in findings_crit if f.category == "Memória (RAM)")
    assert ram_finding_crit.level == FindingLevel.CRITICAL


def test_swap_thrashing_detection() -> None:
    """Verifica detecção de esgotamento de arquivo de paginação (Swap Thrashing)."""
    snap = _create_snapshot(ram_percent=88.0, swap_percent=85.0)
    findings = DiagnosticEngine.evaluate(snap)

    swap_finding = next((f for f in findings if f.category == "Memória Virtual"), None)
    assert swap_finding is not None
    assert swap_finding.level == FindingLevel.WARNING
    assert "Paginação" in swap_finding.title or "Swap" in swap_finding.title


def test_disk_exhaustion_detection() -> None:
    """Verifica detecção de espaço livre crítico no drive do sistema (C:)."""
    snap = _create_snapshot(c_drive_free_bytes=4 * 1024**3)  # Apenas 4 GB livres
    findings = DiagnosticEngine.evaluate(snap)

    disk_finding = next((f for f in findings if f.category == "Armazenamento" and "C:" in f.title), None)
    assert disk_finding is not None
    assert disk_finding.level == FindingLevel.CRITICAL
    assert disk_finding.target_route == "cleaner"


def test_predator_process_detection() -> None:
    """Verifica detecção de processos com consumo desproporcional de memória."""
    snap = _create_snapshot(cpu_percent=50.0)
    procs = [
        ProcessItem(
            pid=1234,
            name="heavy_render.exe",
            memory_rss_bytes=6 * 1024**3,  # 6 GB de 16 GB (~37.5%)
            memory_percent=37.5,
            cpu_percent=15.0,
            status="running",
        ),
        ProcessItem(
            pid=5678,
            name="system_idle.exe",
            memory_rss_bytes=100 * 1024**2,
            memory_percent=0.6,
            cpu_percent=1.0,
            status="running",
        ),
    ]

    findings = DiagnosticEngine.evaluate_with_history(snapshot=snap, processes=procs)
    predator_finding = next((f for f in findings if f.category == "Processos"), None)
    assert predator_finding is not None
    assert predator_finding.level == FindingLevel.WARNING
    assert "heavy_render.exe" in predator_finding.evidence
    assert predator_finding.target_route == "overview"


def test_session_recorder_lifecycle(tmp_path: Path) -> None:
    """Valida o ciclo completo do Gravador de Sessão (Start -> Record -> Stop)."""
    recorder = SessionRecorder(reports_dir=tmp_path)
    assert not recorder.is_recording
    assert recorder.elapsed_seconds == 0
    assert recorder.sample_count == 0

    snap = _create_snapshot(cpu_percent=45.0, ram_percent=60.0)
    procs = [
        ProcessItem(
            pid=100,
            name="test_worker.exe",
            memory_rss_bytes=512 * 1024**2,
            memory_percent=3.2,
            cpu_percent=25.0,
            status="running",
        )
    ]
    findings = DiagnosticEngine.evaluate(snap)

    # Inicia sessão
    log_file = recorder.start_session(snap)
    assert recorder.is_recording
    assert log_file.exists()
    assert log_file.name.startswith("relatorio_sessao_")

    # Grava 3 ticks
    for _ in range(3):
        recorder.record_tick(snap, procs, findings)
        time.sleep(0.02)

    assert recorder.sample_count == 3
    assert recorder.elapsed_seconds >= 0

    # Finaliza sessão
    summary = recorder.stop_session()
    assert not recorder.is_recording
    assert summary["sample_count"] == 3
    assert summary["cpu_avg"] == 45.0
    assert summary["ram_avg"] == 60.0
    assert Path(summary["file_path"]).exists()

    # Valida conteúdo do arquivo em disco
    content = log_file.read_text(encoding="utf-8")
    assert "RELATÓRIO TÉCNICO DE TELEMETRIA" in content
    assert "SUMÁRIO EXECUTIVO DA SESSÃO GRAVADA" in content
    assert "Total de Amostras Colhidas:  3" in content
    assert "test_worker.exe" in content
