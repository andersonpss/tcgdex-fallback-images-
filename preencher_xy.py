"""Preenche a série XY em português com os scans publicados no Limitless."""
import argparse
import hashlib
import json
import re

import preencher_espada_escudo as motor
from auditar_importacao_swsh import auditar

WORK = motor.BASE / 'relatorios' / 'importacao_xy_pt'
MAPA = {'xyp': 'XYP', 'xy0': 'KSS', 'xy1': 'XY', 'xy2': 'FLF', 'xy3': 'FFI',
        'xy4': 'PHF', 'xy5': 'PRC', 'dc1': 'DCR', 'xy6': 'ROS', 'xy7': 'AOR',
        'xy8': 'BKT', 'xy9': 'BKP', 'g1': 'GEN', 'xy10': 'FCO', 'xy11': 'STS', 'xy12': 'EVO'}
YELLOW_A = {'24A': 'PHF', '28A': 'GEN', '54A': 'FCO', '55A': 'FFI', '92A': 'ROS', '107A': 'BKP'}


def chave(sid, numero):
    if sid == 'xyp':
        numero = re.sub(r'^XY', '', numero, flags=re.I)
    return motor.normalizar(numero)


def planejar(cliente):
    pt = json.loads(cliente.cache('serie_pt.json', 'https://api.tcgdex.net/v2/pt/series/xy'))
    en = json.loads(cliente.cache('serie_en.json', 'https://api.tcgdex.net/v2/en/series/xy'))
    conjuntos = {s['id']: s for s in en['sets']}
    conjuntos.update({s['id']: s for s in pt['sets']})
    ids_pt = {s['id'] for s in pt['sets']}
    paginas = {}
    for codigo in MAPA.values():
        pagina = motor.Pagina(cliente.cache(f'limitless_{codigo}.html', f'https://limitlesstcg.com/cards/pt/{codigo}'))
        paginas[codigo] = {motor.normalizar(k): v for k, v in pagina.cartas.items()}
    linhas, extras = [], []
    for sid in conjuntos:
        codigo = MAPA.get(sid)
        origem = paginas.get(codigo, {})
        dados_pt = json.loads(cliente.cache(f'{sid}_pt.json', f'https://api.tcgdex.net/v2/pt/sets/{sid}')) if sid in ids_pt else {'cards': []}
        cartas = {chave(sid, c['localId']): c for c in dados_pt['cards']}
        if not cartas or set(origem) - set(cartas):
            dados_en = json.loads(cliente.cache(f'{sid}_en.json', f'https://api.tcgdex.net/v2/en/sets/{sid}'))
            for c in dados_en['cards']:
                k = chave(sid, c['localId'])
                if not dados_pt['cards'] or k in origem:
                    cartas.setdefault(k, c)
        if sid == 'xya':
            origem = {k: paginas[c].get(k) for k, c in YELLOW_A.items()}
        for k, carta in cartas.items():
            scan = origem.get(k)
            linhas.append({'set': sid, 'id': carta['id'], 'numero': carta['localId'], 'nome': carta['name'],
                           'url': scan['url'].replace('_SM.png', '.png') if scan else '',
                           'pagina': scan['pagina'] if scan else '',
                           'status': 'planejado' if scan else 'sem_correspondencia'})
        # Variantes e energias publicadas no set, mas ainda sem ID de carta TCGdex.
        if sid != 'xya':
            for k, scan in origem.items():
                if k in cartas:
                    continue
                numero = scan['pagina'].rsplit('/', 1)[1]
                if not re.fullmatch(r'(?:\d+[a-z]?|[A-Z]+\d*|\d+b)', numero):
                    raise ValueError(f'Código precisa de revisão: {sid}/{numero}')
                local = f'XY{numero}' if sid == 'xyp' else numero
                linha = {'set': sid, 'id': f'{sid}-{local}', 'numero': local,
                         'nome': f'Variante/energia {local} (código Limitless; sem ID de carta TCGdex)',
                         'url': scan['url'].replace('_SM.png', '.png'), 'pagina': scan['pagina'], 'status': 'planejado'}
                extras.append(linha.copy())
                linhas.append(linha)
        print(f'{sid}: {len(cartas)} cartas TCGdex; {sum(r["set"] == sid and bool(r["url"]) for r in linhas)} correspondências PT', flush=True)
    assert len(linhas) == len({r['id'] for r in linhas})
    assert all('_PT.png' in r['url'] for r in linhas if r['url'])
    (WORK / 'plano.json').write_text(json.dumps(linhas, ensure_ascii=False, indent=2), encoding='utf-8')
    (WORK / 'sem_id_tcgdex.json').write_text(json.dumps(extras, ensure_ascii=False, indent=2), encoding='utf-8')
    return linhas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baixar', action='store_true')
    parser.add_argument('--auditar', action='store_true')
    args = parser.parse_args()
    motor.configurar_idioma('pt')
    motor.WORK = WORK
    WORK.mkdir(parents=True, exist_ok=True)
    if args.auditar:
        auditar('pt', serie='xy', pasta_relatorios=WORK)
        return
    registro = WORK / 'arquivos_anteriores.json'
    if not registro.exists():
        arquivos = {str(p.relative_to(motor.BASE)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (motor.BASE / 'pt/xy').rglob('*') if p.is_file()}
        registro.write_text(json.dumps(arquivos, indent=2), encoding='utf-8')
    cliente = motor.Cliente()
    linhas = planejar(cliente)
    if args.baixar:
        motor.baixar(cliente, linhas, serie='xy')


if __name__ == '__main__':
    main()
