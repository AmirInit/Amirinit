import {step, signature, growth, classify, patterns, toSet, parse} from './life.mjs';

const $ = id => document.getElementById(id);
const world = $('world'), chart = $('chart');
let contributionCells = null, snapshot = null;
let live = new Set(), previous = new Set(), generation = 0, history = [], seen = new Map();
let timer = null, transitionStart = 0, animation = 0, classification = 'Ready';
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function validateSnapshot(data) {
  if (!data || !Array.isArray(data.cells) || !/^\d{4}-\d\d-\d\d$/.test(data.from) || !/^\d{4}-\d\d-\d\d$/.test(data.through)
      || !Number.isSafeInteger(data.contributions) || data.contributions < 0 || data.cells.length > 372) throw new Error('Invalid calendar snapshot');
  const ids = new Set();
  for (const cell of data.cells) {
    if (!Array.isArray(cell) || cell.length !== 3 || !cell.every(Number.isInteger) || cell[0] < 0 || cell[0] > 53 || cell[1] < 0 || cell[1] > 6 || cell[2] < 1 || cell[2] > 4) throw new Error('Invalid calendar cell');
    const id = `${cell[0]},${cell[1]}`;
    if (ids.has(id)) throw new Error('Duplicate calendar cell');
    ids.add(id);
  }
  if (data.contributions < ids.size) throw new Error('Invalid calendar total');
  return data;
}

async function loadSnapshot() {
  // GitHub Actions commits do not trigger another Pages build. Fetching the
  // committed snapshot keeps an already deployed lab current; bundled fallback
  // keeps the lab usable if the public raw endpoint is unavailable.
  for (const url of ['https://raw.githubusercontent.com/AmirInit/Amirinit/main/lab/seed.json', './seed.json']) {
    try {
      const response = await fetch(url, {signal: AbortSignal.timeout(3500)});
      if (!response.ok) throw new Error('Snapshot unavailable');
      return validateSnapshot(await response.json());
    } catch { /* Try the bundled public snapshot. */ }
  }
  throw new Error('The public contribution snapshot is unavailable.');
}

function stop() {
  if (timer !== null) clearTimeout(timer);
  timer = null;
  $('play').textContent = '▶  Start';
  $('status').textContent = 'PAUSED';
}

function reset() {
  stop();
  cancelAnimationFrame(animation);
  const choice = $('pattern').value;
  const source = choice === 'contributions' ? contributionCells : patterns[choice];
  live = toSet(source || []);
  previous = new Set(live);
  generation = 0;
  history = [{generation, population: live.size}];
  seen = new Map([[signature(live), 0]]);
  classification = live.size ? 'Ready' : 'Extinct';
  $('seed-label').textContent = choice === 'contributions' ? 'PUBLIC CONTRIBUTIONS' : choice.toUpperCase();
  update();
  drawWorld(1);
}

function advance() {
  previous = live;
  live = step(previous);
  generation++;
  classification = classify(live, previous, generation, seen);
  const state = signature(live);
  seen.delete(state);
  seen.set(state, generation);
  if (seen.size > 1000) seen.delete(seen.keys().next().value);
  history.push({generation, population: live.size});
  if (history.length > 240) history.shift();
  update();
  transitionStart = performance.now();
  cancelAnimationFrame(animation);
  if (reducedMotion) drawWorld(1);
  else animation = requestAnimationFrame(animate);
}

function animate(now) {
  const t = Math.min(1, (now-transitionStart)/Math.min(180, 800/Number($('speed').value)));
  drawWorld(t*t*(3-2*t));
  if (t < 1) animation = requestAnimationFrame(animate);
}

function run() {
  if (timer !== null) { stop(); return; }
  $('play').textContent = 'Ⅱ  Pause';
  $('status').textContent = 'RUNNING';
  const tick = () => { advance(); timer = setTimeout(tick, 1000/Number($('speed').value)); };
  timer = setTimeout(tick, 1000/Number($('speed').value));
}

function update() {
  $('generation').textContent = String(generation).padStart(3, '0');
  $('population').textContent = live.size;
  const delta = generation ? growth(previous.size, live.size) : null;
  $('growth').textContent = delta === null ? '—' : `${delta > 0 ? '+' : ''}${(delta*100).toFixed(1)}%`;
  $('state').textContent = classification;
  drawChart();
}

function canvasSize(canvas) {
  const rect = canvas.getBoundingClientRect();
  const ratio = Math.min(devicePixelRatio || 1, 2);
  const w = Math.max(1, Math.round(rect.width*ratio)), h = Math.max(1, Math.round(rect.height*ratio));
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  const context = canvas.getContext('2d');
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  return [context, rect.width, rect.height];
}

function drawWorld(t) {
  $('transition-label').textContent = t < 1 ? `VISUAL TRANSITION TO GENERATION ${generation}` : 'DISCRETE STATE';
  const [ctx, w, h] = canvasSize(world);
  ctx.clearRect(0, 0, w, h);
  const all = new Set([...previous, ...live]);
  const points = [...all].map(parse);
  let minX = Math.min(...points.map(p => p[0]), 0), maxX = Math.max(...points.map(p => p[0]), $('pattern').value === 'contributions' ? 53 : 6);
  let minY = Math.min(...points.map(p => p[1]), 0), maxY = Math.max(...points.map(p => p[1]), 6);
  minX -= 3; maxX += 3; minY -= 3; maxY += 3;
  const pitch = Math.min((w-32)/(maxX-minX+1), (h-58)/(maxY-minY+1), 24);
  const ox = (w - (maxX-minX+1)*pitch)/2, oy = (h - (maxY-minY+1)*pitch)/2-5;
  for (let y = minY; y <= maxY; y++) for (let x = minX; x <= maxX; x++) {
    const k = `${x},${y}`, was = previous.has(k), is = live.has(k);
    let brightness = was && is ? 1 : was ? 1-t : is ? t : 0;
    const a = [27, 47, 49], b = [130, 218, 185];
    const color = a.map((n, i) => Math.round(n+(b[i]-n)*brightness));
    ctx.fillStyle = `rgb(${color.join(',')})`;
    const size = Math.max(1, pitch*.72), r = Math.min(3, size*.2);
    ctx.beginPath(); ctx.roundRect(ox+(x-minX)*pitch, oy+(y-minY)*pitch, size, size, r); ctx.fill();
  }
}

function drawChart() {
  const [ctx, w, h] = canvasSize(chart);
  ctx.clearRect(0,0,w,h);
  const left=34, right=12, top=16, bottom=22, max=Math.max(1,...history.map(p=>p.population));
  ctx.font='11px system-ui'; ctx.fillStyle='#91a9a5';
  ctx.textAlign='left'; ctx.fillText(String(max),0,top+4); ctx.fillText('0',0,h-bottom+3);
  ctx.strokeStyle='#28403f'; ctx.lineWidth=1;
  for (let i=0; i<4; i++) { const y=top+(h-top-bottom)*i/3; ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(w-right,y);ctx.stroke(); }
  if (!history.length) return;
  const x = i => left+(w-left-right)*(history.length===1 ? 0 : i/(history.length-1));
  const y = n => h-bottom-(h-top-bottom)*n/max;
  ctx.strokeStyle='#82dab9'; ctx.lineWidth=2; ctx.beginPath();
  history.forEach((p,i)=>i ? ctx.lineTo(x(i),y(p.population)) : ctx.moveTo(x(i),y(p.population)));ctx.stroke();
  const last=history[history.length-1];ctx.fillStyle='#c0f1d1';ctx.beginPath();ctx.arc(x(history.length-1),y(last.population),3,0,Math.PI*2);ctx.fill();
  $('chart-range').textContent = history.length === 1 ? 'GEN 0' : `GEN ${history[0].generation}–${last.generation}`;
}

$('play').addEventListener('click', run);
$('step').addEventListener('click', () => { stop(); advance(); });
$('reset').addEventListener('click', reset);
$('pattern').addEventListener('change', reset);
$('speed').addEventListener('input', e => { $('speed-value').textContent = `${e.target.value} / SEC`; });
window.addEventListener('resize', () => { drawWorld(1); drawChart(); });

try {
  snapshot = await loadSnapshot();
  contributionCells = snapshot.cells;
  $('dataset-note').textContent = `Public GitHub calendar · ${snapshot.from} to ${snapshot.through} · ${snapshot.contributions} contributions. Reset returns to the selected initial state.`;
} catch {
  $('pattern').querySelector('[value=contributions]').disabled = true;
  $('pattern').value = 'glider';
  $('dataset-note').textContent = 'Public contribution data could not be loaded. The canonical patterns remain available.';
}
reset();
