"""Página de Diagnóstico Técnico Explicável — Sollaris Nova.

Apresenta avaliações técnicas em 7 dimensões explicáveis, eliminando falsos positivos
por persistência temporal, filtros por severidade e controle integrado do Gravador de Voo (Flight Recorder).
Renderização fluida sem piscamento de interface através de reciclagem inteligente de widgets.
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from app.theme import LayoutDimensions, ThemeColors, Typography
from core.diagnostics import DiagnosticEngine, DiagnosticFinding, FindingLevel

if TYPE_CHECKING:
    from core.hardware import SystemSnapshot
    from core.processes import ProcessItem
    from core.recorder import SessionRecorder

logger = logging.getLogger("sollaris_nova.diagnostics_page")


class FindingCardWidget:
    """Widget reutilizável para exibição de apontamento técnico com atualização in-place (0ms de flicker)."""

    def __init__(self, parent: ctk.CTkBaseClass, on_navigate: Callable[[str], None] | None) -> None:
        self._on_navigate = on_navigate
        self._target_route: str | None = None
        self._is_packed = False

        self.frame = ctk.CTkFrame(
            parent,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )

        # 1. Topo: Categoria + Título e Badge de Severidade
        top_bar = ctk.CTkFrame(self.frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(LayoutDimensions.PAD_MD, 4))

        self.title_lbl = ctk.CTkLabel(
            top_bar,
            text="",
            font=(Typography.FONT_FAMILY, 12, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY,
        )
        self.title_lbl.pack(side="left")

        self.badge_lbl = ctk.CTkLabel(
            top_bar,
            text="",
            font=Typography.caption(),
        )
        self.badge_lbl.pack(side="right")

        # 2. Caixa de Evidência Técnica (destaque visual escuro #141E2B)
        evidence_box = ctk.CTkFrame(self.frame, fg_color="#141E2B", corner_radius=6)
        evidence_box.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(2, 6))

        evidence_content = ctk.CTkFrame(evidence_box, fg_color="transparent")
        evidence_content.pack(fill="x", padx=LayoutDimensions.PAD_MD, pady=6)

        ctk.CTkLabel(
            evidence_content,
            text="Evidência Técnica: ",
            font=(Typography.FONT_FAMILY, 10, "bold"),
            text_color=ThemeColors.ACCENT_LIGHT,
        ).pack(side="left")

        self.evidence_lbl = ctk.CTkLabel(
            evidence_content,
            text="",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_PRIMARY,
            anchor="w",
        )
        self.evidence_lbl.pack(side="left", fill="x", expand=True)

        # 3. Explicação Técnica (diagnóstico profundo)
        expl_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        expl_frame.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(2, 4))

        ctk.CTkLabel(
            expl_frame,
            text="Diagnóstico: ",
            font=(Typography.FONT_FAMILY, 10, "bold"),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(side="left", anchor="n")

        self.expl_lbl = ctk.CTkLabel(
            expl_frame,
            text="",
            font=Typography.body_regular(),
            text_color=ThemeColors.TEXT_MUTED,
            anchor="w",
            wraplength=760,
            justify="left",
        )
        self.expl_lbl.pack(side="left", fill="x", expand=True)

        # 4. Impacto Provável e Risco da Intervenção
        impact_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        impact_frame.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(2, 6))

        self.impact_lbl = ctk.CTkLabel(
            impact_frame,
            text="",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
            anchor="w",
            wraplength=780,
            justify="left",
        )
        self.impact_lbl.pack(fill="x")

        # 5. Barra Inferior: Reversibilidade, Ação Recomendada e Ação Contextual
        bottom_bar = ctk.CTkFrame(self.frame, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=LayoutDimensions.PAD_LG, pady=(2, LayoutDimensions.PAD_MD))

        self.rev_lbl = ctk.CTkLabel(
            bottom_bar,
            text="",
            font=Typography.caption(),
        )
        self.rev_lbl.pack(side="left", padx=(0, LayoutDimensions.PAD_MD))

        self.action_lbl = ctk.CTkLabel(
            bottom_bar,
            text="",
            font=Typography.caption(),
            text_color=ThemeColors.ACCENT_LIGHT,
            anchor="w",
        )
        self.action_lbl.pack(side="left", fill="x", expand=True)

        self.action_btn = ctk.CTkButton(
            bottom_bar,
            text="",
            font=Typography.caption(),
            fg_color=ThemeColors.BG_SURFACE,
            hover_color=ThemeColors.BG_CARD_HOVER,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.ACCENT_BLUE,
            text_color=ThemeColors.ACCENT_LIGHT,
            height=26,
            command=self._handle_action_click,
        )

    def _handle_action_click(self) -> None:
        """Executa a navegação contextual solicitada."""
        if self._target_route and self._on_navigate:
            self._on_navigate(self._target_route)

    def update_data(self, finding: DiagnosticFinding) -> None:
        """Atualiza o conteúdo dos widgets in-place sem recriação (elimina piscar de tela)."""
        level_styles = {
            FindingLevel.OPTIMAL: (ThemeColors.STATUS_OK, "Estável"),
            FindingLevel.INFO: (ThemeColors.ACCENT_LIGHT, "Informativo"),
            FindingLevel.WARNING: (ThemeColors.STATUS_WARN, "Atenção"),
            FindingLevel.CRITICAL: (ThemeColors.STATUS_ERROR, "Crítico"),
        }
        color, tag_text = level_styles.get(finding.level, (ThemeColors.TEXT_MUTED, "Diagnóstico"))

        # 1. Título e Badge
        title_text = f"[{finding.category}] {finding.title}"
        if self.title_lbl.cget("text") != title_text:
            self.title_lbl.configure(text=title_text)

        badge_text = f"[ {tag_text} ]"
        if self.badge_lbl.cget("text") != badge_text:
            self.badge_lbl.configure(text=badge_text, text_color=color)

        # 2. Evidência
        if self.evidence_lbl.cget("text") != finding.evidence:
            self.evidence_lbl.configure(text=finding.evidence)

        # 3. Explicação
        if self.expl_lbl.cget("text") != finding.technical_explanation:
            self.expl_lbl.configure(text=finding.technical_explanation)

        # 4. Impacto / Risco
        impact_text = f"Impacto: {finding.probable_impact} | Risco: {finding.risk}"
        if self.impact_lbl.cget("text") != impact_text:
            self.impact_lbl.configure(text=impact_text)

        # 5. Reversibilidade e Ação Recomendada
        rev_text = "[ Ação Reversível ]" if finding.is_reversible else "[ Alteração Permanente ]"
        rev_color = ThemeColors.STATUS_OK if finding.is_reversible else ThemeColors.STATUS_WARN
        if self.rev_lbl.cget("text") != rev_text:
            self.rev_lbl.configure(text=rev_text, text_color=rev_color)

        action_text = f"Recomendação: {finding.suggested_action}"
        if self.action_lbl.cget("text") != action_text:
            self.action_lbl.configure(text=action_text)

        # 6. Botão Contextual
        self._target_route = finding.target_route
        if finding.target_route and self._on_navigate:
            route_labels = {
                "overview": "Ver na Visão Geral",
                "cleaner": "Ir para Limpeza",
                "startup": "Ir para Inicialização",
                "history": "Ver Histórico",
            }
            btn_txt = route_labels.get(finding.target_route, "Analisar")
            self.action_btn.configure(text=btn_txt)
            if not self.action_btn.winfo_ismapped():
                self.action_btn.pack(side="right")
        elif self.action_btn.winfo_ismapped():
            self.action_btn.pack_forget()

    def pack_card(self) -> None:
        """Torna o card visível no container."""
        if not self._is_packed:
            self.frame.pack(fill="x", pady=6)
            self._is_packed = True

    def unpack_card(self) -> None:
        """Oculta o card sem destruí-lo (mantém instância em pool)."""
        if self._is_packed:
            self.frame.pack_forget()
            self._is_packed = False


class DiagnosticsPage(ctk.CTkScrollableFrame):
    """Página de Diagnóstico Técnico Explicável com Flight Recorder e Filtros sem flickering."""

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
        self._last_rendered_fingerprint: tuple[Any, ...] | None = None

        # Pool de cards reutilizáveis (evita reflow e piscamento na interface)
        self._card_pool: list[FindingCardWidget] = []

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

        # Card de estado vazio pré-instanciado (sem destroy/recreate)
        self._empty_card = ctk.CTkFrame(
            self._diag_findings_container,
            fg_color=ThemeColors.BG_SURFACE,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        ctk.CTkLabel(
            self._empty_card,
            text="Nenhum apontamento técnico registrado para este filtro de severidade.",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_MUTED,
        ).pack(padx=LayoutDimensions.PAD_LG, pady=LayoutDimensions.PAD_LG)

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
        """Modifica o filtro ativo e renderiza os cards correspondentes instantaneamente."""
        if self._active_filter == filter_id:
            return
        self._active_filter = filter_id
        self._update_filter_button_styles()
        self._render_findings(force=True)

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
        """Sincroniza o rótulo e cor do botão com o estado do SessionRecorder (suave, sem reflow)."""
        if not self._recorder:
            self._recorder_btn.configure(state="disabled", text="Gravador Indisponível")
            return

        if self._recorder.is_recording:
            elapsed = self._recorder.elapsed_seconds
            samples = self._recorder.sample_count
            mins, secs = divmod(elapsed, 60)
            rec_text = f"REC: {mins:02d}:{secs:02d} ({samples} amostras) | Parar"
            if self._recorder_btn.cget("text") != rec_text:
                self._recorder_btn.configure(
                    text=rec_text,
                    fg_color=ThemeColors.STATUS_ERROR,
                    hover_color="#991B1B",
                )
        elif self._recorder_btn.cget("text") != "Gravar Relatório Técnico":
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

        # Atualiza contadores dos botões de filtro sem reconstruir widgets
        count_all = len(findings)
        count_crit = sum(1 for f in findings if f.level == FindingLevel.CRITICAL)
        count_warn = sum(1 for f in findings if f.level == FindingLevel.WARNING)
        count_ok = sum(1 for f in findings if f.level == FindingLevel.OPTIMAL)

        txt_all = f"Todos ({count_all})"
        if self._filter_btn_all.cget("text") != txt_all:
            self._filter_btn_all.configure(text=txt_all)

        txt_crit = f"Críticos ({count_crit})"
        if self._filter_btn_crit.cget("text") != txt_crit:
            self._filter_btn_crit.configure(text=txt_crit)

        txt_warn = f"Atenção ({count_warn})"
        if self._filter_btn_warn.cget("text") != txt_warn:
            self._filter_btn_warn.configure(text=txt_warn)

        txt_ok = f"Estáveis ({count_ok})"
        if self._filter_btn_ok.cget("text") != txt_ok:
            self._filter_btn_ok.configure(text=txt_ok)

        self._render_findings()

    def _render_findings(self, force: bool = False) -> None:
        """Renderiza ou atualiza os cards explicativos de 7 dimensões in-place (sem piscar)."""
        filtered_findings = self._get_filtered_findings()

        # Gera fingerprint dos dados atuais para evitar qualquer reflow se nada mudou
        current_fingerprint = (
            self._active_filter,
            tuple(
                (f.category, f.level.value, f.title, f.evidence, f.technical_explanation, f.suggested_action, f.target_route)
                for f in filtered_findings
            ),
        )

        if not force and current_fingerprint == self._last_rendered_fingerprint:
            return

        self._last_rendered_fingerprint = current_fingerprint
        n_needed = len(filtered_findings)

        if n_needed == 0:
            for card in self._card_pool:
                card.unpack_card()
            self._empty_card.pack(fill="x", pady=8)
            return

        self._empty_card.pack_forget()

        # Expande o pool de cards apenas se necessário
        while len(self._card_pool) < n_needed:
            new_card = FindingCardWidget(self._diag_findings_container, self._on_navigate)
            self._card_pool.append(new_card)

        # Atualiza dados in-place e empacota na ordem
        for idx, finding in enumerate(filtered_findings):
            card = self._card_pool[idx]
            card.update_data(finding)
            card.pack_card()

        # Oculta cards excedentes do pool
        for idx in range(n_needed, len(self._card_pool)):
            self._card_pool[idx].unpack_card()

    def _get_filtered_findings(self) -> list[DiagnosticFinding]:
        """Filtra os apontamentos com base na seleção ativa."""
        if self._active_filter == "critical":
            return [f for f in self._current_findings if f.level == FindingLevel.CRITICAL]
        if self._active_filter == "warning":
            return [f for f in self._current_findings if f.level == FindingLevel.WARNING]
        if self._active_filter == "optimal":
            return [f for f in self._current_findings if f.level == FindingLevel.OPTIMAL]
        return self._current_findings
