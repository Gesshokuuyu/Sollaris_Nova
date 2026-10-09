"""Menu lateral técnico de navegação — Sollaris Nova.

Fornece a barra lateral persistente de 220px com navegação limpa e ícones
técnicos monocromáticos (sem emojis), estilizada conforme o Design System.
"""

import logging
import tkinter as tk
from collections.abc import Callable
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from app.theme import LayoutDimensions, ThemeColors, Typography

logger = logging.getLogger("sollaris_nova.sidebar")


class Sidebar(ctk.CTkFrame):
    """Barra lateral técnica de navegação com 220px de largura fixa."""

    def __init__(
        self,
        master: ctk.CTk,
        on_navigate: Callable[[str], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            width=LayoutDimensions.SIDEBAR_WIDTH,
            fg_color=ThemeColors.BG_SIDEBAR,
            corner_radius=0,
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            **kwargs,
        )
        self.grid_propagate(False)
        self._on_navigate = on_navigate
        self._active_route = "overview"

        self._icon_images: dict[str, tuple[ctk.CTkImage, ctk.CTkImage]] = {}
        self._nav_buttons: dict[str, ctk.CTkButton] = {}

        self._load_nav_icons()
        self._build_header()
        self._build_navigation_items()
        self._build_footer()

    def _load_nav_icons(self) -> None:
        """Carrega os ícones monocromáticos de navegação técnica."""
        icons_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "nav_icons"
        routes = [
            "overview",
            "diagnostics",
            "cleaner",
            "startup",
            "game_mode",
            "history",
            "settings",
        ]

        for route in routes:
            normal_path = icons_dir / f"nav_{route}.png"
            active_path = icons_dir / f"nav_{route}_active.png"

            if normal_path.exists() and active_path.exists():
                try:
                    img_normal = Image.open(normal_path).resize((18, 18), Image.Resampling.LANCZOS)
                    img_active = Image.open(active_path).resize((18, 18), Image.Resampling.LANCZOS)

                    ctk_normal = ctk.CTkImage(light_image=img_normal, dark_image=img_normal, size=(18, 18))
                    ctk_active = ctk.CTkImage(light_image=img_active, dark_image=img_active, size=(18, 18))

                    self._icon_images[route] = (ctk_normal, ctk_active)
                except (OSError, tk.TclError) as exc:
                    logger.debug("Falha ao carregar ícone %s: %s", route, exc)

    def _build_header(self) -> None:
        """Cria o cabeçalho com logotipo e identificação técnica."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(
            fill="x",
            padx=LayoutDimensions.PAD_LG,
            pady=(LayoutDimensions.PAD_XL, LayoutDimensions.PAD_LG),
        )

        logo_path = Path(__file__).resolve().parent.parent.parent / "assets" / "icon_transparent.png"
        if not logo_path.exists():
            logo_path = Path(__file__).resolve().parent.parent.parent / "assets" / "icon.png"

        if logo_path.exists():
            try:
                pil_img = Image.open(logo_path).resize((32, 32), Image.Resampling.LANCZOS)
                self._logo_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(32, 32))
                logo_label = ctk.CTkLabel(header_frame, image=self._logo_image, text="")
                logo_label.pack(side="left", padx=(0, LayoutDimensions.PAD_SM))
            except (OSError, tk.TclError) as exc:
                logger.debug("Falha ao exibir logo na barra lateral: %s", exc)

        titles_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        titles_box.pack(side="left", fill="x", expand=True)

        app_title = ctk.CTkLabel(
            titles_box,
            text="SOLLARIS",
            font=(Typography.FONT_FAMILY, 15, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY,
            anchor="w",
        )
        app_title.pack(fill="x")

        app_subtitle = ctk.CTkLabel(
            titles_box,
            text="PC OPTIMIZER",
            font=(Typography.FONT_FAMILY, 10, "normal"),
            text_color=ThemeColors.ACCENT_LIGHT,
            anchor="w",
        )
        app_subtitle.pack(fill="x")

    def _build_navigation_items(self) -> None:
        """Cria a lista de botões de navegação técnica sem emojis."""
        self._nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._nav_frame.pack(
            fill="both",
            expand=True,
            padx=LayoutDimensions.PAD_MD,
            pady=LayoutDimensions.PAD_SM,
        )

        nav_items = [
            ("overview", "Visão Geral"),
            ("diagnostics", "Diagnóstico"),
            ("cleaner", "Limpeza"),
            ("startup", "Inicialização"),
            ("game_mode", "Modo Game"),
            ("history", "Histórico"),
            ("settings", "Configurações"),
        ]

        for route_id, label in nav_items:
            is_active = route_id == self._active_route
            icon_tuple = self._icon_images.get(route_id)
            current_icon = icon_tuple[1] if (icon_tuple and is_active) else (icon_tuple[0] if icon_tuple else None)

            btn = ctk.CTkButton(
                self._nav_frame,
                text=f"  {label}",
                image=current_icon,
                compound="left",
                anchor="w",
                font=(Typography.FONT_FAMILY, 12, "bold" if is_active else "normal"),
                height=38,
                corner_radius=LayoutDimensions.CORNER_RADIUS_BUTTON,
                fg_color=ThemeColors.ACCENT_BLUE if is_active else "transparent",
                hover_color=ThemeColors.ACCENT_HOVER if is_active else ThemeColors.BG_CARD_HOVER,
                text_color=ThemeColors.TEXT_PRIMARY if is_active else ThemeColors.TEXT_MUTED,
                command=lambda r=route_id: self._handle_click(r),
            )
            btn.pack(fill="x", pady=2)
            self._nav_buttons[route_id] = btn

    def _handle_click(self, route_id: str) -> None:
        """Gerencia a seleção de rota."""
        self.set_active_route(route_id)
        if self._on_navigate:
            self._on_navigate(route_id)

    def set_active_route(self, route_id: str) -> None:
        """Atualiza visualmente o botão selecionado e seus ícones."""
        self._active_route = route_id
        for rid, btn in self._nav_buttons.items():
            is_active = rid == route_id
            icon_tuple = self._icon_images.get(rid)
            active_icon = icon_tuple[1] if (icon_tuple and is_active) else (icon_tuple[0] if icon_tuple else None)

            if is_active:
                btn.configure(
                    image=active_icon,
                    fg_color=ThemeColors.ACCENT_BLUE,
                    hover_color=ThemeColors.ACCENT_HOVER,
                    text_color=ThemeColors.TEXT_PRIMARY,
                    font=(Typography.FONT_FAMILY, 12, "bold"),
                )
            else:
                btn.configure(
                    image=active_icon,
                    fg_color="transparent",
                    hover_color=ThemeColors.BG_CARD_HOVER,
                    text_color=ThemeColors.TEXT_MUTED,
                    font=(Typography.FONT_FAMILY, 12, "normal"),
                )

    def _build_footer(self) -> None:
        """Cria o rodapé da barra lateral com status e versão técnica."""
        footer_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            border_width=LayoutDimensions.BORDER_WIDTH,
            border_color=ThemeColors.BORDER,
            corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        )
        footer_frame.pack(
            fill="x",
            side="bottom",
            padx=LayoutDimensions.PAD_MD,
            pady=LayoutDimensions.PAD_MD,
        )

        status_chip = ctk.CTkLabel(
            footer_frame,
            text="● Monitor Ativo",
            font=Typography.caption(),
            text_color=ThemeColors.STATUS_OK,
            anchor="w",
        )
        status_chip.pack(
            fill="x",
            padx=LayoutDimensions.PAD_SM,
            pady=(LayoutDimensions.PAD_SM, 2),
        )

        version_label = ctk.CTkLabel(
            footer_frame,
            text="v0.1.0-alpha • 64-bit",
            font=Typography.caption(),
            text_color=ThemeColors.TEXT_INACTIVE,
            anchor="w",
        )
        version_label.pack(
            fill="x",
            padx=LayoutDimensions.PAD_SM,
            pady=(0, LayoutDimensions.PAD_SM),
        )
