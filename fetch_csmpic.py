import io
import requests
from pathlib import Path
from PIL import Image

DEST_DIR = Path(r"d:\Imagens TCG\Subir Repo\image-intake\zh-cn\CSMPiC")
DEST_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://pokecardex-scans.b-cdn.net/sets_chn/CSMPIC/{}.jpg"
TOTAL_CARDS = 48

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.pokecardex.com/'
})

downloaded = 0
for n in range(1, TOTAL_CARDS + 1):
    card_num = str(n).zfill(3)
    url = BASE_URL.format(n)
    out_path = DEST_DIR / f"{card_num}.webp"

    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        image = Image.open(io.BytesIO(resp.content))
        image.save(out_path, format='WEBP', lossless=True, quality=100)
        print(f"[{card_num}] {image.size[0]}x{image.size[1]}px -> {out_path.name} ({len(resp.content)//1024}KB)")
        downloaded += 1
    except Exception as e:
        print(f"[{card_num}] ERRO: {e}")

print(f"\nTotal baixados: {downloaded}/{TOTAL_CARDS}")
