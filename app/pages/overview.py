"""Página de Visão Geral (Overview) — Sollaris Nova.

Apresenta a instrumentação em tempo real do sistema:
- Medidores radiais (RadialGauge) de CPU e RAM
- Gráfico histórico dos últimos 60 segundos com curvas fluidas e hover
- Detecção e instrumentação de partições de disco locais
- Especificações de GPU e Sistema Operacional
- Tabela de maiores processos consumidores de memória
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import customtkinter as ctk

from app.components.performance_chart import PerformanceChart
from app.components.radial_gauge import RadialGauge
from app.components.tooltip import Tooltip
from app.theme import LayoutDimensions, ThemeColors, Typography
from core.hardware import (
    DiskPartitionMetrics,
    SystemSnapshot,
    format_bytes,
    format_uptime,
)

if TYPE_CHECKING:
    from core.processes import ProcessItem

logger = logging.getLogger("sollaris_nova.pages.overview")


class OverviewPage(ctk.CTkScrollableFrame):
    """Página de instrumentação técnica e métricas em tempo real."""

    def __init__(self, parent: ctk.CTkBaseClass) -> None:
        super().__init__(parent, fg_color=ThemeColors.BG_MAIN, corner_radius=0)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._current_snapshot: SystemSnapshot | None = None
        self._disk_widget_rows: dict[str, dict[str, ctk.CTkBaseClass]] = {}
        self._proc_rows: list[dict[str, ctk.CTkLabel]] = []
        self._core_chip_labels: list[ctk.CTkLabel] = []

        self._build_cards()

    def _build_cards(self) -> None:
        """Constrói todos os cartões de telemetria da Visão Geral."""
        # 1. Cartão CPU
        self._cpu_card = ctk.CTkFrame(
            self,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._cpu_card.grid(row=0, column=0, sticky="nsew", padx=(0, LayoutDimensions.PAD_MD), pady=(0, LayoutDimensions.PAD_LG))

        cpu_top = ctk.CTkFrame(self._cpu_card, fg_color="transparent")
        cpu_top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_LG, 4))

        ctk.CTkLabel(cpu_top, text="PROCESSADOR (CPU)", font=Typography.card_title(), text_color=ThemeColors.TEXT_MUTED).pack(side="left")
        self._cpu_badge = ctk.CTkLabel(cpu_top, text="Normal", font=Typography.caption(), text_color=ThemeColors.STATUS_OK)
        self._cpu_badge.pack(side="right")

        # Corpo com RadialGauge à esquerda e detalhes técnicos à direita
        cpu_body = ctk.CTkFrame(self._cpu_card, fg_color="transparent")
        cpu_body.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(4, LayoutDimensions.PAD_SM))

        self._cpu_gauge = RadialGauge(
            cpu_body,
            size=116,
            stroke_width=8,
            default_accent_color=ThemeColors.ACCENT_BLUE,
            label="CARGA",
            fg_color=ThemeColors.BG_SURFACE,
        )
        self._cpu_gauge.pack(side="left", padx=(0, LayoutDimensions.PAD_MD), pady=2)
        self._cpu_gauge.set_tooltip(self._get_cpu_tooltip_text)

        cpu_details = ctk.CTkFrame(cpu_body, fg_color="transparent")
        cpu_details.pack(side="left", fill="both", expand=True)

        self._cpu_model_lbl = ctk.CTkLabel(cpu_details, text="• Modelo: Detectando...", font=Typography.caption(), text_color=ThemeColors.TEXT_PRIMARY, anchor="w")
        self._cpu_model_lbl.pack(fill="x", pady=1)

        self._cpu_cores_lbl = ctk.CTkLabel(cpu_details, text="• Núcleos: -- Físicos | -- Lógicos", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._cpu_cores_lbl.pack(fill="x", pady=1)

        self._cpu_freq_lbl = ctk.CTkLabel(cpu_details, text="• Frequência: Base: -- | Atual: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._cpu_freq_lbl.pack(fill="x", pady=1)

        self._cpu_temp_lbl = ctk.CTkLabel(cpu_details, text="• Temperatura: Sensor indisponível", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._cpu_temp_lbl.pack(fill="x", pady=1)

        self._cpu_stats_lbl = ctk.CTkLabel(cpu_details, text="• Janela 60s: Média --% | Pico --%", font=Typography.caption(), text_color=ThemeColors.ACCENT_LIGHT, anchor="w")
        self._cpu_stats_lbl.pack(fill="x", pady=1)

        # Micro-medidores de núcleos
        self._cores_box = ctk.CTkFrame(self._cpu_card, fg_color="transparent")
        self._cores_box.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(2, LayoutDimensions.PAD_LG))

        cores_hdr = ctk.CTkFrame(self._cores_box, fg_color="transparent")
        cores_hdr.pack(fill="x", pady=(2, 4))
        ctk.CTkLabel(cores_hdr, text="Carga por Núcleo Lógico:", font=(Typography.FONT_FAMILY, 10, "bold"), text_color=ThemeColors.TEXT_MUTED).pack(side="left")

        self._grid_cores = ctk.CTkFrame(self._cores_box, fg_color="transparent")
        self._grid_cores.pack(fill="x")
        self._core_chip_labels = []
        cols = 6
        for idx in range(12):
            r = idx // cols
            c = idx % cols
            self._grid_cores.grid_columnconfigure(c, weight=1)
            cell = ctk.CTkFrame(self._grid_cores, fg_color="#141E2B", corner_radius=3)
            cell.grid(row=r, column=c, padx=2, pady=2, sticky="ew")
            lbl = ctk.CTkLabel(cell, text=f"N{idx+1}: 0%", font=(Typography.FONT_FAMILY, 9), text_color=ThemeColors.STATUS_OK)
            lbl.pack(padx=2, pady=1)
            self._core_chip_labels.append(lbl)
            Tooltip(cell, lambda i=idx: self._get_core_tooltip_text(i))
            Tooltip(lbl, lambda i=idx: self._get_core_tooltip_text(i))

        # 2. Cartão RAM
        self._ram_card = ctk.CTkFrame(
            self,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._ram_card.grid(row=0, column=1, sticky="nsew", padx=(LayoutDimensions.PAD_MD, 0), pady=(0, LayoutDimensions.PAD_LG))

        ram_top = ctk.CTkFrame(self._ram_card, fg_color="transparent")
        ram_top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_LG, 4))

        ctk.CTkLabel(ram_top, text="MEMÓRIA RAM & VIRTUAL", font=Typography.card_title(), text_color=ThemeColors.TEXT_MUTED).pack(side="left")
        self._ram_badge = ctk.CTkLabel(ram_top, text="Normal", font=Typography.caption(), text_color=ThemeColors.STATUS_OK)
        self._ram_badge.pack(side="right")

        ram_body = ctk.CTkFrame(self._ram_card, fg_color="transparent")
        ram_body.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(4, LayoutDimensions.PAD_SM))

        self._ram_gauge = RadialGauge(
            ram_body,
            size=116,
            stroke_width=8,
            default_accent_color=ThemeColors.STATUS_OK,
            label="EM USO",
            fg_color=ThemeColors.BG_SURFACE,
        )
        self._ram_gauge.pack(side="left", padx=(0, LayoutDimensions.PAD_MD), pady=2)
        self._ram_gauge.set_tooltip(self._get_ram_tooltip_text)

        ram_details = ctk.CTkFrame(ram_body, fg_color="transparent")
        ram_details.pack(side="left", fill="both", expand=True)

        self._ram_used_lbl = ctk.CTkLabel(ram_details, text="• Em Uso: --", font=Typography.caption(), text_color=ThemeColors.TEXT_PRIMARY, anchor="w")
        self._ram_used_lbl.pack(fill="x", pady=1)

        self._ram_avail_lbl = ctk.CTkLabel(ram_details, text="• Disponível: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._ram_avail_lbl.pack(fill="x", pady=1)

        self._ram_total_lbl = ctk.CTkLabel(ram_details, text="• Total Instalada: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._ram_total_lbl.pack(fill="x", pady=1)

        self._ram_swap_lbl = ctk.CTkLabel(ram_details, text="• Paginação (Swap): --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._ram_swap_lbl.pack(fill="x", pady=1)

        self._ram_stats_lbl = ctk.CTkLabel(ram_details, text="• Janela 60s: Média --% | Pico --%", font=Typography.caption(), text_color=ThemeColors.ACCENT_LIGHT, anchor="w")
        self._ram_stats_lbl.pack(fill="x", pady=1)

        ctk.CTkLabel(
            self._ram_card,
            text="A memória disponível inclui cache reaproveitável pelo Windows.",
            font=(Typography.FONT_FAMILY, 9, "italic"),
            text_color=ThemeColors.TEXT_INACTIVE,
            anchor="w",
        ).pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(2, LayoutDimensions.PAD_MD))

        # 3. Gráfico Histórico dos Últimos 60 Segundos
        self._perf_chart = PerformanceChart(self)
        self._perf_chart.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, LayoutDimensions.PAD_LG))

        # 4. Cartão Armazenamento Local
        self._storage_card = ctk.CTkFrame(
            self,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._storage_card.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, LayoutDimensions.PAD_LG))

        storage_top = ctk.CTkFrame(self._storage_card, fg_color="transparent")
        storage_top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_LG, LayoutDimensions.PAD_SM))
        ctk.CTkLabel(storage_top, text="ARMAZENAMENTO LOCAL (PARTIÇÕES DETECTADAS)", font=Typography.card_title(), text_color=ThemeColors.TEXT_MUTED).pack(side="left")

        self._disks_container = ctk.CTkFrame(self._storage_card, fg_color="transparent")
        self._disks_container.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_LG))

        # 5. Cartão GPU e Display
        self._gpu_card = ctk.CTkFrame(
            self,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._gpu_card.grid(row=3, column=0, sticky="nsew", padx=(0, LayoutDimensions.PAD_MD), pady=(0, LayoutDimensions.PAD_LG))

        gpu_top = ctk.CTkFrame(self._gpu_card, fg_color="transparent")
        gpu_top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_LG, 4))
        ctk.CTkLabel(gpu_top, text="PLACA DE VÍDEO (GPU)", font=Typography.card_title(), text_color=ThemeColors.TEXT_MUTED).pack(side="left")

        gpu_details = ctk.CTkFrame(self._gpu_card, fg_color="transparent")
        gpu_details.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=LayoutDimensions.PAD_SM)

        self._gpu_name_lbl = ctk.CTkLabel(gpu_details, text="• GPU: Detectando...", font=Typography.caption(), text_color=ThemeColors.TEXT_PRIMARY, anchor="w")
        self._gpu_name_lbl.pack(fill="x", pady=2)

        self._gpu_driver_lbl = ctk.CTkLabel(gpu_details, text="• Driver: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._gpu_driver_lbl.pack(fill="x", pady=2)

        self._gpu_res_lbl = ctk.CTkLabel(gpu_details, text="• Resolução: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._gpu_res_lbl.pack(fill="x", pady=2)

        self._gpu_vram_lbl = ctk.CTkLabel(gpu_details, text="• VRAM: Estimando...", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._gpu_vram_lbl.pack(fill="x", pady=2)

        self._gpu_temp_lbl = ctk.CTkLabel(gpu_details, text="• Temperatura GPU: Sensor indisponível", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._gpu_temp_lbl.pack(fill="x", pady=2)

        # 6. Cartão Sistema & Ambiente
        self._sys_card = ctk.CTkFrame(
            self,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._sys_card.grid(row=3, column=1, sticky="nsew", padx=(LayoutDimensions.PAD_MD, 0), pady=(0, LayoutDimensions.PAD_LG))

        sys_top = ctk.CTkFrame(self._sys_card, fg_color="transparent")
        sys_top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_LG, 4))
        ctk.CTkLabel(sys_top, text="SISTEMA & AMBIENTE", font=Typography.card_title(), text_color=ThemeColors.TEXT_MUTED).pack(side="left")

        sys_details = ctk.CTkFrame(self._sys_card, fg_color="transparent")
        sys_details.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=LayoutDimensions.PAD_SM)

        self._sys_os_lbl = ctk.CTkLabel(sys_details, text="• Sistema: Windows", font=Typography.caption(), text_color=ThemeColors.TEXT_PRIMARY, anchor="w")
        self._sys_os_lbl.pack(fill="x", pady=2)

        self._sys_build_lbl = ctk.CTkLabel(sys_details, text="• Compilação: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._sys_build_lbl.pack(fill="x", pady=2)

        self._sys_uptime_lbl = ctk.CTkLabel(sys_details, text="• Tempo de Atividade: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._sys_uptime_lbl.pack(fill="x", pady=2)

        self._sys_runtime_lbl = ctk.CTkLabel(sys_details, text="• Runtime: Python 3.14 (Desktop)", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._sys_runtime_lbl.pack(fill="x", pady=2)

        # 7. Cartão Top Processos
        self._procs_card = ctk.CTkFrame(
            self,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._procs_card.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(0, LayoutDimensions.PAD_LG))

        procs_top = ctk.CTkFrame(self._procs_card, fg_color="transparent")
        procs_top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_LG, LayoutDimensions.PAD_SM))
        ctk.CTkLabel(procs_top, text="PROCESSOS COM MAIOR CONSUMO DE MEMÓRIA (TOP 6)", font=Typography.card_title(), text_color=ThemeColors.TEXT_MUTED).pack(side="left")

        self._procs_container = ctk.CTkFrame(self._procs_card, fg_color="transparent")
        self._procs_container.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_LG))

        header_row = ctk.CTkFrame(self._procs_container, fg_color="#141E2B", corner_radius=3)
        header_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(header_row, text="  PID", width=60, font=(Typography.FONT_FAMILY, 10, "bold"), text_color=ThemeColors.TEXT_MUTED, anchor="w").pack(side="left")
        ctk.CTkLabel(header_row, text="Nome do Processo", font=(Typography.FONT_FAMILY, 10, "bold"), text_color=ThemeColors.TEXT_MUTED, anchor="w").pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(header_row, text="Memória RAM  ", width=120, font=(Typography.FONT_FAMILY, 10, "bold"), text_color=ThemeColors.TEXT_MUTED, anchor="e").pack(side="right")

        self._proc_rows = []
        for _ in range(6):
            row = ctk.CTkFrame(self._procs_container, fg_color="transparent")
            row.pack(fill="x", pady=1)
            p_pid = ctk.CTkLabel(row, text="  --", width=60, font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
            p_pid.pack(side="left")
            p_name = ctk.CTkLabel(row, text="Aguardando coleta...", font=Typography.caption(), text_color=ThemeColors.TEXT_PRIMARY, anchor="w")
            p_name.pack(side="left", fill="x", expand=True)
            p_mem = ctk.CTkLabel(row, text="-- MB  ", width=120, font=Typography.caption(), text_color=ThemeColors.ACCENT_LIGHT, anchor="e")
            p_mem.pack(side="right")
            self._proc_rows.append({"pid": p_pid, "name": p_name, "mem": p_mem})

        # 8. Rodapé informativo
        status_bar = ctk.CTkFrame(self, fg_color="transparent", border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
        status_bar.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, LayoutDimensions.PAD_SM))
        ctk.CTkLabel(
            status_bar,
            text="Status: Operacional • Monitoramento assíncrono em segundo plano • Zero telemetria • Sollaris Nova v0.2.0-alpha",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_INACTIVE,
        ).pack(padx=LayoutDimensions.PAD_MD, pady=LayoutDimensions.PAD_SM)

    def update_data(
        self,
        snap: SystemSnapshot,
        procs: list[ProcessItem],
        history_cpu: list[float] | None = None,
        history_ram: list[float] | None = None,
        window_stats: dict[str, float] | None = None,
    ) -> None:
        """Atualiza valores dos widgets de Visão Geral em sub-3.5ms sem desmontar a árvore de widgets."""
        self._current_snapshot = snap

        # 1. CPU
        cpu_pct = snap.cpu.total_percent
        self._cpu_gauge.set_value(cpu_pct, max_value=100.0, display_text=f"{cpu_pct:.1f}%")

        if cpu_pct > 85.0:
            cpu_status, cpu_color = "Crítico", ThemeColors.STATUS_ERROR
        elif cpu_pct > 70.0:
            cpu_status, cpu_color = "Atenção", ThemeColors.STATUS_WARN
        else:
            cpu_status, cpu_color = "Normal", ThemeColors.STATUS_OK

        self._cpu_badge.configure(text=cpu_status, text_color=cpu_color)
        self._cpu_model_lbl.configure(text=f"• Modelo: {snap.cpu.model_name}")
        self._cpu_cores_lbl.configure(text=f"• Núcleos: {snap.cpu.core_count_physical} Físicos | {snap.cpu.core_count_logical} Lógicos")

        freq_curr = f"{snap.cpu.frequency_current_mhz:.0f} MHz" if snap.cpu.frequency_current_mhz else "--"
        freq_base = f"{snap.cpu.frequency_base_mhz:.0f} MHz" if snap.cpu.frequency_base_mhz else "--"
        self._cpu_freq_lbl.configure(text=f"• Frequência: Base: {freq_base} | Atual: {freq_curr}")

        if snap.cpu.temperature.is_available and snap.cpu.temperature.value is not None:
            self._cpu_temp_lbl.configure(text=f"• Temperatura: {snap.cpu.temperature.value:.1f} °C")
        else:
            self._cpu_temp_lbl.configure(text="• Temperatura: Sensor indisponível")

        # Chips de núcleos
        per_cpu = snap.cpu.per_cpu_percent
        for idx, lbl in enumerate(self._core_chip_labels):
            if idx < len(per_cpu):
                val = per_cpu[idx]
                col = ThemeColors.STATUS_ERROR if val > 85.0 else (ThemeColors.STATUS_WARN if val > 70.0 else ThemeColors.STATUS_OK)
                lbl.configure(text=f"N{idx+1}: {round(val)}%", text_color=col)
            else:
                lbl.configure(text=f"N{idx+1}: --", text_color=ThemeColors.TEXT_INACTIVE)

        # 2. RAM
        ram_pct = snap.ram.percent
        ram_used_str = format_bytes(snap.ram.used_bytes)
        ram_total_str = format_bytes(snap.ram.total_bytes)

        self._ram_gauge.set_value(ram_pct, max_value=100.0, display_text=f"{ram_pct:.1f}%")

        avail_gb = snap.ram.available_bytes / (1024**3)
        if ram_pct > 90.0 or avail_gb < 1.5:
            ram_status, ram_color = "Crítico", ThemeColors.STATUS_ERROR
        elif ram_pct > 80.0 or avail_gb < 2.5:
            ram_status, ram_color = "Atenção", ThemeColors.STATUS_WARN
        else:
            ram_status, ram_color = "Normal", ThemeColors.STATUS_OK

        self._ram_badge.configure(text=ram_status, text_color=ram_color)
        self._ram_used_lbl.configure(text=f"• Em Uso: {ram_used_str} ({ram_pct:.1f}%)")
        self._ram_avail_lbl.configure(text=f"• Disponível: {format_bytes(snap.ram.available_bytes)}")
        self._ram_total_lbl.configure(text=f"• Total Instalada: {ram_total_str}")

        swap_used_str = format_bytes(snap.ram.swap_used_bytes)
        swap_tot_str = format_bytes(snap.ram.swap_total_bytes)
        self._ram_swap_lbl.configure(text=f"• Paginação (Swap): {swap_used_str} / {swap_tot_str} ({snap.ram.swap_percent:.1f}%)")

        # 3. Gráfico e Estatísticas de Janela
        if history_cpu is not None and history_ram is not None:
            self._perf_chart.update_chart(history_cpu, history_ram)

        if window_stats:
            self._cpu_stats_lbl.configure(
                text=f"• Janela 60s: Média {window_stats['cpu_avg']:.1f}% | Pico {window_stats['cpu_max']:.1f}%"
            )
            self._ram_stats_lbl.configure(
                text=f"• Janela 60s: Média {window_stats['ram_avg']:.1f}% | Pico {window_stats['ram_max']:.1f}%"
            )

        # 4. Discos
        for disk in snap.disks:
            self._create_or_update_disk_row(disk)

        # 5. GPU
        self._gpu_name_lbl.configure(text=f"• GPU: {snap.gpu.name}")
        driver_txt = snap.gpu.driver_version or "Padrão do Sistema"
        self._gpu_driver_lbl.configure(text=f"• Driver: {driver_txt}")
        res_txt = snap.gpu.resolution or "Configuração Nativa"
        if snap.gpu.refresh_rate_hz:
            res_txt += f" @ {snap.gpu.refresh_rate_hz}Hz"
        self._gpu_res_lbl.configure(text=f"• Resolução: {res_txt}")

        vram_txt = format_bytes(snap.gpu.adapter_ram_bytes) if snap.gpu.adapter_ram_bytes else "Compartilhada / Integrada"
        self._gpu_vram_lbl.configure(text=f"• VRAM Estimada: {vram_txt}")

        if snap.gpu.temperature.is_available and snap.gpu.temperature.value is not None:
            self._gpu_temp_lbl.configure(text=f"• Temperatura GPU: {snap.gpu.temperature.value:.1f} °C")
        else:
            self._gpu_temp_lbl.configure(text="• Temperatura GPU: Sensor indisponível")

        # 6. Sistema
        self._sys_os_lbl.configure(text=f"• Sistema: {snap.os_name}")
        self._sys_build_lbl.configure(text=f"• Compilação: {snap.os_build} ({snap.architecture})")
        self._sys_uptime_lbl.configure(text=f"• Tempo de Atividade: {format_uptime(snap.uptime_seconds)}")

        # 7. Top Processos
        for idx, row_widgets in enumerate(self._proc_rows):
            if idx < len(procs):
                p = procs[idx]
                row_widgets["pid"].configure(text=f"  {p.pid}")
                row_widgets["name"].configure(text=p.name)
                row_widgets["mem"].configure(text=f"{format_bytes(p.memory_rss_bytes)}  ")
            else:
                row_widgets["pid"].configure(text="  --")
                row_widgets["name"].configure(text="--")
                row_widgets["mem"].configure(text="--  ")

    def _create_or_update_disk_row(self, disk: DiskPartitionMetrics) -> None:
        """Cria ou atualiza uma partição de disco garantindo reciclagem com mini RadialGauge."""
        key = disk.mountpoint
        if key not in self._disk_widget_rows:
            row_frame = ctk.CTkFrame(self._disks_container, fg_color="#141E2B", corner_radius=6)
            row_frame.pack(fill="x", pady=4)

            gauge = RadialGauge(
                row_frame,
                size=56,
                stroke_width=5,
                compact=True,
                default_accent_color=ThemeColors.STATUS_OK,
                fg_color="#141E2B",
            )
            gauge.pack(side="left", padx=(8, 12), pady=6)
            gauge.set_tooltip(lambda k=key: self._get_disk_tooltip_text(k))
            Tooltip(row_frame, lambda k=key: self._get_disk_tooltip_text(k))

            info_col = ctk.CTkFrame(row_frame, fg_color="transparent")
            info_col.pack(side="left", fill="both", expand=True, padx=(0, 12), pady=6)

            top_r = ctk.CTkFrame(info_col, fg_color="transparent")
            top_r.pack(fill="x")
            lbl_title = ctk.CTkLabel(top_r, text="", font=(Typography.FONT_FAMILY, 11, "bold"), text_color=ThemeColors.TEXT_PRIMARY)
            lbl_title.pack(side="left")
            lbl_sub = ctk.CTkLabel(top_r, text="", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED)
            lbl_sub.pack(side="right")

            lbl_detail = ctk.CTkLabel(info_col, text="", font=Typography.caption(), text_color=ThemeColors.TEXT_INACTIVE, anchor="w")
            lbl_detail.pack(fill="x", pady=(2, 0))

            self._disk_widget_rows[key] = {
                "title": lbl_title,
                "sub": lbl_sub,
                "detail": lbl_detail,
                "gauge": gauge,
            }

        widgets = self._disk_widget_rows[key]
        widgets["title"].configure(text=f"Unidade ({disk.device}) [{disk.fstype}]")
        free_str = format_bytes(disk.free_bytes)
        tot_str = format_bytes(disk.total_bytes)
        used_str = format_bytes(disk.used_bytes)
        widgets["sub"].configure(text=f"{free_str} livres de {tot_str}")
        widgets["detail"].configure(
            text=f"Espaço ocupado: {used_str} ({disk.percent:.1f}%) • Ponto de montagem: {disk.mountpoint}"
        )

        p_color = ThemeColors.STATUS_OK
        if disk.percent > 90.0 or (disk.free_bytes / (1024**3)) < 15.0:
            p_color = ThemeColors.STATUS_ERROR
        elif disk.percent > 80.0:
            p_color = ThemeColors.STATUS_WARN

        widgets["gauge"].set_value(
            disk.percent,
            max_value=100.0,
            display_text=f"{round(disk.percent)}%",
            force_color=p_color,
        )

    def _get_cpu_tooltip_text(self) -> str:
        """Retorna texto descritivo para tooltip do indicador de CPU."""
        if not self._current_snapshot:
            return "Processador: Aguardando dados..."
        c = self._current_snapshot.cpu
        freq_str = f"{c.frequency_current_mhz:.0f} MHz" if c.frequency_current_mhz else "N/A"
        return (
            f"Processador: {c.model_name or 'Detectado'}\n"
            f"Carga Total: {c.total_percent:.1f}%\n"
            f"Frequência Atual: {freq_str}\n"
            f"Topologia: {c.physical_cores} Físicos / {c.logical_cores} Lógicos"
        )

    def _get_ram_tooltip_text(self) -> str:
        """Retorna texto descritivo para tooltip do indicador de RAM."""
        if not self._current_snapshot:
            return "Memória RAM: Aguardando dados..."
        r = self._current_snapshot.ram
        used = format_bytes(r.used_bytes)
        avail = format_bytes(r.available_bytes)
        total = format_bytes(r.total_bytes)
        swap_used = format_bytes(r.swap_used_bytes)
        swap_tot = format_bytes(r.swap_total_bytes)
        return (
            f"Memória RAM: {r.percent:.1f}% em uso\n"
            f"Utilizada: {used} de {total}\n"
            f"Disponível Real: {avail}\n"
            f"Arquivo de Paginação (Swap): {swap_used} / {swap_tot} ({r.swap_percent:.1f}%)"
        )

    def _get_core_tooltip_text(self, core_idx: int) -> str:
        """Retorna texto descritivo para tooltip de cada núcleo lógico."""
        if not self._current_snapshot or core_idx >= len(self._current_snapshot.cpu.per_cpu_percent):
            return f"Núcleo Lógico #{core_idx + 1}: Sem dados"
        pct = self._current_snapshot.cpu.per_cpu_percent[core_idx]
        return f"Núcleo Lógico #{core_idx + 1}\nCarga Instantânea: {pct:.1f}%"

    def _get_disk_tooltip_text(self, mountpoint: str) -> str:
        """Retorna texto descritivo para tooltip de partição de disco."""
        if not self._current_snapshot:
            return f"Partição {mountpoint}: Aguardando dados..."
        for d in self._current_snapshot.disks:
            if d.mountpoint == mountpoint:
                free = format_bytes(d.free_bytes)
                tot = format_bytes(d.total_bytes)
                used = format_bytes(d.used_bytes)
                return (
                    f"Partição: {d.mountpoint} ({d.device})\n"
                    f"Sistema de Arquivos: {d.fstype}\n"
                    f"Uso: {d.percent:.1f}%\n"
                    f"Espaço Ocupado: {used}\n"
                    f"Espaço Livre: {free} de {tot}"
                )
        return f"Partição {mountpoint}"
