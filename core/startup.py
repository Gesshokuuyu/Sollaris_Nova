"""Módulo de Consulta de Programas de Inicialização — Sollaris Nova.

Lê as chaves de registro HKCU e HKLM que definem quais programas são
iniciados automaticamente com o Windows.
"""

import logging
import sys
from dataclasses import dataclass

logger = logging.getLogger("sollaris_nova.startup")


@dataclass(frozen=True)
class StartupApp:
    """Representa um item configurado para iniciar com o Windows."""

    name: str
    command: str
    location: str


class StartupManager:
    """Gerencia a identificação dos programas de inicialização."""

    @staticmethod
    def get_startup_applications() -> list[StartupApp]:
        """Consulta as chaves de registro do Windows para listar programas de inicialização."""
        items: list[StartupApp] = []

        if sys.platform != "win32":
            return items

        import winreg

        registry_targets = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU (Usuário Atual)"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM (Máquina Local)"),
        ]

        for hkey, subkey, location in registry_targets:
            try:
                with winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ) as key:
                    values_count = winreg.QueryInfoKey(key)[1]
                    for i in range(values_count):
                        try:
                            name, cmd, _ = winreg.EnumValue(key, i)
                            items.append(
                                StartupApp(
                                    name=str(name),
                                    command=str(cmd),
                                    location=location,
                                )
                            )
                        except OSError:
                            continue
            except (OSError, PermissionError) as exc:
                logger.debug("Falha ao abrir chave de inicialização %s: %s", subkey, exc)

        return items
