As imagens são obtidas das coleções em https://limitlesstcg.com/cards/pt/ e gravadas em `pt/swsh/<set TCGdex>/<localId TCGdex>/high.webp` e `low.webp`.

O script `preencher_espada_escudo.py` inclui os sets principais, especiais, promocionais e galerias da série Espada e Escudo. A lista de cartas vem do TCGdex em português. Quando uma subcoleção está vazia nesse idioma, usa o catálogo inglês para seus IDs, mantendo exclusivamente imagens com marcador `_PT_` no Limitless. Isso é necessário para `cel25cc`, cujas pastas usam `CC001` a `CC025`.

Requisitos: Python 3, `requests` e `Pillow`.

```powershell
python preencher_espada_escudo.py
python preencher_espada_escudo.py --baixar
```

O primeiro comando prepara o mapeamento; o segundo preenche os arquivos ausentes. Arquivos existentes e não vazios são preservados. O programa pode ser executado novamente para retomar o trabalho. Os catálogos consultados ficam em `relatorios/importacao_swsh/`, junto com `plano.json` e `resultado.csv`, que registra a URL de origem, ID, nome e situação de cada carta.

Os downloads são feitos em lotes de 5 cartas, com até 3 transferências simultâneas e pausa de 1 segundo entre lotes. Há timeout e até 3 novas tentativas para falhas temporárias, respeitando `Retry-After`. Cada imagem é decodificada antes de ser salva; arquivos WEBP são escritos temporariamente e renomeados após a conversão.

Usa a imagem original quando disponível, ou a versão LG publicada no Limitless. A proporção é preservada: high cabe em 600×825 pixels; low em 245×337. A conversão usa WEBP com qualidade 95/92. Não tenta substituir por imagens de outro idioma quando o scan português não existe.

As situações `sem_correspondencia` e `erro` ficam registradas para revisão. A primeira significa que a carta do TCGdex não apareceu com imagem PT na página da coleção do Limitless; a segunda contém o erro de download/conversão. Essas situações não comprovam ausência de uma edição física em português.

Também são incluídas as 16 energias básicas de Espada e Escudo e Astros Cintilantes que o Limitless lista, mas que não têm ID de carta nos respectivos catálogos do TCGdex. Para elas, os sets continuam sendo `swsh1` e `swsh9`; as pastas das cartas usam os códigos do Limitless `G`, `R`, `W`, `L`, `P`, `F`, `D` e `M`. Esses códigos de carta não são apresentados como IDs oficiais do TCGdex no nome descritivo do relatório.

Depois da importação, `python auditar_importacao_swsh.py` decodifica os arquivos e gera `resumo.json` e `pendencias.csv` na mesma pasta de relatórios.
