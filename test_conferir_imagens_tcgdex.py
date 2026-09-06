import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import conferir_imagens_tcgdex as app


class ClienteFalso:
    def obter(self, caminho):
        return {"serie": {"id": "sv"}, "cards": [
            {"id": "sv01-001", "localId": "001", "name": "Local"},
            {"id": "sv01-002", "localId": "002", "name": "Falta"},
            {"id": "sv01-003", "localId": "003", "name": "Online", "image": "https://example.test/ok"},
            {"id": "sv01-004", "localId": "004", "name": "Erro", "image": "https://example.test/erro"}]}

    def solicitar(self, url, metodo):
        if "/erro/" in url:
            raise URLError("offline")
        return True


class ConferenciaTest(unittest.TestCase):
    def test_classificacao_local_e_lotes(self):
        with tempfile.TemporaryDirectory(dir=app.BASE) as temp:
            raiz = Path(temp)
            pasta = raiz / "pt/sv/sv01/1"
            pasta.mkdir(parents=True)
            (pasta / "low.webp").write_bytes(b"imagem")
            with patch.object(app.time, "sleep") as sleep:
                linhas = app.conferir_imagens("sv", "sv01", raiz=raiz, lote=2, cliente=ClienteFalso())
            self.assertEqual([r["status"] for r in linhas], ["ja_existe_local", "falta_nos_dois", "disponivel_tcgdex", "inconclusivo"])
            sleep.assert_called_once_with(2.0)

    def test_404_em_todas_variantes(self):
        cliente = ClienteFalso()
        with patch.object(cliente, "solicitar", side_effect=HTTPError("url", 404, "missing", {}, None)) as chamada:
            self.assertEqual(app.imagem_remota(cliente, {"image": "https://example.test"})[0], "ausente")
            self.assertEqual(chamada.call_count, 4)

    def test_prefixos_preservados(self):
        self.assertEqual(app.normalizar("TG001"), app.normalizar("tg1"))
        self.assertNotEqual(app.normalizar("TG01"), app.normalizar("01"))

    def test_serie_incorreta(self):
        with self.assertRaises(ValueError):
            app.conferir_imagens("xy", "sv01", cliente=ClienteFalso())


if __name__ == "__main__":
    unittest.main()
