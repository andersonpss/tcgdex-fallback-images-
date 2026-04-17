#!/usr/bin/env python3
"""
Organiza imagens em pastas pelos 3 últimos números do nome do arquivo e gera:
- high.webp  -> 600x825
- low.webp   -> 245x337

Correções desta versão:
- preserva transparência corretamente;
- evita halo/moldura branca nas bordas;
- recorta margens transparentes antes de redimensionar;
- usa redimensionamento com alpha premultiplicado.

Requisitos:
    pip install pillow
"""

from pathlib import Path
from PIL import Image
import traceback

BASE_DIR = Path(__file__).resolve().parent
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
HIGH_SIZE = (600, 825)
LOW_SIZE = (245, 337)
IGNORED_FILENAMES = {"high.webp", "low.webp"}


def extract_last_3_digits(stem: str):
    digits = "".join(ch for ch in stem if ch.isdigit())
    if len(digits) < 3:
        return None
    return digits[-3:]


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

    # Premultiplica RGB pelo alfa para evitar halo branco
    r = Image.eval(r, lambda v: v)
    g = Image.eval(g, lambda v: v)
    b = Image.eval(b, lambda v: v)

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


def convert_one_file(file_path):
    stem = file_path.stem

    if file_path.name.lower() in IGNORED_FILENAMES:
        return False, f"Ignorado (arquivo de saída): {file_path.name}"

    folder_name = extract_last_3_digits(stem)
    if not folder_name:
        return False, f"Ignorado (sem 3 dígitos no nome): {file_path.name}"

    target_dir = BASE_DIR / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    high_output = target_dir / "high.webp"
    low_output = target_dir / "low.webp"

    with Image.open(file_path) as img:
        high_img = resize_rgba_preserve_alpha(img, HIGH_SIZE)
        low_img = resize_rgba_preserve_alpha(img, LOW_SIZE)

        save_webp_rgba(high_img, high_output, quality=95)
        save_webp_rgba(low_img, low_output, quality=92)

    return True, f"OK: {file_path.name} -> {folder_name}/high.webp, {folder_name}/low.webp"


def main():
    print("=" * 70)
    print("Organizador e conversor de imagens para WEBP")
    print(f"Pasta base: {BASE_DIR}")
    print("=" * 70)

    input_files = []
    for item in BASE_DIR.iterdir():
        if not item.is_file():
            continue
        if item.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        input_files.append(item)

    if not input_files:
        print("Nenhuma imagem encontrada na mesma pasta do script.")
        print("Coloque os arquivos de imagem ao lado deste .py e execute novamente.")
        input("Pressione Enter para sair...")
        return

    input_files.sort(key=lambda p: p.name.lower())

    processed = 0
    skipped = 0
    failed = 0

    for file_path in input_files:
        try:
            ok, message = convert_one_file(file_path)
            print(message)
            if ok:
                processed += 1
            else:
                skipped += 1
        except Exception as exc:
            failed += 1
            print(f"ERRO: {file_path.name} -> {exc}")
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
