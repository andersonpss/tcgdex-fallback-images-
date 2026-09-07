"""Importa scans PT/EN do Limitless, mantendo IDs de sets e cartas do TCGdex."""
import argparse
import csv
import io
import json
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path

import requests
from PIL import Image, ImageOps
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

BASE = Path(__file__).resolve().parent
IDIOMA = 'pt'
WORK = BASE / 'relatorios' / 'importacao_swsh'
MAPA = {'swshp': 'SP', 'swsh1': 'SSH', 'swsh2': 'RCL', 'swsh3': 'DAA',
        'swsh3.5': 'CPA', 'swsh4': 'VIV', 'swsh4.5': 'SHF', 'swsh4.5sv': 'SHF',
        'swsh5': 'BST', 'swsh6': 'CRE', 'swsh7': 'EVS', 'cel25': 'CEL',
        'cel25cc': 'CEL', 'swsh8': 'FST', 'swsh9': 'BRS', 'swsh9tg': 'BRS',
        'swsh10': 'ASR', 'swsh10tg': 'ASR', 'swsh10.5': 'PGO', 'swsh11': 'LOR',
        'swsh11tg': 'LOR', 'swsh12': 'SIT', 'swsh12tg': 'SIT',
        'swsh12.5': 'CRZ', 'swsh12.5gg': 'CRZ'}


def configurar_idioma(idioma):
    global IDIOMA, WORK
    if idioma not in ('pt', 'en'):
        raise ValueError('Idioma deve ser pt ou en.')
    IDIOMA = idioma
    WORK = BASE / 'relatorios' / ('importacao_swsh' if idioma == 'pt' else 'importacao_swsh_en')


class Pagina(HTMLParser):
    def __init__(self, texto):
        super().__init__()
        self.link = ''
        self.cartas = {}
        self.feed(texto)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a':
            self.link = a.get('href', '')
        if tag == 'img' and re.fullmatch(rf'/cards/{IDIOMA}/[^/]+/[^/]+', self.link):
            src = a.get('src', '')
            if f'_{IDIOMA.upper()}_' in src:
                self.cartas[self.link.rsplit('/', 1)[1]] = {'url': src, 'pagina': 'https://limitlesstcg.com' + self.link, 'nome': a.get('alt', '')}

    def handle_endtag(self, tag):
        if tag == 'a':
            self.link = ''


class Cliente:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'LocalPokemonImageCollection/1.0'
        retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504], respect_retry_after_header=True)
        self.session.mount('https://', HTTPAdapter(max_retries=retry))
        self.ultima = 0

    def get(self, url):
        time.sleep(max(0, .3 - (time.monotonic() - self.ultima)))
        self.ultima = time.monotonic()
        r = self.session.get(url, timeout=(15, 40))
        r.raise_for_status()
        return r

    def cache(self, nome, url):
        path = WORK / nome
        if not path.exists():
            path.write_bytes(self.get(url).content)
        return path.read_text(encoding='utf-8')


def normalizar(n):
    return re.sub(r'\d+', lambda m: str(int(m[0])), n.upper())


def energias_basicas():
    linhas = []
    for codigo, sid in [('SSH', 'swsh1'), ('BRS', 'swsh9')]:
        pagina = Pagina((WORK / f'limitless_{codigo}.html').read_text(encoding='utf-8'))
        for numero in ('G', 'R', 'W', 'L', 'P', 'F', 'D', 'M'):
            origem = pagina.cartas.get(numero)
            if origem:
                linhas.append({'set': sid, 'id': f'{sid}-{numero}', 'numero': numero,
                               'nome': f'Energia básica (código Limitless {numero}; sem ID de carta TCGdex)',
                               'url': origem['url'].replace('_SM.png', '.png'),
                               'pagina': origem['pagina'], 'status': 'planejado'})
    return linhas


def planejar(cliente):
    serie = json.loads(cliente.cache('tcgdex_swsh.json', f'https://api.tcgdex.net/v2/{IDIOMA}/series/swsh'))
    linhas = []
    for conjunto in serie['sets']:
        sid = conjunto['id']
        codigo = MAPA.get(sid)
        dados = json.loads(cliente.cache(f'tcgdex_{sid}.json', f'https://api.tcgdex.net/v2/{IDIOMA}/sets/{sid}'))
        if not dados['cards']:
            dados = json.loads(cliente.cache(f'tcgdex_en_{sid}.json', f'https://api.tcgdex.net/v2/en/sets/{sid}'))
        pagina = Pagina(cliente.cache(f'limitless_{codigo}.html', f'https://limitlesstcg.com/cards/{IDIOMA}/{codigo}')) if codigo else Pagina('')
        indice = {normalizar(k): v for k, v in pagina.cartas.items()}
        for carta in dados['cards']:
            numero = carta['localId']
            chave = normalizar(numero)
            if sid == 'swshp':
                chave = normalizar(re.sub(r'^(SWSH|SW)', '', numero, flags=re.I))
            origem = indice.get(chave)
            linhas.append({'set': sid, 'id': carta['id'], 'numero': numero, 'nome': carta['name'],
                           'url': origem['url'].replace('_SM.png', '.png') if origem else '',
                           'pagina': origem['pagina'] if origem else '', 'status': 'planejado' if origem else 'sem_correspondencia'})
        print(f'{sid}: {len(dados["cards"])} cartas; Limitless {codigo}: {len(indice)}', flush=True)
    linhas.extend(energias_basicas())
    (WORK / 'plano.json').write_text(json.dumps(linhas, ensure_ascii=False, indent=2), encoding='utf-8')
    return linhas


def baixar(cliente, linhas, linhas_base=None):
    anteriores = {}
    if (WORK / 'resultado.csv').exists():
        with (WORK / 'resultado.csv').open(encoding='utf-8-sig', newline='') as f:
            anteriores = {r['id']: r for r in csv.DictReader(f, delimiter=';')}
    contexto = threading.local()

    def baixar_carta(linha):
        if not hasattr(contexto, 'cliente'):
            contexto.cliente = Cliente()
        pasta = BASE / IDIOMA / 'swsh' / linha['set'] / linha['numero']
        pasta.mkdir(parents=True, exist_ok=True)
        faltam = [nome for nome in ('high', 'low') if not (pasta / f'{nome}.webp').exists() or (pasta / f'{nome}.webp').stat().st_size == 0]
        if not faltam:
            anterior = anteriores.get(linha['id'], {})
            linha['status'] = 'baixado' if anterior.get('status') == 'baixado' else 'ja_existia'
            if anterior.get('url'):
                linha['url'] = anterior['url']
        elif linha['url']:
            try:
                try:
                    conteudo = contexto.cliente.get(linha['url']).content
                except requests.HTTPError as erro:
                    if erro.response.status_code not in (403, 404):
                        raise
                    # A página oferece também LG, que pode existir sem o original.
                    alternativa = linha['url'].replace(f'_{IDIOMA.upper()}.png', f'_{IDIOMA.upper()}_LG.png')
                    conteudo = contexto.cliente.get(alternativa).content
                    linha['url'] = alternativa
                with Image.open(io.BytesIO(conteudo)) as imagem:
                    imagem.load()
                    if imagem.width < 400 or imagem.height < 550:
                        raise ValueError(f'Resolução insuficiente: {imagem.size}')
                    imagem = imagem.convert('RGB')
                    for nome in faltam:
                        tamanho = (600, 825) if nome == 'high' else (245, 337)
                        saida = ImageOps.contain(imagem, tamanho, Image.Resampling.LANCZOS)
                        temporario = pasta / f'{nome}.webp.part'
                        saida.save(temporario, format='WEBP', quality=95 if nome == 'high' else 92, method=4)
                        temporario.replace(pasta / f'{nome}.webp')
                linha['status'] = 'baixado'
            except Exception as erro:
                linha['status'] = 'erro'
                linha['erro'] = str(erro)

    with ThreadPoolExecutor(max_workers=3) as executor:
        for inicio in range(0, len(linhas), 5):
            list(executor.map(baixar_carta, linhas[inicio:inicio + 5]))
            salvar((linhas_base or []) + linhas)
            print(f'{min(inicio + 5, len(linhas))}/{len(linhas)} | baixadas: {sum(r["status"] == "baixado" for r in linhas)} | erros: {sum(r["status"] == "erro" for r in linhas)}', flush=True)
            time.sleep(1)


def salvar(linhas):
    with (WORK / 'resultado.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['set', 'id', 'numero', 'nome', 'url', 'pagina', 'status', 'erro'], delimiter=';')
        writer.writeheader()
        writer.writerows(linhas)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baixar', action='store_true')
    parser.add_argument('--idioma', choices=('pt', 'en'), default='pt')
    args = parser.parse_args()
    configurar_idioma(args.idioma)
    WORK.mkdir(parents=True, exist_ok=True)
    cliente = Cliente()
    linhas = planejar(cliente)
    if args.baixar:
        baixar(cliente, linhas)
