import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from PIL import Image, ImageDraw
import preencher_espada_escudo as motor


class TransparenciaTest(unittest.TestCase):
    def test_download_preserva_cantos_e_conteudo(self):
        for mode in ('RGBA', 'P', 'RGB'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(dir=motor.BASE) as folder:
                source = Image.new('RGBA', (600, 825), (0, 0, 0, 0))
                ImageDraw.Draw(source).rounded_rectangle((0, 0, 599, 824), radius=35,
                                                        fill=(220, 180, 30, 255))
                source = source.convert(mode)
                data = io.BytesIO()
                source.save(data, format='PNG')
                with Image.open(io.BytesIO(data.getvalue())) as original:
                    center_alpha = original.convert('RGBA').getpixel((300, 412))[3]
                client = Mock()
                client.get.return_value.content = data.getvalue()
                root = Path(folder)
                row = {'id': 'xy1-1', 'set': 'xy1', 'numero': '1', 'url': 'https://example.test/card.png'}
                with patch.object(motor, 'BASE', root), patch.object(motor, 'WORK', root), \
                     patch.object(motor, 'Cliente', return_value=client), \
                     patch.object(motor, 'salvar'), patch.object(motor.time, 'sleep'):
                    motor.baixar(client, [row], serie='xy')
                self.assertEqual(row['status'], 'baixado')
                for name in ('high', 'low'):
                    with Image.open(root / 'pt/xy/xy1/1' / f'{name}.webp') as output:
                        rgba = output.convert('RGBA')
                        self.assertEqual(rgba.getpixel((0, 0))[3], 255 if mode == 'RGB' else 0)
                        self.assertEqual(rgba.getpixel((rgba.width // 2, rgba.height // 2))[3], center_alpha)


if __name__ == '__main__':
    unittest.main()
