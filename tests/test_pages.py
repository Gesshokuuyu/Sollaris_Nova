"""Testes unitários para as páginas desacopladas da interface — Sollaris Nova."""

import customtkinter as ctk

from app.pages import (
    CleanerPage,
    DiagnosticsPage,
    GameModePage,
    HistoryPage,
    OverviewPage,
    SettingsPage,
    StartupPage,
)
from tests.test_window import _build_dummy_snapshot


def test_pages_instantiation_and_lifecycle() -> None:
    """Verifica a instanciação isolada de cada uma das páginas da interface."""
    root = ctk.CTk()
    try:
        overview = OverviewPage(root)
        diagnostics = DiagnosticsPage(root)
        cleaner = CleanerPage(root)
        startup = StartupPage(root)
        game_mode = GameModePage(root)
        history = HistoryPage(root)
        settings = SettingsPage(root)

        assert overview is not None
        assert diagnostics is not None
        assert cleaner is not None
        assert startup is not None
        assert game_mode is not None
        assert history is not None
        assert settings is not None
    finally:
        root.destroy()


def test_pages_data_updates() -> None:
    """Verifica a atualização de dados nas páginas modulares."""
    root = ctk.CTk()
    try:
        snap = _build_dummy_snapshot()

        # 1. Overview
        overview = OverviewPage(root)
        overview.update_data(snap, procs=[])
        assert overview._cpu_gauge._current_value == snap.cpu.total_percent

        # 2. Diagnostics
        diagnostics = DiagnosticsPage(root)
        diagnostics.update_data(snap)
        assert len(diagnostics._diag_findings_container.winfo_children()) >= 1

        # 3. History
        history = HistoryPage(root)
        history.update_data(duration_seconds=120, cpu_samples=[20.0, 30.0], ram_samples=[50.0, 60.0])
        assert "25.0 %" in history._hist_cpu_avg_lbl.cget("text")
        assert "30.0 %" in history._hist_cpu_max_lbl.cget("text")

        # 4. Settings callback
        called_sec: list[float] = []
        settings = SettingsPage(root, on_change_interval=lambda s: called_sec.append(s))
        settings._handle_interval_change(1.5)
        assert called_sec == [1.5]
    finally:
        root.destroy()


def test_diagnostics_page_features(tmp_path) -> None:
    """Verifica filtros de severidade, gravação de sessão e navegação contextual na DiagnosticsPage."""
    from core.recorder import SessionRecorder

    root = ctk.CTk()
    try:
        recorder = SessionRecorder(reports_dir=tmp_path)
        navigated_routes: list[str] = []
        diag_page = DiagnosticsPage(
            root,
            recorder=recorder,
            on_navigate=lambda r: navigated_routes.append(r),
        )

        snap = _build_dummy_snapshot()
        diag_page.update_data(snap)

        # Valida contadores
        assert "Todos" in diag_page._filter_btn_all.cget("text")
        assert len(diag_page._diag_findings_container.winfo_children()) >= 1

        # Filtro: Estáveis
        diag_page._set_active_filter("optimal")
        assert diag_page._active_filter == "optimal"

        # Filtro: Críticos
        diag_page._set_active_filter("critical")
        assert diag_page._active_filter == "critical"

        # Gravador de sessão via botão
        assert not recorder.is_recording
        diag_page._toggle_recording()
        assert recorder.is_recording
        assert "REC:" in diag_page._recorder_btn.cget("text")

        # Parar gravação
        diag_page._toggle_recording()
        assert not recorder.is_recording
        assert "Gravar Relatório" in diag_page._recorder_btn.cget("text")
        assert diag_page._report_notice_frame.winfo_ismapped() or diag_page._report_notice_label.cget("text")
    finally:
        root.destroy()
