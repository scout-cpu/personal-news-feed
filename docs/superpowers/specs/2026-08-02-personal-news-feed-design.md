# Personal News Feed — Design Spec

**Date:** 2026-08-02
**Status:** Approved sources & architecture (per brainstorming session); pending final spec review.

## Purpose

A personal daily AI news site: every morning a new "edition" is published with the
latest AI stories from Hacker News, AI papers (Hugging Face Daily Papers + arXiv),
trending Hugging Face models, and posts from a curated set of Substack newsletters.
Inspired by [the-daily-diff](https://github.com/arpitbbhayani/the-daily-diff) and
[grep](https://ramukaka-9000.github.io/grep/).

## Requirements

- **Daily editions with a browsable archive** — one page per day, prev/next
  navigation, archive index.
- **Score-based ranking, no LLM** — rank by native signals (HN points, HF paper
  upvotes, model likes/downloads); no API keys, no paid services.
- **Zero-cost, token-free sources only** — every source is a public, unauthenticated
  API or RSS feed.
- **Fully automated** — GitHub Actions cron publishes the edition daily with no
  manual step; a single source failing must not block the edition.
- **Deployed on GitHub Pages.**

## Sources

| Section | Source | Endpoint | Ranking |
|---|---|---|---|
| Hacker News · AI | Algolia HN Search API | `hn.algolia.com/api/v1/search_by_date` with AI keyword queries, last 24 h, `points >= 20` | HN points |
| Papers | Hugging Face Daily Papers | `huggingface.co/api/daily_papers` | HF community upvotes |
| Papers (fresh) | arXiv API | `export.arxiv.org/api/query`, categories `cs.AI`, `cs.LG`, `cs.CL`, newest first | Recency (deduped against HF papers by arXiv ID) |
| Trending Models | Hugging Face Hub API | `huggingface.co/api/models?sort=trendingScore&limit=…` | HF trending score |
| Newsletters | Substack RSS | `<newsletter>.substack.com/feed` (and equivalent custom domains) | Recency, last 3 days |

**AI keyword filter for HN** (case-insensitive, matched against title): `AI`,
`LLM`, `GPT`, `Claude`, `Gemini`, `machine learning`, `deep learning`,
`neural`, `transformer`, `agent`, `RAG`, `fine-tun`, `open-source model`,
`Anthropic`, `OpenAI`, `DeepMind`, `Mistral`, `Llama`, `diffusion`. Keywords live
in config, not code.

**Starter newsletter list:** Import AI (Jack Clark), One Useful Thing (Ethan
Mollick), Latent Space, Interconnects (Nathan Lambert), Ahead of AI (Sebastian
Raschka), SemiAnalysis, ChinAI, Don't Worry About the Vase (Zvi Mowshowitz).

All source parameters (keywords, thresholds, feed URLs, item limits) live in
`sources.yml` so the feed can be re-tuned without touching code.

## Architecture

Fully static. No servers, no client-side data fetching.

```
GitHub Actions (cron, daily 01:30 UTC = 07:00 IST)
  └─ scripts/fetch.py   → writes data/YYYY-MM-DD.json  (committed to repo)
  └─ scripts/build.py   → renders data/*.json → site/  (deployed to Pages)
```

### Components

- **`sources.yml`** — feed URLs, keywords, thresholds, per-section item limits.
- **`scripts/fetch.py`** — one fetcher function per source, each wrapped in its
  own try/except. Output: a single normalized JSON file for the day. A failed
  source produces an empty list plus an `errors` entry recorded in the JSON.
- **`scripts/build.py`** — Jinja2 templates render every `data/*.json` into
  `site/editions/YYYY-MM-DD/index.html`, an `site/archive/index.html` list, and
  `site/index.html` (a copy of the latest edition, so the root URL is always
  fresh, with permalinks preserved under `/editions/`).
- **`templates/` + `static/style.css`** — newspaper-style layout, dark/light
  theme via `prefers-color-scheme` plus a small JS toggle (the only JS on the
  site). Sections in order: Hacker News · AI, Papers, Trending Models,
  Newsletters. Each item shows title (linked), score, source/author, age, and a
  short snippet where the source provides one (paper abstracts, RSS excerpts —
  truncated ~200 chars).
- **`.github/workflows/daily.yml`** — cron + `workflow_dispatch`; runs tests,
  fetch, build; commits the new `data/*.json`; deploys `site/` with
  `actions/upload-pages-artifact` + `actions/deploy-pages`.

### Data model (per item in `data/YYYY-MM-DD.json`)

```json
{
  "id": "hn-41234567",
  "section": "hackernews",
  "title": "…",
  "url": "https://…",
  "score": 245,
  "score_label": "245 points",
  "author": "…",
  "published": "2026-08-02T03:15:00Z",
  "snippet": "…",
  "extra_link": {"label": "HN discussion", "url": "https://news.ycombinator.com/item?id=…"}
}
```

The daily file also carries `date`, `generated_at`, and `errors` (list of
source names that failed).

### Cross-edition dedup

HN stories and papers can trend for multiple days. The fetcher loads the item
IDs from the previous 3 editions and drops repeats.

### Error handling

- Each source fetch is independent; failures are logged into the edition JSON
  and the section renders with a small "source unavailable today" note.
- If *every* source fails, the workflow fails loudly (no empty edition is
  published) and the previous edition remains live.
- Network calls use a 30 s timeout and one retry.

## Tech stack

Python 3.12, `requests`, `feedparser`, `jinja2`, `pyyaml`. Tests with `pytest`
against recorded fixture responses (no network in tests).

## Testing

- Unit tests per fetcher: parse recorded fixture responses (JSON/Atom/RSS) into
  the normalized item model; keyword filtering; dedup logic.
- Build test: render a fixture day-file and assert on key HTML content.
- CI runs pytest before fetch/deploy in the daily workflow.

## Deployment

- New public GitHub repo `personal-news-feed` under the user's account.
- GitHub Pages served from Actions artifact (no `gh-pages` branch juggling).
- One-time manual step: enable Pages ("GitHub Actions" source) in repo settings
  via the browser where the user is logged in.

## Out of scope (YAGNI)

- LLM summarization/curation, GitHub trending repos, Reddit, search, tagging
  beyond source sections, email delivery, RSS output feed, analytics.
