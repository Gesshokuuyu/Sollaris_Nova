"""Testes automatizados para o componente de Tooltip — Sollaris Nova."""

import tkinter as tk

import customtkinter as ctk

from app.components.tooltip import Tooltip


def test_tooltip_initialization() -> None:
    """Verifica a criação do Tooltip com string estática e função dinâmica."""
    root = ctk.CTk()
    try:
        btn = ctk.CTkButton(root, text="Teste")
        tip_static = Tooltip(btn, "Dica Estática", delay_ms=50)
        assert tip_static._text_or_fn == "Dica Estática"
        assert tip_static._tip_window is None

        # Função dinâmica
        dynamic_val = "Valor 1"
        tip_dynamic = Tooltip(btn, lambda: dynamic_val, delay_ms=50)
        assert callable(tip_dynamic._text_or_fn)
        assert tip_dynamic._text_or_fn() == "Valor 1"

        # Atualização dinâmica de texto
        tip_static.set_text("Novo Texto")
        assert tip_static._text_or_fn == "Novo Texto"
    finally:
        root.destroy()


def test_tooltip_show_and_hide_lifecycle() -> None:
    """Testa a exibição, cancelamento e fechamento seguro do popup de tooltip."""
    root = ctk.CTk()
    try:
        lbl = ctk.CTkLabel(root, text="Rótulo")
        lbl.pack()
        root.update_idletasks()

        tip = Tooltip(lbl, "Mensagem Técnica", delay_ms=10)

        # Mock event
        event = tk.Event()
        event.x_root = 100
        event.y_root = 100

        # Dispara exibição direta
        tip._show_tip(event)
        assert tip._tip_window is not None
        assert tip._tip_window.winfo_exists()

        # Oculta
        tip._hide_tip()
        assert tip._tip_window is None
    finally:
        root.destroy()
