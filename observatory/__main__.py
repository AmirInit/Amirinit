"""Fetch, validate and render to a temporary directory before replacing assets."""
import json
import os
from pathlib import Path
import tempfile
from PIL import Image
from .data import fetch_calendar, seed
from .render import render


def snapshot(days, initial):
    return {'source': 'GitHub public contribution calendar',
            'from': days[0][0].isoformat(), 'through': days[-1][0].isoformat(),
            'contributions': sum(day[1] for day in days),
            'cells': [[x, y, level] for (x, y), level in sorted(initial.items())]}


def main():
    days = fetch_calendar()
    initial = seed(days)
    with tempfile.TemporaryDirectory(dir='.') as tmp:
        render(days, initial, tmp)
        names = ('observatory.png', 'observatory.gif', 'observatory-mobile.png', 'observatory-mobile.gif')
        for name in names:
            with Image.open(Path(tmp) / name) as image:
                image.verify()
            # Decode every GIF frame before any output is replaced.
            if name.endswith('.gif'):
                with Image.open(Path(tmp) / name) as image:
                    if image.n_frames < 2:
                        raise ValueError('animation contains fewer than two frames')
                    for index in range(image.n_frames):
                        image.seek(index)
                        image.load()
        data = json.dumps(snapshot(days, initial), separators=(',', ':'), ensure_ascii=True) + '\n'
        (Path(tmp) / 'seed.json').write_text(data, encoding='utf-8')
        Path('assets').mkdir(exist_ok=True)
        Path('lab').mkdir(exist_ok=True)
        for name in names:
            os.replace(Path(tmp) / name, Path('assets') / name)
        os.replace(Path(tmp) / 'seed.json', Path('lab') / 'seed.json')
    print(f'Rendered {len(days)} public days, {len(initial)} live seed cells.')


if __name__ == '__main__':
    main()
