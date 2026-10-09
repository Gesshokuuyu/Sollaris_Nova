"""Página de Gerenciamento de Inicialização — Sollaris Nova.

Mapeia e lista programas que inicializam com o Windows no Registro (HKCU/HKLM).
"""

from __future__ import annotations

import customtkinter as ctk

from app.theme import LayoutDimensions, ThemeColors, Typography
from core.startup import StartupManager


class StartupPage(ctk.CTkScrollableFrame):
    """Página de Gerenciamento de Inicialização."""

    def __init__(self, parent: ctk.CTkBaseClass) -> None:
        super().__init__(parent, fg_color=ThemeColors.BG_MAIN, corner_radius=0)

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        """Constrói os componentes da página de inicialização."""
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
            text="PROGRAMAS DE INICIALIZAÇÃO DO WINDOWS",
            font=Typography.card_title(),
            text_color=ThemeColors.ACCENT_LIGHT,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))

        ctk.CTkLabel(
            banner,
            text="Programas cadastrados no Registro do Windows (HKCU/HKLM) para inicializar automaticamente com a sessão do usuário.",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

        self._startup_list_container = ctk.CTkFrame(self, fg_color="transparent")
        self._startup_list_container.pack(fill="x", padx=LayoutDimensions.PAD_SM)

    def update_data(self) -> None:
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
            card = ctk.CTkFrame(
                self._startup_list_container,
                fg_color=ThemeColors.BG_SURFACE,
                border_width=LayoutDimensions.BORDER_WIDTH,
                border_color=ThemeColors.BORDER,
                corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
            )
            card.pack(fill="x", pady=3)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 2))
            ctk.CTkLabel(top, text=app.name, font=(Typography.FONT_FAMILY, 12, "bold"), text_color=ThemeColors.TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(top, text=app.location, font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED).pack(side="right")

            ctk.CTkLabel(
                card,
                text=f"Executável: {app.command}",
                font=Typography.caption(),
                text_color=ThemeColors.TEXT_MUTED,
                anchor="w",
            ).pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))
