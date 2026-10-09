"""Gerador de ícones técnicos monocromáticos para o menu lateral.

Gera ícones vetoriais/lineares limpos de 20x20 px (sem emojis) em conformidade
com o Design System (#8493A7 e #DCE6F1).
"""

from pathlib import Path

from PIL import Image, ImageDraw


def create_nav_icons(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    size = 20

    # Cores
    color_normal = (132, 147, 167, 255)   # #8493A7 (Muted)
    color_active = (220, 230, 241, 255)   # #DCE6F1 (Primary Text)

    def make_icon(draw_fn, name: str) -> None:
        # Versao normal
        img_n = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d_n = ImageDraw.Draw(img_n)
        draw_fn(d_n, color_normal)
        img_n.save(output_dir / f"{name}.png", format="PNG")

        # Versao ativa
        img_a = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d_a = ImageDraw.Draw(img_a)
        draw_fn(d_a, color_active)
        img_a.save(output_dir / f"{name}_active.png", format="PNG")

    # 1. Visão Geral (Grid 2x2 com cantos sutis)
    def draw_overview(draw: ImageDraw.ImageDraw, c: tuple) -> None:
        draw.rectangle([2, 2, 8, 8], outline=c, width=1)
        draw.rectangle([11, 2, 17, 8], outline=c, width=1)
        draw.rectangle([2, 11, 8, 17], outline=c, width=1)
        draw.rectangle([11, 11, 17, 17], outline=c, width=1)

    # 2. Diagnóstico (Linha de pulso técnico / osciloscópio)
    def draw_diagnostics(draw: ImageDraw.ImageDraw, c: tuple) -> None:
        points = [(2, 10), (6, 10), (8, 4), (11, 16), (13, 8), (15, 10), (18, 10)]
        draw.line(points, fill=c, width=2)

    # 3. Limpeza (Vassoura / varredor angular técnico)
    def draw_cleaner(draw: ImageDraw.ImageDraw, c: tuple) -> None:
        # Cabo
        draw.line([(15, 3), (9, 9)], fill=c, width=2)
        # Base da vassoura
        draw.polygon([(6, 12), (12, 6), (14, 8), (8, 14)], outline=c, fill=c)
        # Cerdas
        draw.line([(4, 15), (7, 18)], fill=c, width=2)
        draw.line([(7, 13), (10, 16)], fill=c, width=2)

    # 4. Inicialização (Símbolo IEC de Liga/Desliga ou Raio técnico)
    def draw_startup(draw: ImageDraw.ImageDraw, c: tuple) -> None:
        # Círculo aberto
        draw.arc([3, 4, 17, 18], start=30, end=330, fill=c, width=2)
        # Barra vertical no topo
        draw.line([(10, 2), (10, 9)], fill=c, width=2)

    # 5. Modo Game (D-pad e botões)
    def draw_game_mode(draw: ImageDraw.ImageDraw, c: tuple) -> None:
        # Corpo do controle
        draw.rounded_rectangle([2, 5, 18, 15], radius=3, outline=c, width=1)
        # D-pad (cruz à esquerda)
        draw.line([(5, 10), (9, 10)], fill=c, width=2)
        draw.line([(7, 8), (7, 12)], fill=c, width=2)
        # Botões (pontos à direita)
        draw.point([(13, 9), (15, 11)], fill=c)

    # 6. Histórico (Gráfico de linha com eixos)
    def draw_history(draw: ImageDraw.ImageDraw, c: tuple) -> None:
        # Eixo L
        draw.line([(3, 3), (3, 17), (17, 17)], fill=c, width=1)
        # Linha crescente
        points = [(3, 14), (7, 11), (11, 13), (16, 6)]
        draw.line(points, fill=c, width=2)

    # 7. Configurações (Engrenagem técnica)
    def draw_settings(draw: ImageDraw.ImageDraw, c: tuple) -> None:
        # Círculo central
        draw.ellipse([6, 6, 14, 14], outline=c, width=2)
        # Dentes da engrenagem
        draw.line([(10, 2), (10, 5)], fill=c, width=2)
        draw.line([(10, 15), (10, 18)], fill=c, width=2)
        draw.line([(2, 10), (5, 10)], fill=c, width=2)
        draw.line([(15, 10), (18, 10)], fill=c, width=2)
        draw.line([(4, 4), (6, 6)], fill=c, width=2)
        draw.line([(14, 14), (16, 16)], fill=c, width=2)
        draw.line([(16, 4), (14, 6)], fill=c, width=2)
        draw.line([(4, 16), (6, 14)], fill=c, width=2)

    make_icon(draw_overview, "nav_overview")
    make_icon(draw_diagnostics, "nav_diagnostics")
    make_icon(draw_cleaner, "nav_cleaner")
    make_icon(draw_startup, "nav_startup")
    make_icon(draw_game_mode, "nav_game_mode")
    make_icon(draw_history, "nav_history")
    make_icon(draw_settings, "nav_settings")
    print(f"[OK] 14 ícones técnicos de navegação gerados em {output_dir}")


if __name__ == "__main__":
    assets_icons = Path(__file__).resolve().parent.parent / "assets" / "nav_icons"
    create_nav_icons(assets_icons)
