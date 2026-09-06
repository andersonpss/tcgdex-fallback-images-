#!/usr/bin/env python3
"""Confere imagens em português no TCGdex e na pasta deste script."""
import argparse
import csv
import json
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
API = "https://api.tcgdex.net/v2/pt"
EXTENSOES = {".webp", ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


class Cliente:
    def __init__(self):
        self.ultima = 0.0

    def solicitar(self, url, metodo="GET"):
        for tentativa in range(3):
            time.sleep(max(0, 0.4 - (time.monotonic() - self.ultima)))
            self.ultima = time.monotonic()
            try:
                req = Request(url, method=metodo, headers={"User-Agent": "ConferirImagensLocal/1.0"})
                with urlopen(req, timeout=25) as resposta:
                    if metodo == "HEAD":
                        tipo = resposta.headers.get("Content-Type", "")
                        if not tipo.startswith("image/"):
                            raise ValueError(f"Resposta não é imagem: {tipo}")
                        return True
                    return json.load(resposta)
            except HTTPError as erro:
                if erro.code not in {429, 500, 502, 503, 504} or tentativa == 2:
                    raise
                atraso = 2 ** (tentativa + 1)
                retry = erro.headers.get("Retry-After")
                if retry:
                    try:
                        atraso = max(atraso, float(retry))
                    except ValueError:
                        try:
                            atraso = max(atraso, (parsedate_to_datetime(retry) - datetime.now(timezone.utc)).total_seconds())
                        except (ValueError, TypeError):
                            pass
                print(f"API ocupada ({erro.code}); aguardando {atraso:.0f}s...", flush=True)
                time.sleep(atraso)
            except (URLError, TimeoutError, OSError):
                if tentativa == 2:
                    raise
                time.sleep(2 ** (tentativa + 1))

    def obter(self, caminho):
        return self.solicitar(f"{API}/{caminho}")


def normalizar(valor):
    # 001 e 1 são equivalentes; TG01 e TG1 também. Mantém os prefixos.
    return re.sub(r"\d+", lambda m: str(int(m.group())), str(valor).casefold())


def indice_local(raiz, serie, conjunto):
    pasta = raiz / "pt" / serie / conjunto
    indice = {}
    if not pasta.is_dir():
        return indice
    for arquivo in pasta.rglob("*"):
        if not arquivo.is_file() or arquivo.suffix.lower() not in EXTENSOES or arquivo.stat().st_size == 0:
            continue
        relativo = arquivo.relative_to(pasta)
        chave = relativo.parts[0] if len(relativo.parts) > 1 else arquivo.stem
        if chave.casefold().startswith(conjunto.casefold() + "-"):
            chave = chave[len(conjunto) + 1:]
        indice.setdefault(normalizar(chave), []).append(str(arquivo.relative_to(raiz)))
    return indice


def imagem_remota(cliente, carta):
    base = carta.get("image")
    if not base:
        return "ausente", "API não informa imagem em português"
    erros = []
    for variante in ("high.webp", "low.webp", "high.png", "low.png"):
        url = base.rstrip("/") + "/" + variante
        try:
            cliente.solicitar(url, "HEAD")
            return "disponivel", url
        except HTTPError as erro:
            if erro.code not in {404, 410}:
                erros.append(f"{variante}: HTTP {erro.code}")
                # Não multiplica consultas em caso de bloqueio ou indisponibilidade.
                break
        except (URLError, TimeoutError, OSError, ValueError) as erro:
            erros.append(str(erro))
            break
    if erros:
        return "inconclusivo", "; ".join(erros)
    return "ausente", "Todas as variantes WEBP/PNG retornaram 404/410"


def conferir_imagens(serie, conjunto, *, raiz=BASE, lote=5, pausa=2.0, cliente=None):
    """Retorna uma linha por carta; nunca trata falha de rede como ausência."""
    if not 1 <= lote <= 10 or pausa < 1:
        raise ValueError("Use lotes de 1 a 10 cartas e pausa mínima de 1 segundo.")
    cliente = cliente or Cliente()
    dados = cliente.obter("sets/" + quote(conjunto, safe=""))
    if dados.get("serie", {}).get("id") != serie:
        raise ValueError("O set selecionado não pertence à série informada.")
    cartas = dados["cards"]
    locais = indice_local(Path(raiz), serie, conjunto)
    linhas = []
    for inicio in range(0, len(cartas), lote):
        print(f"Conferindo cartas {inicio + 1}–{min(inicio + lote, len(cartas))} de {len(cartas)}...", flush=True)
        for carta in cartas[inicio:inicio + lote]:
            remoto, detalhe = imagem_remota(cliente, carta)
            arquivos = locais.get(normalizar(carta["localId"]), [])
            status = ("disponivel_tcgdex" if remoto == "disponivel" else
                      "inconclusivo" if remoto == "inconclusivo" else
                      "ja_existe_local" if arquivos else "falta_nos_dois")
            linhas.append(dict(id=carta["id"], numero=carta["localId"], nome=carta["name"],
                               status=status, arquivos_locais="; ".join(arquivos), detalhe=detalhe))
        if inicio + lote < len(cartas):
            time.sleep(pausa)
    return linhas


def selecionar(itens, titulo, escolhido=None):
    if escolhido:
        for item in itens:
            if item["id"].casefold() == escolhido.casefold():
                return item["id"]
        raise ValueError(f"{titulo} não encontrado: {escolhido}")
    if not itens:
        raise ValueError(f"Nenhuma opção disponível para {titulo}.")
    print(f"\nSelecione {titulo}:")
    for i, item in enumerate(itens, 1):
        print(f"{i:3}. {item['name']} ({item['id']})")
    while True:
        valor = input("Digite o número da opção ou o ID (Ctrl+C para sair): ").strip()
        for item in itens:
            if valor.casefold() == item["id"].casefold():
                return item["id"]
        if valor.isdigit() and 1 <= int(valor) <= len(itens):
            return itens[int(valor) - 1]["id"]
        print("Opção inválida.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serie", help="ID da série; omitido abre um menu")
    parser.add_argument("--set", dest="conjunto", help="ID do set; omitido abre um menu")
    parser.add_argument("--lote", type=int, default=5, choices=range(1, 11))
    parser.add_argument("--pausa", type=float, default=2, help="Segundos entre lotes (mínimo 1)")
    args = parser.parse_args()
    if not args.pausa >= 1:
        parser.error("A pausa deve ser de pelo menos 1 segundo.")
    cliente = Cliente()
    serie = selecionar(cliente.obter("series"), "a série", args.serie)
    dados = cliente.obter("series/" + quote(serie, safe=""))
    conjunto = selecionar(dados["sets"], "o set", args.conjunto)
    linhas = conferir_imagens(serie, conjunto, lote=args.lote, pausa=args.pausa, cliente=cliente)
    faltantes = [r for r in linhas if r["status"] == "falta_nos_dois"]
    print("\nIMAGENS QUE FALTAM NO TCGDEX E NA PASTA LOCAL:")
    for linha in faltantes:
        print(f"  {linha['id']} — {linha['nome']}")
    if not faltantes:
        print("  Nenhuma ausência confirmada.")
    for estado, titulo in [("ja_existe_local", "Ausentes no TCGdex, já disponíveis localmente"),
                           ("inconclusivo", "Consultas inconclusivas")]:
        grupo = [r for r in linhas if r["status"] == estado]
        print(f"\n{titulo}: {len(grupo)}")
        for linha in grupo:
            print(f"  {linha['id']} — {linha['nome']}")
    pasta = BASE / "relatorios"
    pasta.mkdir(exist_ok=True)
    nome = re.sub(r"[^a-zA-Z0-9_-]", "_", f"{serie}_{conjunto}")
    destino = pasta / f"{nome}_{datetime.now():%Y%m%d_%H%M%S_%f}.csv"
    with destino.open("w", encoding="utf-8-sig", newline="") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=["id", "numero", "nome", "status", "arquivos_locais", "detalhe"], delimiter=";")
        writer.writeheader()
        writer.writerows(linhas)
    print(f"\nTotal: {len(linhas)} cartas. Faltam nos dois: {len(faltantes)}.\nRelatório completo: {destino}")
    return 2 if any(r["status"] == "inconclusivo" for r in linhas) else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nConsulta cancelada.")
        raise SystemExit(130)
    except (URLError, OSError, ValueError, KeyError) as erro:
        print(f"Não foi possível concluir a consulta: {erro}")
        raise SystemExit(1)
