"""Página de Configurações Técnicas — Sollaris Nova.

Permite alternar parâmetros de operação e exibe informações sobre o software.
"""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from app.theme import LayoutDimensions, ThemeColors, Typography


class SettingsPage(ctk.CTkScrollableFrame):
    """Página de Configurações da Aplicação."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        on_change_interval: Callable[[float], None] | None = None,
    ) -> None:
        super().__init__(parent, fg_color=ThemeColors.BG_MAIN, corner_radius=0)

        self.grid_columnconfigure(0, weight=1)
        self._on_change_interval = on_change_interval
        self._build_ui()

    def _build_ui(self) -> None:
        """Constrói as seções de parâmetros e informações do software."""
        card = ctk.CTkFrame(
            self,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        card.pack(fill="x", padx=LayoutDimensions.PAD_SM, pady=(0, LayoutDimensions.PAD_LG))

        ctk.CTkLabel(
            card,
            text="INTERVALO DO MONITOR DE SEGUNDO PLANO",
            font=Typography.card_title(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))

        opts_frame = ctk.CTkFrame(card, fg_color="transparent")
        opts_frame.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(4, LayoutDimensions.PAD_MD))

        for text, sec in [("1.0s (Alta Precisão)", 1.0), ("1.5s (Recomendado)", 1.5), ("3.0s (Econômico)", 3.0)]:
            btn = ctk.CTkButton(
                opts_frame,
                text=text,
                font=Typography.caption(),
                height=30,
                fg_color=ThemeColors.BG_CARD_HOVER,
                command=lambda s=sec: self._handle_interval_change(s),
            )
            btn.pack(side="left", padx=(0, LayoutDimensions.PAD_MD))

        card_info = ctk.CTkFrame(
            self,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        card_info.pack(fill="x", padx=LayoutDimensions.PAD_SM)

        ctk.CTkLabel(
            card_info,
            text="SOBRE O SOLLARIS NOVA",
            font=Typography.card_title(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))

        info_lines = [
            "• Versão: Sollaris Nova v0.2.0-alpha (Build 2026.10)",
            "• Arquitetura: Monitoramento desacoplado em background thread (MonitorService)",
            "• Desempenho: Coleta em sub-10ms com consumo mínimo de recursos",
            "• Filosofia: Zero telemetria, execução 100% offline",
            "• Licença: MIT Open-Source",
        ]
        for line in info_lines:
            ctk.CTkLabel(
                card_info,
                text=line,
                font=Typography.caption(),
                text_color=ThemeColors.TEXT_PRIMARY,
                anchor="w",
            ).pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=2)

    def _handle_interval_change(self, sec: float) -> None:
        if self._on_change_interval:
            self._on_change_interval(sec)
