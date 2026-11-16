import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from unittest.mock import patch
from urllib.error import URLError
from pathlib import Path
from PIL import Image
from observatory.data import fetch_calendar, parse_calendar, seed
from observatory.life import step
from observatory.render import render, episode, viewport
from observatory.__main__ import snapshot


def fixture():
    start = date(2025, 1, 5)
    return [(start + timedelta(days=i), 1 if i in (0, 2, 7) else 0, 1 if i in (0, 2, 7) else 0) for i in range(364)]


def html_fixture(days):
    return ''.join(f'<td id="contribution-day-component-{i}" data-date="{day}" data-level="{level}"></td><tool-tip for="contribution-day-component-{i}">{count if count else "No"} contributions on a day.</tool-tip>' for i, (day, count, level) in enumerate(days))


class LifeTests(unittest.TestCase):
    def test_still_lifes(self):
        for pattern in ({(0,0),(1,0),(0,1),(1,1)}, {(1,0),(2,0),(0,1),(3,1),(1,2),(2,2)}):
            self.assertEqual(step(pattern), pattern)

    def test_blinker(self):
        horizontal = {(0,0),(1,0),(2,0)}
        self.assertEqual(step(horizontal), {(1,-1),(1,0),(1,1)})
        self.assertEqual(step(step(horizontal)), horizontal)

    def test_glider_and_unbounded_boundary(self):
        glider = {(1,0),(2,1),(0,2),(1,2),(2,2)}
        result = glider
        for _ in range(4):
            result = step(result)
        self.assertEqual(result, {(x+1,y+1) for x,y in glider})
        self.assertIn((0,-1), step({(-1,0),(0,0),(1,0)}))
        self.assertEqual(step(set()), set())


class DataTests(unittest.TestCase):
    def test_parse_and_seed(self):
        days = fixture()
        self.assertEqual(parse_calendar(html_fixture(days)), days)
        self.assertEqual(seed(days), {(0,0):1,(0,2):1,(1,0):1})
        saved = snapshot(days, seed(days))
        self.assertEqual(saved['cells'], [[0,0,1],[0,2,1],[1,0,1]])
        self.assertEqual(saved['contributions'], 3)

    def test_viewport_contains_every_generation(self):
        initial = {(0, 0): 1, (1, 0): 1, (2, 0): 1}
        states = episode(initial, 20)
        xmin, ymin, xmax, ymax = viewport(states, initial)
        self.assertTrue(all(xmin <= x <= xmax and ymin <= y <= ymax for state in states for x, y in state))
        self.assertLess(ymin, 0)

    def test_invalid(self):
        for html in ('', html_fixture(fixture()[:-1]).replace('contributions on a day', 'broken'), html_fixture(fixture()[:3]), html_fixture(fixture()) + html_fixture(fixture()[:1])):
            with self.assertRaises(ValueError):
                parse_calendar(html)

    def test_fetch_retries_and_rejects_stale_calendar(self):
        today = datetime.now(timezone.utc).date()
        days = [(today - timedelta(days=363-i), 0, 0) for i in range(364)]
        payload = html_fixture(days).encode()
        with patch('observatory.data.urlopen', side_effect=[URLError('temporary'), BytesIO(payload)]), patch('observatory.data.sleep'):
            self.assertEqual(fetch_calendar(), days)
        stale = [(d - timedelta(days=10), n, level) for d, n, level in days]
        with patch('observatory.data.urlopen', return_value=BytesIO(html_fixture(stale).encode())):
            with self.assertRaisesRegex(ValueError, 'stale'):
                fetch_calendar()

    def test_render_deterministic(self):
        days = fixture()
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            render(days, seed(days), a, generations=4, subdivisions=2)
            render(days, seed(days), b, generations=4, subdivisions=2)
            for name in ('observatory.png', 'observatory.gif', 'observatory-mobile.png', 'observatory-mobile.gif'):
                self.assertEqual((Path(a)/name).read_bytes(), (Path(b)/name).read_bytes())
                with Image.open(Path(a)/name) as im:
                    self.assertEqual(im.size, (720, 860) if '-mobile' in name else (1200, 680))
                    if name.endswith('.gif'):
                        self.assertGreater(im.n_frames, 1)


if __name__ == '__main__':
    unittest.main()
