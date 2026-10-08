"""Restaura a transparencia nas importacoes SWSH e SM de 06/09/2026."""
from corrigir_transparencia_xy import corrigir
from preencher_espada_escudo import BASE


IMPORTACOES = [
    ('importacao_smp_pt', 'f6c93759', 'pt/sm'),
    ('importacao_swsh', 'f2c767c8', 'pt/swsh'),
    ('importacao_swsh_en', 'f08b189a', 'en/swsh'),
]


def main():
    for pasta, commit, prefix in IMPORTACOES:
        corrigir(BASE / 'relatorios' / pasta, commit, prefix)


if __name__ == '__main__':
    main()
