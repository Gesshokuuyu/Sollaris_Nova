"""Ponto de entrada principal — Sollaris Nova (PC Optimizer).

Inicializa a aplicação desktop, configura logs estruturados e
carrega a interface com as configurações do Design System.
"""

import argparse
import logging
import platform
import sys
from typing import NoReturn

import customtkinter as ctk
import psutil

from app.theme import ThemeColors
from app.window import MainWindow

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
    """Inicializa a interface gráfica do usuário com o painel de monitoramento."""
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    app = MainWindow()
    app.mainloop()


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
