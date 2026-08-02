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
