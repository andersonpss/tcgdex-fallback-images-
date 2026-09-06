"""Valida os WEBP da importação e gera resumo e lista de pendências."""
import csv
import json
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

from PIL import Image
from preencher_espada_escudo import BASE, WORK


def auditar():
    with (WORK / 'resultado.csv').open(encoding='utf-8-sig', newline='') as arquivo:
        linhas = list(csv.DictReader(arquivo, delimiter=';'))
    resumo = defaultdict(Counter)
    pendentes = []
    def verificar(linha):
        problemas = []
        pasta = BASE / 'pt' / 'swsh' / linha['set'] / linha['numero']
        for qualidade in ('high', 'low'):
            imagem = pasta / f'{qualidade}.webp'
            if not imagem.exists():
                problemas.append(f'{qualidade}: arquivo ausente')
                continue
            try:
                with Image.open(imagem) as img:
                    img.load()
                    if img.format != 'WEBP' or min(img.size) < 100:
                        problemas.append(f'{qualidade}: formato ou tamanho inesperado')
            except (OSError, ValueError) as erro:
                problemas.append(f'{qualidade}: {erro}')
        return linha, problemas

    with ThreadPoolExecutor(max_workers=8) as executor:
        for i, (linha, problemas) in enumerate(executor.map(verificar, linhas), 1):
            resumo[linha['set']]['total'] += 1
            if problemas:
                resumo[linha['set']]['pendentes'] += 1
                pendentes.append({**linha, 'problema_local': '; '.join(problemas)})
            else:
                resumo[linha['set']]['completas'] += 1
            if i % 250 == 0:
                print(f'Verificadas {i}/{len(linhas)} cartas', flush=True)
    with (WORK / 'pendencias.csv').open('w', encoding='utf-8-sig', newline='') as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=list(linhas[0]) + ['problema_local'], delimiter=';')
        writer.writeheader()
        writer.writerows(pendentes)
    resultado = {'total': len(linhas), 'completas': len(linhas) - len(pendentes),
                 'pendentes': len(pendentes), 'por_set': dict(resumo)}
    (WORK / 'resumo.json').write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return resultado


if __name__ == '__main__':
    auditar()
