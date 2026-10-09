"""Componente de Dica Técnica Flutuante (Tooltip) — Sollaris Nova.

Fornece balões de informação técnica contextual ao passar o mouse sobre
indicadores, gauges, cartões e medidores de núcleos, no padrão Segoe UI Dark.
"""

from __future__ import annotations

import contextlib
import tkinter as tk
from collections.abc import Callable

from app.theme import ThemeColors, Typography


class Tooltip:
    """Adiciona um tooltip contextual com atraso configurável a qualquer widget Tk/CTk."""

    def __init__(
        self,
        widget: tk.Misc,
        text_or_fn: str | Callable[[], str],
        delay_ms: int = 180,
    ) -> None:
        self._widget = widget
        self._text_or_fn = text_or_fn
        self._delay_ms = delay_ms
        self._tip_window: tk.Toplevel | None = None
        self._after_id: str | None = None

        self._widget.bind("<Enter>", self._on_enter, add="+")
        self._widget.bind("<Leave>", self._on_leave, add="+")
        self._widget.bind("<Motion>", self._on_motion, add="+")
        self._widget.bind("<Destroy>", self._on_destroy, add="+")

    def set_text(self, text_or_fn: str | Callable[[], str]) -> None:
        """Atualiza a mensagem ou callback do tooltip."""
        self._text_or_fn = text_or_fn

    def _on_enter(self, event: tk.Event) -> None:
        self._cancel_scheduled()
        self._after_id = self._widget.after(self._delay_ms, lambda: self._show_tip(event))

    def _on_leave(self, _event: tk.Event) -> None:
        self._cancel_scheduled()
        self._hide_tip()

    def _on_motion(self, event: tk.Event) -> None:
        if self._tip_window and self._tip_window.winfo_exists():
            x = event.x_root + 14
            y = event.y_root + 14
            self._tip_window.geometry(f"+{x}+{y}")

    def _on_destroy(self, _event: tk.Event) -> None:
        self._cancel_scheduled()
        self._hide_tip()

    def _cancel_scheduled(self) -> None:
        if self._after_id:
            with contextlib.suppress(Exception):
                self._widget.after_cancel(self._after_id)
            self._after_id = None

    def _show_tip(self, event: tk.Event) -> None:
        if self._tip_window or not self._widget.winfo_exists():
            return

        text = self._text_or_fn() if callable(self._text_or_fn) else str(self._text_or_fn)
        if not text:
            return

        try:
            cur_x, cur_y = self._widget.winfo_pointerxy()
            x = cur_x + 14
            y = cur_y + 14
        except Exception:  # noqa: BLE001
            x = event.x_root + 14
            y = event.y_root + 14

        self._tip_window = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        tw.geometry(f"+{x}+{y}")

        frame = tk.Frame(
            tw,
            bg=ThemeColors.BG_SIDEBAR,
            highlightthickness=1,
            highlightbackground=ThemeColors.BORDER,
            highlightcolor=ThemeColors.BORDER,
        )
        frame.pack(fill="both", expand=True)

        lbl = tk.Label(
            frame,
            text=text,
            justify="left",
            bg=ThemeColors.BG_SIDEBAR,
            fg=ThemeColors.TEXT_PRIMARY,
            font=(Typography.FONT_FAMILY, 9),
            padx=10,
            pady=6,
        )
        lbl.pack()

    def _hide_tip(self) -> None:
        if self._tip_window:
            with contextlib.suppress(Exception):
                self._tip_window.destroy()
            self._tip_window = None
