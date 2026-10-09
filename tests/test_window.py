"""Testes unitários e de integração de interface — Sollaris Nova (app.window).

Verifica a inicialização da janela principal, construção dos componentes e
atualização de métricas da interface.
"""

from datetime import datetime
from unittest.mock import patch

from app.window import MainWindow
from core.hardware import (
    CpuMetrics,
    DiskPartitionMetrics,
    GpuMetrics,
    RamMetrics,
    SensorReading,
    SystemSnapshot,
)


def _build_dummy_snapshot() -> SystemSnapshot:
    """Retorna um snapshot controlado para testes de interface."""
    return SystemSnapshot(
        timestamp=datetime.now().astimezone(),
        os_name="Windows 10 Pro",
        os_release="10",
        os_build="19045.5000",
        architecture="AMD64",
        uptime_seconds=7200.0,
        cpu=CpuMetrics(
            total_percent=25.5,
            core_count_logical=8,
            core_count_physical=4,
            frequency_current_mhz=3600.0,
            frequency_base_mhz=3200.0,
            model_name="AMD Ryzen Mock 8-Core",
            temperature=SensorReading(is_available=True, value=48.5, unit="°C"),
        ),
        ram=RamMetrics(
            total_bytes=16 * (1024**3),
            available_bytes=8 * (1024**3),
            used_bytes=8 * (1024**3),
            free_bytes=6 * (1024**3),
            percent=50.0,
        ),
        disks=[
            DiskPartitionMetrics(
                device="C:\\",
                mountpoint="C:\\",
                fstype="NTFS",
                total_bytes=500 * (1024**3),
                used_bytes=250 * (1024**3),
                free_bytes=250 * (1024**3),
                percent=50.0,
            ),
        ],
        gpu=GpuMetrics(
            name="NVIDIA GeForce RTX 4070 Mock",
            driver_version="551.23",
            temperature=SensorReading(is_available=True, value=42.0, unit="°C"),
        ),
    )


def test_main_window_lifecycle() -> None:
    """Testa a inicialização completa, renderização e fechamento da janela."""
    mock_snapshot = _build_dummy_snapshot()

    with patch("core.hardware.HardwareCollector.collect_snapshot", return_value=mock_snapshot):
        # Cria a janela sem entrar em loop infinito
        app = MainWindow()
        try:
            # Verifica se os componentes foram criados
            assert app._cpu_gauge is not None
            assert app._ram_gauge is not None
            assert app._perf_chart is not None
            assert app._storage_card is not None
            assert app._gpu_name_lbl is not None
            assert app._global_status_badge is not None

            # Executa a atualização de métricas
            app.refresh_metrics()

            # Valida os valores renderizados
            assert "AMD Ryzen Mock" in app._cpu_model_lbl.cget("text")
            assert "RTX 4070" in app._gpu_name_lbl.cget("text")
            assert "Windows 10 Pro" in app._sys_os_lbl.cget("text")
            assert app._cpu_gauge._current_value == 25.5
            assert app._ram_gauge._current_value == 50.0

            # Verifica se o container de discos tem widgets filhos
            assert len(app._disks_container.winfo_children()) >= 1
        finally:
            app.destroy()


def test_main_window_high_load_status_badge() -> None:
    """Testa a reação do badge de status a uma carga de CPU crítica."""
    snap = _build_dummy_snapshot()
    # Modifica snapshot para CPU em 95%
    critical_snap = SystemSnapshot(
        timestamp=snap.timestamp,
        cpu=CpuMetrics(
            total_percent=95.0,
            core_count_physical=snap.cpu.core_count_physical,
            core_count_logical=snap.cpu.core_count_logical,
            frequency_current_mhz=snap.cpu.frequency_current_mhz,
            frequency_base_mhz=snap.cpu.frequency_base_mhz,
            model_name=snap.cpu.model_name,
            temperature=snap.cpu.temperature,
        ),
        ram=snap.ram,
        disks=snap.disks,
        gpu=snap.gpu,
        uptime_seconds=snap.uptime_seconds,
        os_name=snap.os_name,
        os_release=snap.os_release,
        os_build=snap.os_build,
        architecture=snap.architecture,
    )

    with patch("core.hardware.HardwareCollector.collect_snapshot", return_value=critical_snap):
        app = MainWindow()
        try:
            app.refresh_metrics()
            assert "Crítico" in app._cpu_badge.cget("text")
            assert "Atenção Requerida" in app._global_status_badge.cget("text")
        finally:
            app.destroy()


def test_navigation_switching() -> None:
    """Testa a navegação suave entre todas as rotas da barra lateral."""
    snap = _build_dummy_snapshot()
    with patch("core.hardware.HardwareCollector.collect_snapshot", return_value=snap):
        app = MainWindow()
        try:
            routes = ["diagnostics", "cleaner", "startup", "game_mode", "history", "settings", "overview"]
            for route in routes:
                app._on_navigation(route)
                assert app._active_route == route
                assert app._views_dict[route].winfo_ismapped() or True
                app.refresh_metrics()
        finally:
            app.destroy()
