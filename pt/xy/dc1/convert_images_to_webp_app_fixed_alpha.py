#!/usr/bin/env python3
"""
Converte imagens em subpastas da pasta onde o script está salvo para WEBP.

Regras:
- arquivos com nome "high" -> 600x825
- arquivos com nome "low"  -> 245x337

Esta versão:
- preserva transparência corretamente;
- evita halo/moldura branca nas bordas;
- recorta margens transparentes antes de redimensionar;
- processa subpastas da pasta do script.

Requisitos:
    pip install pillow
"""

from pathlib import Path
from PIL import Image
import traceback

BASE_DIR = Path(__file__).resolve().parent
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
TARGET_SIZES = {
    "high": (600, 825),
    "low": (245, 337),
}


def crop_transparent_border(img):
    rgba = img.convert("RGBA")
    alpha = rgba.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        return rgba.crop(bbox)
    return rgba


def resize_rgba_preserve_alpha(img, target_size):
    img = crop_transparent_border(img).convert("RGBA")

    src_w, src_h = img.size
    dst_w, dst_h = target_size

    if src_w == 0 or src_h == 0:
        return Image.new("RGBA", target_size, (0, 0, 0, 0))

    scale = min(dst_w / src_w, dst_h / src_h)
    new_w = max(1, round(src_w * scale))
    new_h = max(1, round(src_h * scale))

    r, g, b, a = img.split()

    premult = Image.new("RGBA", img.size, (0, 0, 0, 0))
    premult.paste(img, (0, 0), a)

    premult = premult.resize((new_w, new_h), Image.Resampling.LANCZOS)
    alpha_resized = a.resize((new_w, new_h), Image.Resampling.LANCZOS)

    pr, pg, pb, _ = premult.split()
    result = Image.merge("RGBA", (pr, pg, pb, alpha_resized))

    canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    offset_x = (dst_w - new_w) // 2
    offset_y = (dst_h - new_h) // 2
    canvas.paste(result, (offset_x, offset_y), result)
    return canvas


def save_webp_rgba(img, output_path, quality):
    img.save(
        output_path,
        format="WEBP",
        quality=quality,
        method=6,
        lossless=False,
        exact=True,
    )


def process_file(file_path):
    stem_lower = file_path.stem.lower()

    if stem_lower not in TARGET_SIZES:
        return False, f"Ignorado (nome não é high/low): {file_path}"

    target_size = TARGET_SIZES[stem_lower]
    output_path = file_path.with_suffix(".webp")

    with Image.open(file_path) as img:
        converted = resize_rgba_preserve_alpha(img, target_size)
        quality = 95 if stem_lower == "high" else 92
        save_webp_rgba(converted, output_path, quality)

    return True, f"OK: {file_path} -> {output_path.name}"


def main():
    print("=" * 70)
    print("Conversor WEBP com preservação de transparência")
    print(f"Pasta base: {BASE_DIR}")
    print("=" * 70)

    input_files = []
    for item in BASE_DIR.rglob("*"):
        if not item.is_file():
            continue
        if item.parent == BASE_DIR:
            continue
        if item.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        input_files.append(item)

    if not input_files:
        print("Nenhuma imagem encontrada nas subpastas da pasta do script.")
        input("Pressione Enter para sair...")
        return

    input_files.sort(key=lambda p: str(p).lower())

    processed = 0
    skipped = 0
    failed = 0

    for file_path in input_files:
        try:
            ok, message = process_file(file_path)
            print(message)
            if ok:
                processed += 1
            else:
                skipped += 1
        except Exception as exc:
            failed += 1
            print(f"ERRO: {file_path} -> {exc}")
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("Concluído.")
    print(f"Processados: {processed}")
    print(f"Ignorados:   {skipped}")
    print(f"Falhas:      {failed}")
    print("=" * 70)
    input("Pressione Enter para sair...")


if __name__ == "__main__":
    main()
