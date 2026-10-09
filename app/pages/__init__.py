"""Módulo de páginas desacopladas da interface — Sollaris Nova."""

from app.pages.cleaner import CleanerPage
from app.pages.diagnostics import DiagnosticsPage
from app.pages.game_mode import GameModePage
from app.pages.history import HistoryPage
from app.pages.overview import OverviewPage
from app.pages.settings import SettingsPage
from app.pages.startup import StartupPage

__all__ = [
    "CleanerPage",
    "DiagnosticsPage",
    "GameModePage",
    "HistoryPage",
    "OverviewPage",
    "SettingsPage",
    "StartupPage",
]
