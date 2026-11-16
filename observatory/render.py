"""Render Conway states as a finite, visually interpolated episode.

Interpolation and afterglow are presentation only; each state comes from step().
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .life import step

BG = (10, 19, 24)
PANEL = (15, 29, 33)
GRID = (25, 43, 46)
BORDER = (46, 71, 70)
MUTED = (139, 166, 163)
WHITE = (230, 241, 234)
TEAL = (130, 218, 185)
PALETTE = [(25, 43, 46), (53, 119, 98), (76, 159, 124), (116, 202, 153), (194, 237, 196)]
FONT_PATH = Path(__file__).parent / 'fonts' / 'Manrope.ttf'


def font(size, bold=False):
    face = ImageFont.truetype(str(FONT_PATH), size)
    face.set_variation_by_axes([700 if bold else 500])
    return face


def episode(initial, count=25):
    states = [set(initial)]
    for _ in range(count - 1):
        states.append(step(states[-1]))
    return states


def viewport(states, initial):
    """Fixed bounds for the entire episode, including the calendar footprint."""
    points = {(0, 0), (53, 6)} | set(initial)
    for state in states:
        points.update(state)
    return (min(x for x, y in points) - 2, min(y for x, y in points) - 2,
            max(x for x, y in points) + 2, max(y for x, y in points) + 2)


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def draw_frame(days, initial, current, nxt, generation, fraction, bounds, mobile=False, reset=False):
    width, height = (720, 860) if mobile else (1200, 680)
    im = Image.new('RGB', (width, height), BG)
    d = ImageDraw.Draw(im)
    margin = 35 if mobile else 48
    d.rounded_rectangle((1, 1, width-2, height-2), radius=18, outline=BORDER, width=2)
    d.text((margin, 35), 'AMIRINIT  /  LIFE OBSERVATORY', font=font(22 if mobile else 21, True), fill=TEAL)
    d.text((margin, 76), 'Order, in motion.', font=font(43 if mobile else 49, True), fill=WHITE)
    d.text((margin, 145), 'A contribution calendar, set in motion.', font=font(23 if mobile else 24), fill=MUTED)
    top = 215 if mobile else 210
    bottom = 645 if mobile else 535
    d.rounded_rectangle((margin, top, width-margin, bottom), radius=12, fill=PANEL, outline=BORDER, width=1)
    label = 'RESTART  /  RETURNING TO SEED' if reset else 'CONWAY  /  B3–S23'
    d.text((margin+22, top+21), label, font=font(20 if mobile else 19, True), fill=TEAL)
    # During a crossfade both discrete endpoints are shown, not a fabricated count.
    if fraction:
        stats = f'GEN {generation:02} → {(generation + 1):02}    ·    LIVE {len(current)} → {len(nxt)}'
    else:
        stats = f'GEN {generation:02}    ·    LIVE {len(current)}'
    if reset:
        stats = f'GEN {generation:02} → 00    ·    LIVE {len(current)} → {len(nxt)}'
    stats_pos = (margin+22, top+58) if mobile else (width-margin-420, top+21)
    d.text(stats_pos, stats, font=font(22 if mobile else 21, True), fill=WHITE)
    xmin, ymin, xmax, ymax = bounds
    cols, rows = xmax-xmin+1, ymax-ymin+1
    available_w = width - 2*(margin+28)
    available_h = bottom - top - (120 if mobile else 92)
    pitch = min(available_w / cols, available_h / rows, 20 if not mobile else 12)
    x0 = (width-cols*pitch)/2
    y0 = top + (105 if mobile else 75) + (available_h-rows*pitch)/2
    pad = max(0.7, pitch*0.15)
    active = TEAL
    eased = fraction*fraction*(3-2*fraction)
    for row in range(rows):
        for col in range(cols):
            p = (xmin+col, ymin+row)
            old = PALETTE[initial.get(p, 3)] if generation == 0 and p in current else active
            if p in current and p in nxt:
                color = mix(old, active, eased) if generation == 0 else active
            elif p in current:
                color = mix(old, GRID, eased)
            elif p in nxt:
                color = mix(GRID, active if not reset else PALETTE[initial.get(p, 3)], eased)
            else:
                color = GRID
            x, y = x0+col*pitch, y0+row*pitch
            d.rounded_rectangle((round(x+pad), round(y+pad), round(x+pitch-pad), round(y+pitch-pad)), radius=max(1, round(pitch*.18)), fill=color)
    if mobile:
        d.text((margin, 686), f'{days[0][0].isoformat()}  —  {days[-1][0].isoformat()}', font=font(22), fill=WHITE)
        d.text((margin, 724), f'{sum(d[1] for d in days)} CONTRIBUTIONS  /  {len(initial)} SEED CELLS', font=font(20, True), fill=MUTED)
        d.text((margin, 786), 'PUBLIC DATA  ·  FINITE EPISODE', font=font(19, True), fill=TEAL)
    else:
        d.text((margin, 572), f'{days[0][0].isoformat()}  —  {days[-1][0].isoformat()}', font=font(22), fill=WHITE)
        d.text((margin, 614), f'{sum(d[1] for d in days)} CONTRIBUTIONS  /  {len(initial)} SEED CELLS', font=font(19, True), fill=MUTED)
        d.text((width-438, 572), 'PUBLIC DATA  /  FINITE EPISODE', font=font(19, True), fill=TEAL)
        d.text((width-438, 614), 'COLOR INDICATES SEED INTENSITY', font=font(17), fill=MUTED)
    return im


def render(days, initial, output, generations=25, subdivisions=4):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if generations < 2 or subdivisions < 1:
        raise ValueError('at least two generations and one subdivision are required')
    states = episode(initial, generations)
    bounds = viewport(states, initial)
    for mobile, suffix in ((False, ''), (True, '-mobile')):
        frames, durations = [], []
        for generation, (current, nxt) in enumerate(zip(states, states[1:])):
            for part in range(subdivisions):
                frames.append(draw_frame(days, initial, current, nxt, generation, part/subdivisions, bounds, mobile))
                durations.append(1050 if generation == 0 and part == 0 else 100)
        frames.append(draw_frame(days, initial, states[-1], states[-1], len(states)-1, 0, bounds, mobile))
        durations.append(900)
        # The reset is explicitly labeled and is not a Conway transition.
        for part in range(1, 4):
            frames.append(draw_frame(days, initial, states[-1], states[0], len(states)-1, part/4, bounds, mobile, True))
            durations.append(100)
        frames[0].save(output / f'observatory{suffix}.png', optimize=True)
        # One palette for the entire episode keeps unchanged antialiased text
        # and background pixels identical between frames, improving GIF deltas.
        thumb = (frames[0].width // 2, frames[0].height // 2)
        atlas = Image.new('RGB', (thumb[0] * 8, thumb[1]))
        for index in range(8):
            sample = frames[round(index * (len(frames) - 1) / 7)]
            atlas.paste(sample.resize(thumb, Image.Resampling.NEAREST), (index * thumb[0], 0))
        palette = atlas.quantize(colors=192, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        encoded = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
        encoded[0].save(output / f'observatory{suffix}.gif', save_all=True, append_images=encoded[1:],
                        duration=durations, loop=0, optimize=True, disposal=1)
        if (output / f'observatory{suffix}.gif').stat().st_size > 5_000_000:
            raise ValueError('animation exceeds 5 MB limit')
