// Exact Conway B3/S23 on an unbounded plane. Coordinates are integer pairs.
export const key = (x, y) => `${x},${y}`;
export const parse = cell => cell.split(',').map(Number);

export function step(live) {
  const neighbors = new Map();
  for (const cell of live) {
    const [x, y] = parse(cell);
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) {
      if (!dx && !dy) continue;
      const neighbor = key(x + dx, y + dy);
      neighbors.set(neighbor, (neighbors.get(neighbor) || 0) + 1);
    }
  }
  return new Set([...neighbors].filter(([cell, n]) => n === 3 || (n === 2 && live.has(cell))).map(([cell]) => cell));
}

export function signature(live) {
  return [...live].sort().join(';');
}

export function growth(previous, current) {
  return previous === 0 ? null : (current - previous) / previous;
}

export function classify(live, previous, generation, seen) {
  if (!live.size) return 'Extinct';
  const state = signature(live);
  if (state === signature(previous)) return 'Still life';
  if (seen.has(state)) return `Exact cycle · period ${generation - seen.get(state)}`;
  return 'Evolving';
}

export const patterns = {
  glider: [[1,0],[2,1],[0,2],[1,2],[2,2]],
  blinker: [[0,0],[1,0],[2,0]],
  block: [[0,0],[1,0],[0,1],[1,1]],
};
export const toSet = cells => new Set(cells.map(([x,y]) => key(x,y)));
