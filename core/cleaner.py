"""Módulo de Varredura Segura de Arquivos Temporários — Sollaris Nova.

Calcula o espaço ocupado por arquivos temporários do usuário e cache de
forma não-destrutiva, fornecendo estimativas de espaço recuperável.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("sollaris_nova.cleaner")


@dataclass(frozen=True)
class TempCategorySummary:
    """Resumo de uma categoria de arquivos temporários analisada."""

    name: str
    path: str
    file_count: int
    size_bytes: int
    description: str


class CleanerScanner:
    """Varredor de arquivos temporários e caches dispensáveis."""

    @staticmethod
    def scan_temporary_files() -> list[TempCategorySummary]:
        """Varre os diretórios temporários autorizados sem executar exclusão."""
        categories: list[TempCategorySummary] = []

        # 1. Pasta TEMP do Usuário (%LOCALAPPDATA%\Temp)
        user_temp = os.environ.get("TEMP")
        if user_temp and Path(user_temp).exists():
            cnt, sz = CleanerScanner._scan_directory_safe(Path(user_temp))
            categories.append(
                TempCategorySummary(
                    name="Temporários do Usuário",
                    path=user_temp,
                    file_count=cnt,
                    size_bytes=sz,
                    description="Arquivos criados por instaladores e programas em execução recente.",
                )
            )

        # 2. Pasta TEMP do Sistema (C:\Windows\Temp - somente leitura não elevada)
        win_temp = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "Temp"
        if win_temp.exists():
            cnt, sz = CleanerScanner._scan_directory_safe(win_temp)
            categories.append(
                TempCategorySummary(
                    name="Temporários do Sistema",
                    path=str(win_temp),
                    file_count=cnt,
                    size_bytes=sz,
                    description="Arquivos residuais de serviços e atualizações do sistema.",
                )
            )

        return categories

    @staticmethod
    def _scan_directory_safe(target_dir: Path) -> tuple[int, int]:
        """Calcula a contagem e tamanho total de arquivos tratando erros de acesso."""
        count = 0
        total_size = 0

        try:
            for root, _, files in os.walk(str(target_dir)):
                for f in files:
                    try:
                        fp = os.path.join(root, f)
                        # Ignora links simbólicos para evitar loops
                        if not os.path.islink(fp):
                            total_size += os.path.getsize(fp)
                            count += 1
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError) as exc:
            logger.debug("Acesso limitado ao diretório %s: %s", target_dir, exc)

        return count, total_size
