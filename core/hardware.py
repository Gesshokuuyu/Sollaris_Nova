"""Camada de Coleta e Normalização de Hardware — Sollaris Nova.

Este módulo coleta dados autênticos de CPU, RAM, armazenamento, GPU e sensores
térmicos no Windows, fornecendo estruturas de dados tipadas e imutáveis.
Desacoplado de qualquer biblioteca de interface gráfica (100% headless).
"""

import logging
import platform
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import psutil

logger = logging.getLogger("sollaris_nova.hardware")


@dataclass(frozen=True)
class SensorReading:
    """Representa a leitura de um sensor físico com status de disponibilidade."""

    value: float | None
    unit: str = "°C"
    is_available: bool = False
    sensor_name: str | None = None


@dataclass(frozen=True)
class CpuMetrics:
    """Métricas em tempo real e informações do processador."""

    total_percent: float
    core_count_logical: int
    core_count_physical: int
    frequency_current_mhz: float | None
    frequency_base_mhz: float | None
    model_name: str
    temperature: SensorReading


@dataclass(frozen=True)
class RamMetrics:
    """Métricas da memória primária (RAM)."""

    total_bytes: int
    used_bytes: int
    available_bytes: int
    free_bytes: int
    percent: float


@dataclass(frozen=True)
class DiskPartitionMetrics:
    """Métricas de uma partição de armazenamento local."""

    device: str
    mountpoint: str
    fstype: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float


@dataclass(frozen=True)
class GpuMetrics:
    """Informações e métricas da placa de vídeo detectada."""

    name: str
    driver_version: str | None
    temperature: SensorReading


@dataclass(frozen=True)
class SystemSnapshot:
    """Snapshot consolidado do hardware e sistema operacional em um instante."""

    timestamp: datetime
    os_name: str
    os_release: str
    os_build: str
    architecture: str
    uptime_seconds: float
    cpu: CpuMetrics
    ram: RamMetrics
    disks: list[DiskPartitionMetrics]
    gpu: GpuMetrics


def format_bytes(bytes_count: int) -> str:
    """Converte contagem de bytes em string legível (GB, MB, TB) com precisão técnica."""
    if bytes_count < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(bytes_count)
    unit_index = 0
    while value >= 1024.0 and unit_index < len(units) - 1:
        value /= 1024.0
        unit_index += 1

    if unit_index >= 3:  # GB ou maior
        return f"{value:.1f} {units[unit_index]}"
    if unit_index >= 1:  # KB ou MB
        return f"{value:.0f} {units[unit_index]}"
    return f"{int(value)} {units[unit_index]}"


def format_frequency(mhz: float | None) -> str:
    """Converte frequência em MHz para representação técnica em GHz ou MHz."""
    if mhz is None or mhz <= 0:
        return "N/A"
    if mhz >= 1000.0:
        return f"{mhz / 1000.0:.2f} GHz"
    return f"{mhz:.0f} MHz"


def format_uptime(seconds: float) -> str:
    """Converte segundos de atividade em formato amigável (dias, horas, minutos)."""
    if seconds <= 0:
        return "0m"
    total_minutes = int(seconds // 60)
    hours, minutes = divmod(total_minutes, 60)
    days, hours = divmod(hours, 24)

    parts: list[str] = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


class HardwareCollector:
    """Coletor robusto de métricas do sistema e hardware."""

    def __init__(self) -> None:
        self._cpu_name_cached: str | None = None
        self._gpu_cached: tuple[str, str | None] | None = None
        # Warmup inicial do psutil para que a primeira leitura percentual seja consistente
        try:
            psutil.cpu_percent(interval=None)
        except (OSError, RuntimeError) as exc:
            logger.debug("Falha no warmup de CPU: %s", exc)

    def get_cpu_model_name(self) -> str:
        """Obtém o nome do processador via WMI ou registro do Windows com cache."""
        if self._cpu_name_cached:
            return self._cpu_name_cached

        if sys.platform == "win32":
            try:
                import wmi

                c = wmi.WMI()
                for proc in c.Win32_Processor():
                    name = str(proc.Name).strip()
                    if name:
                        self._cpu_name_cached = name
                        return name
            except Exception as exc:  # noqa: BLE001
                # Exceções WMI/COM podem herdar de camadas dinâmicas OLE
                logger.debug("Não foi possível consultar CPU via WMI: %s", exc)

        # Fallback padrão
        fallback = platform.processor() or "Processador Desconhecido"
        self._cpu_name_cached = fallback
        return fallback

    def get_cpu_metrics(self) -> CpuMetrics:
        """Coleta métricas de CPU, núcleos e frequência em tempo real."""
        percent = float(psutil.cpu_percent(interval=None))
        logical_cores = psutil.cpu_count(logical=True) or 1
        physical_cores = psutil.cpu_count(logical=False) or logical_cores

        freq_current: float | None = None
        freq_base: float | None = None
        try:
            freq_info = psutil.cpu_freq()
            if freq_info:
                freq_current = freq_info.current if freq_info.current > 0 else None
                freq_base = freq_info.max if freq_info.max > 0 else None
        except (OSError, RuntimeError, AttributeError) as exc:
            logger.debug("Não foi possível obter frequência da CPU: %s", exc)

        temp = self.get_cpu_temperature()
        model_name = self.get_cpu_model_name()

        return CpuMetrics(
            total_percent=percent,
            core_count_logical=logical_cores,
            core_count_physical=physical_cores,
            frequency_current_mhz=freq_current,
            frequency_base_mhz=freq_base,
            model_name=model_name,
            temperature=temp,
        )

    def get_ram_metrics(self) -> RamMetrics:
        """Coleta métricas detalhadas da memória RAM física."""
        mem = psutil.virtual_memory()
        return RamMetrics(
            total_bytes=mem.total,
            used_bytes=mem.used,
            available_bytes=mem.available,
            free_bytes=mem.free,
            percent=float(mem.percent),
        )

    def get_disk_metrics(self) -> list[DiskPartitionMetrics]:
        """Coleta ocupação de todas as partições montadas e acessíveis."""
        disks: list[DiskPartitionMetrics] = []
        partitions = psutil.disk_partitions(all=False)

        for part in partitions:
            # Ignora partições de CD-ROM ou vazias sem ponto de montagem
            if not part.mountpoint:
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append(
                    DiskPartitionMetrics(
                        device=part.device,
                        mountpoint=part.mountpoint,
                        fstype=part.fstype or "Local",
                        total_bytes=usage.total,
                        used_bytes=usage.used,
                        free_bytes=usage.free,
                        percent=float(usage.percent),
                    )
                )
            except (PermissionError, OSError) as exc:
                # Dispositivo não pronto (ex: leitor de cartão ou drive óptico vazio)
                logger.debug("Partição ignorada (%s): %s", part.mountpoint, exc)
                continue

        return disks

    def get_cpu_temperature(self) -> SensorReading:
        """Coleta a temperatura da CPU quando houver sensor exposto pelo ACPI/WMI."""
        if sys.platform != "win32":
            return SensorReading(value=None, unit="°C", is_available=False)

        try:
            import wmi

            c = wmi.WMI(namespace="root/wmi")
            thermal_zones = c.MSAcpi_ThermalZoneTemperature()
            for zone in thermal_zones:
                raw_temp = getattr(zone, "CurrentTemperature", None)
                if raw_temp is not None and raw_temp > 0:
                    # Kelvin em décimos de Kelvin: (K / 10) - 273.15
                    celsius = (float(raw_temp) / 10.0) - 273.15
                    if 0.0 <= celsius <= 125.0:
                        return SensorReading(
                            value=round(celsius, 1),
                            unit="°C",
                            is_available=True,
                            sensor_name="ACPI ThermalZone",
                        )
        except Exception as exc:  # noqa: BLE001
            # Sensor indisponível ou acesso restrito a nível administrativo
            logger.debug("Sensor de temperatura da CPU indisponível: %s", exc)

        return SensorReading(
            value=None,
            unit="°C",
            is_available=False,
            sensor_name=None,
        )

    def get_gpu_metrics(self) -> GpuMetrics:
        """Coleta adaptador de vídeo detectado e temperatura de GPU."""
        gpu_name = "Adaptador de Vídeo Padrão"
        driver_version: str | None = None

        if self._gpu_cached:
            gpu_name, driver_version = self._gpu_cached
        elif sys.platform == "win32":
            try:
                import wmi

                c = wmi.WMI()
                for gpu in c.Win32_VideoController():
                    name = getattr(gpu, "Name", None)
                    if name:
                        gpu_name = str(name).strip()
                        driver = getattr(gpu, "DriverVersion", None)
                        driver_version = str(driver).strip() if driver else None
                        self._gpu_cached = (gpu_name, driver_version)
                        break
            except Exception as exc:  # noqa: BLE001
                logger.debug("Não foi possível consultar GPU via WMI: %s", exc)

        # Temperatura da GPU (atualmente opcional/indisponível sem driver proprietário)
        gpu_temp = SensorReading(
            value=None,
            unit="°C",
            is_available=False,
            sensor_name=None,
        )

        return GpuMetrics(
            name=gpu_name,
            driver_version=driver_version,
            temperature=gpu_temp,
        )

    def collect_snapshot(self) -> SystemSnapshot:
        """Gera um snapshot atômico com todas as medições de hardware e sistema."""
        cpu = self.get_cpu_metrics()
        ram = self.get_ram_metrics()
        disks = self.get_disk_metrics()
        gpu = self.get_gpu_metrics()

        boot_time = psutil.boot_time()
        uptime_seconds = max(0.0, time.time() - boot_time)

        return SystemSnapshot(
            timestamp=datetime.now(timezone.utc),
            os_name=f"{platform.system()} {platform.release()}",
            os_release=platform.release(),
            os_build=platform.version(),
            architecture=platform.machine(),
            uptime_seconds=uptime_seconds,
            cpu=cpu,
            ram=ram,
            disks=disks,
            gpu=gpu,
        )
