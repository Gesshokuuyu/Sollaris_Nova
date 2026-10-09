"""Janela principal da aplicação desktop — Sollaris Nova (PC Optimizer).

Atua como orquestrador principal da interface:
- Inicializa o frame da aplicação, design system e navegação da barra lateral
- Desacopla e monta as páginas modulares (Overview, Diagnóstico, Limpeza, etc.)
- Gerencia o serviço assíncrono de telemetria em segundo plano (MonitorService)
- Mantém o loop não-bloqueante a 60 FPS com reciclagem atômica de dados
"""

from __future__ import annotations

import contextlib
import logging
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path

import customtkinter as ctk

from app.components.sidebar import Sidebar
from app.components.tooltip import Tooltip
from app.pages import (
    CleanerPage,
    DiagnosticsPage,
    GameModePage,
    HistoryPage,
    OverviewPage,
    SettingsPage,
    StartupPage,
)
from app.theme import LayoutDimensions, ThemeColors, Typography
from core.diagnostics import DiagnosticEngine
from core.hardware import HardwareCollector, SystemSnapshot
from core.monitor import MonitorService
from core.processes import ProcessItem
from core.recorder import SessionRecorder

logger = logging.getLogger("sollaris_nova.window")


class MainWindow(ctk.CTk):
    """Janela principal do Sollaris Nova com arquitetura de páginas modular."""

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
        self._current_snapshot: SystemSnapshot | None = None
        self._poll_after_id: str | None = None
        self._recorder = SessionRecorder()

        # Estatísticas da sessão
        self._session_start_time = time.time()
        self._session_cpu_samples: list[float] = []
        self._session_ram_samples: list[float] = []

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

        # Atalhos de compatibilidade para componentes da Visão Geral
        self._cpu_gauge = self._overview_page._cpu_gauge
        self._ram_gauge = self._overview_page._ram_gauge
        self._perf_chart = self._overview_page._perf_chart
        self._storage_card = self._overview_page._storage_card
        self._disks_container = self._overview_page._disks_container
        self._gpu_name_lbl = self._overview_page._gpu_name_lbl
        self._sys_os_lbl = self._overview_page._sys_os_lbl
        self._cpu_model_lbl = self._overview_page._cpu_model_lbl
        self._cpu_badge = self._overview_page._cpu_badge

        # Inicia o serviço assíncrono em segundo plano
        self._monitor = MonitorService(interval_seconds=1.5)
        self._monitor.start()

        # Amostragem inicial síncrona leve (8ms)
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
            with contextlib.suppress(Exception):
                self.iconbitmap(str(icon_path))

    def _build_header_bar(self) -> None:
        """Constrói a barra de cabeçalho global persistente no topo."""
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
        Tooltip(self._global_status_badge, self._get_status_tooltip_text)

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

        # Barra de progresso indeterminada de 3px (Loader não-bloqueante)
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
        """Instancia e mapeia as páginas modulares desacopladas."""
        self._overview_page = OverviewPage(self._content_root)
        self._diag_page = DiagnosticsPage(self._content_root, recorder=self._recorder, on_navigate=self._switch_view)
        self._cleaner_page = CleanerPage(self._content_root)
        self._startup_page = StartupPage(self._content_root)
        self._game_page = GameModePage(self._content_root)
        self._history_page = HistoryPage(self._content_root)
        self._settings_page = SettingsPage(self._content_root, on_change_interval=self._set_monitor_interval)

        self._views_dict: dict[str, ctk.CTkScrollableFrame] = {
            "overview": self._overview_page,
            "diagnostics": self._diag_page,
            "cleaner": self._cleaner_page,
            "startup": self._startup_page,
            "game_mode": self._game_page,
            "history": self._history_page,
            "settings": self._settings_page,
        }

        # Exibe a visão inicial
        self._overview_page.grid(row=1, column=0, sticky="nsew")

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
                frame.grid_remove()

    def _on_navigation(self, route_id: str) -> None:
        """Trata o clique nos itens de navegação da barra lateral."""
        self._active_route = route_id
        self._switch_view(route_id)

        # Atualizações sob demanda para páginas específicas
        if route_id == "startup":
            self._startup_page.update_data()
        elif route_id == "history":
            duration = int(time.time() - self._session_start_time)
            self._history_page.update_data(duration, self._session_cpu_samples, self._session_ram_samples)
        elif route_id == "diagnostics" and self._current_snapshot:
            cpu_hist, ram_hist = (None, None)
            if hasattr(self, "_monitor") and self._monitor:
                cpu_hist, ram_hist = self._monitor.get_history_snapshot()
            procs = self._monitor.get_latest_data()[1] if hasattr(self, "_monitor") and self._monitor else []
            self._diag_page.update_data(self._current_snapshot, cpu_hist, ram_hist, procs)

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
        self._current_snapshot = snap
        now_str = datetime.now().astimezone().strftime("%H:%M:%S")
        self._timestamp_label.configure(text=f"Última amostragem: {now_str} • Ao Vivo")

        self._session_cpu_samples.append(snap.cpu.total_percent)
        self._session_ram_samples.append(snap.ram.percent)

        cpu_hist = None
        ram_hist = None
        stats = None
        if hasattr(self, "_monitor") and self._monitor:
            cpu_hist, ram_hist = self._monitor.get_history_snapshot()
            stats = self._monitor.get_window_statistics()

        # Se o Flight Recorder estiver gravando, registra a telemetria do tick (0ms overhead)
        if hasattr(self, "_recorder") and self._recorder and self._recorder.is_recording:
            findings = DiagnosticEngine.evaluate_with_history(
                snapshot=snap,
                cpu_history=cpu_hist,
                ram_history=ram_hist,
                processes=procs,
            )
            self._recorder.record_tick(snap, procs, findings)

        # Sempre atualiza a Visão Geral (para manter medidores sincronizados)
        self._overview_page.update_data(snap, procs, cpu_hist, ram_hist, stats)

        # Atualizações condicionais dependendo da rota ativa
        if self._active_route == "diagnostics":
            self._diag_page.update_data(snap, cpu_hist, ram_hist, procs)
        elif self._active_route == "history":
            duration = int(time.time() - self._session_start_time)
            self._history_page.update_data(duration, self._session_cpu_samples, self._session_ram_samples)

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

    def _get_status_tooltip_text(self) -> str:
        """Retorna texto descritivo do badge de integridade global."""
        if not self._current_snapshot:
            return "Monitoramento: Inicializando diagnóstico de recursos..."
        cpu_pct = self._current_snapshot.cpu.total_percent
        ram_pct = self._current_snapshot.ram.percent
        if cpu_pct > 85.0 or ram_pct > 90.0:
            status = "Sobrecarga Crítica detectada"
        elif cpu_pct > 70.0 or ram_pct > 80.0:
            status = "Consumo Elevado de recursos"
        else:
            status = "Sistema Saudável e Estável"
        return (
            f"Condição Global: {status}\n"
            f"CPU: {cpu_pct:.1f}% | RAM: {ram_pct:.1f}%\n"
            "Monitoramento contínuo em segundo plano (sub-1% CPU)."
        )

    def _set_monitor_interval(self, sec: float) -> None:
        """Modifica a cadência do monitor de background."""
        if self._monitor:
            self._monitor.set_interval(sec)
        logger.info("Intervalo do MonitorService alterado para %.1f s", sec)

    def destroy(self) -> None:
        """Finaliza a janela parando a thread assíncrona, gravador e timers pendentes."""
        self._is_destroyed = True
        if hasattr(self, "_recorder") and self._recorder and self._recorder.is_recording:
            with contextlib.suppress(Exception):
                self._recorder.stop_session()

        if self._poll_after_id:
            try:
                self.after_cancel(self._poll_after_id)
            except (tk.TclError, ValueError) as exc:
                logger.debug("Timer de poll já finalizado: %s", exc)
            self._poll_after_id = None

        if hasattr(self, "_monitor") and self._monitor:
            self._monitor.stop()

        super().destroy()
