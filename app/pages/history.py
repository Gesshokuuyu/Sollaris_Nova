"""Página de Histórico e Estatísticas da Sessão — Sollaris Nova.

Apresenta as médias, picos e tempo de monitoramento acumulados durante a sessão atual.
"""

from __future__ import annotations

import customtkinter as ctk

from app.theme import LayoutDimensions, ThemeColors, Typography
from core.hardware import format_uptime


class HistoryPage(ctk.CTkScrollableFrame):
    """Página de Estatísticas da Sessão Atual."""

    def __init__(self, parent: ctk.CTkBaseClass) -> None:
        super().__init__(parent, fg_color=ThemeColors.BG_MAIN, corner_radius=0)

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        """Constrói os cartões de estatísticas acumuladas da sessão."""
        banner = ctk.CTkFrame(
            self,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        banner.pack(fill="x", pady=(0, LayoutDimensions.PAD_LG), padx=LayoutDimensions.PAD_SM)

        ctk.CTkLabel(
            banner,
            text="MÉTRICAS DA SESSÃO ATUAL",
            font=Typography.card_title(),
            text_color=ThemeColors.ACCENT_LIGHT,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))

        self._hist_uptime_lbl = ctk.CTkLabel(
            banner,
            text="Tempo monitorado nesta sessão: 0s",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
        )
        self._hist_uptime_lbl.pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

        stats_grid = ctk.CTkFrame(self, fg_color="transparent")
        stats_grid.pack(fill="x", padx=LayoutDimensions.PAD_SM)
        stats_grid.grid_columnconfigure(0, weight=1)
        stats_grid.grid_columnconfigure(1, weight=1)

        c_stat = ctk.CTkFrame(
            stats_grid,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        c_stat.grid(row=0, column=0, sticky="nsew", padx=(0, LayoutDimensions.PAD_MD))
        ctk.CTkLabel(c_stat, text="HISTÓRICO DE CPU", font=Typography.card_title(), text_color=ThemeColors.TEXT_MUTED).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))
        self._hist_cpu_avg_lbl = ctk.CTkLabel(c_stat, text="• Média de Uso: -- %", font=Typography.body_regular(), text_color=ThemeColors.TEXT_PRIMARY)
        self._hist_cpu_avg_lbl.pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=2)
        self._hist_cpu_max_lbl = ctk.CTkLabel(c_stat, text="• Pico Máximo Registrado: -- %", font=Typography.body_regular(), text_color=ThemeColors.TEXT_MUTED)
        self._hist_cpu_max_lbl.pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(2, LayoutDimensions.PAD_MD))

        r_stat = ctk.CTkFrame(
            stats_grid,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        r_stat.grid(row=0, column=1, sticky="nsew", padx=(LayoutDimensions.PAD_MD, 0))
        ctk.CTkLabel(r_stat, text="HISTÓRICO DE RAM", font=Typography.card_title(), text_color=ThemeColors.TEXT_MUTED).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))
        self._hist_ram_avg_lbl = ctk.CTkLabel(r_stat, text="• Média de Uso: -- %", font=Typography.body_regular(), text_color=ThemeColors.TEXT_PRIMARY)
        self._hist_ram_avg_lbl.pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=2)
        self._hist_ram_max_lbl = ctk.CTkLabel(r_stat, text="• Pico Máximo Registrado: -- %", font=Typography.body_regular(), text_color=ThemeColors.TEXT_MUTED)
        self._hist_ram_max_lbl.pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(2, LayoutDimensions.PAD_MD))

    def update_data(self, duration_seconds: int, cpu_samples: list[float], ram_samples: list[float]) -> None:
        """Atualiza a página de Histórico com médias e picos observados."""
        sample_count = len(cpu_samples)
        self._hist_uptime_lbl.configure(
            text=f"Tempo monitorado nesta sessão: {format_uptime(duration_seconds)} ({sample_count} amostras)"
        )

        if cpu_samples:
            cpu_avg = sum(cpu_samples) / len(cpu_samples)
            cpu_max = max(cpu_samples)
            self._hist_cpu_avg_lbl.configure(text=f"• Média de Uso: {cpu_avg:.1f} %")
            self._hist_cpu_max_lbl.configure(text=f"• Pico Máximo Registrado: {cpu_max:.1f} %")

        if ram_samples:
            ram_avg = sum(ram_samples) / len(ram_samples)
            ram_max = max(ram_samples)
            self._hist_ram_avg_lbl.configure(text=f"• Média de Uso: {ram_avg:.1f} %")
            self._hist_ram_max_lbl.configure(text=f"• Pico Máximo Registrado: {ram_max:.1f} %")
