"""Testes de validação do ambiente de desenvolvimento e integridade de padrões."""

import re
import sys
from pathlib import Path

from app.theme import LayoutDimensions, ThemeColors, Typography


def test_python_version() -> None:
    """Garante que a versão do Python é 3.14 ou superior."""
    assert sys.version_info >= (3, 14), f"Versão do Python ({sys.version}) deve ser >= 3.14"


def test_core_dependencies_importable() -> None:
    """Verifica se as dependências essenciais do projeto estão instaladas."""
    import customtkinter  # noqa: F401
    import matplotlib  # noqa: F401
    import psutil  # noqa: F401
    import pytest  # noqa: F401

    assert True


def test_theme_tokens_integrity() -> None:
    """Valida se os tokens de cores do design system são válidos e seguem o spec."""
    hex_color_pattern = re.compile(r"^#[0-9a-fA-F]{6}$")

    # Verifica se as cores essenciais do spec estão definidas no formato hex válido
    colors = [
        ThemeColors.BG_MAIN,
        ThemeColors.BG_SIDEBAR,
        ThemeColors.BG_SURFACE,
        ThemeColors.BORDER,
        ThemeColors.ACCENT_BLUE,
        ThemeColors.ACCENT_LIGHT,
        ThemeColors.TEXT_PRIMARY,
        ThemeColors.TEXT_MUTED,
        ThemeColors.STATUS_OK,
        ThemeColors.STATUS_WARN,
        ThemeColors.STATUS_ERROR,
    ]

    for color in colors:
        assert hex_color_pattern.match(color), f"Cor inválida encontrada: {color}"

    # Validações dos valores exatos exigidos na especificação
    assert ThemeColors.BG_MAIN.upper() == "#0B0F14"
    assert ThemeColors.BG_SIDEBAR.upper() == "#0E141C"
    assert ThemeColors.BG_SURFACE.upper() == "#111923"
    assert ThemeColors.BORDER.upper() == "#263345"
    assert ThemeColors.ACCENT_BLUE.upper() == "#3B82F6"
    assert ThemeColors.ACCENT_LIGHT.upper() == "#60A5FA"
    assert ThemeColors.TEXT_PRIMARY.upper() == "#DCE6F1"
    assert ThemeColors.TEXT_MUTED.upper() == "#8493A7"
    assert ThemeColors.STATUS_OK.upper() == "#4FBF8A"
    assert ThemeColors.STATUS_WARN.upper() == "#EAB308"
    assert ThemeColors.STATUS_ERROR.upper() == "#EF4444"

    # Tipografia e dimensões
    assert Typography.FONT_FAMILY == "Segoe UI"
    assert LayoutDimensions.WINDOW_DEFAULT_WIDTH == 1180
    assert LayoutDimensions.WINDOW_DEFAULT_HEIGHT == 760
    assert LayoutDimensions.SIDEBAR_WIDTH == 220


def test_directory_structure_exists() -> None:
    """Verifica se todos os diretórios fundamentais da arquitetura foram criados."""
    root_dir = Path(__file__).resolve().parent.parent

    expected_directories = [
        root_dir / "docs" / "specs",
        root_dir / "docs" / "architecture",
        root_dir / "docs" / "standards",
        root_dir / "docs" / "changelogs",
        root_dir / "docs" / "setup",
        root_dir / "app" / "components",
        root_dir / "app" / "pages",
        root_dir / "core",
        root_dir / "database",
        root_dir / "safety",
        root_dir / "tests",
        root_dir / "data",
    ]

    for path in expected_directories:
        assert path.exists() and path.is_dir(), f"Diretório mandatório ausente: {path}"
