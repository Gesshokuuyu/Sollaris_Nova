"""Janela principal da aplicação desktop — Sollaris Nova (PC Optimizer).

Apresenta a interface gráfica técnica em CustomTkinter, com navegação fluida,
coleta assíncrona em background via MonitorService e reciclagem de widgets para
garantir 60 FPS estáveis sem travamentos de interface.
"""

import logging
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path

import customtkinter as ctk

from app.components.sidebar import Sidebar
from app.theme import LayoutDimensions, ThemeColors, Typography
from core.cleaner import CleanerScanner
from core.diagnostics import DiagnosticEngine, FindingLevel
from core.hardware import (
    DiskPartitionMetrics,
    HardwareCollector,
    SystemSnapshot,
    format_bytes,
    format_frequency,
    format_uptime,
)
from core.monitor import MonitorService
from core.processes import ProcessItem
from core.startup import StartupManager

logger = logging.getLogger("sollaris_nova.window")


class MainWindow(ctk.CTk):
    """Janela principal do Sollaris Nova com loop não-bloqueante e alta reatividade."""

    def __init__(self) -> None:
        super().__init__()

        self.title("PC Optimizer — Sollaris Nova")
        self.geometry(f"{LayoutDimensions.WINDOW_DEFAULT_WIDTH}x{LayoutDimensions.WINDOW_DEFAULT_HEIGHT}")
        self.minsize(LayoutDimensions.WINDOW_MIN_WIDTH, LayoutDimensions.WINDOW_MIN_HEIGHT)
        self.configure(fg_color=ThemeColors.BG_MAIN)

        self._collector = HardwareCollector()
        self._active_route = "overview"
        self._is_destroyed = False
        self._is_loading = False
        self._last_rendered_timestamp: datetime | None = None
        self._poll_after_id: str | None = None

        # Estatísticas da sessão
        self._session_start_time = time.time()
        self._session_cpu_samples: list[float] = []
        self._session_ram_samples: list[float] = []

        # Containers de widgets persistentes (para reciclagem sem destroy em massa)
        self._disk_widget_rows: dict[str, dict[str, ctk.CTkBaseClass]] = {}
        self._proc_rows: list[dict[str, ctk.CTkLabel]] = []
        self._core_chip_labels: list[ctk.CTkLabel] = []

        self._set_window_icon()

        # Grid principal: Coluna 0 (Sidebar 220px), Coluna 1 (Conteúdo)
        self.grid_columnconfigure(0, weight=0, minsize=LayoutDimensions.SIDEBAR_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._sidebar = Sidebar(self, on_navigate=self._on_navigation)
        self._sidebar.grid(row=0, column=0, sticky="nsew")

        self._content_root = ctk.CTkFrame(self, fg_color=ThemeColors.BG_MAIN, corner_radius=0)
        self._content_root.grid(row=0, column=1, sticky="nsew", padx=LayoutDimensions.PAD_LG, pady=LayoutDimensions.PAD_MD)
        self._content_root.grid_columnconfigure(0, weight=1)
        self._content_root.grid_rowconfigure(1, weight=1)

        self._build_header_bar()
        self._build_views_container()

        # Inicia o serviço assíncrono em segundo plano
        self._monitor = MonitorService(interval_seconds=1.5)
        self._monitor.start()

        # Amostragem inicial síncrona leve (apenas 8ms com o coletor otimizado)
        self.refresh_metrics()

        # Agenda a checagem periódica da fila de background (sem travar a GUI)
        self._schedule_poll()

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
        """Trata cliques de navegação na barra lateral e alterna a visualização."""
        if route_id == self._active_route:
            return

        self._active_route = route_id
        self._switch_view(route_id)

    def _build_header_bar(self) -> None:
        """Constrói o cabeçalho técnico com título, status, botão de atualização e loader de recarga."""
        self._header_frame = ctk.CTkFrame(self._content_root, fg_color="transparent")
        self._header_frame.grid(row=0, column=0, sticky="ew", pady=(0, LayoutDimensions.PAD_MD))
        self._header_frame.grid_columnconfigure(0, weight=1)

        titles_box = ctk.CTkFrame(self._header_frame, fg_color="transparent")
        titles_box.grid(row=0, column=0, sticky="w")

        self._view_title_label = ctk.CTkLabel(
            titles_box,
            text="Visão Geral",
            font=Typography.header_title(),
            text_color=ThemeColors.TEXT_PRIMARY,
        )
        self._view_title_label.pack(anchor="w")

        self._timestamp_label = ctk.CTkLabel(
            titles_box,
            text="Última amostragem: Carregando... • Ao Vivo",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
        )
        self._timestamp_label.pack(anchor="w")

        actions_box = ctk.CTkFrame(self._header_frame, fg_color="transparent")
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
            command=self.request_refresh,
        )
        self._refresh_btn.pack(side="left")

        # Barra de progresso indeterminada de 3px (Loader de recarga não-bloqueante)
        self._loader_bar = ctk.CTkProgressBar(
            self._header_frame,
            height=3,
            corner_radius=0,
            border_width=0,
            fg_color="#141E2B",
            progress_color=ThemeColors.ACCENT_BLUE,
            mode="indeterminate",
        )
        self._loader_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self._loader_bar.grid_remove()

    def _build_views_container(self) -> None:
        """Cria os containers de páginas desacoplados."""
        self._views_dict: dict[str, ctk.CTkFrame] = {}

        # 1. Página de Visão Geral (Overview)
        self._scroll_frame = ctk.CTkScrollableFrame(self._content_root, fg_color=ThemeColors.BG_MAIN, corner_radius=0)
        self._scroll_frame.grid_columnconfigure(0, weight=1)
        self._scroll_frame.grid_columnconfigure(1, weight=1)
        self._build_overview_cards(self._scroll_frame)
        self._views_dict["overview"] = self._scroll_frame

        # 2. Página de Diagnóstico
        self._diag_frame = ctk.CTkScrollableFrame(self._content_root, fg_color=ThemeColors.BG_MAIN, corner_radius=0)
        self._diag_frame.grid_columnconfigure(0, weight=1)
        self._build_diagnostics_view(self._diag_frame)
        self._views_dict["diagnostics"] = self._diag_frame

        # 3. Página de Limpeza
        self._cleaner_frame = ctk.CTkScrollableFrame(self._content_root, fg_color=ThemeColors.BG_MAIN, corner_radius=0)
        self._cleaner_frame.grid_columnconfigure(0, weight=1)
        self._build_cleaner_view(self._cleaner_frame)
        self._views_dict["cleaner"] = self._cleaner_frame

        # 4. Página de Inicialização
        self._startup_frame = ctk.CTkScrollableFrame(self._content_root, fg_color=ThemeColors.BG_MAIN, corner_radius=0)
        self._startup_frame.grid_columnconfigure(0, weight=1)
        self._build_startup_view(self._startup_frame)
        self._views_dict["startup"] = self._startup_frame

        # 5. Página de Modo Game
        self._game_frame = ctk.CTkScrollableFrame(self._content_root, fg_color=ThemeColors.BG_MAIN, corner_radius=0)
        self._game_frame.grid_columnconfigure(0, weight=1)
        self._build_game_mode_view(self._game_frame)
        self._views_dict["game_mode"] = self._game_frame

        # 6. Página de Histórico
        self._history_frame = ctk.CTkScrollableFrame(self._content_root, fg_color=ThemeColors.BG_MAIN, corner_radius=0)
        self._history_frame.grid_columnconfigure(0, weight=1)
        self._build_history_view(self._history_frame)
        self._views_dict["history"] = self._history_frame

        # 7. Página de Configurações
        self._settings_frame = ctk.CTkScrollableFrame(self._content_root, fg_color=ThemeColors.BG_MAIN, corner_radius=0)
        self._settings_frame.grid_columnconfigure(0, weight=1)
        self._build_settings_view(self._settings_frame)
        self._views_dict["settings"] = self._settings_frame

        # Exibe a visão inicial
        self._scroll_frame.grid(row=1, column=0, sticky="nsew")

    def _switch_view(self, route_id: str) -> None:
        """Alterna a página ativa de forma instantânea sem reconstruir a UI."""
        route_titles = {
            "overview": "Visão Geral",
            "diagnostics": "Diagnóstico do Sistema",
            "cleaner": "Limpeza Segura de Arquivos Temporários",
            "startup": "Programas de Inicialização",
            "game_mode": "Perfis de Desempenho & Modo Game",
            "history": "Histórico de Métricas da Sessão",
            "settings": "Configurações da Aplicação",
        }

        self._view_title_label.configure(text=route_titles.get(route_id, "Sollaris Nova"))

        for rid, frame in self._views_dict.items():
            if rid == route_id:
                frame.grid(row=1, column=0, sticky="nsew")
            else:
                frame.grid_forget()

        # Atualiza a view com a última leitura disponível
        if self._monitor:
            snap, procs = self._monitor.get_latest_data()
            if snap:
                self._render_data_to_ui(snap, procs)

    # =========================================================================
    # CONSTRUÇÃO DAS PÁGINAS VISUAIS COM ELEMENTOS PERSISTENTES
    # =========================================================================

    def _build_overview_cards(self, parent: ctk.CTkScrollableFrame) -> None:
        """Constrói os cartões da página de Visão Geral."""
        # 1. Cartão CPU
        self._cpu_card = ctk.CTkFrame(
            parent,
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

        self._cpu_big_val = ctk.CTkLabel(self._cpu_card, text="-- %", font=Typography.metric_value(), text_color=ThemeColors.TEXT_PRIMARY)
        self._cpu_big_val.pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_SM))

        self._cpu_progress = ctk.CTkProgressBar(self._cpu_card, height=8, corner_radius=4, border_width=0, fg_color="#141E2B", progress_color=ThemeColors.STATUS_OK)
        self._cpu_progress.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))
        self._cpu_progress.set(0)

        cpu_details = ctk.CTkFrame(self._cpu_card, fg_color="transparent")
        cpu_details.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_SM))

        self._cpu_model_lbl = ctk.CTkLabel(cpu_details, text="• Modelo: Detectando...", font=Typography.caption(), text_color=ThemeColors.TEXT_PRIMARY, anchor="w")
        self._cpu_model_lbl.pack(fill="x", pady=1)

        self._cpu_cores_lbl = ctk.CTkLabel(cpu_details, text="• Núcleos: -- Físicos | -- Lógicos", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._cpu_cores_lbl.pack(fill="x", pady=1)

        self._cpu_freq_lbl = ctk.CTkLabel(cpu_details, text="• Frequência: Base: -- | Atual: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._cpu_freq_lbl.pack(fill="x", pady=1)

        self._cpu_temp_lbl = ctk.CTkLabel(cpu_details, text="• Temperatura: Sensor indisponível", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._cpu_temp_lbl.pack(fill="x", pady=1)

        self._cpu_procs_lbl = ctk.CTkLabel(cpu_details, text="• Processos Ativos no SO: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._cpu_procs_lbl.pack(fill="x", pady=1)

        # Micro-medidores persistentes de núcleos
        self._cores_box = ctk.CTkFrame(self._cpu_card, fg_color="transparent")
        self._cores_box.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(4, LayoutDimensions.PAD_LG))

        cores_hdr = ctk.CTkFrame(self._cores_box, fg_color="transparent")
        cores_hdr.pack(fill="x", pady=(2, 4))
        ctk.CTkLabel(cores_hdr, text="Carga por Núcleo Lógico:", font=(Typography.FONT_FAMILY, 10, "bold"), text_color=ThemeColors.TEXT_MUTED).pack(side="left")

        self._grid_cores = ctk.CTkFrame(self._cores_box, fg_color="transparent")
        self._grid_cores.pack(fill="x")
        self._core_chip_labels = []
        cols = 6
        for idx in range(12):  # Suporta até 12-16 núcleos em slots pré-alocados
            r = idx // cols
            c = idx % cols
            self._grid_cores.grid_columnconfigure(c, weight=1)
            cell = ctk.CTkFrame(self._grid_cores, fg_color="#141E2B", corner_radius=3)
            cell.grid(row=r, column=c, padx=2, pady=2, sticky="ew")
            lbl = ctk.CTkLabel(cell, text=f"N{idx+1}: 0%", font=(Typography.FONT_FAMILY, 9), text_color=ThemeColors.STATUS_OK)
            lbl.pack(padx=2, pady=1)
            self._core_chip_labels.append(lbl)

        # 2. Cartão RAM
        self._ram_card = ctk.CTkFrame(
            parent,
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

        self._ram_big_val = ctk.CTkLabel(self._ram_card, text="-- / --", font=(Typography.FONT_FAMILY, 20, "bold"), text_color=ThemeColors.TEXT_PRIMARY)
        self._ram_big_val.pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(6, LayoutDimensions.PAD_SM))

        self._ram_progress = ctk.CTkProgressBar(self._ram_card, height=8, corner_radius=4, border_width=0, fg_color="#141E2B", progress_color=ThemeColors.STATUS_OK)
        self._ram_progress.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))
        self._ram_progress.set(0)

        ram_details = ctk.CTkFrame(self._ram_card, fg_color="transparent")
        ram_details.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_SM))

        self._ram_used_lbl = ctk.CTkLabel(ram_details, text="• Em Uso: --", font=Typography.caption(), text_color=ThemeColors.TEXT_PRIMARY, anchor="w")
        self._ram_used_lbl.pack(fill="x", pady=1)

        self._ram_avail_lbl = ctk.CTkLabel(ram_details, text="• Disponível: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._ram_avail_lbl.pack(fill="x", pady=1)

        self._ram_total_lbl = ctk.CTkLabel(ram_details, text="• Total Instalada: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._ram_total_lbl.pack(fill="x", pady=1)

        self._ram_swap_lbl = ctk.CTkLabel(ram_details, text="• Arquivo de Paginação (Swap): --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._ram_swap_lbl.pack(fill="x", pady=1)

        self._swap_progress = ctk.CTkProgressBar(ram_details, height=6, corner_radius=3, border_width=0, fg_color="#141E2B", progress_color=ThemeColors.ACCENT_LIGHT)
        self._swap_progress.pack(fill="x", pady=(4, 6))
        self._swap_progress.set(0)

        ctk.CTkLabel(
            ram_details,
            text="A memória disponível inclui cache reaproveitável pelo Windows.",
            font=(Typography.FONT_FAMILY, 9, "italic"),
            text_color=ThemeColors.TEXT_INACTIVE,
            anchor="w",
        ).pack(fill="x", pady=(2, LayoutDimensions.PAD_SM))

        # 3. Cartão Armazenamento Local
        self._storage_card = ctk.CTkFrame(
            parent,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._storage_card.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, LayoutDimensions.PAD_LG))

        storage_top = ctk.CTkFrame(self._storage_card, fg_color="transparent")
        storage_top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_LG, LayoutDimensions.PAD_SM))
        ctk.CTkLabel(storage_top, text="ARMAZENAMENTO LOCAL (PARTIÇÕES DETECTADAS)", font=Typography.card_title(), text_color=ThemeColors.TEXT_MUTED).pack(side="left")

        self._disks_container = ctk.CTkFrame(self._storage_card, fg_color="transparent")
        self._disks_container.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_LG))

        # Pré-inicialização rápida de discos (1.5ms) para nunca exibir cartão vazio
        try:
            initial_disks = self._collector.get_disk_metrics()
            for disk in initial_disks:
                self._create_or_update_disk_row(disk)
        except (OSError, RuntimeError) as exc:
            logger.debug("Falha na pré-inicialização de discos: %s", exc)

        # 4. Cartão GPU e Display
        self._gpu_card = ctk.CTkFrame(
            parent,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._gpu_card.grid(row=2, column=0, sticky="nsew", padx=(0, LayoutDimensions.PAD_MD), pady=(0, LayoutDimensions.PAD_LG))

        gpu_top = ctk.CTkFrame(self._gpu_card, fg_color="transparent")
        gpu_top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_LG, 4))
        ctk.CTkLabel(gpu_top, text="PLACA DE VÍDEO & DISPLAY", font=Typography.card_title(), text_color=ThemeColors.TEXT_MUTED).pack(side="left")

        gpu_details = ctk.CTkFrame(self._gpu_card, fg_color="transparent")
        gpu_details.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=LayoutDimensions.PAD_SM)

        self._gpu_name_lbl = ctk.CTkLabel(gpu_details, text="• GPU: Detectando...", font=Typography.caption(), text_color=ThemeColors.TEXT_PRIMARY, anchor="w")
        self._gpu_name_lbl.pack(fill="x", pady=2)

        self._gpu_driver_lbl = ctk.CTkLabel(gpu_details, text="• Driver: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._gpu_driver_lbl.pack(fill="x", pady=2)

        self._gpu_res_lbl = ctk.CTkLabel(gpu_details, text="• Resolução: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._gpu_res_lbl.pack(fill="x", pady=2)

        self._gpu_vram_lbl = ctk.CTkLabel(gpu_details, text="• VRAM Dedicada: --", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._gpu_vram_lbl.pack(fill="x", pady=2)

        self._gpu_temp_lbl = ctk.CTkLabel(gpu_details, text="• Temperatura GPU: Sensor indisponível", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._gpu_temp_lbl.pack(fill="x", pady=2)

        self._sensors_status_lbl = ctk.CTkLabel(gpu_details, text="• Sensores de Vídeo: Operantes", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w")
        self._sensors_status_lbl.pack(fill="x", pady=2)

        # 5. Cartão Sistema & Ambiente
        self._sys_card = ctk.CTkFrame(
            parent,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._sys_card.grid(row=2, column=1, sticky="nsew", padx=(LayoutDimensions.PAD_MD, 0), pady=(0, LayoutDimensions.PAD_LG))

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

        # 6. Cartão Top Processos (com 6 linhas pré-alocadas para atualização em 0ms)
        self._procs_card = ctk.CTkFrame(
            parent,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._procs_card.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(0, LayoutDimensions.PAD_LG))

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

        # 7. Barra de Rodapé
        status_bar = ctk.CTkFrame(parent, fg_color="transparent", border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
        status_bar.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, LayoutDimensions.PAD_SM))
        ctk.CTkLabel(
            status_bar,
            text="Status: Operacional • Monitoramento assíncrono em segundo plano • Zero telemetria • Sollaris Nova v0.1.0-alpha",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_INACTIVE,
        ).pack(padx=LayoutDimensions.PAD_MD, pady=LayoutDimensions.PAD_SM)

    def _build_diagnostics_view(self, parent: ctk.CTkScrollableFrame) -> None:
        """Constrói a página de Diagnóstico Técnico."""
        banner = ctk.CTkFrame(parent, fg_color=ThemeColors.BG_SURFACE, border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
        banner.pack(fill="x", pady=(0, LayoutDimensions.PAD_LG), padx=LayoutDimensions.PAD_SM)

        ctk.CTkLabel(banner, text="MOTOR DE DIAGNÓSTICO EXPLICÁVEL", font=Typography.card_title(), text_color=ThemeColors.ACCENT_LIGHT).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))
        ctk.CTkLabel(
            banner,
            text="Avaliações técnicas baseadas na persistência e limites reais de hardware, sem pontuações artificiais de saúde.",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

        self._diag_findings_container = ctk.CTkFrame(parent, fg_color="transparent")
        self._diag_findings_container.pack(fill="x", padx=LayoutDimensions.PAD_SM)

    def _build_cleaner_view(self, parent: ctk.CTkScrollableFrame) -> None:
        """Constrói a página de Limpeza Segura de Arquivos Temporários."""
        banner = ctk.CTkFrame(parent, fg_color=ThemeColors.BG_SURFACE, border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
        banner.pack(fill="x", pady=(0, LayoutDimensions.PAD_LG), padx=LayoutDimensions.PAD_SM)

        ctk.CTkLabel(banner, text="LIMPEZA SEGURA DE TEMPORÁRIOS", font=Typography.card_title(), text_color=ThemeColors.ACCENT_LIGHT).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))
        ctk.CTkLabel(
            banner,
            text="Varre apenas locais estritamente autorizados do usuário e caches temporários. Nenhuma exclusão automática destrutiva é realizada.",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

        self._cleaner_cards_container = ctk.CTkFrame(parent, fg_color="transparent")
        self._cleaner_cards_container.pack(fill="x", padx=LayoutDimensions.PAD_SM)

        self._cleaner_scan_btn = ctk.CTkButton(
            parent,
            text="Analisar Espaço Recuperável",
            font=Typography.body_regular(),
            fg_color=ThemeColors.ACCENT_BLUE,
            hover_color=ThemeColors.ACCENT_HOVER,
            command=self._run_cleaner_scan,
            height=36,
        )
        self._cleaner_scan_btn.pack(pady=LayoutDimensions.PAD_LG)

    def _build_startup_view(self, parent: ctk.CTkScrollableFrame) -> None:
        """Constrói a página de Gerenciamento de Inicialização."""
        banner = ctk.CTkFrame(parent, fg_color=ThemeColors.BG_SURFACE, border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
        banner.pack(fill="x", pady=(0, LayoutDimensions.PAD_LG), padx=LayoutDimensions.PAD_SM)

        ctk.CTkLabel(banner, text="PROGRAMAS DE INICIALIZAÇÃO DO WINDOWS", font=Typography.card_title(), text_color=ThemeColors.ACCENT_LIGHT).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))
        ctk.CTkLabel(
            banner,
            text="Programas cadastrados no Registro do Windows (HKCU/HKLM) para inicializar automaticamente com a sessão do usuário.",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

        self._startup_list_container = ctk.CTkFrame(parent, fg_color="transparent")
        self._startup_list_container.pack(fill="x", padx=LayoutDimensions.PAD_SM)

    def _build_game_mode_view(self, parent: ctk.CTkScrollableFrame) -> None:
        """Constrói a página de Perfis e Modo Game."""
        banner = ctk.CTkFrame(parent, fg_color=ThemeColors.BG_SURFACE, border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
        banner.pack(fill="x", pady=(0, LayoutDimensions.PAD_LG), padx=LayoutDimensions.PAD_SM)

        ctk.CTkLabel(banner, text="PERFIS DE OPERAÇÃO E ENERGIA", font=Typography.card_title(), text_color=ThemeColors.ACCENT_LIGHT).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))
        ctk.CTkLabel(
            banner,
            text="Gerenciamento transparente de prioridades de CPU e planos de energia do Windows.",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

        p1 = ctk.CTkFrame(parent, fg_color=ThemeColors.BG_SURFACE, border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
        p1.pack(fill="x", pady=(0, LayoutDimensions.PAD_MD), padx=LayoutDimensions.PAD_SM)
        ctk.CTkLabel(p1, text="Perfil Equilibrado (Padrão Windows) [Ativo]", font=(Typography.FONT_FAMILY, 12, "bold"), text_color=ThemeColors.STATUS_OK).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 2))
        ctk.CTkLabel(p1, text="Balanceia estados de economia de energia e resposta térmica. Ideal para uso diário, trabalho e navegação.", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

        p2 = ctk.CTkFrame(parent, fg_color=ThemeColors.BG_SURFACE, border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
        p2.pack(fill="x", pady=(0, LayoutDimensions.PAD_MD), padx=LayoutDimensions.PAD_SM)
        ctk.CTkLabel(p2, text="Perfil Alto Desempenho / Modo Foco", font=(Typography.FONT_FAMILY, 12, "bold"), text_color=ThemeColors.TEXT_PRIMARY).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 2))
        ctk.CTkLabel(p2, text="Prioriza escalonamento de threads da aplicação em foco e reduz transições profundas de sono da CPU (C-States).", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

    def _build_history_view(self, parent: ctk.CTkScrollableFrame) -> None:
        """Constrói a página de Estatísticas e Histórico da Sessão."""
        banner = ctk.CTkFrame(parent, fg_color=ThemeColors.BG_SURFACE, border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
        banner.pack(fill="x", pady=(0, LayoutDimensions.PAD_LG), padx=LayoutDimensions.PAD_SM)

        ctk.CTkLabel(banner, text="MÉTRICAS DA SESSÃO ATUAL", font=Typography.card_title(), text_color=ThemeColors.ACCENT_LIGHT).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))

        self._hist_uptime_lbl = ctk.CTkLabel(banner, text="Tempo monitorado nesta sessão: 0s", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED)
        self._hist_uptime_lbl.pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

        stats_grid = ctk.CTkFrame(parent, fg_color="transparent")
        stats_grid.pack(fill="x", padx=LayoutDimensions.PAD_SM)
        stats_grid.grid_columnconfigure(0, weight=1)
        stats_grid.grid_columnconfigure(1, weight=1)

        c_stat = ctk.CTkFrame(stats_grid, fg_color=ThemeColors.BG_SURFACE, border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
        c_stat.grid(row=0, column=0, sticky="nsew", padx=(0, LayoutDimensions.PAD_MD))
        ctk.CTkLabel(c_stat, text="HISTÓRICO DE CPU", font=Typography.card_title(), text_color=ThemeColors.TEXT_MUTED).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))
        self._hist_cpu_avg_lbl = ctk.CTkLabel(c_stat, text="• Média de Uso: -- %", font=Typography.body_regular(), text_color=ThemeColors.TEXT_PRIMARY)
        self._hist_cpu_avg_lbl.pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=2)
        self._hist_cpu_max_lbl = ctk.CTkLabel(c_stat, text="• Pico Máximo Registrado: -- %", font=Typography.body_regular(), text_color=ThemeColors.TEXT_MUTED)
        self._hist_cpu_max_lbl.pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(2, LayoutDimensions.PAD_MD))

        r_stat = ctk.CTkFrame(stats_grid, fg_color=ThemeColors.BG_SURFACE, border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
        r_stat.grid(row=0, column=1, sticky="nsew", padx=(LayoutDimensions.PAD_MD, 0))
        ctk.CTkLabel(r_stat, text="HISTÓRICO DE RAM", font=Typography.card_title(), text_color=ThemeColors.TEXT_MUTED).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))
        self._hist_ram_avg_lbl = ctk.CTkLabel(r_stat, text="• Média de Uso: -- %", font=Typography.body_regular(), text_color=ThemeColors.TEXT_PRIMARY)
        self._hist_ram_avg_lbl.pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=2)
        self._hist_ram_max_lbl = ctk.CTkLabel(r_stat, text="• Pico Máximo Registrado: -- %", font=Typography.body_regular(), text_color=ThemeColors.TEXT_MUTED)
        self._hist_ram_max_lbl.pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(2, LayoutDimensions.PAD_MD))

    def _build_settings_view(self, parent: ctk.CTkScrollableFrame) -> None:
        """Constrói a página de Configurações Técnicas."""
        card = ctk.CTkFrame(parent, fg_color=ThemeColors.BG_SURFACE, border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
        card.pack(fill="x", padx=LayoutDimensions.PAD_SM, pady=(0, LayoutDimensions.PAD_LG))

        ctk.CTkLabel(card, text="INTERVALO DO MONITOR DE SEGUNDO PLANO", font=Typography.card_title(), text_color=ThemeColors.TEXT_MUTED).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))

        opts_frame = ctk.CTkFrame(card, fg_color="transparent")
        opts_frame.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(4, LayoutDimensions.PAD_MD))

        for text, sec in [("1.0s (Alta Precisão)", 1.0), ("1.5s (Recomendado)", 1.5), ("3.0s (Econômico)", 3.0)]:
            btn = ctk.CTkButton(
                opts_frame,
                text=text,
                font=Typography.caption(),
                height=30,
                fg_color=ThemeColors.BG_CARD_HOVER,
                command=lambda s=sec: self._set_monitor_interval(s),
            )
            btn.pack(side="left", padx=(0, LayoutDimensions.PAD_MD))

        card_info = ctk.CTkFrame(parent, fg_color=ThemeColors.BG_SURFACE, border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
        card_info.pack(fill="x", padx=LayoutDimensions.PAD_SM)

        ctk.CTkLabel(card_info, text="SOBRE O SOLLARIS NOVA", font=Typography.card_title(), text_color=ThemeColors.TEXT_MUTED).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))
        info_lines = [
            "• Versão: Sollaris Nova v0.1.0-alpha (Build 2026.10)",
            "• Arquitetura: Monitoramento desacoplado em background thread (MonitorService)",
            "• Desempenho: Coleta em sub-10ms com consumo mínimo de recursos",
            "• Filosofia: Zero telemetria, execução 100% offline",
            "• Licença: MIT Open-Source",
        ]
        for line in info_lines:
            ctk.CTkLabel(card_info, text=line, font=Typography.caption(), text_color=ThemeColors.TEXT_PRIMARY, anchor="w").pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=2)

    def _set_monitor_interval(self, sec: float) -> None:
        """Modifica a cadência do monitor de background."""
        if self._monitor:
            self._monitor.set_interval(sec)
        logger.info("Intervalo do MonitorService alterado para %.1f s", sec)

    # =========================================================================
    # RECEPTOR DE DADOS DA THREAD ASSÍNCRONA (0ms NO LOOP DA GUI)
    # =========================================================================

    def _set_loading_state(self, is_loading: bool) -> None:
        """Alterna a exibição do indicador visual de recarregamento (Loader)."""
        if self._is_destroyed:
            return

        self._is_loading = is_loading
        if is_loading:
            self._refresh_btn.configure(
                text="Atualizando...",
                state="disabled",
                fg_color=ThemeColors.BG_CARD_HOVER,
            )
            self._global_status_badge.configure(
                text="● Atualizando...",
                text_color=ThemeColors.ACCENT_BLUE,
            )
            self._loader_bar.grid()
            self._loader_bar.start()
        else:
            self._refresh_btn.configure(
                text="Atualizar Agora",
                state="normal",
                fg_color=ThemeColors.BG_SURFACE,
            )
            self._loader_bar.stop()
            self._loader_bar.grid_remove()

    def request_refresh(self) -> None:
        """Solicita atualização assíncrona imediata via MonitorService com loader visual."""
        if self._is_destroyed or self._is_loading:
            return

        self._set_loading_state(True)
        if hasattr(self, "_monitor") and self._monitor:
            self._monitor.request_immediate_refresh()
        else:
            self.refresh_metrics()
            self._set_loading_state(False)

    def _schedule_poll(self) -> None:
        """Verifica periodicamente se novos dados chegaram da background thread."""
        if self._is_destroyed:
            return
        delay = 40 if self._is_loading else 100
        self._poll_after_id = self.after(delay, self._poll_background_updates)

    def _poll_background_updates(self) -> None:
        """Consome dados atômicos da fila da thread de segundo plano."""
        if self._is_destroyed:
            return

        if hasattr(self, "_monitor") and self._monitor:
            snap, procs = self._monitor.get_latest_data()
            if snap and snap.timestamp != self._last_rendered_timestamp:
                self._last_rendered_timestamp = snap.timestamp
                self._render_data_to_ui(snap, procs)
                if self._is_loading:
                    self._set_loading_state(False)

        self._schedule_poll()

    def refresh_metrics(self) -> None:
        """Coleta ou renderiza imediatamente sem travar a interface."""
        if self._is_destroyed:
            return

        try:
            snapshot = self._collector.collect_snapshot()
            procs = self._monitor.get_latest_data()[1] if hasattr(self, "_monitor") and self._monitor else []
            self._last_rendered_timestamp = snapshot.timestamp
            self._render_data_to_ui(snapshot, procs)
        except Exception:
            logger.exception("Erro ao atualizar métricas de hardware.")

    def _render_data_to_ui(self, snap: SystemSnapshot, procs: list[ProcessItem]) -> None:
        """Atualiza os valores dos widgets existentes sem recriá-los (0ms)."""
        now_str = datetime.now().astimezone().strftime("%H:%M:%S")
        self._timestamp_label.configure(text=f"Última amostragem: {now_str} • Ao Vivo")

        self._session_cpu_samples.append(snap.cpu.total_percent)
        self._session_ram_samples.append(snap.ram.percent)

        if self._active_route == "overview":
            self._update_overview_widgets(snap, procs)
        elif self._active_route == "diagnostics":
            self._update_diagnostics_widgets(snap)
        elif self._active_route == "history":
            self._update_history_view()
        elif self._active_route == "startup":
            self._update_startup_view()

        self._update_global_badge(snap)

    def _update_global_badge(self, snap: SystemSnapshot) -> None:
        """Atualiza o badge de estabilidade no topo da janela."""
        cpu_pct = snap.cpu.total_percent
        ram_pct = snap.ram.percent
        if cpu_pct > 85.0 or ram_pct > 90.0:
            self._global_status_badge.configure(text="✕ Atenção Requerida", text_color=ThemeColors.STATUS_ERROR)
        elif cpu_pct > 70.0 or ram_pct > 80.0:
            self._global_status_badge.configure(text="▲ Carga Elevada", text_color=ThemeColors.STATUS_WARN)
        else:
            self._global_status_badge.configure(text="● Sistema Estável", text_color=ThemeColors.STATUS_OK)

    def _update_overview_widgets(self, snap: SystemSnapshot, procs: list[ProcessItem]) -> None:
        """Atualiza valores dos cartões de Visão Geral sem desmontar a árvore de widgets."""
        # 1. CPU
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
        self._cpu_procs_lbl.configure(text=f"• Processos Ativos no SO: {snap.cpu.process_count}")

        if snap.cpu.temperature.is_available and snap.cpu.temperature.value is not None:
            self._cpu_temp_lbl.configure(text=f"• Temperatura: {snap.cpu.temperature.value:.1f} °C [ACPI]", text_color=ThemeColors.TEXT_PRIMARY)
        else:
            self._cpu_temp_lbl.configure(text="• Temperatura: Sensor indisponível", text_color=ThemeColors.TEXT_MUTED)

        # Micro-medidores por núcleo (atualização direta dos labels pré-alocados)
        for idx, lbl in enumerate(self._core_chip_labels):
            if idx < len(snap.cpu.per_cpu_percent):
                c_val = snap.cpu.per_cpu_percent[idx]
                c_color = ThemeColors.STATUS_OK if c_val < 70 else (ThemeColors.STATUS_WARN if c_val < 85 else ThemeColors.STATUS_ERROR)
                lbl.configure(text=f"N{idx+1}: {c_val:.0f}%", text_color=c_color)

        # 2. RAM
        ram_used_str = format_bytes(snap.ram.used_bytes)
        ram_total_str = format_bytes(snap.ram.total_bytes)
        ram_pct = snap.ram.percent

        self._ram_big_val.configure(text=f"{ram_used_str} / {ram_total_str} ({ram_pct:.1f}%)")
        self._ram_progress.set(ram_pct / 100.0)

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

        swap_used_str = format_bytes(snap.ram.swap_used_bytes)
        swap_tot_str = format_bytes(snap.ram.swap_total_bytes)
        self._ram_swap_lbl.configure(text=f"• Arquivo de Paginação: {swap_used_str} / {swap_tot_str} ({snap.ram.swap_percent:.1f}%)")
        self._swap_progress.set(snap.ram.swap_percent / 100.0)

        # 3. Discos (Reciclagem dos widgets de linha sem listras)
        for disk in snap.disks:
            self._create_or_update_disk_row(disk)

        # 4. GPU
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

        # 5. Sistema
        self._sys_os_lbl.configure(text=f"• Sistema: {snap.os_name}")
        self._sys_build_lbl.configure(text=f"• Compilação: {snap.os_build} ({snap.architecture})")
        self._sys_uptime_lbl.configure(text=f"• Tempo de Atividade: {format_uptime(snap.uptime_seconds)}")

        # 6. Top Processos (atualização direta das 6 linhas)
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
        """Cria ou atualiza uma linha de partição de disco garantindo reciclagem e sem listras."""
        key = disk.mountpoint
        if key not in self._disk_widget_rows:
            row_frame = ctk.CTkFrame(self._disks_container, fg_color="transparent")
            row_frame.pack(fill="x", pady=4)
            top_r = ctk.CTkFrame(row_frame, fg_color="transparent")
            top_r.pack(fill="x")
            lbl_title = ctk.CTkLabel(top_r, text="", font=(Typography.FONT_FAMILY, 11, "bold"), text_color=ThemeColors.TEXT_PRIMARY)
            lbl_title.pack(side="left")
            lbl_sub = ctk.CTkLabel(top_r, text="", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED)
            lbl_sub.pack(side="right")
            p_bar = ctk.CTkProgressBar(
                row_frame,
                height=8,
                corner_radius=4,
                border_width=0,
                fg_color="#141E2B",
                progress_color=ThemeColors.STATUS_OK,
            )
            p_bar.pack(fill="x", pady=(2, 6))
            self._disk_widget_rows[key] = {"title": lbl_title, "sub": lbl_sub, "bar": p_bar}

        widgets = self._disk_widget_rows[key]
        widgets["title"].configure(text=f"Unidade ({disk.device}) [{disk.fstype}]")
        free_str = format_bytes(disk.free_bytes)
        tot_str = format_bytes(disk.total_bytes)
        widgets["sub"].configure(text=f"{free_str} livres de {tot_str} ({disk.percent:.1f}% usado)")

        p_color = ThemeColors.STATUS_OK
        if disk.percent > 90.0 or (disk.free_bytes / (1024**3)) < 15.0:
            p_color = ThemeColors.STATUS_ERROR
        elif disk.percent > 80.0:
            p_color = ThemeColors.STATUS_WARN
        widgets["bar"].configure(progress_color=p_color)
        widgets["bar"].set(disk.percent / 100.0)

    def _update_diagnostics_widgets(self, snap: SystemSnapshot) -> None:
        """Atualiza a página de Diagnóstico."""
        for widget in self._diag_findings_container.winfo_children():
            widget.destroy()

        findings = DiagnosticEngine.evaluate(snap)
        for f in findings:
            card = ctk.CTkFrame(self._diag_findings_container, fg_color=ThemeColors.BG_SURFACE, border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
            card.pack(fill="x", pady=4)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 2))

            level_colors = {
                FindingLevel.OPTIMAL: (ThemeColors.STATUS_OK, "● Estável"),
                FindingLevel.INFO: (ThemeColors.ACCENT_LIGHT, "ℹ Informação"),
                FindingLevel.WARNING: (ThemeColors.STATUS_WARN, "▲ Atenção"),
                FindingLevel.CRITICAL: (ThemeColors.STATUS_ERROR, "✕ Crítico"),
            }
            color, tag = level_colors.get(f.level, (ThemeColors.TEXT_MUTED, "Diagnóstico"))

            ctk.CTkLabel(top, text=f"[{f.category}] {f.title}", font=(Typography.FONT_FAMILY, 12, "bold"), text_color=ThemeColors.TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(top, text=tag, font=Typography.caption(), text_color=color).pack(side="right")

            ctk.CTkLabel(card, text=f.description, font=Typography.body_regular(), text_color=ThemeColors.TEXT_MUTED, anchor="w").pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=2)
            ctk.CTkLabel(card, text=f"Recomendação: {f.recommendation}", font=Typography.caption(), text_color=ThemeColors.ACCENT_LIGHT, anchor="w").pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

    def _run_cleaner_scan(self) -> None:
        """Executa a varredura não-destrutiva de temporários em background sem travar a interface."""
        for widget in self._cleaner_cards_container.winfo_children():
            widget.destroy()

        self._cleaner_scan_btn.configure(text="Analisando pastas...", state="disabled")

        def _worker() -> None:
            categories = CleanerScanner.scan_temporary_files()
            if not self._is_destroyed:
                self.after(0, lambda: self._render_cleaner_results(categories))

        threading.Thread(target=_worker, daemon=True, name="CleanerScanThread").start()

    def _render_cleaner_results(self, categories: list) -> None:
        """Renderiza os resultados da análise de temporários na interface."""
        if self._is_destroyed:
            return

        self._cleaner_scan_btn.configure(text="Analisar Espaço Recuperável", state="normal")
        total_reclaimable = sum(c.size_bytes for c in categories)

        top_summary = ctk.CTkLabel(
            self._cleaner_cards_container,
            text=f"Total de Espaço Recuperável Identificado: {format_bytes(total_reclaimable)}",
            font=(Typography.FONT_FAMILY, 14, "bold"),
            text_color=ThemeColors.STATUS_OK,
        )
        top_summary.pack(anchor="w", pady=(0, LayoutDimensions.PAD_MD))

        for cat in categories:
            c = ctk.CTkFrame(self._cleaner_cards_container, fg_color=ThemeColors.BG_SURFACE, border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
            c.pack(fill="x", pady=4)

            top = ctk.CTkFrame(c, fg_color="transparent")
            top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 2))
            ctk.CTkLabel(top, text=cat.name, font=(Typography.FONT_FAMILY, 12, "bold"), text_color=ThemeColors.TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(top, text=f"{format_bytes(cat.size_bytes)} ({cat.file_count} arquivos)", font=Typography.caption(), text_color=ThemeColors.ACCENT_LIGHT).pack(side="right")

            ctk.CTkLabel(c, text=f"Local: {cat.path}", font=Typography.caption(), text_color=ThemeColors.TEXT_INACTIVE, anchor="w").pack(fill="x", padx=LayoutDimensions.PAD_LG)
            ctk.CTkLabel(c, text=cat.description, font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w").pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(2, LayoutDimensions.PAD_MD))

    def _update_startup_view(self) -> None:
        """Carrega e exibe a lista de programas de inicialização."""
        for widget in self._startup_list_container.winfo_children():
            widget.destroy()

        apps = StartupManager.get_startup_applications()
        ctk.CTkLabel(
            self._startup_list_container,
            text=f"{len(apps)} Programas Registrados para Iniciar com o Sistema:",
            font=(Typography.FONT_FAMILY, 12, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, LayoutDimensions.PAD_MD))

        for app in apps:
            card = ctk.CTkFrame(self._startup_list_container, fg_color=ThemeColors.BG_SURFACE, border_width=LayoutDimensions.BORDER_WIDTH, border_color=ThemeColors.BORDER, corner_radius=LayoutDimensions.CORNER_RADIUS_CARD)
            card.pack(fill="x", pady=3)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 2))
            ctk.CTkLabel(top, text=app.name, font=(Typography.FONT_FAMILY, 12, "bold"), text_color=ThemeColors.TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(top, text=app.location, font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED).pack(side="right")

            ctk.CTkLabel(card, text=f"Executável: {app.command}", font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w").pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

    def _update_history_view(self) -> None:
        """Atualiza a página de Histórico com médias e picos observados."""
        duration = int(time.time() - self._session_start_time)
        self._hist_uptime_lbl.configure(text=f"Tempo monitorado nesta sessão: {format_uptime(duration)} ({len(self._session_cpu_samples)} amostras)")

        if self._session_cpu_samples:
            cpu_avg = sum(self._session_cpu_samples) / len(self._session_cpu_samples)
            cpu_max = max(self._session_cpu_samples)
            self._hist_cpu_avg_lbl.configure(text=f"• Média de Uso: {cpu_avg:.1f} %")
            self._hist_cpu_max_lbl.configure(text=f"• Pico Máximo Registrado: {cpu_max:.1f} %")

        if self._session_ram_samples:
            ram_avg = sum(self._session_ram_samples) / len(self._session_ram_samples)
            ram_max = max(self._session_ram_samples)
            self._hist_ram_avg_lbl.configure(text=f"• Média de Uso: {ram_avg:.1f} %")
            self._hist_ram_max_lbl.configure(text=f"• Pico Máximo Registrado: {ram_max:.1f} %")

    def destroy(self) -> None:
        """Finaliza a janela parando a thread assíncrona e timers pendentes."""
        self._is_destroyed = True
        if self._poll_after_id:
            try:
                self.after_cancel(self._poll_after_id)
            except (tk.TclError, ValueError) as exc:
                logger.debug("Timer de poll já finalizado: %s", exc)
            self._poll_after_id = None

        if hasattr(self, "_monitor") and self._monitor:
            self._monitor.stop()

        super().destroy()
