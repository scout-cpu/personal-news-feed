# The Signal — personal AI news feed

A fully automated daily AI briefing, published as a static site on GitHub Pages.
Every morning at 07:00 IST a GitHub Actions cron builds a fresh edition with:

- **Hacker News · AI** — AI stories from the last 24 h (Algolia HN API), keyword-filtered, ranked by points
- **Papers** — Hugging Face Daily Papers ranked by community upvotes, plus the freshest arXiv papers (cs.AI / cs.LG / cs.CL)
- **Trending Models** — what's hot on the Hugging Face Hub right now
- **Newsletters** — latest posts from a curated set of AI Substacks

No servers, no API keys, no cost. Inspired by
[the-daily-diff](https://github.com/arpitbbhayani/the-daily-diff) and
[grep](https://ramukaka-9000.github.io/grep/).

## Tuning the feed

Everything lives in [`sources.yml`](sources.yml):

- **Add/remove newsletters** — edit the `newsletters.feeds` list (any RSS/Atom URL works, not just Substack).
- **Change the HN filter** — edit `hackernews.keywords` (a trailing `*` makes a keyword a prefix match, e.g. `fine-tun*`) or `min_points`.
- **Resize sections** — per-section `limit` values.

## How it works

```
GitHub Actions (daily cron, 01:30 UTC)
  ├─ pytest                        # never publish from broken code
  ├─ python -m newsfeed.fetch      # all sources → data/YYYY-MM-DD.json (committed)
  └─ python -m newsfeed.build      # data/*.json → site/ → GitHub Pages
```

Each day-file is committed to `data/`, so the archive is rebuilt from history on
every deploy. A failing source just leaves a note in that day's edition; the
edition is only skipped if *every* source fails.

## Local development

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pytest                     # run tests (no network needed)
.venv/bin/python -m newsfeed.fetch   # fetch today's edition
.venv/bin/python -m newsfeed.build   # render site/
.venv/bin/python -m http.server -d site 8899
```

## Startup timeline

A separate `startups.html` page recreates Chrono's homepage layout with real
startup funding data from [Startups Gallery](https://startups.gallery/news).
The existing daily briefing remains at `index.html`; its navigation links to
Startups when a funding snapshot exists.

- Desktop defaults to a horizontal, alternating timeline. Scroll with a mouse
  wheel/trackpad or focus the timeline and use Left/Right, Home and End.
- Switch to the vertical timeline using the bottom-right control. Mobile uses
  the vertical layout automatically.
- Search companies, investors, funding amounts and descriptions; filter rounds
  by stage. The person icon opens saved rounds. Saved rounds and appearance
  preferences stay in this browser's local storage.
- Open a card for funding details, original announcement and company profile.
- The information card explains provenance and the last successful refresh.

```bash
.venv/bin/python -m newsfeed.startups  # refresh public data and local artwork
.venv/bin/python -m newsfeed.build
.venv/bin/python -m http.server -d site 8899
# Open http://localhost:8899/startups.html
```

`newsfeed/startups.py` extracts the first public batch of funding records
(currently 50), deduplicates responsive table variants, and writes
`data/startups/latest.json`. Company artwork is cached in
`static/startups/images/`; no source images or fonts are hotlinked at runtime.
The daily GitHub Actions job refreshes and commits the snapshot and cached
images alongside edition data. A page fetch/parsing failure preserves the last
successful snapshot and its visible checked date. This is a build-time snapshot,
not a live browser API, and does not include records behind “Load More.”

The clone retains the reference's Inter/system-ui font declaration. Chrono did
not load an Inter font file during capture, so the same system fallback is used.
The original Chrono control vectors, small logo mark and black-hole artwork are
stored locally. Company artwork replaces general-news photos, and Signal
branding identifies the page as this independent project. See
`static/startups/ASSETS.md` for asset provenance and `design-qa.md` for the
visual and interaction checks. Chrono's authentication, paid subscriptions,
waitlist and AI services are outside this startup news page.
