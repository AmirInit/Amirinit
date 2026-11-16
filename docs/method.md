# Method & operation

The observatory reads the **unauthenticated public** GitHub contribution calendar at `github.com/users/AmirInit/contributions`. It uses no credential and thus does not reveal anything beyond what GitHub already exposes publicly; if public settings include anonymized private contributions, those aggregate counts are already public. GitHub's GraphQL contribution calendar is an official API, but querying as the account owner can return nonpublic activity. The public HTML endpoint avoids that ambiguity. Its markup is not a stable API: if GitHub changes it, strict validation stops the refresh and leaves the previous assets intact.

Dates are sorted and validated as a continuous year. Columns are weeks, Sunday through Saturday are rows, and a day with count > 0 seeds a live cell. The calendar's four intensity levels color generation zero only; no magnitude changes Conway's rules. B3/S23 evolves synchronously on an unbounded plane. The fixed viewport crops any cells outside it; the live count includes the entire plane. Dead-cell afterglow is rendering only. The animation shows 25 exact generations, then explicitly restarts from the same public seed; extinction or a still life is an honest result, not an invitation to inject cells. No random values or fabricated activity are used.

Reproduce on Linux with Python 3.11+ and network access:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m observatory
```

The run fetches current public data, validates it, renders both files in a temporary directory, verifies the images, and replaces assets only after success. GIFs work in GitHub READMEs without client-side JavaScript. Images are committed locally to the repository; GitHub caches images and updates may not be immediately visible. The GIF has a 5 MB limit, loops after its labeled finite episode, and the PNG is its first frame. A GitHub Actions schedule and manual dispatch refresh the default branch after merge, with contents-only write permission; a non-fast-forward push fails safely rather than overwriting concurrent work. Scheduled Actions may be delayed by GitHub. The PR CI runs tests without write permission; it does not test the later scheduled run.

Inspired by [github4life](https://github.com/ethomson/github4life), which uses a multi-color decay variant and a finite GIF for GitHub's cache. This implementation retains canonical binary Conway rules and separates the visualization from the simulation.
