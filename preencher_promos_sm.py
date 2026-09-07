"""Preenche pt/sm/smp com imagens portuguesas do Limitless (Sun & Moon Promos)."""
import argparse
import hashlib
import json
import re

import preencher_espada_escudo as motor
from auditar_importacao_swsh import auditar

WORK = motor.BASE / 'relatorios' / 'importacao_smp_pt'


def numero_limitless(numero):
    return motor.normalizar(re.sub(r'^SM', '', numero, flags=re.I))


def planejar(cliente):
    dados = json.loads(cliente.cache('tcgdex_smp_pt.json', 'https://api.tcgdex.net/v2/pt/sets/smp'))
    assert dados['id'] == 'smp' and dados['serie']['id'] == 'sm'
    pagina = motor.Pagina(cliente.cache('limitless_SMP_pt.html', 'https://limitlesstcg.com/cards/pt/SMP'))
    origem = {motor.normalizar(k): v for k, v in pagina.cartas.items()}
    cartas = {numero_limitless(c['localId']): c for c in dados['cards']}
    # Completa lacunas de IDs do catálogo PT somente quando há scan PT no Limitless.
    if set(origem) - set(cartas):
        ingles = json.loads(cliente.cache('tcgdex_smp_en.json', 'https://api.tcgdex.net/v2/en/sets/smp'))
        for carta in ingles['cards']:
            chave = numero_limitless(carta['localId'])
            if chave in origem and chave not in cartas:
                cartas[chave] = carta
    linhas = []
    for chave, carta in cartas.items():
        scan = origem.get(chave)
        linhas.append({'set': 'smp', 'id': carta['id'], 'numero': carta['localId'], 'nome': carta['name'],
                       'url': scan['url'].replace('_SM.png', '.png') if scan else '',
                       'pagina': scan['pagina'] if scan else '',
                       'status': 'planejado' if scan else 'sem_correspondencia'})
    extras = {k: v for k, v in origem.items() if k not in cartas}
    for chave, scan in extras.items():
        numero = scan['pagina'].rsplit('/', 1)[1]
        if not re.fullmatch(r'\d+a', numero):
            raise ValueError(f'Variante precisa de mapeamento: {numero}')
        local = f'SM{numero}'
        linhas.append({'set': 'smp', 'id': f'smp-{local}', 'numero': local,
                       'nome': f'Variante {local} (código local derivado do Limitless; sem ID TCGdex)',
                       'url': scan['url'].replace('_SM.png', '.png'), 'pagina': scan['pagina'], 'status': 'planejado'})
    assert len(linhas) == len({r['id'] for r in linhas})
    assert all('_PT.png' in r['url'] for r in linhas if r['url'])
    (WORK / 'plano.json').write_text(json.dumps(linhas, ensure_ascii=False, indent=2), encoding='utf-8')
    (WORK / 'sem_id_tcgdex.json').write_text(json.dumps(extras, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'TCGdex PT: {len(dados["cards"])}; scans PT Limitless: {len(origem)}; plano: {len(linhas)}; sem ID TCGdex: {len(extras)}', flush=True)
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
        auditar('pt', serie='sm', pasta_relatorios=WORK)
        return
    registro = WORK / 'arquivos_anteriores.json'
    if not registro.exists():
        arquivos = {str(p.relative_to(motor.BASE)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (motor.BASE / 'pt/sm/smp').rglob('*') if p.is_file()}
        registro.write_text(json.dumps(arquivos, indent=2), encoding='utf-8')
    cliente = motor.Cliente()
    linhas = planejar(cliente)
    if args.baixar:
        motor.baixar(cliente, linhas, serie='sm')


if __name__ == '__main__':
    main()
