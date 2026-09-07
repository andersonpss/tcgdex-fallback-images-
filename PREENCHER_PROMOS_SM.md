Para preencher Sun & Moon Promos em português:

```powershell
python preencher_promos_sm.py --baixar
python preencher_promos_sm.py --auditar
```

Requer Python 3, requests e Pillow. Usa o importador existente, em lotes de 5 cartas, até 3 downloads simultâneos e pausa de 1 segundo entre lotes. Preserva arquivos locais não vazios e grava `high.webp` e `low.webp` em `pt/sm/smp/<número>/`.

Fonte: https://limitlesstcg.com/cards/pt/SMP. Usa os IDs do catálogo português do TCGdex e complementa IDs ausentes com o catálogo inglês somente quando existe imagem portuguesa no Limitless. Os scans permanecem exclusivamente em português. O relatório pode conservar nomes ingleses nesses registros adicionais.

As variantes 30a, 103a e 104a do Limitless não têm ID no catálogo TCGdex consultado. Foram incluídas como `SM30a`, `SM103a` e `SM104a`, códigos locais documentados em `relatorios/importacao_smp_pt/sem_id_tcgdex.json`.

Os relatórios ficam em `relatorios/importacao_smp_pt/`: `resultado.csv` registra origem e situação; `pendencias.csv` lista arquivos ausentes/inválidos; `resumo.json` traz os totais após a auditoria. `arquivos_anteriores.json` guarda hashes dos arquivos anteriores para conferir sua preservação.
