"""Relator Técnico de Sessão e Gravador Contínuo de Telemetria — Sollaris Nova.

Fornece gravação contínua e assíncrona de telemetria ("Flight Recorder")
em arquivo de log estruturado sob demanda, com I/O em segundo plano (0ms na GUI)
e sumário executivo final para diagnóstico e análise de estabilidade.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from core.hardware import format_bytes, format_uptime

if TYPE_CHECKING:
    from core.diagnostics import DiagnosticFinding
    from core.hardware import SystemSnapshot
    from core.processes import ProcessItem

logger = logging.getLogger("sollaris_nova.recorder")


class SessionRecorder:
    """Gravador contínuo de telemetria e anomalias de hardware em segundo plano."""

    def __init__(self, reports_dir: Path | None = None) -> None:
        self._reports_dir = reports_dir or (Path(__file__).resolve().parent.parent / "data" / "reports")
        self._lock = threading.Lock()
        self._is_recording = False
        self._start_time: float = 0.0
        self._sample_count: int = 0
        self._current_file: Path | None = None

        # Estatísticas acumuladas da sessão gravada
        self._cpu_samples: list[float] = []
        self._ram_samples: list[float] = []
        self._anomalies_count: int = 0

        # Concorrência e fila assíncrona de I/O
        self._queue: queue.Queue[str | None] = queue.Queue(maxsize=2000)
        self._writer_thread: threading.Thread | None = None

    @property
    def is_recording(self) -> bool:
        """Indica se há uma sessão de gravação ativa."""
        with self._lock:
            return self._is_recording

    @property
    def elapsed_seconds(self) -> int:
        """Retorna os segundos decorridos desde o início da gravação atual."""
        with self._lock:
            if not self._is_recording:
                return 0
            return int(time.time() - self._start_time)

    @property
    def sample_count(self) -> int:
        """Retorna o total de amostras colhidas na sessão atual."""
        with self._lock:
            return self._sample_count

    @property
    def current_file_path(self) -> Path | None:
        """Caminho absoluto do arquivo de relatório ativo."""
        with self._lock:
            return self._current_file

    @property
    def reports_dir(self) -> Path:
        """Diretório base onde os relatórios técnicos são armazenados."""
        return self._reports_dir

    def start_session(self, initial_snapshot: SystemSnapshot) -> Path:
        """Inicia a gravação contínua da sessão e prepara o arquivo de relatório."""
        with self._lock:
            if self._is_recording:
                return self._current_file or Path()

            self._reports_dir.mkdir(parents=True, exist_ok=True)
            timestamp_str = datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S")
            self._current_file = self._reports_dir / f"relatorio_sessao_{timestamp_str}.log"
            self._current_file.touch()

            self._is_recording = True
            self._start_time = time.time()
            self._sample_count = 0
            self._cpu_samples.clear()
            self._ram_samples.clear()
            self._anomalies_count = 0

            # Limpa qualquer item residual da fila
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break

            # Inicia a thread trabalhadora de escrita em disco
            self._writer_thread = threading.Thread(
                target=self._writer_loop,
                args=(self._current_file,),
                daemon=True,
                name="SessionRecorderWriter",
            )
            self._writer_thread.start()

            # Gera e enfileira o cabeçalho técnico da máquina
            header = self._build_session_header(initial_snapshot)
            self._queue.put(header)

            logger.info("Sessão de gravação técnica iniciada: %s", self._current_file)
            return self._current_file

    def record_tick(
        self,
        snapshot: SystemSnapshot,
        processes: list[ProcessItem],
        findings: list[DiagnosticFinding],
    ) -> None:
        """Enfileira um tick de amostragem periódica sem bloquear a interface gráfica (0ms)."""
        with self._lock:
            if not self._is_recording:
                return

            self._sample_count += 1
            self._cpu_samples.append(snapshot.cpu.total_percent)
            self._ram_samples.append(snapshot.ram.percent)

            # Contabiliza anomalias e alertas críticos/atenção
            active_anomalies = [f for f in findings if f.level.value in ("warning", "critical")]
            self._anomalies_count += len(active_anomalies)

            entry = self._build_tick_entry(snapshot, processes, active_anomalies)
            try:
                self._queue.put_nowait(entry)
            except queue.Full:
                logger.warning("Fila do SessionRecorder cheia; descartando tick para não bloquear telemetria.")

    def stop_session(self) -> dict[str, Any]:
        """Finaliza a gravação, aguarda descarga do buffer e escreve o sumário executivo final."""
        with self._lock:
            if not self._is_recording:
                return {}

            self._is_recording = False
            duration = int(time.time() - self._start_time)
            samples = self._sample_count
            cpu_avg = sum(self._cpu_samples) / max(1, len(self._cpu_samples))
            cpu_max = max(self._cpu_samples) if self._cpu_samples else 0.0
            ram_avg = sum(self._ram_samples) / max(1, len(self._ram_samples))
            ram_max = max(self._ram_samples) if self._ram_samples else 0.0
            anomalies = self._anomalies_count
            file_path = self._current_file

            summary_text = self._build_session_summary(
                duration_sec=duration,
                samples=samples,
                cpu_avg=cpu_avg,
                cpu_max=cpu_max,
                ram_avg=ram_avg,
                ram_max=ram_max,
                anomalies=anomalies,
            )
            self._queue.put(summary_text)
            self._queue.put(None)  # Sentinela de término da thread de escrita

        # Aguarda término ordenado da thread de escrita
        if self._writer_thread and self._writer_thread.is_alive():
            self._writer_thread.join(timeout=3.0)

        logger.info("Sessão de gravação finalizada: %s (%d amostras)", file_path, samples)

        return {
            "file_path": str(file_path),
            "duration_seconds": duration,
            "sample_count": samples,
            "cpu_avg": cpu_avg,
            "cpu_max": cpu_max,
            "ram_avg": ram_avg,
            "ram_max": ram_max,
            "anomalies_count": anomalies,
        }

    def _writer_loop(self, target_path: Path) -> None:
        """Loop trabalhador em background que drena a fila e grava no arquivo em disco."""
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                while True:
                    entry = self._queue.get()
                    if entry is None:
                        f.flush()
                        break
                    f.write(entry)
                    f.flush()
        except OSError:
            logger.exception("Falha ao gravar arquivo de relatório: %s", target_path)

    def _build_session_header(self, snap: SystemSnapshot) -> str:
        """Gera o cabeçalho técnico detalhado com as especificações da máquina."""
        now_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        freq_str = f"{snap.cpu.frequency_base_mhz:.0f} MHz" if snap.cpu.frequency_base_mhz else "N/A"
        ram_str = format_bytes(snap.ram.total_bytes)

        lines = [
            "================================================================================",
            "SOLLARIS NOVA — RELATÓRIO TÉCNICO DE TELEMETRIA E DIAGNÓSTICO (FLIGHT RECORDER)",
            "================================================================================",
            f"Data/Hora de Início:    {now_str}",
            f"Sistema Operacional:    {snap.os_name} {snap.os_release} (Build {snap.os_build}) [{snap.architecture}]",
            f"Processador (CPU):      {snap.cpu.model_name or 'Detectado'}",
            f"Topologia de CPU:       {snap.cpu.core_count_physical} Núcleos Físicos / {snap.cpu.core_count_logical} Núcleos Lógicos | Base: {freq_str}",
            f"Memória RAM Total:      {ram_str}",
            f"Placa de Vídeo (GPU):   {snap.gpu.name} (Driver: {snap.gpu.driver_version or 'Nativo'})",
            f"Tempo de Uptime Prévio: {format_uptime(snap.uptime_seconds)}",
            "--------------------------------------------------------------------------------",
            "REGISTRO CRONOLÓGICO DE AMOSTRAGEM E EVENTOS:",
            "--------------------------------------------------------------------------------\n",
        ]
        return "\n".join(lines)

    def _build_tick_entry(
        self,
        snap: SystemSnapshot,
        procs: list[ProcessItem],
        active_anomalies: list[DiagnosticFinding],
    ) -> str:
        """Formata uma linha de amostragem de telemetria e eventuais anomalias ativas."""
        time_str = datetime.now().astimezone().strftime("%H:%M:%S")
        c_pct = snap.cpu.total_percent
        r_pct = snap.ram.percent
        r_used = format_bytes(snap.ram.used_bytes)
        r_tot = format_bytes(snap.ram.total_bytes)
        s_pct = snap.ram.swap_percent

        freq_curr = f"{snap.cpu.frequency_current_mhz:.0f}MHz" if snap.cpu.frequency_current_mhz else "--"

        top_procs_txt = ", ".join(
            f"{p.name} (PID: {p.pid}, {format_bytes(p.memory_rss_bytes)})"
            for p in procs[:3]
        ) if procs else "Nenhum processo monitorado"

        lines = [
            f"[{time_str}] CPU: {c_pct:5.1f}% ({freq_curr:>7}) | RAM: {r_pct:5.1f}% ({r_used}/{r_tot}) | SWAP: {s_pct:4.1f}%",
            f"         TOP: {top_procs_txt}",
        ]

        if active_anomalies:
            for a in active_anomalies:
                tag = "CRÍTICO" if a.level.value == "critical" else "ATENÇÃO"
                lines.append(f"         >>> [{tag}] {a.title}: {a.evidence}")

        lines.append("")  # Linha em branco separadora
        return "\n".join(lines)

    def _build_session_summary(
        self,
        duration_sec: int,
        samples: int,
        cpu_avg: float,
        cpu_max: float,
        ram_avg: float,
        ram_max: float,
        anomalies: int,
    ) -> str:
        """Gera o sumário executivo de encerramento da sessão."""
        end_time_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "--------------------------------------------------------------------------------",
            "SUMÁRIO EXECUTIVO DA SESSÃO GRAVADA:",
            "--------------------------------------------------------------------------------",
            f"Data/Hora de Encerramento:   {end_time_str}",
            f"Duração Total Monitorada:    {format_uptime(duration_sec)} ({duration_sec} segundos)",
            f"Total de Amostras Colhidas:  {samples} amostras",
            f"Processador (CPU):           Média: {cpu_avg:5.1f}% | Pico Máximo: {cpu_max:5.1f}%",
            f"Memória RAM:                 Média: {ram_avg:5.1f}% | Pico Máximo: {ram_max:5.1f}%",
            f"Total de Alertas/Anomalias:  {anomalies} ocorrências registradas",
            "Estado Geral da Sessão:      " + ("CRÍTICO (Gargalos sustentados detectados)" if anomalies > 5 else ("ATENÇÃO" if anomalies > 0 else "ESTÁVEL (Sem violações de estabilidade)")),
            "================================================================================\n",
        ]
        return "\n".join(lines)
