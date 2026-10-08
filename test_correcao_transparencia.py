import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image, ImageChops, ImageDraw, ImageOps
import corrigir_transparencia_xy as repair


class CorrecaoTest(unittest.TestCase):
    def test_repara_apenas_arquivos_do_commit_e_preserva_alpha(self):
        for prefix in ('pt/sm', 'pt/swsh', 'en/swsh'):
            with self.subTest(prefix=prefix), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                target = f'{prefix}/set/1/high.webp'
                high = root / target
                high.parent.mkdir(parents=True)
                low = high.with_name('low.webp')
                source = Image.new('RGBA', (600, 825), (0, 0, 0, 0))
                ImageDraw.Draw(source).rounded_rectangle((0, 0, 599, 824), radius=35,
                                                        fill=(210, 150, 30, 255))
                source.convert('RGB').save(high, 'WEBP')
                source.convert('RGB').save(low, 'WEBP')
                low_before = low.read_bytes()
                payload = io.BytesIO()
                source.save(payload, 'PNG')
                self.write_rows(root)
                client = Mock()
                client.get.return_value.content = payload.getvalue()
                with patch.object(repair.motor, 'BASE', root), \
                     patch.object(repair.motor, 'Cliente', return_value=client), \
                     patch.object(repair.subprocess, 'check_output', return_value=target + '\n'):
                    repair.corrigir(root, 'test-commit', prefix)
                    first = high.read_bytes()
                    repair.corrigir(root, 'test-commit', prefix)
                self.assertEqual(first, high.read_bytes())
                self.assertEqual(low_before, low.read_bytes())
                with Image.open(high) as output:
                    expected = ImageOps.contain(source, (600, 825), Image.Resampling.LANCZOS)
                    self.assertIsNone(ImageChops.difference(output.getchannel('A'),
                                                           expected.getchannel('A')).getbbox())
                report = json.loads((root / 'correcao_transparencia.json').read_text(encoding='utf-8'))
                self.assertEqual(len(report[0]['arquivos']), 1)
                self.assertFalse(report[0]['arquivos'][0]['corrigido'])

    def test_fonte_ausente_interrompe_antes_do_download(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.write_rows(root)
            with patch.object(repair.subprocess, 'check_output',
                              return_value='pt/sm/set/2/high.webp\n'), \
                 patch.object(repair.motor, 'Cliente') as client:
                with self.assertRaises(ValueError):
                    repair.corrigir(root, 'test-commit', 'pt/sm')
                client.assert_not_called()

    @staticmethod
    def write_rows(root):
        with (root / 'resultado.csv').open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'set', 'numero', 'url'], delimiter=';')
            writer.writeheader()
            writer.writerow({'id': 'set-1', 'set': 'set', 'numero': '1',
                             'url': 'https://example.test/source.png'})


if __name__ == '__main__':
    unittest.main()
