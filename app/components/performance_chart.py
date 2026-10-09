"""Componente de Gráfico de Telemetria em Tempo Real — Sollaris Nova.

Renderiza o histórico dos últimos 60 segundos de CPU e RAM utilizando o
Matplotlib embarcado (FigureCanvasTkAgg) com consumo sub-3ms por ciclo,
eixos configurados no tema escuro e seletores de modo.
"""

from __future__ import annotations

import logging
from typing import Literal

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.theme import LayoutDimensions, ThemeColors, Typography

logger = logging.getLogger("sollaris_nova.chart")

ChartMode = Literal["both", "cpu", "ram"]


class PerformanceChart(ctk.CTkFrame):
    """Cartão de gráfico histórico contínuo dos últimos 60 segundos com Matplotlib."""

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

        # 1. Cabeçalho do Cartão com Título e Modos
        self._build_header()

        # 2. Configuração da Figura Matplotlib
        self._build_figure()

    def _build_header(self) -> None:
        """Constrói o cabeçalho técnico com controles de modo e badges de leitura."""
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

        # Legenda / Leitura Atual
        self._legend_lbl = ctk.CTkLabel(
            controls_box,
            text="CPU: -- %  |  RAM: -- %",
            font=(Typography.FONT_FAMILY, 10, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY,
            padx=8,
        )
        self._legend_lbl.pack(side="left", padx=(8, 0))

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

        # Linhas de plot pré-alocadas (atualizadas por set_data sem recriar nós)
        (self._line_cpu,) = self._ax.plot(
            [],
            [],
            color=ThemeColors.ACCENT_BLUE,
            linewidth=1.8,
            label="CPU",
            antialiased=True,
        )
        (self._line_ram,) = self._ax.plot(
            [],
            [],
            color=ThemeColors.STATUS_OK,
            linewidth=1.8,
            label="RAM",
            antialiased=True,
        )

        # Canvas Tkinter integrado
        self._fig_canvas_container = ctk.CTkFrame(self, fg_color="transparent")
        self._fig_canvas_container.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

        self._fig_canvas = FigureCanvasTkAgg(self._fig, master=self._fig_canvas_container)
        self._fig_canvas_widget = self._fig_canvas.get_tk_widget()
        self._fig_canvas_widget.pack(fill="both", expand=True)
        self._fig_canvas_widget.configure(bg=ThemeColors.BG_SURFACE, highlightthickness=0, bd=0)

        # Renderização inicial estática
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
        self._line_cpu.set_visible(mode in ("both", "cpu"))
        self._line_ram.set_visible(mode in ("both", "ram"))

        self._fig_canvas.draw_idle()

    def update_chart(self, cpu_samples: list[float], ram_samples: list[float]) -> None:
        """Atualiza os vetores de dados das curvas em sub-2ms."""
        self._cpu_data = cpu_samples
        self._ram_data = ram_samples

        if not cpu_samples and not ram_samples:
            return

        n_cpu = len(cpu_samples)
        n_ram = len(ram_samples)

        # Mapeia os pontos no eixo X de -60s até 0s (alinhando os mais recentes à direita)
        if n_cpu > 0:
            x_cpu = [-(n_cpu - 1 - i) * (60.0 / max(1, n_cpu - 1)) if n_cpu > 1 else 0 for i in range(n_cpu)]
            self._line_cpu.set_data(x_cpu, cpu_samples)

        if n_ram > 0:
            x_ram = [-(n_ram - 1 - i) * (60.0 / max(1, n_ram - 1)) if n_ram > 1 else 0 for i in range(n_ram)]
            self._line_ram.set_data(x_ram, ram_samples)

        # Atualiza a legenda no topo
        latest_cpu = f"{cpu_samples[-1]:.1f}%" if cpu_samples else "--"
        latest_ram = f"{ram_samples[-1]:.1f}%" if ram_samples else "--"
        self._legend_lbl.configure(text=f"CPU: {latest_cpu}  |  RAM: {latest_ram}")

        # Despacha redesenho não-bloqueante
        self._fig_canvas.draw_idle()
