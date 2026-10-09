"""Testes automatizados da camada de hardware (core/hardware.py)."""

from datetime import datetime
from unittest.mock import patch

import pytest

from core.hardware import (
    CpuMetrics,
    DiskPartitionMetrics,
    GpuMetrics,
    HardwareCollector,
    RamMetrics,
    SensorReading,
    SystemSnapshot,
    format_bytes,
    format_frequency,
    format_uptime,
)


def test_format_bytes_utility() -> None:
    """Valida a conversão correta de bytes em unidades legíveis."""
    assert format_bytes(0) == "0 B"
    assert format_bytes(512) == "512 B"
    assert format_bytes(1024) == "1 KB"
    assert format_bytes(1024 * 1024) == "1 MB"
    assert format_bytes(1024 * 1024 * 1024) == "1.0 GB"
    assert format_bytes(int(1.5 * 1024 * 1024 * 1024)) == "1.5 GB"
    assert format_bytes(int(2.5 * 1024 * 1024 * 1024 * 1024)) == "2.5 TB"
    assert format_bytes(-100) == "0 B"


def test_format_frequency_utility() -> None:
    """Valida a conversão de frequências de MHz para GHz e MHz."""
    assert format_frequency(None) == "N/A"
    assert format_frequency(0) == "N/A"
    assert format_frequency(-50) == "N/A"
    assert format_frequency(800.0) == "800 MHz"
    assert format_frequency(2400.0) == "2.40 GHz"
    assert format_frequency(4250.0) == "4.25 GHz"


def test_format_uptime_utility() -> None:
    """Valida a formatação de tempo de atividade em dias, horas e minutos."""
    assert format_uptime(0) == "0m"
    assert format_uptime(45) == "0m"
    assert format_uptime(125) == "2m"
    assert format_uptime(3600) == "1h 0m"
    assert format_uptime(3665) == "1h 1m"
    assert format_uptime(86400 + 7200 + 180) == "1d 2h 3m"


def test_dataclasses_immutability() -> None:
    """Garante que as dataclasses são imutáveis (frozen=True)."""
    sensor = SensorReading(value=45.0, unit="°C", is_available=True)
    with pytest.raises(AttributeError):
        # Tentativa de mutação deve falhar
        sensor.value = 50.0  # type: ignore[misc]

    ram = RamMetrics(
        total_bytes=16000000000,
        used_bytes=8000000000,
        available_bytes=8000000000,
        free_bytes=8000000000,
        percent=50.0,
    )
    with pytest.raises(AttributeError):
        ram.percent = 60.0  # type: ignore[misc]


def test_cpu_metrics_live() -> None:
    """Valida se o coletor obtém métricas de CPU dentro de limites plausíveis."""
    collector = HardwareCollector()
    cpu = collector.get_cpu_metrics()

    assert isinstance(cpu, CpuMetrics)
    assert 0.0 <= cpu.total_percent <= 100.0
    assert cpu.core_count_logical >= 1
    assert cpu.core_count_physical >= 1
    assert len(cpu.model_name) > 0
    assert isinstance(cpu.temperature, SensorReading)


def test_ram_metrics_live() -> None:
    """Valida se as métricas de RAM são autênticas e coerentes."""
    collector = HardwareCollector()
    ram = collector.get_ram_metrics()

    assert isinstance(ram, RamMetrics)
    assert ram.total_bytes > 0
    assert ram.used_bytes > 0
    assert ram.available_bytes > 0
    assert 0.0 <= ram.percent <= 100.0
    # O total deve ser maior que o que está em uso
    assert ram.total_bytes >= ram.used_bytes


def test_disk_metrics_live() -> None:
    """Valida se o coletor detecta pelo menos a unidade principal do sistema."""
    collector = HardwareCollector()
    disks = collector.get_disk_metrics()

    assert isinstance(disks, list)
    assert len(disks) >= 1  # Pelo menos drive C:\ deve existir no Windows

    for d in disks:
        assert isinstance(d, DiskPartitionMetrics)
        assert len(d.mountpoint) > 0
        assert d.total_bytes > 0
        assert 0.0 <= d.percent <= 100.0
        assert d.free_bytes <= d.total_bytes


def test_temperature_fallback_on_wmi_error() -> None:
    """Garante que falhas ou permissões no WMI retornam is_available=False sem crash."""
    collector = HardwareCollector()

    with (
        patch("sys.platform", "win32"),
        patch("wmi.WMI", side_effect=RuntimeError("Access Denied or Not Supported")),
    ):
        temp = collector.get_cpu_temperature()
        assert isinstance(temp, SensorReading)
        assert temp.is_available is False
        assert temp.value is None


def test_collect_snapshot_integration() -> None:
    """Valida a integração completa de geração de snapshot."""
    collector = HardwareCollector()
    snapshot = collector.collect_snapshot()

    assert isinstance(snapshot, SystemSnapshot)
    assert isinstance(snapshot.timestamp, datetime)
    assert len(snapshot.os_name) > 0
    assert snapshot.uptime_seconds >= 0.0
    assert isinstance(snapshot.cpu, CpuMetrics)
    assert isinstance(snapshot.ram, RamMetrics)
    assert isinstance(snapshot.gpu, GpuMetrics)
    assert len(snapshot.disks) >= 1
