import unittest
import preencher_espada_escudo as app


class IdiomaTest(unittest.TestCase):
    def tearDown(self):
        app.configurar_idioma('pt')

    def test_ingles_rejeita_imagens_portuguesas(self):
        app.configurar_idioma('en')
        pagina = app.Pagina('''
            <a href="/cards/en/SSH/1"><img src="https://example.test/SSH_001_R_EN_SM.png"></a>
            <a href="/cards/en/SSH/2"><img src="https://example.test/SSH_002_R_PT_SM.png"></a>
            <a href="/cards/pt/SSH/3"><img src="https://example.test/SSH_003_R_PT_SM.png"></a>
        ''')
        self.assertEqual(list(pagina.cartas), ['1'])
        self.assertIn('/cards/en/', pagina.cartas['1']['pagina'])

    def test_relatorios_separados(self):
        app.configurar_idioma('en')
        ingles = app.WORK
        self.assertEqual(ingles.name, 'importacao_swsh_en')
        app.configurar_idioma('pt')
        self.assertEqual(app.WORK.name, 'importacao_swsh')
        self.assertNotEqual(ingles, app.WORK)

    def test_portugues_continua_funcionando(self):
        app.configurar_idioma('pt')
        pagina = app.Pagina('<a href="/cards/pt/CEL/1"><img src="https://example.test/CEL_001_R_PT_SM.png"></a>')
        self.assertEqual(list(pagina.cartas), ['1'])

    def test_idioma_invalido(self):
        with self.assertRaises(ValueError):
            app.configurar_idioma('../en')


if __name__ == '__main__':
    unittest.main()
