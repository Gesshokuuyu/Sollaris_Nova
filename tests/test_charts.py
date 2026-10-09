"""Testes unitários do componente PerformanceChart e histórico de 60s — Sollaris Nova."""

from collections import deque

import customtkinter as ctk

from app.components.performance_chart import PerformanceChart
from core.monitor import MonitorService


def test_performance_chart_initialization() -> None:
    """Verifica a inicialização da figura Matplotlib e eixos integrados."""
    root = ctk.CTk()
    try:
        chart = PerformanceChart(root)
        assert chart._mode == "both"
        assert chart._fig is not None
        assert chart._ax is not None
        assert chart._line_cpu is not None
        assert chart._line_ram is not None
    finally:
        root.destroy()


def test_performance_chart_mode_switching() -> None:
    """Testa a comutação entre modos Ambos, CPU e RAM."""
    root = ctk.CTk()
    try:
        chart = PerformanceChart(root)

        # Modo CPU isolado
        chart._set_mode("cpu")
        assert chart._mode == "cpu"
        assert chart._line_cpu.get_visible() is True
        assert chart._line_ram.get_visible() is False

        # Modo RAM isolado
        chart._set_mode("ram")
        assert chart._mode == "ram"
        assert chart._line_cpu.get_visible() is False
        assert chart._line_ram.get_visible() is True

        # Modo Ambos
        chart._set_mode("both")
        assert chart._mode == "both"
        assert chart._line_cpu.get_visible() is True
        assert chart._line_ram.get_visible() is True
    finally:
        root.destroy()


def test_performance_chart_data_updating() -> None:
    """Valida a atualização dos vetores de curvas com diferentes tamanhos de amostra."""
    root = ctk.CTk()
    try:
        chart = PerformanceChart(root)

        # Atualização com dados vazios (não deve quebrar)
        chart.update_chart([], [])

        # Atualização parcial (10 pontos)
        cpu_samples = [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0]
        ram_samples = [40.0] * 10
        chart.update_chart(cpu_samples, ram_samples)
        assert len(chart._line_cpu.get_xdata()) == 10
        assert len(chart._line_ram.get_ydata()) == 10

        # Atualização cheia (60 pontos)
        full_cpu = [float(i) for i in range(60)]
        full_ram = [50.0] * 60
        chart.update_chart(full_cpu, full_ram)
        assert len(chart._line_cpu.get_xdata()) == 60
        assert "59.0%" in chart._legend_lbl.cget("text")
    finally:
        root.destroy()


def test_monitor_history_and_statistics() -> None:
    """Valida o cálculo do buffer circular de 60 segundos e das estatísticas da janela."""
    monitor = MonitorService(interval_seconds=1.0)

    # Força preenchimento controlado do buffer
    with monitor._lock:
        monitor.cpu_history = deque([10.0, 20.0, 30.0, 40.0, 50.0], maxlen=60)
        monitor.ram_history = deque([50.0, 50.0, 60.0, 60.0, 55.0], maxlen=60)

    cpu_hist, ram_hist = monitor.get_history_snapshot()
    assert len(cpu_hist) == 5
    assert len(ram_hist) == 5
    assert cpu_hist[-1] == 50.0

    stats = monitor.get_window_statistics()
    assert stats["cpu_avg"] == 30.0
    assert stats["cpu_max"] == 50.0
    assert stats["cpu_min"] == 10.0
    assert stats["ram_avg"] == 55.0
    assert stats["ram_max"] == 60.0
    assert stats["ram_min"] == 50.0
    assert stats["samples_count"] == 5.0
