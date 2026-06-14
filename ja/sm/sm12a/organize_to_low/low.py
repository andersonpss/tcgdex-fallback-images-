from pathlib import Path
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Cria uma pasta para cada arquivo e renomeia para 'low'"
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Pasta contendo os arquivos",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Sobrescreve arquivos existentes",
    )

    args = parser.parse_args()

    base_dir: Path = args.input_dir

    if not base_dir.is_dir():
        raise SystemExit("O caminho informado não é uma pasta válida.")

    files = [p for p in base_dir.iterdir() if p.is_file()]

    if not files:
        print("Nenhum arquivo encontrado.")
        return

    print(f"Processando {len(files)} arquivo(s)...")

    for file in files:
        folder_name = file.stem               # nome do arquivo sem extensão
        new_dir = base_dir / folder_name
        new_dir.mkdir(exist_ok=True)

        new_file = new_dir / f"low{file.suffix}"

        if new_file.exists() and not args.overwrite:
            print(f"Pulado (já existe): {new_file}")
            continue

        try:
            file.rename(new_file)
            print(f"OK: {file.name} → {new_file}")
        except Exception as e:
            print(f"Erro em {file.name}: {e}")

    print("Concluído!")


if __name__ == "__main__":
    main()
