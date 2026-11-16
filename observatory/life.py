"""Synchronous B3/S23 on an unbounded, initially finite plane."""
from collections import Counter


def step(live):
    counts = Counter((x + dx, y + dy) for x, y in live
                     for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                     if dx or dy)
    return {cell for cell, n in counts.items() if n == 3 or (n == 2 and cell in live)}
