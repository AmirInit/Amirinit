"""Render deterministic, finite episodes; no visual trail affects the model."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .life import step

W, H = 1200, 620
BG = (11, 20, 26)
MUTED = (114, 145, 150)
WHITE = (224, 237, 231)
TEAL = (111, 216, 187)
PALETTE = [(24, 55, 54), (48, 112, 94), (66, 155, 121), (110, 206, 154), (188, 239, 197)]


def font(size, bold=False):
    face = ImageFont.truetype(str(Path(__file__).parent / 'fonts' / 'Manrope.ttf'), size)
    face.set_variation_by_axes([700 if bold else 500])
    return face


def draw_frame(days, initial, live, generation, trails):
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((1, 1, W-2, H-2), radius=16, outline=(43, 71, 73), width=2)
    d.text((56, 44), 'A M I R I N I T   /   L I F E  O B S E R V A T O R Y', font=font(15, True), fill=TEAL)
    d.text((56, 87), 'Order, in motion.', font=font(38, True), fill=WHITE)
    d.text((57, 144), 'A contribution calendar becomes a cellular universe.', font=font(19), fill=MUTED)
    d.line((56, 194, 1144, 194), fill=(38, 65, 66), width=1)
    d.text((56, 215), 'CONWAY  /  B3-S23', font=font(14, True), fill=TEAL)
    d.text((760, 215), 'GEN %02d   /   LIVE %03d' % (generation, len(live)), font=font(14, True), fill=WHITE)
    # Grid is a fixed window into the unbounded simulation; the 53-week seed
    # is centered vertically, leaving room for its descendants to spread.
    x0, y0, pitch, size = 56, 263, 20, 14
    for x in range(54):
        for y in range(12):
            cx, cy = x0 + pitch*x, y0 + pitch*y
            p = (x, y-2)
            color = (21, 39, 43)
            if p in trails and p not in live:
                color = (27, 59, 54) if trails[p] > 1 else (23, 47, 47)
            if p in live:
                color = PALETTE[initial.get(p, 3)] if generation == 0 else (111, 216, 178)
            d.rounded_rectangle((cx, cy, cx+size, cy+size), radius=3, fill=color)
    d.line((56, 525, 1144, 525), fill=(38, 65, 66), width=1)
    d.text((56, 549), '%s  —  %s' % (days[0][0].isoformat(), days[-1][0].isoformat()), font=font(14), fill=WHITE)
    d.text((56, 578), '%d PUBLIC CONTRIBUTIONS  /  %d SEED CELLS' % (sum(d[1] for d in days), len(initial)), font=font(12, True), fill=MUTED)
    d.text((775, 549), 'FINITE EPISODE  /  RESTARTS', font=font(13, True), fill=TEAL)
    d.text((775, 578), 'COLOR = INITIAL ACTIVITY INTENSITY', font=font(11), fill=MUTED)
    return im


def render(days, initial, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    frames = []
    live = set(initial)
    trails = {}
    for generation in range(25):
        frames.append(draw_frame(days, initial, live, generation, trails))
        trails = {p: age-1 for p, age in trails.items() if age > 1}
        nxt = step(live)
        trails.update({p: 3 for p in live - nxt})
        live = nxt
    frames[0].save(output / 'observatory.png', optimize=True)
    frames[0].save(output / 'observatory.gif', save_all=True, append_images=frames[1:], duration=[1600]+[360]*23+[1200], loop=0, optimize=True, disposal=2)
    if (output / 'observatory.gif').stat().st_size > 5_000_000:
        raise ValueError('animation exceeds 5 MB limit')
