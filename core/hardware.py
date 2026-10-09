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
    per_cpu_percent: tuple[float, ...] = ()
    process_count: int = 0
    thread_count: int = 0


@dataclass(frozen=True)
class RamMetrics:
    """Métricas da memória primária (RAM)."""

    total_bytes: int
    used_bytes: int
    available_bytes: int
    free_bytes: int
    percent: float
    swap_total_bytes: int = 0
    swap_used_bytes: int = 0
    swap_percent: float = 0.0


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
    adapter_ram_bytes: int | None = None
    resolution: str | None = None
    refresh_rate_hz: int | None = None


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
    """Coletor robusto e de altíssimo desempenho de métricas de hardware."""

    def __init__(self) -> None:
        self._cpu_name_cached: str | None = None
        self._gpu_cached: tuple[str, str | None, int | None, str | None, int | None] | None = None
        self._thermal_zone_available: bool | None = None
        self._cached_partitions: list[tuple[str, str, str]] | None = None
        self._last_partitions_check = 0.0

        # Warmup inicial do psutil para que a primeira leitura percentual seja consistente
        try:
            psutil.cpu_percent(interval=None)
        except (OSError, RuntimeError) as exc:
            logger.debug("Falha no warmup de CPU: %s", exc)

    def get_cpu_model_name(self) -> str:
        """Obtém o nome do processador via Registro do Windows (0.03ms) ou fallback."""
        if self._cpu_name_cached:
            return self._cpu_name_cached

        if sys.platform == "win32":
            try:
                import winreg

                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                    name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                    if name and str(name).strip():
                        clean_name = str(name).strip()
                        self._cpu_name_cached = clean_name
                        return clean_name
            except OSError as exc:
                logger.debug("Consulta ao registro CentralProcessor falhou: %s", exc)

        fallback = platform.processor() or "Processador Desconhecido"
        self._cpu_name_cached = fallback
        return fallback

    def get_cpu_metrics(self) -> CpuMetrics:
        """Coleta métricas de CPU, núcleos e frequência em tempo real."""
        percent = float(psutil.cpu_percent(interval=None))
        logical_cores = psutil.cpu_count(logical=True) or 1
        physical_cores = psutil.cpu_count(logical=False) or logical_cores

        per_cpu: tuple[float, ...] = ()
        try:
            per_cpu_raw = psutil.cpu_percent(interval=None, percpu=True)
            per_cpu = tuple(float(x) for x in per_cpu_raw)
        except (OSError, RuntimeError):
            per_cpu = ()

        process_count = 0
        try:
            process_count = len(psutil.pids())
        except (OSError, RuntimeError):
            pass

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
            per_cpu_percent=per_cpu,
            process_count=process_count,
        )

    def get_ram_metrics(self) -> RamMetrics:
        """Coleta métricas detalhadas da memória RAM física e virtual."""
        mem = psutil.virtual_memory()

        swap_total = 0
        swap_used = 0
        swap_pct = 0.0

        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", wintypes.DWORD),
                        ("dwMemoryLoad", wintypes.DWORD),
                        ("ullTotalPhys", ctypes.c_uint64),
                        ("ullAvailPhys", ctypes.c_uint64),
                        ("ullTotalPageFile", ctypes.c_uint64),
                        ("ullAvailPageFile", ctypes.c_uint64),
                        ("ullTotalVirtual", ctypes.c_uint64),
                        ("ullAvailVirtual", ctypes.c_uint64),
                        ("ullAvailExtendedVirtual", ctypes.c_uint64),
                    ]

                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                    swap_total = int(stat.ullTotalPageFile)
                    swap_used = max(0, swap_total - int(stat.ullAvailPageFile))
                    swap_pct = round((swap_used / swap_total) * 100.0, 1) if swap_total > 0 else 0.0
            except Exception as exc:  # noqa: BLE001
                logger.debug("Falha em GlobalMemoryStatusEx: %s", exc)

        if swap_total == 0:
            try:
                swap = psutil.swap_memory()
                swap_total = swap.total
                swap_used = swap.used
                swap_pct = float(swap.percent)
            except (OSError, RuntimeError):
                pass

        return RamMetrics(
            total_bytes=mem.total,
            used_bytes=mem.used,
            available_bytes=mem.available,
            free_bytes=mem.free,
            percent=float(mem.percent),
            swap_total_bytes=swap_total,
            swap_used_bytes=swap_used,
            swap_percent=swap_pct,
        )

    def get_disk_metrics(self) -> list[DiskPartitionMetrics]:
        """Coleta ocupação de todas as partições montadas e acessíveis."""
        if sys.platform == "win32":
            try:
                return self._get_disk_metrics_win32()
            except Exception as exc:  # noqa: BLE001
                logger.debug("Fallback para psutil após exceção win32 de disco: %s", exc)

        now = time.time()
        if self._cached_partitions is None or (now - self._last_partitions_check) > 30.0:
            cached: list[tuple[str, str, str]] = []
            try:
                for part in psutil.disk_partitions(all=False):
                    if part.mountpoint and part.fstype and "cdrom" not in part.opts:
                        cached.append((part.device, part.mountpoint, part.fstype))
            except (OSError, RuntimeError) as exc:
                logger.debug("Falha ao enumerar partições de disco: %s", exc)
            self._cached_partitions = cached
            self._last_partitions_check = now

        disks: list[DiskPartitionMetrics] = []
        for dev, mount, fstype in self._cached_partitions:
            try:
                usage = psutil.disk_usage(mount)
                disks.append(
                    DiskPartitionMetrics(
                        device=dev,
                        mountpoint=mount,
                        fstype=fstype,
                        total_bytes=usage.total,
                        used_bytes=usage.used,
                        free_bytes=usage.free,
                        percent=float(usage.percent),
                    )
                )
            except (PermissionError, OSError):
                continue

        return disks

    def _get_disk_metrics_win32(self) -> list[DiskPartitionMetrics]:
        """Coleta partições via Win32 API direta em 1ms sem bloquear unidades vazias."""
        import ctypes

        kernel32 = ctypes.windll.kernel32
        # SEM_FAILCRITICALERRORS (0x0001) | SEM_NOOPENFILEERRORBOX (0x8000)
        old_mode = kernel32.SetErrorMode(0x0001 | 0x8000)

        buf = ctypes.create_unicode_buffer(512)
        n = kernel32.GetLogicalDriveStringsW(512, buf)
        drive_list = [d for d in buf[:n].split("\x00") if d]

        disks: list[DiskPartitionMetrics] = []
        try:
            for drive in drive_list:
                dtype = kernel32.GetDriveTypeW(drive)
                if dtype in (3, 2):  # DRIVE_FIXED, DRIVE_REMOVABLE
                    free_bytes = ctypes.c_ulonglong(0)
                    total_bytes = ctypes.c_ulonglong(0)
                    total_free = ctypes.c_ulonglong(0)
                    ok = kernel32.GetDiskFreeSpaceExW(
                        drive,
                        ctypes.byref(free_bytes),
                        ctypes.byref(total_bytes),
                        ctypes.byref(total_free),
                    )
                    if ok and total_bytes.value > 0:
                        vol_name = ctypes.create_unicode_buffer(261)
                        fs_name = ctypes.create_unicode_buffer(261)
                        kernel32.GetVolumeInformationW(
                            drive,
                            vol_name,
                            261,
                            None,
                            None,
                            None,
                            fs_name,
                            261,
                        )
                        used = total_bytes.value - free_bytes.value
                        pct = round((used / total_bytes.value) * 100.0, 1)
                        disks.append(
                            DiskPartitionMetrics(
                                device=drive,
                                mountpoint=drive,
                                fstype=fs_name.value or "NTFS",
                                total_bytes=total_bytes.value,
                                used_bytes=used,
                                free_bytes=free_bytes.value,
                                percent=pct,
                            )
                        )
        finally:
            kernel32.SetErrorMode(old_mode)

        if not disks:
            raise RuntimeError("Nenhuma partição encontrada via Win32")
        return disks

    def get_cpu_temperature(self) -> SensorReading:
        """Coleta a temperatura da CPU quando houver sensor exposto pelo ACPI/WMI."""
        if sys.platform != "win32" or self._thermal_zone_available is False:
            return SensorReading(value=None, unit="°C", is_available=False, sensor_name=None)

        try:
            import wmi

            c = wmi.WMI(namespace="root/wmi")
            thermal_zones = c.MSAcpi_ThermalZoneTemperature()
            for zone in thermal_zones:
                raw_temp = getattr(zone, "CurrentTemperature", None)
                if raw_temp is not None and raw_temp > 0:
                    celsius = (float(raw_temp) / 10.0) - 273.15
                    if 0.0 <= celsius <= 125.0:
                        self._thermal_zone_available = True
                        return SensorReading(
                            value=round(celsius, 1),
                            unit="°C",
                            is_available=True,
                            sensor_name="ACPI ThermalZone",
                        )
            self._thermal_zone_available = False
        except Exception as exc:  # noqa: BLE001
            logger.debug("Sensor de temperatura da CPU indisponível: %s", exc)
            self._thermal_zone_available = False

        return SensorReading(
            value=None,
            unit="°C",
            is_available=False,
            sensor_name=None,
        )

    def get_gpu_metrics(self) -> GpuMetrics:
        """Coleta adaptador de vídeo detectado, resolução e taxa de atualização com alta velocidade."""
        gpu_name = "Adaptador de Vídeo Padrão"
        driver_version: str | None = None
        adapter_ram: int | None = None
        resolution: str | None = None
        refresh_rate: int | None = None

        if self._gpu_cached:
            gpu_name, driver_version, adapter_ram, resolution, refresh_rate = self._gpu_cached
        elif sys.platform == "win32":
            try:
                import winreg

                import win32api

                dev = win32api.EnumDisplayDevices(None, 0)
                if dev and dev.DeviceString:
                    gpu_name = str(dev.DeviceString).strip()

                try:
                    settings = win32api.EnumDisplaySettings(dev.DeviceName, -1)
                    if settings:
                        resolution = f"{settings.PelsWidth}x{settings.PelsHeight}"
                        refresh_rate = int(settings.DisplayFrequency)
                except Exception as exc:  # noqa: BLE001
                    logger.debug("EnumDisplaySettings falhou: %s", exc)

                # Busca rápida de versão do driver no registro
                for sub in ["0000", "0001", "0002"]:
                    try:
                        with winreg.OpenKey(
                            winreg.HKEY_LOCAL_MACHINE,
                            rf"SYSTEM\CurrentControlSet\Control\Class\{{4d36e968-e325-11ce-bfc1-08002be10318}}\{sub}",
                        ) as k:
                            drv, _ = winreg.QueryValueEx(k, "DriverVersion")
                            if drv:
                                driver_version = str(drv).strip()
                                break
                    except OSError:
                        continue

                self._gpu_cached = (gpu_name, driver_version, adapter_ram, resolution, refresh_rate)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Consulta rápida de GPU via Win32 falhou: %s", exc)

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
            adapter_ram_bytes=adapter_ram,
            resolution=resolution,
            refresh_rate_hz=refresh_rate,
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
