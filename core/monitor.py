"""Serviço de Monitoramento Assíncrono em Segundo Plano — Sollaris Nova.

Executa uma thread daemon desacoplada da interface para amostragem contínua
de hardware e processos, garantindo que a GUI nunca congele ou sofra bloqueio.
"""

import logging
import queue
import threading
import time
from collections import deque

from core.hardware import HardwareCollector, SystemSnapshot
from core.processes import ProcessCollector, ProcessItem

logger = logging.getLogger("sollaris_nova.monitor")


class MonitorService:
    """Thread em segundo plano que alimenta a interface gráfica sem bloquear o loop principal."""

    def __init__(self, interval_seconds: float = 1.5) -> None:
        self._interval = interval_seconds
        self._collector = HardwareCollector()
        self._queue: queue.Queue[tuple[SystemSnapshot, list[ProcessItem]]] = queue.Queue(maxsize=2)
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._latest_snapshot: SystemSnapshot | None = None
        self._latest_processes: list[ProcessItem] = []
        self._lock = threading.Lock()

        # Buffer circular em memória para histórico recente (consumo estritamente fixo)
        self.cpu_history: deque[float] = deque(maxlen=60)
        self.ram_history: deque[float] = deque(maxlen=60)

    def request_immediate_refresh(self) -> None:
        """Sinaliza a thread de background para coletar dados imediatamente."""
        self._wake_event.set()

    def start(self) -> None:
        """Inicia a thread de monitoramento assíncrono."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._wake_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="MonitorServiceThread")
        self._thread.start()
        logger.info("MonitorService iniciado em segundo plano com intervalo de %.1fs", self._interval)

    def stop(self) -> None:
        """Sinaliza parada e aguarda término da thread."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info("MonitorService finalizado.")

    def set_interval(self, interval_seconds: float) -> None:
        """Atualiza a cadência de coleta."""
        self._interval = max(0.5, float(interval_seconds))

    def get_latest_data(self) -> tuple[SystemSnapshot | None, list[ProcessItem]]:
        """Retorno atômico e não-bloqueante para a thread da interface gráfica."""
        # Esvazia a fila se houver dados mais recentes
        while not self._queue.empty():
            try:
                snap, procs = self._queue.get_nowait()
                with self._lock:
                    self._latest_snapshot = snap
                    self._latest_processes = procs
            except queue.Empty:
                break

        with self._lock:
            return self._latest_snapshot, list(self._latest_processes)

    def _worker_loop(self) -> None:
        """Loop executado em thread separada do sistema operacional."""
        try:
            import pythoncom

            pythoncom.CoInitialize()
        except (ImportError, Exception) as exc:  # noqa: BLE001
            logger.debug("CoInitialize não disponível: %s", exc)

        last_proc_scan = 0.0
        current_procs: list[ProcessItem] = []

        try:
            while not self._stop_event.is_set():
                t_start = time.perf_counter()
                try:
                    snapshot = self._collector.collect_snapshot()

                    # Atualiza buffer circular
                    self.cpu_history.append(snapshot.cpu.total_percent)
                    self.ram_history.append(snapshot.ram.percent)

                    # Amostragem de processos a cada 3.5 segundos para baixo overhead
                    now = time.time()
                    if now - last_proc_scan >= 3.5 or not current_procs:
                        current_procs = ProcessCollector.get_top_processes(limit=6)
                        last_proc_scan = now

                    # Envia para a fila da UI descartando itens defasados
                    if self._queue.full():
                        try:
                            self._queue.get_nowait()
                        except queue.Empty:
                            pass
                    self._queue.put((snapshot, current_procs))

                    with self._lock:
                        self._latest_snapshot = snapshot
                        self._latest_processes = current_procs

                except Exception:
                    logger.exception("Erro durante ciclo de coleta assíncrona.")

                elapsed = time.perf_counter() - t_start
                sleep_time = max(0.1, self._interval - elapsed)
                if self._wake_event.wait(timeout=sleep_time):
                    self._wake_event.clear()
                if self._stop_event.is_set():
                    break
        finally:
            try:
                import pythoncom

                pythoncom.CoUninitialize()
            except (ImportError, Exception) as exc:  # noqa: BLE001
                logger.debug("CoUninitialize falhou: %s", exc)
