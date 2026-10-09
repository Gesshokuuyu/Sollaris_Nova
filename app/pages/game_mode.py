"""Página de Perfis de Desempenho & Modo Game — Sollaris Nova.

Gerencia perfis operacionais e planos de energia do Windows.
"""

from __future__ import annotations

import customtkinter as ctk

from app.theme import LayoutDimensions, ThemeColors, Typography


class GameModePage(ctk.CTkScrollableFrame):
    """Página de Perfis de Desempenho e Otimização para Jogos."""

    def __init__(self, parent: ctk.CTkBaseClass) -> None:
        super().__init__(parent, fg_color=ThemeColors.BG_MAIN, corner_radius=0)

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        """Constrói os cartões de perfis de energia e operação."""
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
            text="PERFIS DE OPERAÇÃO E ENERGIA",
            font=Typography.card_title(),
            text_color=ThemeColors.ACCENT_LIGHT,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))

        ctk.CTkLabel(
            banner,
            text="Gerenciamento transparente de prioridades de CPU e planos de energia do Windows.",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

        p1 = ctk.CTkFrame(
            self,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        p1.pack(fill="x", pady=(0, LayoutDimensions.PAD_MD), padx=LayoutDimensions.PAD_SM)
        ctk.CTkLabel(
            p1,
            text="Perfil Equilibrado (Padrão Windows) [Ativo]",
            font=(Typography.FONT_FAMILY, 12, "bold"),
            text_color=ThemeColors.STATUS_OK,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 2))
        ctk.CTkLabel(
            p1,
            text="Balanceia estados de economia de energia e resposta térmica. Ideal para uso diário, trabalho e navegação.",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

        p2 = ctk.CTkFrame(
            self,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        p2.pack(fill="x", pady=(0, LayoutDimensions.PAD_MD), padx=LayoutDimensions.PAD_SM)
        ctk.CTkLabel(
            p2,
            text="Perfil Alto Desempenho / Modo Foco",
            font=(Typography.FONT_FAMILY, 12, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 2))
        ctk.CTkLabel(
            p2,
            text="Prioriza escalonamento de threads da aplicação em foco e reduz transições profundas de sono da CPU (C-States).",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))
