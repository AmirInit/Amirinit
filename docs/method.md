# Method & operation

## Public data and Conway's rules

The observatory reads GitHub's **unauthenticated public** contribution calendar at `github.com/users/AmirInit/contributions`. It uses no credential, so it exposes only information already visible publicly. If the profile is configured to include anonymized private contributions, those aggregate counts are already public. GitHub's official GraphQL API can expose additional activity when queried as the account owner; the public page avoids that ambiguity. Its HTML is not a stable API: strict validation rejects incomplete, malformed, stale, or inconsistent calendars and leaves the previous generated files in place. Network failures are retried; persistent failures stop the refresh.

Dates are sorted and checked for a continuous year. Columns are weeks, Sunday through Saturday are rows, and a day with a nonzero count seeds a live cell. GitHub's four intensity levels color generation zero only. B3/S23 evolves synchronously on an unbounded plane; colors, fades, and animation have no effect on the binary state. The renderer computes all 25 discrete generations before choosing a single fixed viewport containing every live cell in the episode, with room around the original calendar. During a fade, both endpoint generation numbers and populations are shown. The labeled reset is a visual transition back to the seed, not another Conway generation. No cells are injected and no activity is fabricated.

## Emergence Lab

The lab implements the same unbounded B3/S23 rules in browser-side JavaScript. Start, pause, step, reset, speed, and pattern controls operate on discrete states; the brief cell fade is visual only. Its viewport fits the current and preceding states. The chart records actual populations (the most recent 240 generations); growth is `(current − previous) / previous`, shown as `—` when the previous population is zero or no previous generation exists.

The lab detects extinction, a still life, and exact repeated configurations using absolute coordinates. It retains up to 1,000 distinct recent states, so it does not guarantee detection of longer cycles. Translated patterns such as gliders are not counted as repeats unless the complete state reappears at exactly the same coordinates. An empty set is reported as extinct, rather than as a still life. The public seed snapshot is generated alongside the GIF. The lab first requests the current `lab/seed.json` from this repository's `main` branch via GitHub's public raw endpoint, then falls back to its bundled snapshot if unavailable. The displayed date range identifies the snapshot in use; GitHub caches may delay updates.

## Reproduce and deploy

With Python 3.11+, Node.js 20+, and network access:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
node --test tests/lab.test.mjs
.venv/bin/python -m observatory
python3 -m http.server 8765 --directory lab
```

Open `http://localhost:8765/` for the local lab. The generator renders and verifies both desktop and mobile GIFs and their static PNGs in a temporary directory before replacing the published files and public snapshot. Each GIF uses a shared episode-wide palette for compact, stable frame deltas and is limited to 5 MB. The README uses a GitHub-supported `<picture>` source for narrow displays and retains a desktop fallback; the PNGs provide static alternatives. GIFs work without README JavaScript and may be cached by GitHub.

The daily and manually dispatched refresh workflow runs only on `main`, uses contents-only write permission, serializes refreshes, and commits only changed assets and the snapshot. A failed fetch, validation, rendering, or non-fast-forward push leaves the last committed output intact. The separate Pages workflow deploys only the `lab/` directory to this repository's project site; it does not modify the personal website repository. Changes made by the refresh workflow's `GITHUB_TOKEN` do not trigger another Pages build, so the lab reads the current public snapshot from `main` with the bundled fallback described above. Scheduled Actions can be delayed by GitHub.

Inspired by [github4life](https://github.com/ethomson/github4life), which uses a multi-color decay variant and a finite GIF for GitHub's cache. This implementation retains canonical binary Conway rules and separates visualization from simulation. The bundled Manrope typeface is distributed under the [SIL Open Font License](../observatory/fonts/OFL.txt).
