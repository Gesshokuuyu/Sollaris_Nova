"""Ponto de entrada principal — Sollaris Nova (PC Optimizer).

Inicializa a aplicação desktop, configura logs estruturados e
carrega a interface com as configurações do Design System.
"""

import argparse
import logging
import platform
import sys
import tkinter as tk
from pathlib import Path
from typing import NoReturn

import customtkinter as ctk
import psutil

from app.theme import LayoutDimensions, ThemeColors, Typography

logger = logging.getLogger("sollaris_nova")


def configure_logging(verbose: bool = False) -> None:
    """Configura o sistema de logs local."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def check_environment() -> None:
    """Valida a integridade do ambiente e imprime o diagnóstico no terminal."""
    print("=" * 60)
    print(" Sollaris Nova (PC Optimizer) — Verificação de Ambiente")
    print("=" * 60)
    print(f"Sistema Operacional: {platform.system()} {platform.release()} ({platform.version()})")
    print(f"Arquitetura:         {platform.machine()}")
    print(f"Versão do Python:    {platform.python_version()} (Requerido >= 3.14)")
    print(f"Núcleos de CPU:      {psutil.cpu_count(logical=False)} físicos, {psutil.cpu_count(logical=True)} lógicos")
    mem = psutil.virtual_memory()
    print(f"Memória RAM Total:   {mem.total / (1024**3):.2f} GB (Disponível: {mem.available / (1024**3):.2f} GB)")
    print(f"CustomTkinter:       v{ctk.__version__}")
    print(f"Tema Base:           {ThemeColors.BG_MAIN} (Fundo Principal)")
    print("=" * 60)
    print("[OK] Ambiente validado com sucesso e em conformidade com a especificação.")


def launch_gui() -> None:
    """Inicializa a interface gráfica do usuário."""
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("PC Optimizer — Sollaris Nova (Ambiente Inicializado)")
    root.geometry(f"{LayoutDimensions.WINDOW_DEFAULT_WIDTH}x{LayoutDimensions.WINDOW_DEFAULT_HEIGHT}")
    root.minsize(LayoutDimensions.WINDOW_MIN_WIDTH, LayoutDimensions.WINDOW_MIN_HEIGHT)
    root.configure(fg_color=ThemeColors.BG_MAIN)

    icon_path = Path(__file__).resolve().parent / "assets" / "icon.ico"
    if icon_path.exists():
        try:
            root.iconbitmap(str(icon_path))
        except (OSError, tk.TclError) as exc:
            logger.debug("Não foi possível carregar o ícone da janela: %s", exc)

    center_frame = ctk.CTkFrame(
        root,
        fg_color=ThemeColors.BG_SURFACE,
        corner_radius=LayoutDimensions.CORNER_RADIUS_CARD,
        border_width=LayoutDimensions.BORDER_WIDTH,
        border_color=ThemeColors.BORDER,
    )
    center_frame.pack(expand=True, fill="both", padx=30, pady=30)

    title_label = ctk.CTkLabel(
        center_frame,
        text="SOLLARIS NOVA — PC OPTIMIZER",
        font=Typography.header_title(),
        text_color=ThemeColors.TEXT_PRIMARY,
    )
    title_label.pack(pady=(40, 10))

    status_label = ctk.CTkLabel(
        center_frame,
        text="Ambiente de desenvolvimento e padronização configurados com sucesso.",
        font=Typography.body_regular(),
        text_color=ThemeColors.STATUS_OK,
    )
    status_label.pack(pady=(0, 20))

    info_text = (
        "• Especificações ativas: docs/specs/PROJECT_SPEC.md\n"
        "• Arquitetura em camadas: docs/architecture/ARCHITECTURE.md\n"
        "• Design System: docs/standards/DESIGN_SYSTEM.md\n"
        "• Padrões de código: docs/standards/CODE_STANDARDS.md\n"
        "• Próxima etapa recomendada: Fase 1 (Monitoramento de CPU, RAM e Armazenamento)"
    )

    info_box = ctk.CTkLabel(
        center_frame,
        text=info_text,
        font=Typography.body_regular(),
        text_color=ThemeColors.TEXT_MUTED,
        justify="left",
    )
    info_box.pack(pady=20)

    close_btn = ctk.CTkButton(
        center_frame,
        text="Fechar",
        font=Typography.body_regular(),
        fg_color=ThemeColors.ACCENT_BLUE,
        hover_color=ThemeColors.ACCENT_HOVER,
        text_color=ThemeColors.TEXT_PRIMARY,
        command=root.destroy,
    )
    close_btn.pack(pady=30)

    root.mainloop()


def main() -> NoReturn:
    """Ponto de entrada de execução."""
    parser = argparse.ArgumentParser(description="PC Optimizer (Sollaris Nova)")
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Executa a verificação técnica do ambiente no terminal e sai",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Habilita logs detalhados de depuração",
    )
    args = parser.parse_args()

    configure_logging(verbose=args.verbose)

    if args.check_env:
        check_environment()
        sys.exit(0)

    try:
        launch_gui()
        sys.exit(0)
    except Exception as exc:
        logger.critical("Erro fatal ao inicializar a interface: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
