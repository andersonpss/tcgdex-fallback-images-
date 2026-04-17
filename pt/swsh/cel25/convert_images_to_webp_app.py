import sys
import threading
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple

try:
    from PIL import Image, ImageOps
except ImportError:
    print("Pillow não está instalado. Instale com: pip install pillow")
    sys.exit(1)

import tkinter as tk
from tkinter import messagebox, ttk

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
TARGET_SIZES = {
    "high": (600, 825),
    "low": (245, 337),
}
APP_DIR = Path(__file__).resolve().parent


@dataclass
class ConversionResult:
    converted: int = 0
    skipped: int = 0
    failed: int = 0
    details: Optional[List[str]] = None

    def __post_init__(self):
        if self.details is None:
            self.details = []


class ImageConverter:
    def __init__(self, quality: int = 90, recursive: bool = True, overwrite: bool = True):
        self.quality = quality
        self.recursive = recursive
        self.overwrite = overwrite

    def collect_files(self, folder: Path) -> List[Path]:
        iterator = folder.rglob("*") if self.recursive else folder.glob("*")
        files: List[Path] = []
        for path in iterator:
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            if path.parent == folder:
                # Ignora arquivos na mesma pasta do aplicativo; processa apenas subpastas.
                continue
            files.append(path)
        return sorted(files)

    def infer_target_size(self, file_path: Path) -> Optional[Tuple[int, int]]:
        stem = file_path.stem.lower()
        return TARGET_SIZES.get(stem)

    def build_output_path(self, file_path: Path) -> Path:
        return file_path.with_suffix(".webp")

    def convert_folder(self, folder: Path, progress_callback=None, log_callback=None) -> ConversionResult:
        result = ConversionResult()
        files = self.collect_files(folder)
        total = len(files)

        if total == 0:
            result.details.append("Nenhuma imagem suportada encontrada nas subpastas.")
            return result

        for index, file_path in enumerate(files, start=1):
            try:
                target_size = self.infer_target_size(file_path)
                if target_size is None:
                    result.skipped += 1
                    msg = f"Ignorado: {file_path} (nome deve ser 'high' ou 'low')"
                    result.details.append(msg)
                    if log_callback:
                        log_callback(msg)
                else:
                    output_path = self.build_output_path(file_path)
                    if output_path.exists() and not self.overwrite and output_path != file_path:
                        result.skipped += 1
                        msg = f"Ignorado: {output_path} já existe"
                        result.details.append(msg)
                        if log_callback:
                            log_callback(msg)
                    else:
                        self.convert_image(file_path, output_path, target_size)
                        result.converted += 1
                        msg = f"Convertido: {file_path} -> {output_path.name} {target_size[0]}x{target_size[1]}"
                        result.details.append(msg)
                        if log_callback:
                            log_callback(msg)
            except Exception as exc:
                result.failed += 1
                msg = f"Erro: {file_path} ({exc})"
                result.details.append(msg)
                if log_callback:
                    log_callback(msg)

            if progress_callback:
                progress_callback(index, total)

        return result

    def convert_image(self, input_path: Path, output_path: Path, target_size: Tuple[int, int]) -> None:
        with Image.open(input_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode in ("RGBA", "LA"):
                background = Image.new("RGBA", img.size, (255, 255, 255, 255))
                background.alpha_composite(img.convert("RGBA"))
                img = background.convert("RGB")
            elif img.mode != "RGB":
                img = img.convert("RGB")

            resized = ImageOps.fit(
                img,
                target_size,
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            resized.save(output_path, format="WEBP", quality=self.quality, method=6)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Conversor de imagens para WEBP")
        self.geometry("900x640")
        self.minsize(780, 540)

        self.base_folder_var = tk.StringVar(value=str(APP_DIR))
        self.quality_var = tk.IntVar(value=90)
        self.recursive_var = tk.BooleanVar(value=True)
        self.overwrite_var = tk.BooleanVar(value=True)

        self._build_ui()
        self.converter_thread: Optional[threading.Thread] = None

    def _build_ui(self):
        main = ttk.Frame(self, padding=14)
        main.pack(fill="both", expand=True)

        title = ttk.Label(
            main,
            text="Converter imagens das subpastas para WEBP",
            font=("Segoe UI", 14, "bold"),
        )
        title.pack(anchor="w", pady=(0, 10))

        rules = (
            "A aplicação usa automaticamente a pasta onde ela está salva como base.\n"
            "Ela processa arquivos dentro das subpastas dessa pasta.\n\n"
            "Regras:\n"
            "- 'high' -> 600x825\n"
            "- 'low' -> 245x337\n"
            "- outros nomes são ignorados\n"
            "- a imagem é ajustada para preencher o tamanho final"
        )
        ttk.Label(main, text=rules, justify="left").pack(anchor="w", pady=(0, 12))

        base_frame = ttk.LabelFrame(main, text="Pasta base", padding=10)
        base_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(base_frame, textvariable=self.base_folder_var).pack(anchor="w")

        options = ttk.LabelFrame(main, text="Opções", padding=10)
        options.pack(fill="x", pady=(0, 10))

        row1 = ttk.Frame(options)
        row1.pack(fill="x")
        ttk.Label(row1, text="Qualidade WEBP (1-100):").pack(side="left")
        quality_spin = ttk.Spinbox(row1, from_=1, to=100, textvariable=self.quality_var, width=6)
        quality_spin.pack(side="left", padx=(8, 20))
        ttk.Checkbutton(row1, text="Processar subpastas", variable=self.recursive_var).pack(side="left", padx=(0, 20))
        ttk.Checkbutton(row1, text="Sobrescrever WEBP existente", variable=self.overwrite_var).pack(side="left")

        buttons = ttk.Frame(main)
        buttons.pack(fill="x", pady=(0, 10))
        self.convert_button = ttk.Button(buttons, text="Converter subpastas", command=self.start_conversion)
        self.convert_button.pack(side="left")
        ttk.Button(buttons, text="Limpar log", command=self.clear_log).pack(side="left", padx=8)

        self.progress = ttk.Progressbar(main, mode="determinate")
        self.progress.pack(fill="x", pady=(0, 6))
        self.status_label = ttk.Label(main, text="Aguardando...")
        self.status_label.pack(anchor="w", pady=(0, 8))

        log_frame = ttk.LabelFrame(main, text="Log", padding=8)
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(log_frame, wrap="word", height=20)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def clear_log(self):
        self.log_text.delete("1.0", tk.END)

    def append_log(self, message: str):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def set_status(self, text: str):
        self.status_label.config(text=text)
        self.update_idletasks()

    def update_progress(self, current: int, total: int):
        self.progress["maximum"] = max(total, 1)
        self.progress["value"] = current
        self.set_status(f"Processando {current}/{total}...")

    def start_conversion(self):
        folder = APP_DIR

        quality = self.quality_var.get()
        if quality < 1 or quality > 100:
            messagebox.showerror("Erro", "A qualidade deve estar entre 1 e 100.")
            return

        self.convert_button.config(state="disabled")
        self.progress["value"] = 0
        self.clear_log()
        self.append_log(f"Pasta base: {folder}")
        self.append_log("Processando apenas arquivos dentro das subpastas.\n")
        self.set_status("Iniciando...")

        converter = ImageConverter(
            quality=quality,
            recursive=self.recursive_var.get(),
            overwrite=self.overwrite_var.get(),
        )

        def worker():
            result = converter.convert_folder(
                folder,
                progress_callback=lambda c, t: self.after(0, self.update_progress, c, t),
                log_callback=lambda msg: self.after(0, self.append_log, msg),
            )
            self.after(0, self.finish_conversion, result)

        self.converter_thread = threading.Thread(target=worker, daemon=True)
        self.converter_thread.start()

    def finish_conversion(self, result: ConversionResult):
        self.convert_button.config(state="normal")
        summary = (
            f"Concluído. Convertidas: {result.converted} | "
            f"Ignoradas: {result.skipped} | Erros: {result.failed}"
        )
        self.set_status(summary)
        messagebox.showinfo("Finalizado", summary)


if __name__ == "__main__":
    app = App()
    app.mainloop()
