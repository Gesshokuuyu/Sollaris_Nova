"""Janela principal da aplicação desktop — Sollaris Nova (PC Optimizer).

Apresenta a interface gráfica técnica em CustomTkinter, dividida em
menu lateral e painel de métricas de hardware da Fase 1.
"""

import logging
import tkinter as tk
from datetime import datetime
from pathlib import Path

import customtkinter as ctk

from app.components.sidebar import Sidebar
from app.theme import LayoutDimensions, ThemeColors, Typography
from core.hardware import (
    HardwareCollector,
    SystemSnapshot,
    format_bytes,
    format_frequency,
    format_uptime,
)

logger = logging.getLogger("sollaris_nova.window")


class MainWindow(ctk.CTk):
    """Janela principal do Sollaris Nova."""

    def __init__(self) -> None:
        super().__init__()

        self.title("PC Optimizer — Sollaris Nova")
        self.geometry(f"{LayoutDimensions.WINDOW_DEFAULT_WIDTH}x{LayoutDimensions.WINDOW_DEFAULT_HEIGHT}")
        self.minsize(LayoutDimensions.WINDOW_MIN_WIDTH, LayoutDimensions.WINDOW_MIN_HEIGHT)
        self.configure(fg_color=ThemeColors.BG_MAIN)

        self._collector = HardwareCollector()
        self._set_window_icon()

        # Grid principal: Coluna 0 (Sidebar 220px), Coluna 1 (Área de conteúdo expansível)
        self.grid_columnconfigure(0, weight=0, minsize=LayoutDimensions.SIDEBAR_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._sidebar = Sidebar(self, on_navigate=self._on_navigation)
        self._sidebar.grid(row=0, column=0, sticky="nsew")

        self._build_content_area()
        self.refresh_metrics()

    def _set_window_icon(self) -> None:
        """Aplica o ícone oficial à janela e barra de tarefas do Windows."""
        assets_dir = Path(__file__).resolve().parent.parent / "assets"
        icon_path = assets_dir / "sollaris_nova.ico"
        if not icon_path.exists():
            icon_path = assets_dir / "icon.ico"

        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except (OSError, tk.TclError) as exc:
                logger.debug("Falha ao configurar ícone da janela: %s", exc)

    def _on_navigation(self, route_id: str) -> None:
        """Trata cliques de navegação na barra lateral."""
        logger.debug("Navegação acionada: %s", route_id)

    def _build_content_area(self) -> None:
        """Constrói a área principal com scroll e painéis técnicos."""
        self._scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=ThemeColors.BG_MAIN,
            corner_radius=0,
        )
        self._scroll_frame.grid(row=0, column=1, sticky="nsew", padx=LayoutDimensions.PAD_LG, pady=LayoutDimensions.PAD_MD)
        self._scroll_frame.grid_columnconfigure(0, weight=1)
        self._scroll_frame.grid_columnconfigure(1, weight=1)

        self._build_header_bar()
        self._build_cpu_and_ram_cards()
        self._build_storage_card()
        self._build_gpu_and_system_cards()
        self._build_bottom_status_bar()

    def _build_header_bar(self) -> None:
        """Constrói o cabeçalho técnico com título, status e botão de atualização."""
        header_frame = ctk.CTkFrame(self._scroll_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, LayoutDimensions.PAD_LG))
        header_frame.grid_columnconfigure(0, weight=1)

        titles_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        titles_box.grid(row=0, column=0, sticky="w")

        title_label = ctk.CTkLabel(
            titles_box,
            text="Visão Geral",
            font=Typography.header_title(),
            text_color=ThemeColors.TEXT_PRIMARY,
        )
        title_label.pack(anchor="w")

        self._timestamp_label = ctk.CTkLabel(
            titles_box,
            text="Última amostragem: Carregando...",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
        )
        self._timestamp_label.pack(anchor="w")

        actions_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_box.grid(row=0, column=1, sticky="e")

        self._global_status_badge = ctk.CTkLabel(
            actions_box,
            text="● Sistema Estável",
            font=Typography.body_regular(),
            text_color=ThemeColors.STATUS_OK,
            corner_radius=LayoutDimensions.CORNER_RADIUS_BUTTON,
            fg_color=ThemeColors.BG_SURFACE,
            padx=12,
            pady=4,
        )
        self._global_status_badge.pack(side="left", padx=(0, LayoutDimensions.PAD_MD))

        self._refresh_btn = ctk.CTkButton(
            actions_box,
            text="Atualizar Agora",
            font=Typography.body_regular(),
            fg_color=ThemeColors.BG_SURFACE,
            hover_color=ThemeColors.BG_CARD_HOVER,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            text_color=ThemeColors.TEXT_PRIMARY,
            height=32,
            command=self.refresh_metrics,
        )
        self._refresh_btn.pack(side="left")

    def _build_cpu_and_ram_cards(self) -> None:
        """Constrói os cartões de CPU e Memória RAM na linha superior."""
        # 1. Cartão CPU
        self._cpu_card = ctk.CTkFrame(
            self._scroll_frame,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._cpu_card.grid(row=1, column=0, sticky="nsew", padx=(0, LayoutDimensions.PAD_MD), pady=(0, LayoutDimensions.PAD_LG))

        cpu_top = ctk.CTkFrame(self._cpu_card, fg_color="transparent")
        cpu_top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_LG, 4))

        ctk.CTkLabel(
            cpu_top,
            text="PROCESSADOR (CPU)",
            font=Typography.card_title(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(side="left")

        self._cpu_badge = ctk.CTkLabel(
            cpu_top,
            text="Normal",
            font=Typography.caption(),
            text_color=ThemeColors.STATUS_OK,
        )
        self._cpu_badge.pack(side="right")

        self._cpu_big_val = ctk.CTkLabel(
            self._cpu_card,
            text="-- %",
            font=Typography.metric_value(),
            text_color=ThemeColors.TEXT_PRIMARY,
        )
        self._cpu_big_val.pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_SM))

        self._cpu_progress = ctk.CTkProgressBar(
            self._cpu_card,
            height=6,
            corner_radius=2,
            fg_color="#1C2736",
            progress_color=ThemeColors.STATUS_OK,
        )
        self._cpu_progress.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))
        self._cpu_progress.set(0)

        cpu_details = ctk.CTkFrame(self._cpu_card, fg_color="transparent")
        cpu_details.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_LG))

        self._cpu_model_lbl = ctk.CTkLabel(cpu_details, text="• Modelo: Detectando...", font=Typography.caption(), text_color=ThemeColors.TEXT_PRIMARY, anchor="w")
        self._cpu_model_lbl.pack(fill="x", pady=1)

        self._cpu_cores_lbl = ctk.CTkLabel(cpu_details, text="• Núcleos: -- Físicos | -- Lógicos", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._cpu_cores_lbl.pack(fill="x", pady=1)

        self._cpu_freq_lbl = ctk.CTkLabel(cpu_details, text="• Frequência: Base: -- | Atual: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._cpu_freq_lbl.pack(fill="x", pady=1)

        self._cpu_temp_lbl = ctk.CTkLabel(cpu_details, text="• Temperatura: Sensor indisponível", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._cpu_temp_lbl.pack(fill="x", pady=1)

        # 2. Cartão RAM
        self._ram_card = ctk.CTkFrame(
            self._scroll_frame,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._ram_card.grid(row=1, column=1, sticky="nsew", padx=(LayoutDimensions.PAD_MD, 0), pady=(0, LayoutDimensions.PAD_LG))

        ram_top = ctk.CTkFrame(self._ram_card, fg_color="transparent")
        ram_top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_LG, 4))

        ctk.CTkLabel(
            ram_top,
            text="MEMÓRIA RAM",
            font=Typography.card_title(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(side="left")

        self._ram_badge = ctk.CTkLabel(
            ram_top,
            text="Normal",
            font=Typography.caption(),
            text_color=ThemeColors.STATUS_OK,
        )
        self._ram_badge.pack(side="right")

        self._ram_big_val = ctk.CTkLabel(
            self._ram_card,
            text="-- / --",
            font=(Typography.FONT_FAMILY, 20, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY,
        )
        self._ram_big_val.pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(6, LayoutDimensions.PAD_SM))

        self._ram_progress = ctk.CTkProgressBar(
            self._ram_card,
            height=6,
            corner_radius=2,
            fg_color="#1C2736",
            progress_color=ThemeColors.STATUS_OK,
        )
        self._ram_progress.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))
        self._ram_progress.set(0)

        ram_details = ctk.CTkFrame(self._ram_card, fg_color="transparent")
        ram_details.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_LG))

        self._ram_used_lbl = ctk.CTkLabel(ram_details, text="• Em Uso: --", font=Typography.caption(), text_color=ThemeColors.TEXT_PRIMARY, anchor="w")
        self._ram_used_lbl.pack(fill="x", pady=1)

        self._ram_avail_lbl = ctk.CTkLabel(ram_details, text="• Disponível: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._ram_avail_lbl.pack(fill="x", pady=1)

        self._ram_total_lbl = ctk.CTkLabel(ram_details, text="• Total Instalada: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._ram_total_lbl.pack(fill="x", pady=1)

        note_lbl = ctk.CTkLabel(
            ram_details,
            text="A memória disponível inclui cache reutilizável pelo sistema.",
            font=(Typography.FONT_FAMILY, 9, "italic"),
            text_color=ThemeColors.TEXT_INACTIVE,
            anchor="w",
        )
        note_lbl.pack(fill="x", pady=(4, 0))

    def _build_storage_card(self) -> None:
        """Constrói o cartão de armazenamento local com todas as partições detectadas."""
        self._storage_card = ctk.CTkFrame(
            self._scroll_frame,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._storage_card.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, LayoutDimensions.PAD_LG))

        storage_top = ctk.CTkFrame(self._storage_card, fg_color="transparent")
        storage_top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_LG, LayoutDimensions.PAD_SM))

        ctk.CTkLabel(
            storage_top,
            text="ARMAZENAMENTO LOCAL (PARTIÇÕES)",
            font=Typography.card_title(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(side="left")

        self._disks_container = ctk.CTkFrame(self._storage_card, fg_color="transparent")
        self._disks_container.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_LG))

    def _build_gpu_and_system_cards(self) -> None:
        """Constrói os cartões inferiores de GPU e Resumo do Sistema."""
        # Cartão GPU
        self._gpu_card = ctk.CTkFrame(
            self._scroll_frame,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._gpu_card.grid(row=3, column=0, sticky="nsew", padx=(0, LayoutDimensions.PAD_MD), pady=(0, LayoutDimensions.PAD_LG))

        gpu_top = ctk.CTkFrame(self._gpu_card, fg_color="transparent")
        gpu_top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_LG, 4))

        ctk.CTkLabel(
            gpu_top,
            text="PLACA DE VÍDEO & SENSORES",
            font=Typography.card_title(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(side="left")

        gpu_details = ctk.CTkFrame(self._gpu_card, fg_color="transparent")
        gpu_details.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=LayoutDimensions.PAD_SM)

        self._gpu_name_lbl = ctk.CTkLabel(gpu_details, text="• GPU: Detectando...", font=Typography.caption(), text_color=ThemeColors.TEXT_PRIMARY, anchor="w")
        self._gpu_name_lbl.pack(fill="x", pady=2)

        self._gpu_driver_lbl = ctk.CTkLabel(gpu_details, text="• Driver: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._gpu_driver_lbl.pack(fill="x", pady=2)

        self._gpu_temp_lbl = ctk.CTkLabel(gpu_details, text="• Temperatura GPU: Sensor indisponível", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._gpu_temp_lbl.pack(fill="x", pady=2)

        self._sensors_status_lbl = ctk.CTkLabel(gpu_details, text="• Interface WMI: Operante", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._sensors_status_lbl.pack(fill="x", pady=2)

        # Cartão Resumo do Sistema
        self._sys_card = ctk.CTkFrame(
            self._scroll_frame,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._sys_card.grid(row=3, column=1, sticky="nsew", padx=(LayoutDimensions.PAD_MD, 0), pady=(0, LayoutDimensions.PAD_LG))

        sys_top = ctk.CTkFrame(self._sys_card, fg_color="transparent")
        sys_top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_LG, 4))

        ctk.CTkLabel(
            sys_top,
            text="SISTEMA & AMBIENTE",
            font=Typography.card_title(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(side="left")

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

    def _build_bottom_status_bar(self) -> None:
        """Constrói a barra de status técnica no rodapé."""
        status_bar = ctk.CTkFrame(
            self._scroll_frame,
            fg_color="transparent",
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        status_bar.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, LayoutDimensions.PAD_SM))

        ctk.CTkLabel(
            status_bar,
            text="Status: Operacional • Executando localmente sem privilégios administrativos • Sollaris Nova v0.1.0-alpha",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_INACTIVE,
        ).pack(padx=LayoutDimensions.PAD_MD, pady=LayoutDimensions.PAD_SM)

    def refresh_metrics(self) -> None:
        """Coleta métricas reais do hardware e atualiza todos os cartões visuais."""
        try:
            snapshot = self._collector.collect_snapshot()
            self._update_ui_with_snapshot(snapshot)
        except Exception:
            logger.exception("Erro ao atualizar métricas de hardware.")

    def _update_ui_with_snapshot(self, snap: SystemSnapshot) -> None:
        """Distribui os dados do snapshot entre os componentes da interface."""
        now_str = datetime.now().astimezone().strftime("%H:%M:%S")
        self._timestamp_label.configure(text=f"Última amostragem: {now_str}")

        # 1. Atualização CPU
        cpu_pct = snap.cpu.total_percent
        self._cpu_big_val.configure(text=f"{cpu_pct:.1f} %")
        self._cpu_progress.set(cpu_pct / 100.0)

        if cpu_pct > 85.0:
            cpu_status, cpu_color = "Crítico", ThemeColors.STATUS_ERROR
        elif cpu_pct > 70.0:
            cpu_status, cpu_color = "Elevado", ThemeColors.STATUS_WARN
        else:
            cpu_status, cpu_color = "Normal", ThemeColors.STATUS_OK

        self._cpu_badge.configure(text=cpu_status, text_color=cpu_color)
        self._cpu_progress.configure(progress_color=cpu_color)

        self._cpu_model_lbl.configure(text=f"• Modelo: {snap.cpu.model_name}")
        self._cpu_cores_lbl.configure(text=f"• Núcleos: {snap.cpu.core_count_physical} Físicos | {snap.cpu.core_count_logical} Lógicos")
        freq_str = f"Base: {format_frequency(snap.cpu.frequency_base_mhz)} | Atual: {format_frequency(snap.cpu.frequency_current_mhz)}"
        self._cpu_freq_lbl.configure(text=f"• Frequência: {freq_str}")

        if snap.cpu.temperature.is_available and snap.cpu.temperature.value is not None:
            self._cpu_temp_lbl.configure(
                text=f"• Temperatura: {snap.cpu.temperature.value:.1f} °C [ACPI]",
                text_color=ThemeColors.TEXT_PRIMARY,
            )
        else:
            self._cpu_temp_lbl.configure(
                text="• Temperatura: Sensor indisponível",
                text_color=ThemeColors.TEXT_MUTED,
            )

        # 2. Atualização RAM
        ram_used_str = format_bytes(snap.ram.used_bytes)
        ram_total_str = format_bytes(snap.ram.total_bytes)
        ram_pct = snap.ram.percent

        self._ram_big_val.configure(text=f"{ram_used_str} / {ram_total_str} ({ram_pct:.1f}%)")
        self._ram_progress.set(ram_pct / 100.0)

        # Critério de pressão de memória: < 10% ou < 1.5GB
        avail_gb = snap.ram.available_bytes / (1024**3)
        if ram_pct > 90.0 or avail_gb < 1.5:
            ram_status, ram_color = "Crítico", ThemeColors.STATUS_ERROR
        elif ram_pct > 80.0 or avail_gb < 2.5:
            ram_status, ram_color = "Atenção", ThemeColors.STATUS_WARN
        else:
            ram_status, ram_color = "Normal", ThemeColors.STATUS_OK

        self._ram_badge.configure(text=ram_status, text_color=ram_color)
        self._ram_progress.configure(progress_color=ram_color)

        self._ram_used_lbl.configure(text=f"• Em Uso: {ram_used_str} ({ram_pct:.1f}%)")
        self._ram_avail_lbl.configure(text=f"• Disponível: {format_bytes(snap.ram.available_bytes)}")
        self._ram_total_lbl.configure(text=f"• Total Instalada: {ram_total_str}")

        # 3. Atualização Discos
        for widget in self._disks_container.winfo_children():
            widget.destroy()

        for disk in snap.disks:
            disk_row = ctk.CTkFrame(self._disks_container, fg_color="transparent")
            disk_row.pack(fill="x", pady=4)

            top_row = ctk.CTkFrame(disk_row, fg_color="transparent")
            top_row.pack(fill="x")

            ctk.CTkLabel(
                top_row,
                text=f"Unidade ({disk.device}) [{disk.fstype}]",
                font=(Typography.FONT_FAMILY, 11, "bold"),
                text_color=ThemeColors.TEXT_PRIMARY,
            ).pack(side="left")

            free_str = format_bytes(disk.free_bytes)
            tot_str = format_bytes(disk.total_bytes)
            ctk.CTkLabel(
                top_row,
                text=f"{free_str} livres de {tot_str} ({disk.percent:.1f}% usado)",
                font=Typography.caption(),
                text_color=ThemeColors.TEXT_MUTED,
            ).pack(side="right")

            p_color = ThemeColors.STATUS_OK
            if disk.percent > 90.0 or (disk.free_bytes / (1024**3)) < 15.0:
                p_color = ThemeColors.STATUS_ERROR
            elif disk.percent > 80.0:
                p_color = ThemeColors.STATUS_WARN

            p_bar = ctk.CTkProgressBar(
                disk_row,
                height=6,
                corner_radius=2,
                fg_color="#1C2736",
                progress_color=p_color,
            )
            p_bar.pack(fill="x", pady=(2, 6))
            p_bar.set(disk.percent / 100.0)

        # 4. Atualização GPU
        self._gpu_name_lbl.configure(text=f"• GPU: {snap.gpu.name}")
        driver_txt = snap.gpu.driver_version or "Padrão do Sistema"
        self._gpu_driver_lbl.configure(text=f"• Driver: {driver_txt}")
        if snap.gpu.temperature.is_available and snap.gpu.temperature.value is not None:
            self._gpu_temp_lbl.configure(text=f"• Temperatura GPU: {snap.gpu.temperature.value:.1f} °C")
        else:
            self._gpu_temp_lbl.configure(text="• Temperatura GPU: Sensor indisponível")

        # 5. Atualização Sistema
        self._sys_os_lbl.configure(text=f"• Sistema: {snap.os_name}")
        self._sys_build_lbl.configure(text=f"• Compilação: {snap.os_build} ({snap.architecture})")
        self._sys_uptime_lbl.configure(text=f"• Tempo de Atividade: {format_uptime(snap.uptime_seconds)}")

        # Status Global Badge
        if cpu_status == "Crítico" or ram_status == "Crítico":
            self._global_status_badge.configure(text="✕ Atenção Requerida", text_color=ThemeColors.STATUS_ERROR)
        elif cpu_status == "Elevado" or ram_status == "Atenção":
            self._global_status_badge.configure(text="▲ Carga Elevada", text_color=ThemeColors.STATUS_WARN)
        else:
            self._global_status_badge.configure(text="● Sistema Estável", text_color=ThemeColors.STATUS_OK)
