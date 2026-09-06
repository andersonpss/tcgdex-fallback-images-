Execute nesta pasta, com Python 3 (sem instalar dependências):

```powershell
python conferir_imagens_tcgdex.py
```

Escolha a série e depois o set digitando o número do menu ou o ID. Para selecionar diretamente:

```powershell
python conferir_imagens_tcgdex.py --serie swsh --set cel25
```

A consulta usa exclusivamente o idioma `pt`. Obtém a lista de cartas do set uma vez e verifica as imagens em lotes de 5 cartas, sem paralelismo, com 2 segundos entre lotes e pelo menos 0,4 segundo entre requisições. Pode ajustar com `--lote 3 --pausa 4` (máximo 10 cartas; pausa mínima 1 segundo). Erros temporários têm até 3 tentativas e respeitam `Retry-After`.

Quando a API não informa imagem, a carta é considerada sem imagem cadastrada. Quando informa, são verificadas por HEAD as variantes high/low em WEBP/PNG até encontrar uma disponível. Erros de conexão, bloqueios e respostas inesperadas são classificados como inconclusivos, nunca como imagem ausente.

A comparação local procura arquivos de imagem não vazios em `pt/série/set/número/`, incluindo high/low, e arquivos diretamente no set com nome igual ao número ou `set-número`. Aceita zeros à esquerda (001 e 1) e prefixos como SM e TG. Nomes livres de scans não são identificados automaticamente. A presença local indica um arquivo existente, sem validar sua integridade ou exigir as duas resoluções.

Ao final, o terminal lista as cartas sem imagem nos dois lugares, as ausentes no TCGdex que já existem localmente e as inconclusivas. Um CSV completo, compatível com Excel, fica em `relatorios/`. A cobertura se limita às cartas que o TCGdex lista no set em português. Ctrl+C cancela a consulta; uma execução cancelada não gera relatório parcial. Nenhuma imagem é alterada ou baixada.

Função reutilizável: `conferir_imagens(serie, conjunto, raiz=BASE, lote=5, pausa=2.0)` retorna uma lista de registros. Código de saída: 0 concluído, 2 com consultas inconclusivas, 1 falha, 130 cancelamento.

Referências oficiais: https://tcgdex.dev/rest/sets e https://tcgdex.dev/pt-br/sdks/javascript (variantes de imagem).
