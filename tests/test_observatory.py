import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from PIL import Image
from observatory.data import parse_calendar, seed
from observatory.life import step
from observatory.render import render


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

    def test_invalid(self):
        for html in ('', html_fixture(fixture()[:-1]).replace('contributions on a day', 'broken'), html_fixture(fixture()[:3])):
            with self.assertRaises(ValueError):
                parse_calendar(html)

    def test_render_deterministic(self):
        days = fixture()
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            render(days, seed(days), a)
            render(days, seed(days), b)
            for name in ('observatory.png', 'observatory.gif'):
                self.assertEqual((Path(a)/name).read_bytes(), (Path(b)/name).read_bytes())
                with Image.open(Path(a)/name) as im:
                    self.assertEqual(im.size, (1200,620))
                    if name.endswith('.gif'):
                        self.assertGreater(im.n_frames, 1)


if __name__ == '__main__':
    unittest.main()
