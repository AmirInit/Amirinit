"""Fetch, validate and render to a temporary directory before replacing assets."""
import os
from pathlib import Path
import tempfile
from PIL import Image
from .data import fetch_calendar, seed
from .render import render


def main():
    days = fetch_calendar()
    initial = seed(days)
    with tempfile.TemporaryDirectory(dir='.') as tmp:
        render(days, initial, tmp)
        for name in ('observatory.png', 'observatory.gif'):
            with Image.open(Path(tmp) / name) as image:
                image.verify()
        Path('assets').mkdir(exist_ok=True)
        for name in ('observatory.png', 'observatory.gif'):
            os.replace(Path(tmp) / name, Path('assets') / name)
    print(f'Rendered {len(days)} public days, {len(initial)} live seed cells.')


if __name__ == '__main__':
    main()
