"""Processamento e geracao dos icones oficiais baseados na referencia do usuario."""

from pathlib import Path

from PIL import Image, ImageDraw


def build_icons() -> None:
    root = Path(__file__).resolve().parent.parent
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

    # 1. Versao Render High-Tech (sollaris_nova_icon_1791552330509.jpg)
    src_render = Path(r"C:\Users\Notebook\.gemini\antigravity\brain\eab19d6f-aa95-4a75-97e1-4f0c76ba66e1\sollaris_nova_icon_1791552330509.jpg")
    if src_render.exists():
        img = Image.open(src_render).convert("RGBA")
        size = img.size[0]

        # Cria mascara squircle com cantos arredondados modernos (estilo app do Windows)
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, size, size], radius=int(size * 0.18), fill=255)

        badge = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        badge.paste(img, (0, 0), mask=mask)

        # Salva PNG principal (512x512)
        png_512 = badge.resize((512, 512), Image.Resampling.LANCZOS)
        png_512.save(assets / "icon.png", format="PNG")

        # Salva ICO do Windows
        badge.save(assets / "icon.ico", format="ICO", sizes=icon_sizes)
        print("Salvo assets/icon.ico e assets/icon.png (Versao High-Tech)")

    # 2. Versao Vetorial Transparente (direta do PNG do usuario com cores do Sollaris Nova)
    src_trans = assets / "icon_original_blue.png"
    if src_trans.exists():
        img_trans = Image.open(src_trans).convert("RGBA")
        # Garante aspect ratio 1:1 centralizado
        w, h = img_trans.size
        max_dim = max(w, h)
        square = Image.new("RGBA", (max_dim, max_dim), (0, 0, 0, 0))
        square.paste(img_trans, ((max_dim - w) // 2, (max_dim - h) // 2))

        square.save(assets / "icon_transparent.png", format="PNG")
        square.save(assets / "icon_transparent.ico", format="ICO", sizes=icon_sizes)
        print("Salvo assets/icon_transparent.ico e assets/icon_transparent.png")


if __name__ == "__main__":
    build_icons()
