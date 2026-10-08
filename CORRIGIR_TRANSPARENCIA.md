Para restaurar a transparência original das importações de 6 de setembro de 2026:

```powershell
python corrigir_transparencia_20260906.py
```

São verificados apenas os arquivos adicionados nestes commits:

- `f6c93759`: Sol e Lua Promos em português (`pt/sm`).
- `f2c767c8`: Espada e Escudo em português (`pt/swsh`).
- `f08b189a`: Espada e Escudo em inglês (`en/swsh`).

O commit `1aa0e2e2` apenas renomeou quatro promos de Sol e Lua (`SM245` a
`SM248`), sem alterar suas imagens. Elas já possuem transparência e não são
regeneradas.

A rotina baixa a fonte registrada em cada `resultado.csv`, preserva seu canal
alfa e compara as versões `high` e `low` com os arquivos locais. Somente imagens
com transparência ou dimensões diferentes são regeneradas. As dimensões, a
qualidade e o idioma seguem a importação original. Nenhum arredondamento
artificial é aplicado. Arquivos anteriores às importações são preservados.

Cada pasta de importação em `relatorios/` recebe `correcao_transparencia.json`,
com o resultado por carta e arquivo. O relatório é atualizado a cada 25 cartas;
uma execução interrompida pode ser reiniciada e os arquivos já correspondentes
à fonte serão preservados. O relatório descreve a execução mais recente.

A correção de XY continua disponível por `python corrigir_transparencia_xy.py`.
