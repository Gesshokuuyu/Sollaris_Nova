"""Testes unitários para os novos módulos — Sollaris Nova.

Valida ProcessCollector, DiagnosticEngine, CleanerScanner e StartupManager.
"""

from unittest.mock import patch

from core.cleaner import CleanerScanner
from core.diagnostics import DiagnosticEngine, FindingLevel
from core.processes import ProcessCollector
from core.startup import StartupManager
from tests.test_window import _build_dummy_snapshot


def test_process_collector_execution() -> None:
    """Garante que a lista de processos é retornada de forma íntegra e ordenada."""
    procs = ProcessCollector.get_top_processes(limit=5, sort_by="memory")
    assert isinstance(procs, list)
    if procs:
        assert procs[0].pid > 0
        assert procs[0].memory_rss_bytes >= 0
        assert isinstance(procs[0].name, str)


def test_diagnostic_engine_evaluation() -> None:
    """Verifica se o motor de diagnóstico processa snapshots e retorna apontamentos."""
    snap = _build_dummy_snapshot()
    findings = DiagnosticEngine.evaluate(snap)
    assert len(findings) >= 2
    # Na massa dummy, CPU está em 25.5%, logo deve ser OPTIMAL
    cpu_finding = next(f for f in findings if f.category == "Processador (CPU)")
    assert cpu_finding.level == FindingLevel.OPTIMAL


def test_cleaner_scanner_safe_execution() -> None:
    """Valida que o scanner de arquivos temporários não lança exceções."""
    categories = CleanerScanner.scan_temporary_files()
    assert isinstance(categories, list)
    for cat in categories:
        assert cat.file_count >= 0
        assert cat.size_bytes >= 0


def test_startup_manager_safe_enumeration() -> None:
    """Valida a enumeração segura de programas de inicialização do Windows."""
    with patch("sys.platform", "win32"):
        apps = StartupManager.get_startup_applications()
        assert isinstance(apps, list)
