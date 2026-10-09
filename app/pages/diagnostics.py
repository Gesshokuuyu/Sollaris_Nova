"""Página de Diagnóstico Técnico Explicável — Sollaris Nova.

Apresenta avaliações técnicas em 7 dimensões explicáveis, eliminando falsos positivos
por persistência temporal, filtros por severidade e controle integrado do Gravador de Voo (Flight Recorder).
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Callable
from typing import TYPE_CHECKING

import customtkinter as ctk

from app.theme import LayoutDimensions, ThemeColors, Typography
from core.diagnostics import DiagnosticEngine, DiagnosticFinding, FindingLevel

if TYPE_CHECKING:
    from core.hardware import SystemSnapshot
    from core.processes import ProcessItem
    from core.recorder import SessionRecorder

logger = logging.getLogger("sollaris_nova.diagnostics_page")


class DiagnosticsPage(ctk.CTkScrollableFrame):
    """Página de Diagnóstico Técnico Explicável com Flight Recorder e Filtros."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        recorder: SessionRecorder | None = None,
        on_navigate: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent, fg_color=ThemeColors.BG_MAIN, corner_radius=0)

        self.grid_columnconfigure(0, weight=1)
        self._recorder = recorder
        self._on_navigate = on_navigate

        self._active_filter: str = "all"
        self._last_snapshot: SystemSnapshot | None = None
        self._current_findings: list[DiagnosticFinding] = []
        self._last_reported_file: str | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        """Constrói a estrutura visual completa da página."""
        # 1. Banner superior e controle do Relator / Gravador de Voo
        self._banner = ctk.CTkFrame(
            self,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        self._banner.pack(fill="x", pady=(0, LayoutDimensions.PAD_MD), padx=LayoutDimensions.PAD_SM)
        self._banner.grid_columnconfigure(0, weight=1)

        # Cabeçalho e Subtítulo
        header_box = ctk.CTkFrame(self._banner, fg_color="transparent")
        header_box.grid(row=0, column=0, sticky="ew", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 2))

        ctk.CTkLabel(
            header_box,
            text="MOTOR DE DIAGNÓSTICO EXPLICÁVEL",
            font=Typography.card_title(),
            text_color=ThemeColors.ACCENT_LIGHT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_box,
            text="Avaliações técnicas baseadas na persistência e limites reais de hardware, sem pontuações artificiais de saúde.",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # Botão de Ação do Gravador de Voo (Flight Recorder)
        actions_box = ctk.CTkFrame(self._banner, fg_color="transparent")
        actions_box.grid(row=0, column=1, sticky="e", padx=LayoutDimensions.PAD_LG, pady=LayoutDimensions.PAD_MD)

        self._recorder_btn = ctk.CTkButton(
            actions_box,
            text="Gravar Relatório Técnico",
            font=Typography.body_regular(),
            fg_color=ThemeColors.ACCENT_BLUE,
            hover_color=ThemeColors.ACCENT_HOVER,
            text_color=ThemeColors.TEXT_PRIMARY,
            height=34,
            command=self._toggle_recording,
        )
        self._recorder_btn.pack(side="right")

        # Notificação de Relatório Concluído (oculto por padrão)
        self._report_notice_frame = ctk.CTkFrame(self._banner, fg_color="#141E2B", corner_radius=6)
        self._report_notice_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=LayoutDimensions.PAD_LG, pady=(0, LayoutDimensions.PAD_MD))
        self._report_notice_frame.grid_remove()

        self._report_notice_label = ctk.CTkLabel(
            self._report_notice_frame,
            text="Relatório técnico gravado com sucesso.",
            font=Typography.caption(),
            text_color=ThemeColors.STATUS_OK,
            anchor="w",
        )
        self._report_notice_label.pack(side="left", padx=LayoutDimensions.PAD_MD, pady=6)

        self._open_reports_btn = ctk.CTkButton(
            self._report_notice_frame,
            text="Abrir Pasta de Relatórios",
            font=Typography.caption(),
            fg_color=ThemeColors.BG_SURFACE,
            hover_color=ThemeColors.BG_CARD_HOVER,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            text_color=ThemeColors.TEXT_PRIMARY,
            height=26,
            command=self._open_reports_folder,
        )
        self._open_reports_btn.pack(side="right", padx=LayoutDimensions.PAD_MD, pady=6)

        # 2. Barra de Filtros e Contadores por Severidade
        self._filters_bar = ctk.CTkFrame(self, fg_color="transparent")
        self._filters_bar.pack(fill="x", padx=LayoutDimensions.PAD_SM, pady=(0, LayoutDimensions.PAD_MD))

        self._filter_btn_all = self._create_filter_button("Todos (0)", "all")
        self._filter_btn_crit = self._create_filter_button("Críticos (0)", "critical")
        self._filter_btn_warn = self._create_filter_button("Atenção (0)", "warning")
        self._filter_btn_ok = self._create_filter_button("Estáveis (0)", "optimal")

        self._filter_buttons = {
            "all": self._filter_btn_all,
            "critical": self._filter_btn_crit,
            "warning": self._filter_btn_warn,
            "optimal": self._filter_btn_ok,
        }
        self._update_filter_button_styles()

        # 3. Container da lista de cards de diagnósticos
        self._diag_findings_container = ctk.CTkFrame(self, fg_color="transparent")
        self._diag_findings_container.pack(fill="x", padx=LayoutDimensions.PAD_SM)

    def _create_filter_button(self, label: str, filter_id: str) -> ctk.CTkButton:
        """Cria um botão em estilo pill de filtro de severidade."""
        btn = ctk.CTkButton(
            self._filters_bar,
            text=label,
            font=Typography.caption(),
            height=28,
            corner_radius=14,
            command=lambda: self._set_active_filter(filter_id),
        )
        btn.pack(side="left", padx=(0, 8))
        return btn

    def _set_active_filter(self, filter_id: str) -> None:
        """Modifica o filtro ativo e renderiza os cards correspondentes."""
        if self._active_filter == filter_id:
            return
        self._active_filter = filter_id
        self._update_filter_button_styles()
        self._render_findings()

    def _update_filter_button_styles(self) -> None:
        """Atualiza visualmente os botões de filtro para destacar o ativo."""
        for fid, btn in self._filter_buttons.items():
            if fid == self._active_filter:
                btn.configure(
                    fg_color=ThemeColors.ACCENT_BLUE,
                    text_color="#FFFFFF",
                    hover_color=ThemeColors.ACCENT_HOVER,
                    border_width=0,
                )
            else:
                btn.configure(
                    fg_color=ThemeColors.BG_SURFACE,
                    text_color=ThemeColors.TEXT_MUTED,
                    hover_color=ThemeColors.BG_CARD_HOVER,
                    border_width=LayoutDimensions.BORDER_WIDTH,
                    border_color=ThemeColors.BORDER,
                )

    def _toggle_recording(self) -> None:
        """Inicia ou encerra a sessão contínua do Gravador de Voo."""
        if not self._recorder:
            return

        if not self._recorder.is_recording:
            if self._last_snapshot:
                file_path = self._recorder.start_session(self._last_snapshot)
                self._report_notice_frame.grid_remove()
                self._update_recorder_button_state()
                logger.info("Gravação de sessão técnica iniciada em: %s", file_path)
        else:
            summary = self._recorder.stop_session()
            self._update_recorder_button_state()
            if summary:
                file_name = os.path.basename(summary.get("file_path", "relatorio.log"))
                samples = summary.get("sample_count", 0)
                duration = summary.get("duration_seconds", 0)
                mins, secs = divmod(duration, 60)
                self._report_notice_label.configure(
                    text=f"Relatório gravado: {file_name} ({mins:02d}:{secs:02d} monitorados, {samples} amostras).",
                )
                self._report_notice_frame.grid()
                logger.info("Gravação de sessão finalizada: %s", summary)

    def _update_recorder_button_state(self) -> None:
        """Sincroniza o rótulo e cor do botão com o estado do SessionRecorder."""
        if not self._recorder:
            self._recorder_btn.configure(state="disabled", text="Gravador Indisponível")
            return

        if self._recorder.is_recording:
            elapsed = self._recorder.elapsed_seconds
            samples = self._recorder.sample_count
            mins, secs = divmod(elapsed, 60)
            self._recorder_btn.configure(
                text=f"REC: {mins:02d}:{secs:02d} ({samples} amostras) | Parar",
                fg_color=ThemeColors.STATUS_ERROR,
                hover_color="#991B1B",
            )
        else:
            self._recorder_btn.configure(
                text="Gravar Relatório Técnico",
                fg_color=ThemeColors.ACCENT_BLUE,
                hover_color=ThemeColors.ACCENT_HOVER,
            )

    def _open_reports_folder(self) -> None:
        """Abre o diretório de relatórios técnicos no explorador de arquivos do sistema operacional."""
        try:
            reports_dir = self._recorder.reports_dir if self._recorder else os.path.abspath("data/reports")
            os.makedirs(reports_dir, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(str(reports_dir))
            else:
                import subprocess

                subprocess.Popen(["xdg-open", str(reports_dir)])
        except Exception:
            logger.exception("Falha ao abrir pasta de relatórios técnicos.")

    def update_data(
        self,
        snap: SystemSnapshot,
        cpu_history: list[float] | None = None,
        ram_history: list[float] | None = None,
        processes: list[ProcessItem] | None = None,
    ) -> None:
        """Atualiza os diagnósticos técnicos explicáveis cruzando histórico temporal e snapshot."""
        self._last_snapshot = snap
        self._update_recorder_button_state()

        # Avaliação de saúde técnica com histórico temporal
        findings = DiagnosticEngine.evaluate_with_history(
            snapshot=snap,
            cpu_history=cpu_history,
            ram_history=ram_history,
            processes=processes,
        )
        self._current_findings = findings

        # Atualiza contadores dos botões de filtro
        count_all = len(findings)
        count_crit = sum(1 for f in findings if f.level == FindingLevel.CRITICAL)
        count_warn = sum(1 for f in findings if f.level == FindingLevel.WARNING)
        count_ok = sum(1 for f in findings if f.level == FindingLevel.OPTIMAL)

        self._filter_btn_all.configure(text=f"Todos ({count_all})")
        self._filter_btn_crit.configure(text=f"Críticos ({count_crit})")
        self._filter_btn_warn.configure(text=f"Atenção ({count_warn})")
        self._filter_btn_ok.configure(text=f"Estáveis ({count_ok})")

        self._render_findings()

    def _render_findings(self) -> None:
        """Renderiza os cards explicativos de 7 dimensões respeitando o filtro ativo."""
        for widget in self._diag_findings_container.winfo_children():
            widget.destroy()

        filtered_findings = self._get_filtered_findings()

        if not filtered_findings:
            empty_card = ctk.CTkFrame(
                self._diag_findings_container,
                fg_color=ThemeColors.BG_SURFACE,
                border_width=LayoutDimensions.BORDER_WIDTH,
                border_color=ThemeColors.BORDER,
                corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
            )
            empty_card.pack(fill="x", pady=8)
            ctk.CTkLabel(
                empty_card,
                text="Nenhum apontamento técnico registrado para este filtro de severidade.",
                font=Typography.caption(),
                text_color=ThemeColors.TEXT_MUTED,
            ).pack(padx=LayoutDimensions.PAD_LG, pady=LayoutDimensions.PAD_LG)
            return

        for finding in filtered_findings:
            self._build_finding_card(finding)

    def _get_filtered_findings(self) -> list[DiagnosticFinding]:
        """Filtra os apontamentos com base na seleção ativa."""
        if self._active_filter == "critical":
            return [f for f in self._current_findings if f.level == FindingLevel.CRITICAL]
        if self._active_filter == "warning":
            return [f for f in self._current_findings if f.level == FindingLevel.WARNING]
        if self._active_filter == "optimal":
            return [f for f in self._current_findings if f.level == FindingLevel.OPTIMAL]
        return self._current_findings

    def _build_finding_card(self, finding: DiagnosticFinding) -> None:
        """Constrói um card estruturado com as 7 dimensões explicáveis e ação contextual."""
        card = ctk.CTkFrame(
            self._diag_findings_container,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        card.pack(fill="x", pady=6)

        level_styles = {
            FindingLevel.OPTIMAL: (ThemeColors.STATUS_OK, "Estável"),
            FindingLevel.INFO: (ThemeColors.ACCENT_LIGHT, "Informativo"),
            FindingLevel.WARNING: (ThemeColors.STATUS_WARN, "Atenção"),
            FindingLevel.CRITICAL: (ThemeColors.STATUS_ERROR, "Crítico"),
        }
        color, tag_text = level_styles.get(finding.level, (ThemeColors.TEXT_MUTED, "Diagnóstico"))

        # 1. Topo: Categoria + Título e Badge de Severidade
        top_bar = ctk.CTkFrame(card, fg_color="transparent")
        top_bar.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))

        ctk.CTkLabel(
            top_bar,
            text=f"[{finding.category}] {finding.title}",
            font=(Typography.FONT_FAMILY, 12, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY,
        ).pack(side="left")

        badge = ctk.CTkLabel(
            top_bar,
            text=f"[ {tag_text} ]",
            font=Typography.caption(),
            text_color=color,
        )
        badge.pack(side="right")

        # 2. Caixa de Evidência Técnica (destaque visual com fundo diferenciado)
        evidence_box = ctk.CTkFrame(card, fg_color="#141E2B", corner_radius=6)
        evidence_box.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(2, 6))

        evidence_content = ctk.CTkFrame(evidence_box, fg_color="transparent")
        evidence_content.pack(fill="x", padx=LayoutDimensions.PAD_MD, pady=6)

        ctk.CTkLabel(
            evidence_content,
            text="Evidência Técnica: ",
            font=(Typography.FONT_FAMILY, 10, "bold"),
            text_color=ThemeColors.ACCENT_LIGHT,
        ).pack(side="left")

        ctk.CTkLabel(
            evidence_content,
            text=finding.evidence,
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # 3. Explicação Técnica (diagnóstico profundo)
        expl_frame = ctk.CTkFrame(card, fg_color="transparent")
        expl_frame.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(2, 4))

        ctk.CTkLabel(
            expl_frame,
            text="Diagnóstico: ",
            font=(Typography.FONT_FAMILY, 10, "bold"),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(side="left", anchor="n")

        ctk.CTkLabel(
            expl_frame,
            text=finding.technical_explanation,
            font=Typography.body_regular(),
            text_color=ThemeColors.TEXT_MUTED,
            anchor="w",
            wraplength=760,
            justify="left",
        ).pack(side="left", fill="x", expand=True)

        # 4. Impacto Provável e Risco da Intervenção
        impact_frame = ctk.CTkFrame(card, fg_color="transparent")
        impact_frame.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(2, 6))

        impact_text = f"Impacto: {finding.probable_impact} | Risco: {finding.risk}"
        ctk.CTkLabel(
            impact_frame,
            text=impact_text,
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
            anchor="w",
            wraplength=780,
            justify="left",
        ).pack(fill="x")

        # 5. Barra Inferior: Reversibilidade, Ação Recomendada e Ação Contextual
        bottom_bar = ctk.CTkFrame(card, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(2, LayoutDimensions.PAD_MD))

        # Indicador de Reversibilidade
        rev_text = "Ação Reversível" if finding.is_reversible else "Alteração Permanente"
        rev_color = ThemeColors.STATUS_OK if finding.is_reversible else ThemeColors.STATUS_WARN
        ctk.CTkLabel(
            bottom_bar,
            text=f"[ {rev_text} ]",
            font=Typography.caption(),
            text_color=rev_color,
        ).pack(side="left", padx=(0, LayoutDimensions.PAD_MD))

        # Texto da Ação Recomendada
        ctk.CTkLabel(
            bottom_bar,
            text=f"Recomendação: {finding.suggested_action}",
            font=Typography.caption(),
            text_color=ThemeColors.ACCENT_LIGHT,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # Botão de Navegação Contextual
        if finding.target_route and self._on_navigate:
            route_labels = {
                "overview": "Ver na Visão Geral",
                "cleaner": "Ir para Limpeza",
                "startup": "Ir para Inicialização",
                "history": "Ver Histórico",
            }
            btn_text = route_labels.get(finding.target_route, "Analisar")
            ctk.CTkButton(
                bottom_bar,
                text=btn_text,
                font=Typography.caption(),
                fg_color=ThemeColors.BG_SURFACE,
                hover_color=ThemeColors.BG_CARD_HOVER,
                border_width=LayoutDimensions.BORDER_WIDTH,
                border_color=ThemeColors.ACCENT_BLUE,
                text_color=ThemeColors.ACCENT_LIGHT,
                height=26,
                command=lambda r=finding.target_route: self._on_navigate(r),
            ).pack(side="right")
