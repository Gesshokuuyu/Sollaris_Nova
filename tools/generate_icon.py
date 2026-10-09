"""Gerador de ícones e assets de identidade visual — Sollaris Nova.

Gera o ícone técnico multi-resolução (.ico e .png) em conformidade com o Design System.
"""

from pathlib import Path

from PIL import Image, ImageDraw


def create_sollaris_icon(output_dir: Path) -> None:
    """Cria os arquivos icon.png e icon.ico no padrão visual minimalista azul/preto."""
    output_dir.mkdir(parents=True, exist_ok=True)
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Base arredondada escura (Superfície #111923 com borda #263345)
    margin = 12
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=48,
        fill=(17, 25, 35, 255),       # #111923
        outline=(38, 51, 69, 255),    # #263345
        width=4,
    )

    # 2. Hexágono técnico externo (#3B82F6)
    # Vértices de hexágono centralizado
    cx, cy = size // 2, size // 2
    r_outer = 78
    points_hex = [
        (cx, cy - r_outer),
        (cx + int(r_outer * 0.866), cy - r_outer // 2),
        (cx + int(r_outer * 0.866), cy + r_outer // 2),
        (cx, cy + r_outer),
        (cx - int(r_outer * 0.866), cy + r_outer // 2),
        (cx - int(r_outer * 0.866), cy - r_outer // 2),
    ]
    draw.polygon(points_hex, outline=(59, 130, 246, 255), width=6)  # #3B82F6

    # 3. Núcleo central "Nova Pulse" / CPU Matrix (#60A5FA e #DCE6F1)
    inner_r = 38
    draw.rounded_rectangle(
        [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
        radius=12,
        fill=(30, 48, 72, 220),
        outline=(96, 165, 250, 255),  # #60A5FA
        width=4,
    )

    # Linhas de circuito / vetor de desempenho
    draw.line([(cx - 22, cy), (cx + 22, cy)], fill=(220, 230, 241, 255), width=4)
    draw.line([(cx, cy - 22), (cx, cy + 22)], fill=(220, 230, 241, 255), width=4)

    # Pontos de conexão nos 4 quadrantes
    dot_r = 5
    for dx, dy in [(-16, -16), (16, -16), (-16, 16), (16, 16)]:
        draw.ellipse(
            [cx + dx - dot_r, cy + dy - dot_r, cx + dx + dot_r, cy + dy + dot_r],
            fill=(96, 165, 250, 255),
        )

    # Salva o PNG em alta resolução
    png_path = output_dir / "icon.png"
    img.save(png_path, format="PNG")
    print(f"PNG gerado: {png_path}")

    # Salva o ICO multi-resolução para o Windows
    ico_path = output_dir / "icon.ico"
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"ICO gerado: {ico_path}")


if __name__ == "__main__":
    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    create_sollaris_icon(assets_dir)
