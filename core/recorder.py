"""Relator Técnico de Sessão e Gravador Contínuo de Telemetria — Sollaris Nova.

Fornece gravação contínua e assíncrona de telemetria ("Flight Recorder")
em arquivo de log estruturado e altamente detalhado sob demanda, com I/O em segundo plano
(0ms na GUI) e sumário executivo analítico para diagnóstico e análise de estabilidade.
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
        self._initial_snapshot: SystemSnapshot | None = None

        # Estatísticas acumuladas da sessão gravada
        self._cpu_samples: list[float] = []
        self._ram_samples: list[float] = []
        self._temp_samples: list[float] = []
        self._anomalies_count: int = 0
        self._anomalies_by_category: dict[str, int] = {}
        self._recorded_anomalies: list[DiagnosticFinding] = []
        self._top_processes_stats: dict[str, dict[str, Any]] = {}
        self._initial_ram_bytes: int = 0
        self._final_ram_bytes: int = 0

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
            self._initial_snapshot = initial_snapshot
            self._initial_ram_bytes = initial_snapshot.ram.used_bytes
            self._final_ram_bytes = initial_snapshot.ram.used_bytes

            self._cpu_samples.clear()
            self._ram_samples.clear()
            self._temp_samples.clear()
            self._anomalies_count = 0
            self._anomalies_by_category.clear()
            self._recorded_anomalies.clear()
            self._top_processes_stats.clear()

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
            self._final_ram_bytes = snapshot.ram.used_bytes

            if snapshot.cpu.temperature.is_available and snapshot.cpu.temperature.value is not None:
                self._temp_samples.append(snapshot.cpu.temperature.value)

            # Contabiliza anomalias e alertas críticos/atenção
            active_anomalies = [f for f in findings if f.level.value in ("warning", "critical")]
            self._anomalies_count += len(active_anomalies)

            for a in active_anomalies:
                self._anomalies_by_category[a.category] = self._anomalies_by_category.get(a.category, 0) + 1
                if not any(existing.title == a.title for existing in self._recorded_anomalies):
                    self._recorded_anomalies.append(a)

            # Rastreia estatísticas acumuladas dos top processos
            for p in processes[:5]:
                if p.name not in self._top_processes_stats:
                    self._top_processes_stats[p.name] = {
                        "pid": p.pid,
                        "ram_bytes_max": p.memory_rss_bytes,
                        "ram_bytes_sum": p.memory_rss_bytes,
                        "cpu_max": p.cpu_percent,
                        "occurrences": 1,
                    }
                else:
                    item = self._top_processes_stats[p.name]
                    item["pid"] = p.pid
                    item["ram_bytes_max"] = max(item["ram_bytes_max"], p.memory_rss_bytes)
                    item["ram_bytes_sum"] += p.memory_rss_bytes
                    item["cpu_max"] = max(item["cpu_max"], p.cpu_percent)
                    item["occurrences"] += 1

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
            cpu_min = min(self._cpu_samples) if self._cpu_samples else 0.0
            ram_avg = sum(self._ram_samples) / max(1, len(self._ram_samples))
            ram_max = max(self._ram_samples) if self._ram_samples else 0.0
            ram_min = min(self._ram_samples) if self._ram_samples else 0.0
            anomalies = self._anomalies_count
            file_path = self._current_file

            temp_avg = (sum(self._temp_samples) / len(self._temp_samples)) if self._temp_samples else None
            temp_max = max(self._temp_samples) if self._temp_samples else None

            summary_text = self._build_session_summary(
                duration_sec=duration,
                samples=samples,
                cpu_avg=cpu_avg,
                cpu_max=cpu_max,
                cpu_min=cpu_min,
                ram_avg=ram_avg,
                ram_max=ram_max,
                ram_min=ram_min,
                temp_avg=temp_avg,
                temp_max=temp_max,
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
            with open(target_path, "a", encoding="utf-8") as f:
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
        """Gera o cabeçalho técnico altamente detalhado com as especificações da máquina."""
        now_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        freq_base = f"{snap.cpu.frequency_base_mhz:.0f} MHz" if snap.cpu.frequency_base_mhz else "N/A"
        freq_curr = f"{snap.cpu.frequency_current_mhz:.0f} MHz" if snap.cpu.frequency_current_mhz else "N/A"
        ram_tot = format_bytes(snap.ram.total_bytes)
        ram_avail = format_bytes(snap.ram.available_bytes)
        swap_tot = format_bytes(snap.ram.swap_total_bytes)
        temp_cpu = f"{snap.cpu.temperature.value:.1f}{snap.cpu.temperature.unit}" if snap.cpu.temperature.is_available and snap.cpu.temperature.value is not None else "Sensor WMI indisponível"

        lines = [
            "================================================================================",
            "SOLLARIS NOVA — RELATÓRIO TÉCNICO DE TELEMETRIA E DIAGNÓSTICO (FLIGHT RECORDER)",
            "================================================================================",
            f"Data/Hora de Início:    {now_str}",
            f"Sistema Operacional:    {snap.os_name} {snap.os_release} (Build {snap.os_build}) [{snap.architecture}]",
            f"Tempo de Uptime Prévio: {format_uptime(snap.uptime_seconds)}",
            f"Processos Ativos no SO: {snap.cpu.process_count} processos | {snap.cpu.thread_count} threads em execução",
            "--------------------------------------------------------------------------------",
            "ESPECIFICAÇÕES DE HARDWARE IDENTIFICADAS:",
            "--------------------------------------------------------------------------------",
            f"Processador (CPU):      {snap.cpu.model_name or 'Detectado'}",
            f"  Topologia:            {snap.cpu.core_count_physical} Núcleos Físicos / {snap.cpu.core_count_logical} Núcleos Lógicos",
            f"  Frequência:           Base: {freq_base} | Atual no início: {freq_curr}",
            f"  Temperatura Térmica:  {temp_cpu}",
            f"Memória RAM Primária:   {ram_tot} instalada ({ram_avail} livre no início da sessão)",
            f"  Arquivo de Swap:      {swap_tot} total alocado para paginação dinâmica",
            f"Placa de Vídeo (GPU):   {snap.gpu.name} (Driver: {snap.gpu.driver_version or 'Nativo'})",
        ]

        if snap.gpu.adapter_ram_bytes:
            lines.append(f"  VRAM Dedicada:        {format_bytes(snap.gpu.adapter_ram_bytes)}")
        if snap.gpu.temperature.is_available and snap.gpu.temperature.value is not None:
            lines.append(f"  Temperatura da GPU:   {snap.gpu.temperature.value:.1f}{snap.gpu.temperature.unit}")

        lines.extend([
            "--------------------------------------------------------------------------------",
            "UNIDADES DE ARMAZENAMENTO DETECTADAS:",
            "--------------------------------------------------------------------------------",
        ])

        for d in snap.disks:
            tot = format_bytes(d.total_bytes)
            used = format_bytes(d.used_bytes)
            free = format_bytes(d.free_bytes)
            lines.append(f"  [{d.device}] Mount: {d.mountpoint:<6} | Tipo: {d.fstype:<5} | Total: {tot:>9} | Usado: {used:>9} ({d.percent:5.1f}%) | Livre: {free:>9}")

        lines.extend([
            "--------------------------------------------------------------------------------",
            "REGISTRO CRONOLÓGICO DE AMOSTRAGEM E EVENTOS:",
            "--------------------------------------------------------------------------------\n",
        ])
        return "\n".join(lines)

    def _build_tick_entry(
        self,
        snap: SystemSnapshot,
        procs: list[ProcessItem],
        active_anomalies: list[DiagnosticFinding],
    ) -> str:
        """Formata uma linha de amostragem de telemetria rica e eventuais anomalias ativas."""
        time_str = datetime.now().astimezone().strftime("%H:%M:%S")
        c_pct = snap.cpu.total_percent
        r_pct = snap.ram.percent
        r_used = format_bytes(snap.ram.used_bytes)
        r_tot = format_bytes(snap.ram.total_bytes)
        s_pct = snap.ram.swap_percent

        freq_curr = f"{snap.cpu.frequency_current_mhz:.0f}MHz" if snap.cpu.frequency_current_mhz else "--"
        temp_str = f" | Temp: {snap.cpu.temperature.value:.0f}°C" if snap.cpu.temperature.is_available and snap.cpu.temperature.value is not None else ""

        lines = [
            f"[{time_str}] CPU: {c_pct:5.1f}% ({freq_curr:>7}{temp_str}) | RAM: {r_pct:5.1f}% ({r_used}/{r_tot}) | SWAP: {s_pct:4.1f}%"
        ]

        # Top 5 processos formatados
        if procs:
            procs_formatted = [
                f"{p.name} (PID: {p.pid}, {format_bytes(p.memory_rss_bytes)})"
                for p in procs[:5]
            ]
            lines.append(f"         TOP: {', '.join(procs_formatted[:3])}")
            if len(procs_formatted) > 3:
                lines.append(f"              {', '.join(procs_formatted[3:])}")

        # Anomalias ativas do instante
        if active_anomalies:
            for a in active_anomalies:
                tag = "CRÍTICO" if a.level.value == "critical" else "ATENÇÃO"
                lines.append(f"         >>> [{tag}] [{a.category}] {a.title}: {a.evidence}")
                lines.append(f"             Impacto: {a.probable_impact}")
                lines.append(f"             Ação:    {a.suggested_action}")

        lines.append("")  # Linha em branco separadora
        return "\n".join(lines)

    def _build_session_summary(
        self,
        duration_sec: int,
        samples: int,
        cpu_avg: float,
        cpu_max: float,
        cpu_min: float,
        ram_avg: float,
        ram_max: float,
        ram_min: float,
        temp_avg: float | None,
        temp_max: float | None,
        anomalies: int,
    ) -> str:
        """Gera o sumário executivo analítico e conclusivo de encerramento da sessão."""
        end_time_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        cadence_str = f"~{duration_sec / max(1, samples):.1f}s/amostra" if samples > 0 else "N/A"
        ram_delta_bytes = self._final_ram_bytes - self._initial_ram_bytes
        ram_delta_sign = "+" if ram_delta_bytes >= 0 else "-"
        ram_delta_str = f"{ram_delta_sign}{format_bytes(abs(ram_delta_bytes))}"

        lines = [
            "--------------------------------------------------------------------------------",
            "SUMÁRIO EXECUTIVO DA SESSÃO GRAVADA:",
            "--------------------------------------------------------------------------------",
            f"Data/Hora de Encerramento:   {end_time_str}",
            f"Duração Total Monitorada:    {format_uptime(duration_sec)} ({duration_sec} segundos)",
            f"Total de Amostras Colhidas:  {samples} amostras (Cadência média: {cadence_str})",
            "",
            "ESTATÍSTICAS CONSOLIDADAS DE PROCESSAMENTO (CPU):",
            f"  Média de Utilização:       {cpu_avg:5.1f}%",
            f"  Pico Máximo Registrado:    {cpu_max:5.1f}%",
            f"  Mínimo Registrado:         {cpu_min:5.1f}%",
        ]

        if temp_avg is not None and temp_max is not None:
            lines.append(f"  Temperatura Térmica:       Média: {temp_avg:.1f}°C | Pico: {temp_max:.1f}°C")

        lines.extend([
            "",
            "ESTATÍSTICAS CONSOLIDADAS DE MEMÓRIA (RAM):",
            f"  Média de Utilização:       {ram_avg:5.1f}%",
            f"  Pico Máximo Registrado:    {ram_max:5.1f}%",
            f"  Mínimo Registrado:         {ram_min:5.1f}%",
            f"  Variação de Working Set:   {ram_delta_str} durante a sessão monitorada",
            "",
            "ANÁLISE DE ANOMALIAS E ESTABILIDADE TÉCNICA:",
            f"  Total de Alertas/Anomalias:  {anomalies} ocorrências registradas",
        ])

        if self._anomalies_by_category:
            for cat, count in self._anomalies_by_category.items():
                lines.append(f"  - {cat:<24} {count} ocorrências")
        else:
            lines.append("  - Nenhuma anomalia crítica ou aviso registrado durante a sessão.")

        if self._recorded_anomalies:
            lines.extend([
                "",
                "DIAGNÓSTICOS TÉCNICOS DETECTADOS NA SESSÃO:",
            ])
            for idx, a in enumerate(self._recorded_anomalies, 1):
                lines.append(f"  {idx}. [{a.category}] {a.title}")
                lines.append(f"     Evidência:    {a.evidence}")
                lines.append(f"     Causa:        {a.technical_explanation}")
                lines.append(f"     Recomendação: {a.suggested_action} (Reversível: {'Sim' if a.is_reversible else 'Não'})")

        if self._top_processes_stats:
            lines.extend([
                "",
                "PROCESSOS MAIS RELEVANTES DA SESSÃO (TOP CONSUMIDORES):",
            ])
            sorted_procs = sorted(
                self._top_processes_stats.items(),
                key=lambda x: x[1]["ram_bytes_max"],
                reverse=True,
            )[:5]
            for idx, (pname, pdata) in enumerate(sorted_procs, 1):
                avg_ram = pdata["ram_bytes_sum"] / max(1, pdata["occurrences"])
                lines.append(
                    f"  {idx}. {pname:<24} PID: {pdata['pid']:<6} | RAM Média: {format_bytes(int(avg_ram)):>9} | Pico RAM: {format_bytes(pdata['ram_bytes_max']):>9} | Pico CPU: {pdata['cpu_max']:4.1f}%"
                )

        lines.extend([
            "",
            "Estado Geral da Sessão:      " + (
                "CRÍTICO (Gargalos severos sustentados identificados)"
                if anomalies > 5
                else ("ATENÇÃO (Anomalias pontuais registradas)" if anomalies > 0 else "ESTÁVEL (Sem violações de estabilidade)")
            ),
            "================================================================================\n",
        ])
        return "\n".join(lines)
