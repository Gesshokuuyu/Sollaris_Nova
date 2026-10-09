"""Página de Limpeza Segura de Arquivos Temporários — Sollaris Nova.

Executa varredura e limpeza não-destrutiva de temporários e caches do sistema e do usuário.
"""

from __future__ import annotations

import contextlib
import threading

import customtkinter as ctk

from app.theme import LayoutDimensions, ThemeColors, Typography
from core.cleaner import CleanerScanner, TempCategorySummary
from core.hardware import format_bytes


class CleanerPage(ctk.CTkScrollableFrame):
    """Página de Limpeza Segura de Temporários."""

    def __init__(self, parent: ctk.CTkBaseClass) -> None:
        super().__init__(parent, fg_color=ThemeColors.BG_MAIN, corner_radius=0)

        self.grid_columnconfigure(0, weight=1)
        self._is_active = True
        self._build_ui()

    def _build_ui(self) -> None:
        """Constrói os componentes visuais da página de limpeza."""
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
            text="LIMPEZA SEGURA DE TEMPORÁRIOS",
            font=Typography.card_title(),
            text_color=ThemeColors.ACCENT_LIGHT,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))

        ctk.CTkLabel(
            banner,
            text="Varre apenas locais estritamente autorizados do usuário e caches temporários. Nenhuma exclusão automática destrutiva é realizada.",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(anchor="w", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))

        self._cleaner_cards_container = ctk.CTkFrame(self, fg_color="transparent")
        self._cleaner_cards_container.pack(fill="x", padx=LayoutDimensions.PAD_SM)

        self._cleaner_scan_btn = ctk.CTkButton(
            self,
            text="Analisar Espaço Recuperável",
            font=Typography.body_regular(),
            fg_color=ThemeColors.ACCENT_BLUE,
            hover_color=ThemeColors.ACCENT_HOVER,
            command=self._run_cleaner_scan,
            height=36,
        )
        self._cleaner_scan_btn.pack(pady=LayoutDimensions.PAD_LG)

    def _run_cleaner_scan(self) -> None:
        """Executa a varredura não-destrutiva de temporários em background sem travar a interface."""
        for widget in self._cleaner_cards_container.winfo_children():
            widget.destroy()

        self._cleaner_scan_btn.configure(text="Analisando pastas...", state="disabled")

        def _worker() -> None:
            categories = CleanerScanner.scan_temporary_files()
            if self._is_active:
                with contextlib.suppress(Exception):
                    self.after(0, lambda: self._render_cleaner_results(categories))

        threading.Thread(target=_worker, daemon=True, name="CleanerScanThread").start()

    def _render_cleaner_results(self, categories: list[TempCategorySummary]) -> None:
        """Renderiza os resultados da análise de temporários na interface."""
        if not self._is_active:
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
            c = ctk.CTkFrame(
                self._cleaner_cards_container,
                fg_color=ThemeColors.BG_SURFACE,
                border_width=LayoutDimensions.BORDER_WIDTH,
                border_color=ThemeColors.BORDER,
                corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
            )
            c.pack(fill="x", pady=4)

            top = ctk.CTkFrame(c, fg_color="transparent")
            top.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 2))
            ctk.CTkLabel(top, text=cat.name, font=(Typography.FONT_FAMILY, 12, "bold"), text_color=ThemeColors.TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(top, text=f"{format_bytes(cat.size_bytes)} ({cat.file_count} arquivos)", font=Typography.caption(), text_color=ThemeColors.ACCENT_LIGHT).pack(side="right")

            ctk.CTkLabel(c, text=f"Local: {cat.path}", font=Typography.caption(), text_color=ThemeColors.TEXT_INACTIVE, anchor="w").pack(fill="x", padx=LayoutDimensions.PAD_LG)
            ctk.CTkLabel(c, text=cat.description, font=Typography.caption(), text_color=ThemeColors.TEXT_MUTED, anchor="w").pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(2, LayoutDimensions.PAD_MD))

    def destroy(self) -> None:
        self._is_active = False
        super().destroy()
