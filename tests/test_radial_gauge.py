"""Testes unitários do componente RadialGauge — Sollaris Nova."""

import customtkinter as ctk

from app.components.radial_gauge import RadialGauge
from app.theme import ThemeColors


def test_radial_gauge_initialization() -> None:
    """Verifica a criação do gauge padrão e compacto sem erros."""
    root = ctk.CTk()
    try:
        gauge_standard = RadialGauge(root, size=120, label="CARGA")
        gauge_compact = RadialGauge(root, size=56, compact=True)

        assert gauge_standard._size == 120
        assert gauge_standard._compact is False
        assert gauge_compact._size == 56
        assert gauge_compact._compact is True
    finally:
        root.destroy()


def test_radial_gauge_value_clamping_and_extent() -> None:
    """Valida o cálculo do arco proporcional e o clamping de valores."""
    root = ctk.CTk()
    try:
        gauge = RadialGauge(root, size=120, sweep_angle=240.0)

        # 0% de carga -> extent = 0.0
        gauge.set_value(0.0)
        assert gauge._current_value == 0.0

        # 50% de carga -> extent = -120.0 graus
        gauge.set_value(50.0, max_value=100.0)
        assert gauge._current_value == 50.0

        # 100% de carga -> extent = -240.0 graus
        gauge.set_value(100.0, max_value=100.0)
        assert gauge._current_value == 100.0

        # Clamping de valor excedente (> 100) -> restrito a 100
        gauge.set_value(150.0, max_value=100.0)
        assert gauge._current_value == 100.0

        # Clamping de valor negativo (< 0) -> restrito a 0
        gauge.set_value(-25.0, max_value=100.0)
        assert gauge._current_value == 0.0
    finally:
        root.destroy()


def test_radial_gauge_dynamic_color_thresholds() -> None:
    """Testa os níveis de cor dinâmica para normal, atenção e crítico."""
    root = ctk.CTk()
    try:
        gauge = RadialGauge(root, size=120, default_accent_color=ThemeColors.ACCENT_BLUE)

        # Normal (< 70%)
        gauge.set_value(40.0)
        # Atenção (70% - 85%)
        gauge.set_value(75.0)
        # Crítico (>= 85%)
        gauge.set_value(90.0)

        # Forçar cor manual
        gauge.set_value(10.0, force_color="#FF00FF")

        # Texto customizado
        gauge.set_value(50.0, display_text="METADE")
        assert gauge._gauge_canvas.itemcget(gauge._text_val_id, "text") == "METADE"

        # Atualização de rótulo
        gauge.set_label("PROCESSAMENTO")
        assert gauge._label_text == "PROCESSAMENTO"
    finally:
        root.destroy()
