Para preencher XY em português:

```powershell
python preencher_xy.py --baixar
python preencher_xy.py --auditar
```

Requer Python 3, requests e Pillow. Os arquivos `high.webp` e `low.webp` ficam em `pt/xy/<set>/<localId>/`, com os códigos do TCGdex. Arquivos existentes não vazios são preservados. Os downloads usam lotes de 5 cartas, até 3 transferências simultâneas e pausa de 1 segundo entre lotes.

Fonte das imagens: https://limitlesstcg.com/cards/pt. O catálogo inglês do TCGdex complementa IDs que faltam no português, incluindo XY Promos, Yellow A Alternate e Generations. Somente URLs de scans portugueses são aceitas; nomes de cartas sem tradução cadastrada podem permanecer em inglês no relatório.

As seis variantes Yellow A usam os IDs do set `xya` e os scans das respectivas coleções de origem no Limitless. Quando o TCGdex também cadastra a mesma variante no set de origem, ambos os caminhos são preenchidos para corresponder à API.

Os relatórios ficam em `relatorios/importacao_xy_pt/`: `plano.json`, `resultado.csv`, `pendencias.csv` e `resumo.json`. O registro `arquivos_anteriores.json` contém hashes dos arquivos anteriores. A auditoria decodifica cada WEBP para verificar sua integridade. Erros de download ficam registrados e não são substituídos por imagens de outro idioma.
