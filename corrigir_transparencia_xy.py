"""Restaura os arquivos XY adicionados no commit 46eb5bbe usando as fontes originais."""
import csv
import io
import json
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageOps, ImageChops
import preencher_espada_escudo as motor


def corrigir(work, commit, prefix, report_name='correcao_transparencia.json'):
    paths = subprocess.check_output(
        ['git', '-C', str(motor.BASE), 'diff-tree', '--no-commit-id', '--name-only',
         '-r', '--diff-filter=A', commit, '--', prefix], text=True).splitlines()
    targets = set(paths)
    with (work / 'resultado.csv').open(encoding='utf-8-sig', newline='') as f:
        rows = [r for r in csv.DictReader(f, delimiter=';')
                if any(f"{prefix}/{r['set']}/{r['numero']}/{n}.webp" in targets
                       for n in ('high', 'low'))]
    covered = {f"{prefix}/{r['set']}/{r['numero']}/{n}.webp"
               for r in rows if r['url'] for n in ('high', 'low')} & targets
    if not targets or covered != targets:
        raise ValueError(f'Arquivos sem fonte: {sorted(targets - covered)}')
    context = threading.local()

    def repair(row):
        result = {'id': row['id'], 'url': row['url'], 'arquivos': []}
        try:
            if not hasattr(context, 'client'):
                context.client = motor.Cliente()
            content = context.client.get(row['url']).content
            with Image.open(io.BytesIO(content)) as source:
                source.load()
                if source.width < 400 or source.height < 550:
                    raise ValueError(f'Resolucao insuficiente: {source.size}')
                source = source.convert('RGBA')
                for name, size, quality in [('high', (600, 825), 95), ('low', (245, 337), 92)]:
                    rel = f"{prefix}/{row['set']}/{row['numero']}/{name}.webp"
                    if rel not in targets:
                        continue
                    path = motor.BASE / rel
                    expected = ImageOps.contain(source, size, Image.Resampling.LANCZOS)
                    alpha = expected.getchannel('A')
                    with Image.open(path) as current:
                        same = current.size == expected.size and ImageChops.difference(
                            current.convert('RGBA').getchannel('A'), alpha).getbbox() is None
                    if not same:
                        temp = path.with_suffix('.webp.part')
                        expected.save(temp, format='WEBP', quality=quality, method=4)
                        with Image.open(temp) as check:
                            check.load()
                            assert check.size == expected.size
                            assert ImageChops.difference(check.convert('RGBA').getchannel('A'), alpha).getbbox() is None
                        temp.replace(path)
                    result['arquivos'].append({'path': rel, 'corrigido': not same,
                                               'alpha_min': alpha.getextrema()[0]})
        except Exception as error:
            result['erro'] = str(error)
        return result

    results = []
    report = work / report_name
    print(f'{prefix}: {len(rows)} cartas; commit {commit}', flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(repair, rows):
            results.append(result)
            if len(results) % 25 == 0 or 'erro' in result:
                report.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
                print(f"{prefix}: {len(results)}/{len(rows)}; erros: {sum('erro' in r for r in results)}", flush=True)
    report.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    errors = sum('erro' in r for r in results)
    print(f"Concluido: {len(results)} cartas, {errors} erros; "
          f"{sum(a['corrigido'] for r in results for a in r['arquivos'])} arquivos corrigidos", flush=True)
    if errors:
        raise SystemExit(1)


def main():
    corrigir(motor.BASE / 'relatorios/importacao_xy_pt', '46eb5bbe', 'pt/xy')


if __name__ == '__main__':
    main()
