"""Design System e Definições de Tema — Sollaris Nova (PC Optimizer).

Este módulo centraliza as constantes visuais, paleta de cores,
tipografia e espaçamentos, garantindo consistência técnica em toda a interface.
"""

from typing import Final


class ThemeColors:
    """Paleta de cores oficial do PC Optimizer (Azul e Preto Minimalista)."""

    # Superfícies e Fundos
    BG_MAIN: Final[str] = "#0B0F14"
    BG_SIDEBAR: Final[str] = "#0E141C"
    BG_SURFACE: Final[str] = "#111923"
    BG_CARD_HOVER: Final[str] = "#16202C"

    # Bordas e Divisores
    BORDER: Final[str] = "#263345"
    BORDER_FOCUSED: Final[str] = "#3B82F6"

    # Acentos e Interação
    ACCENT_BLUE: Final[str] = "#3B82F6"
    ACCENT_LIGHT: Final[str] = "#60A5FA"
    ACCENT_HOVER: Final[str] = "#2563EB"

    # Tipografia
    TEXT_PRIMARY: Final[str] = "#DCE6F1"
    TEXT_MUTED: Final[str] = "#8493A7"
    TEXT_INACTIVE: Final[str] = "#526071"

    # Estados Semânticos
    STATUS_OK: Final[str] = "#4FBF8A"      # Verde técnico
    STATUS_WARN: Final[str] = "#EAB308"    # Amarelo de atenção
    STATUS_ERROR: Final[str] = "#EF4444"   # Vermelho de alerta ou erro


class Typography:
    """Definições tipográficas padronizadas baseadas em Segoe UI."""

    FONT_FAMILY: Final[str] = "Segoe UI"

    @classmethod
    def header_title(cls) -> tuple[str, int, str]:
        """Título de seção principal (ex.: 'Visão Geral')."""
        return (cls.FONT_FAMILY, 20, "bold")

    @classmethod
    def card_title(cls) -> tuple[str, int, str]:
        """Rótulo de cartão métrico ou cabeçalho de tabela."""
        return (cls.FONT_FAMILY, 12, "bold")

    @classmethod
    def metric_value(cls) -> tuple[str, int, str]:
        """Valor numérico em destaque (ex.: '42%')."""
        return (cls.FONT_FAMILY, 28, "bold")

    @classmethod
    def metric_unit(cls) -> tuple[str, int, str]:
        """Unidade do valor numérico (ex.: 'GB', '%', '°C')."""
        return (cls.FONT_FAMILY, 13, "normal")

    @classmethod
    def body_regular(cls) -> tuple[str, int, str]:
        """Texto padrão de leitura e botões secundários."""
        return (cls.FONT_FAMILY, 12, "normal")

    @classmethod
    def caption(cls) -> tuple[str, int, str]:
        """Legendas pequenas, timestamps e notas de rodapé."""
        return (cls.FONT_FAMILY, 10, "normal")


class LayoutDimensions:
    """Dimensões padrão e regras de espaçamento da janela."""

    # Janela Principal
    WINDOW_DEFAULT_WIDTH: Final[int] = 1180
    WINDOW_DEFAULT_HEIGHT: Final[int] = 760
    WINDOW_MIN_WIDTH: Final[int] = 960
    WINDOW_MIN_HEIGHT: Final[int] = 640

    # Menu Lateral
    SIDEBAR_WIDTH: Final[int] = 220

    # Espaçamento (Padding & Margins)
    PAD_XS: Final[int] = 4
    PAD_SM: Final[int] = 8
    PAD_MD: Final[int] = 12
    PAD_LG: Final[int] = 16
    PAD_XL: Final[int] = 24

    # Raio de Bordas
    CORNER_RADIUS_CARD: Final[int] = 6
    CORNER_RADIUS_BUTTON: Final[int] = 4
    BORDER_WIDTH: Final[int] = 1
