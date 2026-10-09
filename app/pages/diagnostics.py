"""Página de Diagnóstico do Sistema — Sollaris Nova.

Apresenta as avaliações técnicas explicáveis baseadas nas métricas e regras de hardware.
"""

from __future__ import annotations

import customtkinter as ctk

from app.theme import LayoutDimensions, ThemeColors, Typography
from core.diagnostics import DiagnosticEngine, FindingLevel
from core.hardware import SystemSnapshot


class DiagnosticsPage(ctk.CTkScrollableFrame):
    """Página de Diagnóstico Técnico Explicável."""

    def __init__(self, parent: ctk.CTkBaseClass) -> None:
        super().__init__(parent, fg_color=ThemeColors.BG_MAIN, corner_radius=0)

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        """Constrói o cabeçalho e container de diagnósticos."""
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
            text="MOTOR DE DIAGNÓSTICO EXPLICÁVEL",
            font=Typography.card_title(),
            text_color=ThemeColors.ACCENT_LIGHT,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))

        ctk.CTkLabel(
            banner,
            text="Avaliações técnicas baseadas na persistência e limites reais de hardware, sem pontuações artificiais de saúde.",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

        self._diag_findings_container = ctk.CTkFrame(self, fg_color="transparent")
        self._diag_findings_container.pack(fill="x", padx=LayoutDimensions.PAD_SM)

    def update_data(self, snap: SystemSnapshot) -> None:
        """Atualiza a lista de diagnósticos técnicos com base no snapshot atual."""
        for widget in self._diag_findings_container.winfo_children():
            widget.destroy()

        findings = DiagnosticEngine.evaluate(snap)
        for f in findings:
            card = ctk.CTkFrame(
                self._diag_findings_container,
                fg_color=ThemeColors.BG_SURFACE,
                border_width=LayoutDimensions.BORDER_WIDTH,
                border_color=ThemeColors.BORDER,
                corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
            )
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
