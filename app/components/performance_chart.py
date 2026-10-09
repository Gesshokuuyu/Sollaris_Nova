"""Componente de Gráfico de Telemetria em Tempo Real — Sollaris Nova.

Renderiza o histórico dos últimos 60 segundos de CPU e RAM utilizando o
Matplotlib embarcado (FigureCanvasTkAgg) com curvas fluidas suavizadas por
interpolação, preenchimento sombreado sob as curvas, badges coloridos de
identificação e hover interativo com cursor vertical e leitura temporal no segundo apontado.
"""

from __future__ import annotations

import contextlib
import logging
from typing import Literal

import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.collections import PolyCollection
from matplotlib.figure import Figure

from app.theme import LayoutDimensions, ThemeColors, Typography

logger = logging.getLogger("sollaris_nova.chart")

ChartMode = Literal["both", "cpu", "ram"]


def _smooth_data(
    x_raw: list[float], y_raw: list[float], num_points: int = 180
) -> tuple[np.ndarray, np.ndarray]:
    """Gera curvas suaves e fluidas através de interpolação densa e filtro Hanning."""
    n = len(x_raw)
    if n < 4:
        return np.array(x_raw, dtype=float), np.array(y_raw, dtype=float)

    x_arr = np.array(x_raw, dtype=float)
    y_arr = np.array(y_raw, dtype=float)

    dense_x = np.linspace(x_arr[0], x_arr[-1], num_points)
    dense_y = np.interp(dense_x, x_arr, y_arr)

    # Filtro suave de 5 pontos ponderado
    kernel = np.array([0.1, 0.25, 0.3, 0.25, 0.1], dtype=float)
    smoothed_y = np.convolve(dense_y, kernel, mode="same")

    # Garante que o último ponto seja a medição real em tempo real
    smoothed_y[-1] = y_arr[-1]
    smoothed_y[0] = y_arr[0]

    return dense_x, np.clip(smoothed_y, 0.0, 100.0)


class PerformanceChart(ctk.CTkFrame):
    """Cartão de gráfico histórico contínuo dos últimos 60 segundos com Matplotlib e hover dinâmico."""

    def __init__(self, parent: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(
            parent,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
            **kwargs,
        )

        self._mode: ChartMode = "both"
        self._cpu_data: list[float] = []
        self._ram_data: list[float] = []
        self._is_hovering = False

        self._fill_cpu: PolyCollection | None = None
        self._fill_ram: PolyCollection | None = None

        # 1. Cabeçalho do Cartão com Título e Modos
        self._build_header()

        # 2. Configuração da Figura Matplotlib
        self._build_figure()

    def _build_header(self) -> None:
        """Constrói o cabeçalho técnico com controles de modo e badges coloridos de leitura."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 6))

        # Título
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="HISTÓRICO DE DESEMPENHO (ÚLTIMOS 60 SEGUNDOS)",
            font=Typography.card_title(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(side="left")

        # Controles de Modo (Pílulas)
        controls_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_box.pack(side="right")

        self._btn_both = ctk.CTkButton(
            controls_box,
            text="Ambos",
            width=64,
            height=24,
            font=(Typography.FONT_FAMILY, 10, "bold"),
            fg_color=ThemeColors.ACCENT_BLUE,
            hover_color=ThemeColors.ACCENT_HOVER,
            text_color=ThemeColors.TEXT_PRIMARY,
            command=lambda: self._set_mode("both"),
        )
        self._btn_both.pack(side="left", padx=2)

        self._btn_cpu = ctk.CTkButton(
            controls_box,
            text="CPU",
            width=50,
            height=24,
            font=(Typography.FONT_FAMILY, 10),
            fg_color="#141E2B",
            hover_color=ThemeColors.BG_CARD_HOVER,
            text_color=ThemeColors.TEXT_MUTED,
            command=lambda: self._set_mode("cpu"),
        )
        self._btn_cpu.pack(side="left", padx=2)

        self._btn_ram = ctk.CTkButton(
            controls_box,
            text="RAM",
            width=50,
            height=24,
            font=(Typography.FONT_FAMILY, 10),
            fg_color="#141E2B",
            hover_color=ThemeColors.BG_CARD_HOVER,
            text_color=ThemeColors.TEXT_MUTED,
            command=lambda: self._set_mode("ram"),
        )
        self._btn_ram.pack(side="left", padx=2)

        # Indicador de tempo e Badges coloridos de CPU / RAM
        self._time_pill = ctk.CTkLabel(
            controls_box,
            text="[ Ao Vivo ]",
            font=(Typography.FONT_FAMILY, 9),
            text_color=ThemeColors.TEXT_MUTED,
            padx=4,
        )
        self._time_pill.pack(side="left", padx=(8, 4))

        self._cpu_pill = ctk.CTkLabel(
            controls_box,
            text="● CPU: -- %",
            font=(Typography.FONT_FAMILY, 10, "bold"),
            text_color=ThemeColors.ACCENT_LIGHT,
            fg_color="#141E2B",
            corner_radius=4,
            padx=8,
            pady=2,
        )
        self._cpu_pill.pack(side="left", padx=2)

        self._ram_pill = ctk.CTkLabel(
            controls_box,
            text="● RAM: -- %",
            font=(Typography.FONT_FAMILY, 10, "bold"),
            text_color=ThemeColors.STATUS_OK,
            fg_color="#141E2B",
            corner_radius=4,
            padx=8,
            pady=2,
        )
        self._ram_pill.pack(side="left", padx=2)

        # Alias de compatibilidade
        self._legend_lbl = self._cpu_pill

    def _build_figure(self) -> None:
        """Cria e customiza o canvas Matplotlib com estética Dark Minimalist."""
        # Figura com fundo combinando com ThemeColors.BG_SURFACE
        self._fig = Figure(figsize=(7.5, 2.0), dpi=100, facecolor=ThemeColors.BG_SURFACE)
        self._ax = self._fig.add_subplot(111)

        # Ajuste fino das margens para aproveitar o espaço horizontal
        self._fig.subplots_adjust(left=0.05, right=0.98, top=0.90, bottom=0.18)

        # Configuração da área de plot
        self._ax.set_facecolor(ThemeColors.BG_MAIN)
        self._ax.set_ylim(0, 100)
        self._ax.set_xlim(-60, 0)

        # Ticks e marcações
        self._ax.set_yticks([0, 25, 50, 75, 100])
        self._ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=8, color=ThemeColors.TEXT_MUTED)
        self._ax.set_xticks([-60, -45, -30, -15, 0])
        self._ax.set_xticklabels(["-60s", "-45s", "-30s", "-15s", "Agora"], fontsize=8, color=ThemeColors.TEXT_MUTED)

        # Grid discreto
        self._ax.grid(True, which="both", axis="y", color="#192331", linestyle=":", linewidth=0.8, alpha=0.7)

        # Spines (bordas dos eixos)
        self._ax.spines["top"].set_visible(False)
        self._ax.spines["right"].set_visible(False)
        self._ax.spines["left"].set_color(ThemeColors.BORDER)
        self._ax.spines["left"].set_linewidth(1.0)
        self._ax.spines["bottom"].set_color(ThemeColors.BORDER)
        self._ax.spines["bottom"].set_linewidth(1.0)

        # Linhas de plot pré-alocadas
        (self._line_cpu,) = self._ax.plot(
            [],
            [],
            color=ThemeColors.ACCENT_BLUE,
            linewidth=2.0,
            label="CPU",
            antialiased=True,
            zorder=3,
        )
        (self._line_ram,) = self._ax.plot(
            [],
            [],
            color=ThemeColors.STATUS_OK,
            linewidth=2.0,
            label="RAM",
            antialiased=True,
            zorder=4,
        )

        # Elementos de Hover: cursor vertical tracejado e marcadores pontuais
        (self._cursor_line,) = self._ax.plot(
            [0, 0],
            [0, 100],
            color=ThemeColors.ACCENT_LIGHT,
            linestyle="--",
            linewidth=1.0,
            alpha=0.75,
            visible=False,
            zorder=5,
        )
        (self._marker_cpu,) = self._ax.plot(
            [],
            [],
            marker="o",
            markersize=6,
            color=ThemeColors.ACCENT_LIGHT,
            markeredgecolor="#0B0F14",
            markeredgewidth=1.5,
            linestyle="None",
            visible=False,
            zorder=6,
        )
        (self._marker_ram,) = self._ax.plot(
            [],
            [],
            marker="o",
            markersize=6,
            color=ThemeColors.STATUS_OK,
            markeredgecolor="#0B0F14",
            markeredgewidth=1.5,
            linestyle="None",
            visible=False,
            zorder=6,
        )

        # Canvas Tkinter integrado
        self._fig_canvas_container = ctk.CTkFrame(self, fg_color="transparent")
        self._fig_canvas_container.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

        self._fig_canvas = FigureCanvasTkAgg(self._fig, master=self._fig_canvas_container)
        self._fig_canvas_widget = self._fig_canvas.get_tk_widget()
        self._fig_canvas_widget.pack(fill="both", expand=True)
        self._fig_canvas_widget.configure(bg=ThemeColors.BG_SURFACE, highlightthickness=0, bd=0)

        # Conecta eventos interativos de mouse
        self._fig_canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        self._fig_canvas.mpl_connect("axes_leave_event", self._on_mouse_leave)

        # Renderização inicial estática
        self._fig_canvas.draw_idle()

    def _on_mouse_move(self, event) -> None:
        """Exibe o cursor guia e atualiza os valores pontuais exatos do segundo apontado."""
        if not event.inaxes or not self._cpu_data:
            self._on_mouse_leave(event)
            return

        self._is_hovering = True
        t_x = float(event.xdata)
        clamped_x = max(-60.0, min(0.0, t_x))

        n_cpu = len(self._cpu_data)
        n_ram = len(self._ram_data)

        # Encontra o índice correspondente no histórico
        if n_cpu > 1:
            step = 60.0 / (n_cpu - 1)
            idx_cpu = round((clamped_x + 60.0) / step)
            idx_cpu = max(0, min(idx_cpu, n_cpu - 1))
            val_cpu = self._cpu_data[idx_cpu]
        else:
            idx_cpu = 0
            val_cpu = self._cpu_data[0] if n_cpu > 0 else 0.0

        if n_ram > 1:
            step_ram = 60.0 / (n_ram - 1)
            idx_ram = round((clamped_x + 60.0) / step_ram)
            idx_ram = max(0, min(idx_ram, n_ram - 1))
            val_ram = self._ram_data[idx_ram]
        else:
            val_ram = self._ram_data[0] if n_ram > 0 else 0.0

        sec_label = f"{round(clamped_x)}s" if clamped_x < -0.5 else "Agora"

        # Posiciona cursor e marcadores
        self._cursor_line.set_xdata([clamped_x, clamped_x])
        self._cursor_line.set_visible(True)

        if self._mode in ("both", "cpu"):
            self._marker_cpu.set_data([clamped_x], [val_cpu])
            self._marker_cpu.set_visible(True)
        else:
            self._marker_cpu.set_visible(False)

        if self._mode in ("both", "ram"):
            self._marker_ram.set_data([clamped_x], [val_ram])
            self._marker_ram.set_visible(True)
        else:
            self._marker_ram.set_visible(False)

        # Atualiza badges no cabeçalho
        self._time_pill.configure(text=f"[ {sec_label} ]", text_color=ThemeColors.ACCENT_LIGHT)
        self._cpu_pill.configure(text=f"● CPU: {val_cpu:.1f}%")
        self._ram_pill.configure(text=f"● RAM: {val_ram:.1f}%")

        self._fig_canvas.draw_idle()

    def _on_mouse_leave(self, _event) -> None:
        """Oculta o cursor e retorna os badges para o estado em tempo real (Ao Vivo)."""
        self._is_hovering = False
        self._cursor_line.set_visible(False)
        self._marker_cpu.set_visible(False)
        self._marker_ram.set_visible(False)

        latest_cpu = f"{self._cpu_data[-1]:.1f}%" if self._cpu_data else "-- %"
        latest_ram = f"{self._ram_data[-1]:.1f}%" if self._ram_data else "-- %"

        self._time_pill.configure(text="[ Ao Vivo ]", text_color=ThemeColors.TEXT_MUTED)
        self._cpu_pill.configure(text=f"● CPU: {latest_cpu}")
        self._ram_pill.configure(text=f"● RAM: {latest_ram}")

        self._fig_canvas.draw_idle()

    def _set_mode(self, mode: ChartMode) -> None:
        """Alterna a visualização entre Ambos, CPU e RAM."""
        if mode == self._mode:
            return

        self._mode = mode

        # Atualiza o estilo dos botões
        active_btn_color = ThemeColors.ACCENT_BLUE
        inactive_btn_color = "#141E2B"

        self._btn_both.configure(
            fg_color=active_btn_color if mode == "both" else inactive_btn_color,
            text_color=ThemeColors.TEXT_PRIMARY if mode == "both" else ThemeColors.TEXT_MUTED,
            font=(Typography.FONT_FAMILY, 10, "bold" if mode == "both" else "normal"),
        )
        self._btn_cpu.configure(
            fg_color=active_btn_color if mode == "cpu" else inactive_btn_color,
            text_color=ThemeColors.TEXT_PRIMARY if mode == "cpu" else ThemeColors.TEXT_MUTED,
            font=(Typography.FONT_FAMILY, 10, "bold" if mode == "cpu" else "normal"),
        )
        self._btn_ram.configure(
            fg_color=active_btn_color if mode == "ram" else inactive_btn_color,
            text_color=ThemeColors.TEXT_PRIMARY if mode == "ram" else ThemeColors.TEXT_MUTED,
            font=(Typography.FONT_FAMILY, 10, "bold" if mode == "ram" else "normal"),
        )

        # Visibilidade das curvas
        show_cpu = mode in ("both", "cpu")
        show_ram = mode in ("both", "ram")

        self._line_cpu.set_visible(show_cpu)
        self._line_ram.set_visible(show_ram)

        if self._fill_cpu:
            self._fill_cpu.set_visible(show_cpu)
        if self._fill_ram:
            self._fill_ram.set_visible(show_ram)

        self._fig_canvas.draw_idle()

    def update_chart(self, cpu_samples: list[float], ram_samples: list[float]) -> None:
        """Atualiza os vetores de dados das curvas com interpolação suave em sub-2ms."""
        self._cpu_data = cpu_samples
        self._ram_data = ram_samples

        if not cpu_samples and not ram_samples:
            return

        n_cpu = len(cpu_samples)
        n_ram = len(ram_samples)

        # Remove preenchimentos anteriores para manter uso de memória estritamente constante
        if self._fill_cpu is not None:
            with contextlib.suppress(Exception):
                self._fill_cpu.remove()
            self._fill_cpu = None

        if self._fill_ram is not None:
            with contextlib.suppress(Exception):
                self._fill_ram.remove()
            self._fill_ram = None

        # 1. Curva e Preenchimento CPU (Fluida)
        if n_cpu > 0:
            x_cpu_raw = [-(n_cpu - 1 - i) * (60.0 / max(1, n_cpu - 1)) if n_cpu > 1 else 0.0 for i in range(n_cpu)]
            smooth_x_cpu, smooth_y_cpu = _smooth_data(x_cpu_raw, cpu_samples, num_points=120)
            self._line_cpu.set_data(smooth_x_cpu, smooth_y_cpu)

            if self._mode in ("both", "cpu"):
                self._fill_cpu = self._ax.fill_between(
                    smooth_x_cpu,
                    smooth_y_cpu,
                    0,
                    color=ThemeColors.ACCENT_BLUE,
                    alpha=0.14,
                    zorder=1,
                )

        # 2. Curva e Preenchimento RAM (Fluida)
        if n_ram > 0:
            x_ram_raw = [-(n_ram - 1 - i) * (60.0 / max(1, n_ram - 1)) if n_ram > 1 else 0.0 for i in range(n_ram)]
            smooth_x_ram, smooth_y_ram = _smooth_data(x_ram_raw, ram_samples, num_points=120)
            self._line_ram.set_data(smooth_x_ram, smooth_y_ram)

            if self._mode in ("both", "ram"):
                self._fill_ram = self._ax.fill_between(
                    smooth_x_ram,
                    smooth_y_ram,
                    0,
                    color=ThemeColors.STATUS_OK,
                    alpha=0.08,
                    zorder=2,
                )

        # Atualiza badges no cabeçalho se o mouse não estiver no meio de um hover
        if not self._is_hovering:
            latest_cpu = f"{cpu_samples[-1]:.1f}%" if cpu_samples else "-- %"
            latest_ram = f"{ram_samples[-1]:.1f}%" if ram_samples else "-- %"
            self._time_pill.configure(text="[ Ao Vivo ]", text_color=ThemeColors.TEXT_MUTED)
            self._cpu_pill.configure(text=f"● CPU: {latest_cpu}")
            self._ram_pill.configure(text=f"● RAM: {latest_ram}")

        # Despacha redesenho não-bloqueante
        self._fig_canvas.draw_idle()
