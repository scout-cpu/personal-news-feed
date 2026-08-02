# Personal AI News Feed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A static daily AI news site (HN, HF papers, arXiv, HF trending models, Substack newsletters) built by a Python pipeline and published to GitHub Pages by a daily GitHub Actions cron.

**Architecture:** `newsfeed` Python package: one fetcher module per source normalizes items into a shared `Item` model; an orchestrator writes `data/YYYY-MM-DD.json`; a builder renders all day-files through Jinja2 templates into `site/`. GitHub Actions runs tests → fetch → commit data → build → deploy Pages.

**Tech Stack:** Python 3.12, requests, feedparser, jinja2, pyyaml, pytest. No JS frameworks; one small theme-toggle script.

## Global Constraints

- No paid services, API keys, or tokens anywhere (spec: "Zero-cost, token-free sources only").
- All tunables (keywords, thresholds, feed URLs, limits) live in `sources.yml`, never hardcoded.
- Tests never hit the network — fixtures only.
- Every fetcher failure is isolated; edition publishes unless ALL sources fail.
- Network calls: 30 s timeout, one retry.
- Edition date is the run date in `Asia/Kolkata`.
- Site must work at a sub-path (GitHub Pages project site) → all URLs relative, per-page `base` prefix.

## File Structure

```
sources.yml                  # all tunables
requirements.txt
newsfeed/
  __init__.py
  models.py                  # Item dataclass + (de)serialization
  config.py                  # load sources.yml
  http.py                    # get() with timeout + 1 retry
  keywords.py                # keyword matcher for HN titles
  fetchers/
    __init__.py              # FETCHERS registry {section: fn}
    hackernews.py
    papers.py                # HF daily papers + arXiv, merged & deduped
    models_hub.py            # HF trending models
    newsletters.py           # Substack RSS
  dedup.py                   # cross-edition dedup
  fetch.py                   # python -m newsfeed.fetch → data/DATE.json
  build.py                   # python -m newsfeed.build → site/
templates/base.html, edition.html, archive.html
static/style.css, theme.js
data/                        # committed day-files
tests/fixtures/*             # recorded API responses
tests/test_*.py
.github/workflows/daily.yml
README.md
```

---

### Task 1: Scaffolding, Item model, config loader

**Files:**
- Create: `requirements.txt`, `sources.yml`, `.gitignore`, `newsfeed/__init__.py`, `newsfeed/models.py`, `newsfeed/config.py`, `tests/test_models.py`, `tests/test_config.py`

**Interfaces:**
- Produces: `Item` dataclass with fields `id: str`, `section: str`, `title: str`, `url: str`, `score: int | None`, `score_label: str`, `author: str`, `published: str` (ISO 8601 UTC), `snippet: str`, `extra_link: dict | None` (`{"label": str, "url": str}`); methods `to_dict() -> dict`, `Item.from_dict(d) -> Item`.
- Produces: `config.load(path="sources.yml") -> dict` (parsed YAML).

- [ ] **Step 1: Write scaffolding + failing tests**

`requirements.txt`:
```
requests==2.32.*
feedparser==6.0.*
jinja2==3.1.*
PyYAML==6.0.*
pytest==8.*
```

`.gitignore`:
```
__pycache__/
.pytest_cache/
site/
.venv/
```

`sources.yml`:
```yaml
hackernews:
  min_points: 20
  window_hours: 24
  limit: 15
  keywords:
    - AI
    - LLM
    - GPT
    - Claude
    - Gemini
    - machine learning
    - deep learning
    - neural
    - transformer
    - agent
    - RAG
    - fine-tun
    - Anthropic
    - OpenAI
    - DeepMind
    - Mistral
    - Llama
    - diffusion
    - open-source model
papers:
  hf_limit: 12
  arxiv_categories: [cs.AI, cs.LG, cs.CL]
  arxiv_limit: 8
models:
  limit: 10
newsletters:
  window_days: 3
  limit: 12
  feeds:
    - name: Import AI
      url: https://importai.substack.com/feed
    - name: One Useful Thing
      url: https://www.oneusefulthing.org/feed
    - name: Latent Space
      url: https://www.latent.space/feed
    - name: Interconnects
      url: https://www.interconnects.ai/feed
    - name: Ahead of AI
      url: https://magazine.sebastianraschka.com/feed
    - name: SemiAnalysis
      url: https://semianalysis.com/feed
    - name: ChinAI
      url: https://chinai.substack.com/feed
    - name: Don't Worry About the Vase
      url: https://thezvi.substack.com/feed
dedup_lookback_editions: 3
site:
  title: The Signal
  tagline: Your daily AI briefing — Hacker News, papers, models & newsletters
```

`tests/test_models.py`:
```python
from newsfeed.models import Item


def test_item_roundtrip():
    item = Item(
        id="hn-1", section="hackernews", title="T", url="https://x",
        score=42, score_label="42 points", author="a",
        published="2026-08-02T00:00:00+00:00", snippet="s",
        extra_link={"label": "HN", "url": "https://news.ycombinator.com/item?id=1"},
    )
    assert Item.from_dict(item.to_dict()) == item


def test_item_optional_fields_default():
    item = Item(id="x", section="papers", title="T", url="https://x")
    d = item.to_dict()
    assert d["score"] is None and d["extra_link"] is None
    assert d["snippet"] == "" and d["author"] == ""
```

`tests/test_config.py`:
```python
from newsfeed import config


def test_load_sources_yml():
    cfg = config.load()
    assert cfg["hackernews"]["min_points"] == 20
    assert len(cfg["newsletters"]["feeds"]) == 8
    assert cfg["dedup_lookback_editions"] == 3
```

- [ ] **Step 2: Run tests, verify they fail** — `pytest -q` → import errors.

- [ ] **Step 3: Implement**

`newsfeed/models.py`:
```python
from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class Item:
    id: str
    section: str
    title: str
    url: str
    score: int | None = None
    score_label: str = ""
    author: str = ""
    published: str = ""
    snippet: str = ""
    extra_link: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Item":
        return cls(**d)
```

`newsfeed/config.py`:
```python
from pathlib import Path

import yaml


def load(path: str | Path = "sources.yml") -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
```

`newsfeed/__init__.py` is empty.

- [ ] **Step 4: `pip install -r requirements.txt` (in a venv), `pytest -q` → all pass.**
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat: scaffolding, Item model, config loader"`

---

### Task 2: HTTP helper and keyword matcher

**Files:**
- Create: `newsfeed/http.py`, `newsfeed/keywords.py`, `tests/test_http.py`, `tests/test_keywords.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `http.get(url: str, params: dict | None = None) -> requests.Response` (raises on final failure; 30 s timeout, one retry, custom User-Agent).
- Produces: `keywords.matcher(keywords: list[str]) -> Callable[[str], bool]` — word-boundary, case-insensitive; a keyword ending in a non-alphanumeric char (e.g. `fine-tun`) is treated as a prefix.

- [ ] **Step 1: Write failing tests**

`tests/test_keywords.py`:
```python
from newsfeed.keywords import matcher

KW = ["AI", "LLM", "fine-tun", "machine learning"]


def test_matches_word_boundary():
    m = matcher(KW)
    assert m("New AI model released")
    assert m("Scaling LLMs is hard") is False or True  # see next test for exact rule
    assert not m("Airline stocks tumble")      # 'AI' must not match inside 'Airline'
    assert not m("Ferrari unveils new car")    # no keyword
    assert m("A machine learning approach")


def test_prefix_keywords():
    m = matcher(KW)
    assert m("Fine-tuning Llama at home")   # 'fine-tun' prefix
    assert m("fine-tuned models")


def test_case_insensitive():
    m = matcher(KW)
    assert m("ai is eating software")
```

Note: `LLM` with a word boundary does NOT match `LLMs`? It must. Rule: every keyword gets `\b` prefix; suffix `\b` only applies when the keyword's last char is alphanumeric AND we want whole-word... Decision: suffix boundary is `(?![a-z0-9-])` replaced by allowing plural `s`: append `(?:s|es)?\b`. So `LLM` matches `LLMs`, `agent` matches `agents`, `AI` does not match `Air` (`r` fails both `s?` and `\b`). Replace the ambiguous assertion above with `assert m("Scaling LLMs is hard")`.

`tests/test_http.py`:
```python
import requests

from newsfeed import http


def test_get_retries_once_then_succeeds(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None, headers=None):
        calls.append(url)
        if len(calls) == 1:
            raise requests.ConnectionError("boom")
        resp = requests.Response()
        resp.status_code = 200
        return resp

    monkeypatch.setattr(http.requests, "get", fake_get)
    resp = http.get("https://example.com")
    assert resp.status_code == 200
    assert len(calls) == 2


def test_get_raises_after_second_failure(monkeypatch):
    def fake_get(url, params=None, timeout=None, headers=None):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(http.requests, "get", fake_get)
    try:
        http.get("https://example.com")
        assert False, "should have raised"
    except requests.ConnectionError:
        pass
```

- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement**

`newsfeed/http.py`:
```python
import requests

TIMEOUT = 30
HEADERS = {"User-Agent": "personal-news-feed/1.0 (+https://github.com)"}


def get(url: str, params: dict | None = None) -> requests.Response:
    last_exc = None
    for _ in range(2):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT, headers=HEADERS)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_exc = exc
    raise last_exc
```

(Adjust the first test: fake response needs `raise_for_status` to no-op — a bare `requests.Response()` with `status_code=200` already does.)

`newsfeed/keywords.py`:
```python
import re
from typing import Callable


def matcher(keywords: list[str]) -> Callable[[str], bool]:
    parts = []
    for kw in keywords:
        esc = re.escape(kw)
        if kw and kw[-1].isalnum():
            parts.append(rf"\b{esc}(?:s|es)?\b")
        else:
            parts.append(rf"\b{esc}")
    pattern = re.compile("|".join(parts), re.IGNORECASE)
    return lambda text: bool(pattern.search(text))
```

- [ ] **Step 4: `pytest -q` → pass.**
- [ ] **Step 5: Commit** — `"feat: http helper with retry, keyword matcher"`

---

### Task 3: Hacker News fetcher

**Files:**
- Create: `newsfeed/fetchers/__init__.py`, `newsfeed/fetchers/hackernews.py`, `tests/test_hackernews.py`, `tests/fixtures/hn.json`

**Interfaces:**
- Consumes: `http.get`, `keywords.matcher`, `Item`.
- Produces: `hackernews.fetch(cfg: dict, now: datetime) -> list[Item]` — `cfg` is the full sources.yml dict; `now` is tz-aware UTC. Every fetcher in this project has this exact signature.
- Produces: `fetchers.FETCHERS: dict[str, Callable]` registry mapping section name → fetch fn (grows in later tasks).

- [ ] **Step 1: Record fixture**

```bash
curl -s "https://hn.algolia.com/api/v1/search_by_date?tags=story&numericFilters=points>=20&hitsPerPage=30" > tests/fixtures/hn.json
```

- [ ] **Step 2: Write failing test**

`tests/test_hackernews.py`:
```python
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from newsfeed import config
from newsfeed.fetchers import hackernews

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "hn.json").read_text())


@patch("newsfeed.fetchers.hackernews.http.get")
def test_fetch_filters_and_ranks(mock_get):
    mock_get.return_value = Mock(json=lambda: FIXTURE)
    cfg = config.load()
    items = hackernews.fetch(cfg, now=datetime.now(timezone.utc))

    assert len(items) <= cfg["hackernews"]["limit"]
    matches = hackernews_matcher = __import__("newsfeed.keywords", fromlist=["matcher"]).matcher(
        cfg["hackernews"]["keywords"])
    for item in items:
        assert item.section == "hackernews"
        assert item.score >= cfg["hackernews"]["min_points"]
        assert matches(item.title)
        assert item.extra_link["url"].startswith("https://news.ycombinator.com/item?id=")
    scores = [i.score for i in items]
    assert scores == sorted(scores, reverse=True)


@patch("newsfeed.fetchers.hackernews.http.get")
def test_ask_hn_without_url_links_to_hn(mock_get):
    hit = {"objectID": "1", "title": "Ask HN: best LLM?", "url": None,
           "points": 50, "author": "x", "created_at_i": 1754000000}
    mock_get.return_value = Mock(json=lambda: {"hits": [hit]})
    cfg = config.load()
    items = hackernews.fetch(cfg, now=datetime.now(timezone.utc))
    assert items[0].url == "https://news.ycombinator.com/item?id=1"
```

- [ ] **Step 3: Run, verify fail.**
- [ ] **Step 4: Implement**

`newsfeed/fetchers/hackernews.py`:
```python
from datetime import datetime, timedelta, timezone

from newsfeed import http
from newsfeed.keywords import matcher
from newsfeed.models import Item

API = "https://hn.algolia.com/api/v1/search_by_date"


def fetch(cfg: dict, now: datetime) -> list[Item]:
    c = cfg["hackernews"]
    since = int((now - timedelta(hours=c["window_hours"])).timestamp())
    resp = http.get(API, params={
        "tags": "story",
        "numericFilters": f"created_at_i>{since},points>={c['min_points']}",
        "hitsPerPage": 1000,
    })
    match = matcher(c["keywords"])
    items = []
    for hit in resp.json()["hits"]:
        title = hit.get("title") or ""
        if not match(title):
            continue
        hn_url = f"https://news.ycombinator.com/item?id={hit['objectID']}"
        published = datetime.fromtimestamp(hit["created_at_i"], tz=timezone.utc)
        items.append(Item(
            id=f"hn-{hit['objectID']}",
            section="hackernews",
            title=title,
            url=hit.get("url") or hn_url,
            score=hit.get("points", 0),
            score_label=f"{hit.get('points', 0)} points",
            author=hit.get("author", ""),
            published=published.isoformat(),
            extra_link={"label": "HN discussion", "url": hn_url},
        ))
    items.sort(key=lambda i: i.score, reverse=True)
    return items[: c["limit"]]
```

`newsfeed/fetchers/__init__.py`:
```python
from newsfeed.fetchers import hackernews

FETCHERS = {
    "hackernews": hackernews.fetch,
}
```

- [ ] **Step 5: `pytest -q` → pass. Commit** — `"feat: hacker news fetcher"`

---

### Task 4: Papers fetcher (HF Daily Papers + arXiv)

**Files:**
- Create: `newsfeed/fetchers/papers.py`, `tests/test_papers.py`, `tests/fixtures/hf_papers.json`, `tests/fixtures/arxiv.xml`
- Modify: `newsfeed/fetchers/__init__.py` (register `"papers": papers.fetch`)

**Interfaces:**
- Consumes: `http.get`, `Item`.
- Produces: `papers.fetch(cfg, now) -> list[Item]` — HF papers ranked by upvotes first (limit `hf_limit`), then fresh arXiv papers (limit `arxiv_limit`) not already present, deduped by arXiv ID. Item ids are `paper-<arxiv_id>` (no version suffix) for both branches so cross-edition dedup works.

- [ ] **Step 1: Record fixtures**

```bash
curl -s "https://huggingface.co/api/daily_papers?limit=30" > tests/fixtures/hf_papers.json
curl -s "http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results=25" > tests/fixtures/arxiv.xml
```

- [ ] **Step 2: Write failing test**

`tests/test_papers.py`:
```python
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from newsfeed import config
from newsfeed.fetchers import papers

FIX = Path(__file__).parent / "fixtures"


def fake_get(url, params=None):
    if "daily_papers" in url:
        return Mock(json=lambda: json.loads((FIX / "hf_papers.json").read_text()))
    return Mock(text=(FIX / "arxiv.xml").read_text())


@patch("newsfeed.fetchers.papers.http.get", side_effect=fake_get)
def test_fetch_merges_and_dedupes(mock_get):
    cfg = config.load()
    items = papers.fetch(cfg, now=datetime.now(timezone.utc))

    ids = [i.id for i in items]
    assert len(ids) == len(set(ids)), "no duplicate arxiv ids"
    assert len(items) <= cfg["papers"]["hf_limit"] + cfg["papers"]["arxiv_limit"]
    hf_items = [i for i in items if i.score is not None]
    scores = [i.score for i in hf_items]
    assert scores == sorted(scores, reverse=True)
    for i in items:
        assert i.section == "papers"
        assert i.id.startswith("paper-")


@patch("newsfeed.fetchers.papers.http.get", side_effect=fake_get)
def test_arxiv_items_have_no_score(mock_get):
    cfg = config.load()
    items = papers.fetch(cfg, now=datetime.now(timezone.utc))
    arxiv_only = [i for i in items if i.score is None]
    assert all(i.score_label == "new on arXiv" for i in arxiv_only)
```

- [ ] **Step 3: Run, verify fail.**
- [ ] **Step 4: Implement**

`newsfeed/fetchers/papers.py`:
```python
import re
from datetime import datetime

import feedparser

from newsfeed import http
from newsfeed.models import Item

HF_API = "https://huggingface.co/api/daily_papers"
ARXIV_API = "http://export.arxiv.org/api/query"


def _strip_version(arxiv_id: str) -> str:
    return re.sub(r"v\d+$", "", arxiv_id)


def _truncate(text: str, n: int = 220) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def fetch(cfg: dict, now: datetime) -> list[Item]:
    c = cfg["papers"]
    items: list[Item] = []
    seen: set[str] = set()

    resp = http.get(HF_API, params={"limit": 50})
    hf_entries = resp.json()
    hf_items = []
    for entry in hf_entries:
        paper = entry.get("paper") or {}
        pid = _strip_version(paper.get("id") or "")
        if not pid or pid in seen:
            continue
        seen.add(pid)
        authors = [a.get("name", "") for a in (paper.get("authors") or [])]
        hf_items.append(Item(
            id=f"paper-{pid}",
            section="papers",
            title=paper.get("title") or "",
            url=f"https://huggingface.co/papers/{pid}",
            score=paper.get("upvotes", 0),
            score_label=f"{paper.get('upvotes', 0)} upvotes",
            author=", ".join(a for a in authors[:3] if a) + (" et al." if len(authors) > 3 else ""),
            published=entry.get("publishedAt") or "",
            snippet=_truncate(paper.get("summary") or ""),
            extra_link={"label": "arXiv", "url": f"https://arxiv.org/abs/{pid}"},
        ))
    hf_items.sort(key=lambda i: i.score, reverse=True)
    items.extend(hf_items[: c["hf_limit"]])

    query = " OR ".join(f"cat:{cat}" for cat in c["arxiv_categories"])
    resp = http.get(ARXIV_API, params={
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": 40,
    })
    feed = feedparser.parse(resp.text)
    arxiv_items = []
    for entry in feed.entries:
        pid = _strip_version(entry.id.rsplit("/abs/", 1)[-1])
        if pid in seen:
            continue
        seen.add(pid)
        arxiv_items.append(Item(
            id=f"paper-{pid}",
            section="papers",
            title=" ".join(entry.title.split()),
            url=f"https://arxiv.org/abs/{pid}",
            score=None,
            score_label="new on arXiv",
            author=", ".join(a.name for a in entry.authors[:3])
                   + (" et al." if len(entry.authors) > 3 else ""),
            published=entry.get("published", ""),
            snippet=_truncate(entry.get("summary", "")),
        ))
    items.extend(arxiv_items[: c["arxiv_limit"]])
    return items
```

Register in `newsfeed/fetchers/__init__.py`:
```python
from newsfeed.fetchers import hackernews, papers

FETCHERS = {
    "hackernews": hackernews.fetch,
    "papers": papers.fetch,
}
```

- [ ] **Step 5: `pytest -q` → pass. Commit** — `"feat: papers fetcher (HF daily papers + arXiv)"`

---

### Task 5: Trending models fetcher

**Files:**
- Create: `newsfeed/fetchers/models_hub.py`, `tests/test_models_hub.py`, `tests/fixtures/hf_models.json`
- Modify: `newsfeed/fetchers/__init__.py` (register `"models": models_hub.fetch`)

**Interfaces:**
- Consumes: `http.get`, `Item`.
- Produces: `models_hub.fetch(cfg, now) -> list[Item]` — id `model-<modelId>`, score = likes, snippet = pipeline tag + library.

- [ ] **Step 1: Record fixture**

```bash
curl -s "https://huggingface.co/api/models?sort=trendingScore&limit=15" > tests/fixtures/hf_models.json
```

- [ ] **Step 2: Write failing test**

`tests/test_models_hub.py`:
```python
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from newsfeed import config
from newsfeed.fetchers import models_hub

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "hf_models.json").read_text())


@patch("newsfeed.fetchers.models_hub.http.get")
def test_fetch_trending_models(mock_get):
    mock_get.return_value = Mock(json=lambda: FIXTURE)
    cfg = config.load()
    items = models_hub.fetch(cfg, now=datetime.now(timezone.utc))

    assert 0 < len(items) <= cfg["models"]["limit"]
    for item in items:
        assert item.section == "models"
        assert item.id.startswith("model-")
        assert item.url.startswith("https://huggingface.co/")
        assert "likes" in item.score_label
```

- [ ] **Step 3: Run, verify fail.**
- [ ] **Step 4: Implement**

`newsfeed/fetchers/models_hub.py`:
```python
from datetime import datetime

from newsfeed import http
from newsfeed.models import Item

API = "https://huggingface.co/api/models"


def fetch(cfg: dict, now: datetime) -> list[Item]:
    c = cfg["models"]
    resp = http.get(API, params={"sort": "trendingScore", "limit": c["limit"]})
    items = []
    for m in resp.json():
        model_id = m.get("modelId") or m.get("id") or ""
        if not model_id:
            continue
        likes = m.get("likes", 0)
        downloads = m.get("downloads", 0)
        bits = [b for b in [m.get("pipeline_tag"), m.get("library_name")] if b]
        items.append(Item(
            id=f"model-{model_id}",
            section="models",
            title=model_id,
            url=f"https://huggingface.co/{model_id}",
            score=likes,
            score_label=f"{likes:,} likes · {downloads:,} downloads",
            author=model_id.split("/")[0],
            published=m.get("createdAt", ""),
            snippet=" · ".join(bits),
        ))
    return items[: c["limit"]]
```

Register `"models": models_hub.fetch` in the registry (same pattern as Task 4).

- [ ] **Step 5: `pytest -q` → pass. Commit** — `"feat: trending models fetcher"`

---

### Task 6: Newsletters fetcher

**Files:**
- Create: `newsfeed/fetchers/newsletters.py`, `tests/test_newsletters.py`, `tests/fixtures/substack.xml`
- Modify: `newsfeed/fetchers/__init__.py` (register `"newsletters": newsletters.fetch`)

**Interfaces:**
- Consumes: `http.get`, `Item`.
- Produces: `newsletters.fetch(cfg, now) -> list[Item]` — items from all feeds within `window_days`, newest first, capped at `limit`. One feed failing must not kill the others. Item id `nl-<link-url>`.

- [ ] **Step 1: Record fixture**

```bash
curl -sL -A "Mozilla/5.0" "https://www.interconnects.ai/feed" > tests/fixtures/substack.xml
```

- [ ] **Step 2: Write failing test**

`tests/test_newsletters.py`:
```python
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import feedparser

from newsfeed import config
from newsfeed.fetchers import newsletters

FIXTURE_TEXT = (Path(__file__).parent / "fixtures" / "substack.xml").read_text()


def _now_from_fixture():
    # anchor "now" just after the newest entry so the window test is deterministic
    feed = feedparser.parse(FIXTURE_TEXT)
    newest = max(datetime(*e.published_parsed[:6], tzinfo=timezone.utc) for e in feed.entries)
    return newest + timedelta(hours=1)


@patch("newsfeed.fetchers.newsletters.http.get")
def test_window_and_ordering(mock_get):
    mock_get.return_value = Mock(text=FIXTURE_TEXT)
    cfg = config.load()
    cfg["newsletters"]["feeds"] = [{"name": "Interconnects", "url": "https://x/feed"}]
    now = _now_from_fixture()
    items = newsletters.fetch(cfg, now=now)

    window = timedelta(days=cfg["newsletters"]["window_days"])
    for item in items:
        published = datetime.fromisoformat(item.published)
        assert now - published <= window
        assert item.author == "Interconnects"
        assert item.section == "newsletters"
    dates = [i.published for i in items]
    assert dates == sorted(dates, reverse=True)


@patch("newsfeed.fetchers.newsletters.http.get")
def test_one_bad_feed_does_not_kill_others(mock_get):
    def side_effect(url, params=None):
        if "bad" in url:
            raise RuntimeError("down")
        return Mock(text=FIXTURE_TEXT)

    mock_get.side_effect = side_effect
    cfg = config.load()
    cfg["newsletters"]["feeds"] = [
        {"name": "Bad", "url": "https://bad/feed"},
        {"name": "Interconnects", "url": "https://x/feed"},
    ]
    items = newsletters.fetch(cfg, now=_now_from_fixture())
    assert items, "good feed items survive a bad feed"
```

- [ ] **Step 3: Run, verify fail.**
- [ ] **Step 4: Implement**

`newsfeed/fetchers/newsletters.py`:
```python
import re
from datetime import datetime, timedelta, timezone

import feedparser

from newsfeed import http
from newsfeed.models import Item

TAG_RE = re.compile(r"<[^>]+>")


def _truncate(text: str, n: int = 220) -> str:
    text = " ".join(TAG_RE.sub(" ", text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def fetch(cfg: dict, now: datetime) -> list[Item]:
    c = cfg["newsletters"]
    window = timedelta(days=c["window_days"])
    items = []
    for feed_cfg in c["feeds"]:
        try:
            resp = http.get(feed_cfg["url"])
            feed = feedparser.parse(resp.text)
            for entry in feed.entries:
                parsed = entry.get("published_parsed") or entry.get("updated_parsed")
                if not parsed:
                    continue
                published = datetime(*parsed[:6], tzinfo=timezone.utc)
                if now - published > window:
                    continue
                link = entry.get("link", "")
                items.append(Item(
                    id=f"nl-{link}",
                    section="newsletters",
                    title=entry.get("title", ""),
                    url=link,
                    score=None,
                    score_label=feed_cfg["name"],
                    author=feed_cfg["name"],
                    published=published.isoformat(),
                    snippet=_truncate(entry.get("summary", "")),
                ))
        except Exception:
            continue
    items.sort(key=lambda i: i.published, reverse=True)
    return items[: c["limit"]]
```

Register `"newsletters": newsletters.fetch`.

- [ ] **Step 5: `pytest -q` → pass. Commit** — `"feat: newsletters fetcher"`

---

### Task 7: Cross-edition dedup + fetch orchestrator

**Files:**
- Create: `newsfeed/dedup.py`, `newsfeed/fetch.py`, `tests/test_dedup.py`, `tests/test_fetch.py`

**Interfaces:**
- Consumes: `FETCHERS` registry, `config.load`, `Item`.
- Produces: `dedup.recent_ids(data_dir: Path, before_date: str, lookback: int) -> set[str]` — item ids from up to `lookback` most recent edition files dated strictly before `before_date`.
- Produces: `fetch.run(date: str | None = None, data_dir="data", config_path="sources.yml") -> Path` — writes `data/<date>.json` with shape `{"date", "generated_at", "errors": [...], "sections": {name: [item dicts]}}`. Dedup applies only to sections `hackernews` and `papers`. Exits/raises `SystemExit(1)` if every section is empty and errors exist. `python -m newsfeed.fetch` entrypoint; default date = today in Asia/Kolkata.

- [ ] **Step 1: Write failing tests**

`tests/test_dedup.py`:
```python
import json

from newsfeed.dedup import recent_ids


def _write(dir, date, ids):
    (dir / f"{date}.json").write_text(json.dumps(
        {"date": date, "sections": {"hackernews": [{"id": i} for i in ids]}}))


def test_recent_ids_lookback(tmp_path):
    _write(tmp_path, "2026-07-30", ["a"])
    _write(tmp_path, "2026-07-31", ["b"])
    _write(tmp_path, "2026-08-01", ["c"])
    _write(tmp_path, "2026-08-02", ["d"])  # today: excluded

    ids = recent_ids(tmp_path, before_date="2026-08-02", lookback=2)
    assert ids == {"b", "c"}


def test_recent_ids_empty_dir(tmp_path):
    assert recent_ids(tmp_path, before_date="2026-08-02", lookback=3) == set()
```

`tests/test_fetch.py`:
```python
import json
from unittest.mock import patch

import pytest

from newsfeed.models import Item
from newsfeed import fetch


def _item(id, section, score=1):
    return Item(id=id, section=section, title=id, url="https://x", score=score)


def test_run_writes_edition_and_dedupes(tmp_path):
    fetchers = {
        "hackernews": lambda cfg, now: [_item("hn-1", "hackernews"), _item("hn-2", "hackernews")],
        "papers": lambda cfg, now: [_item("paper-1", "papers")],
    }
    # yesterday already had hn-1
    (tmp_path / "2026-08-01.json").write_text(json.dumps(
        {"date": "2026-08-01", "sections": {"hackernews": [{"id": "hn-1"}]}}))

    with patch.object(fetch, "FETCHERS", fetchers):
        out = fetch.run(date="2026-08-02", data_dir=tmp_path)

    day = json.loads(out.read_text())
    ids = [i["id"] for i in day["sections"]["hackernews"]]
    assert ids == ["hn-2"], "hn-1 deduped against yesterday"
    assert day["sections"]["papers"][0]["id"] == "paper-1"
    assert day["errors"] == []


def test_run_records_source_errors(tmp_path):
    def boom(cfg, now):
        raise RuntimeError("api down")

    fetchers = {"hackernews": boom,
                "papers": lambda cfg, now: [_item("paper-1", "papers")]}
    with patch.object(fetch, "FETCHERS", fetchers):
        out = fetch.run(date="2026-08-02", data_dir=tmp_path)
    day = json.loads(out.read_text())
    assert day["sections"]["hackernews"] == []
    assert "hackernews" in day["errors"]


def test_run_fails_when_everything_fails(tmp_path):
    def boom(cfg, now):
        raise RuntimeError("down")

    with patch.object(fetch, "FETCHERS", {"hackernews": boom, "papers": boom}):
        with pytest.raises(SystemExit):
            fetch.run(date="2026-08-02", data_dir=tmp_path)
```

- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement**

`newsfeed/dedup.py`:
```python
import json
from pathlib import Path


def recent_ids(data_dir: Path, before_date: str, lookback: int) -> set[str]:
    files = sorted(
        (p for p in Path(data_dir).glob("*.json") if p.stem < before_date),
        reverse=True,
    )[:lookback]
    ids: set[str] = set()
    for path in files:
        day = json.loads(path.read_text())
        for section_items in day.get("sections", {}).values():
            ids.update(item["id"] for item in section_items)
    return ids
```

`newsfeed/fetch.py`:
```python
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from newsfeed import config
from newsfeed.dedup import recent_ids
from newsfeed.fetchers import FETCHERS

DEDUP_SECTIONS = {"hackernews", "papers"}


def run(date: str | None = None, data_dir: str | Path = "data",
        config_path: str = "sources.yml") -> Path:
    cfg = config.load(config_path)
    now = datetime.now(timezone.utc)
    if date is None:
        date = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")

    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    seen = recent_ids(data_dir, before_date=date,
                      lookback=cfg.get("dedup_lookback_editions", 3))

    sections: dict[str, list[dict]] = {}
    errors: list[str] = []
    for name, fetcher in FETCHERS.items():
        try:
            items = fetcher(cfg, now)
        except Exception as exc:
            print(f"[fetch] {name} failed: {exc}", file=sys.stderr)
            sections[name] = []
            errors.append(name)
            continue
        if name in DEDUP_SECTIONS:
            items = [i for i in items if i.id not in seen]
        sections[name] = [i.to_dict() for i in items]

    if errors and not any(sections.values()):
        print("[fetch] all sources failed — refusing to publish empty edition",
              file=sys.stderr)
        raise SystemExit(1)

    out = data_dir / f"{date}.json"
    out.write_text(json.dumps({
        "date": date,
        "generated_at": now.isoformat(),
        "errors": errors,
        "sections": sections,
    }, indent=2, ensure_ascii=False))
    print(f"[fetch] wrote {out}")
    return out


if __name__ == "__main__":
    run(date=sys.argv[1] if len(sys.argv) > 1 else None)
```

- [ ] **Step 4: `pytest -q` → pass.**
- [ ] **Step 5: Live smoke test** — `python -m newsfeed.fetch` → inspect `data/<today>.json` has items in all 4 sections; keep the file (first real edition).
- [ ] **Step 6: Commit** — `"feat: fetch orchestrator with cross-edition dedup"`

---

### Task 8: Site builder (templates, CSS, theme toggle)

**Files:**
- Create: `newsfeed/build.py`, `templates/base.html`, `templates/edition.html`, `templates/archive.html`, `static/style.css`, `static/theme.js`, `tests/test_build.py`

**Interfaces:**
- Consumes: `data/*.json` day-files (shape from Task 7), `config.load` (site title/tagline).
- Produces: `build.run(data_dir="data", out_dir="site", config_path="sources.yml") -> Path` — renders `site/index.html` (latest edition), `site/editions/<date>/index.html` for every day-file, `site/archive/index.html`, copies `static/` → `site/static/`, writes `site/.nojekyll`. Templates receive: `site` (dict), `day` (edition dict), `base` (`""` for root page, `"../../"` for edition pages, `"../"` for archive), `prev_date`/`next_date` (str|None), `section_meta` (ordered list of `(key, heading)` pairs: hackernews→"Hacker News · AI", papers→"Papers", models→"Trending Models", newsletters→"Newsletters").
- `python -m newsfeed.build` entrypoint.

- [ ] **Step 1: Write failing test**

`tests/test_build.py`:
```python
import json
from pathlib import Path

from newsfeed import build


DAY = {
    "date": "2026-08-02", "generated_at": "2026-08-02T02:00:00+00:00",
    "errors": ["models"],
    "sections": {
        "hackernews": [{"id": "hn-1", "section": "hackernews", "title": "Big AI Story",
                        "url": "https://ex.com/a", "score": 100, "score_label": "100 points",
                        "author": "pg", "published": "2026-08-02T00:00:00+00:00",
                        "snippet": "", "extra_link": {"label": "HN discussion",
                                                       "url": "https://news.ycombinator.com/item?id=1"}}],
        "papers": [], "models": [],
        "newsletters": [{"id": "nl-1", "section": "newsletters", "title": "Post",
                          "url": "https://ex.com/p", "score": None, "score_label": "Import AI",
                          "author": "Import AI", "published": "2026-08-01T00:00:00+00:00",
                          "snippet": "hello", "extra_link": None}],
    },
}


def _setup(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "2026-08-01.json").write_text(json.dumps({**DAY, "date": "2026-08-01"}))
    (data / "2026-08-02.json").write_text(json.dumps(DAY))
    return data, tmp_path / "site"


def test_build_outputs(tmp_path):
    data, site = _setup(tmp_path)
    build.run(data_dir=data, out_dir=site)

    root = (site / "index.html").read_text()
    assert "Big AI Story" in root
    assert "2026-08-02" in root
    assert (site / "editions" / "2026-08-02" / "index.html").exists()
    assert (site / "editions" / "2026-08-01" / "index.html").exists()
    assert (site / "archive" / "index.html").exists()
    assert (site / "static" / "style.css").exists()
    assert (site / ".nojekyll").exists()


def test_prev_next_navigation(tmp_path):
    data, site = _setup(tmp_path)
    build.run(data_dir=data, out_dir=site)
    latest = (site / "editions" / "2026-08-02" / "index.html").read_text()
    assert "2026-08-01" in latest          # prev link
    oldest = (site / "editions" / "2026-08-01" / "index.html").read_text()
    assert "2026-08-02" in oldest          # next link


def test_failed_source_note(tmp_path):
    data, site = _setup(tmp_path)
    build.run(data_dir=data, out_dir=site)
    root = (site / "index.html").read_text()
    assert "unavailable" in root.lower()   # models failed → note rendered
```

- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement builder**

`newsfeed/build.py`:
```python
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from newsfeed import config

SECTION_META = [
    ("hackernews", "Hacker News · AI"),
    ("papers", "Papers"),
    ("models", "Trending Models"),
    ("newsletters", "Newsletters"),
]

ROOT = Path(__file__).resolve().parent.parent


def _env() -> Environment:
    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html"]))
    env.filters["pretty_date"] = lambda d: datetime.strptime(d, "%Y-%m-%d").strftime("%A, %B %-d, %Y")
    return env


def run(data_dir: str | Path = "data", out_dir: str | Path = "site",
        config_path: str | Path = "sources.yml") -> Path:
    cfg = config.load(config_path)
    data_dir, out_dir = Path(data_dir), Path(out_dir)
    days = []
    for path in sorted(data_dir.glob("*.json")):
        days.append(json.loads(path.read_text()))
    if not days:
        raise SystemExit("no data files to build")

    env = _env()
    edition_tpl = env.get_template("edition.html")
    archive_tpl = env.get_template("archive.html")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    shutil.copytree(ROOT / "static", out_dir / "static")
    (out_dir / ".nojekyll").write_text("")

    site = cfg["site"]
    for idx, day in enumerate(days):
        prev_date = days[idx - 1]["date"] if idx > 0 else None
        next_date = days[idx + 1]["date"] if idx < len(days) - 1 else None
        ctx = dict(site=site, day=day, section_meta=SECTION_META,
                   prev_date=prev_date, next_date=next_date)
        page_dir = out_dir / "editions" / day["date"]
        page_dir.mkdir(parents=True)
        (page_dir / "index.html").write_text(
            edition_tpl.render(**ctx, base="../../", is_root=False))

    latest = days[-1]
    (out_dir / "index.html").write_text(edition_tpl.render(
        site=site, day=latest, section_meta=SECTION_META,
        prev_date=days[-2]["date"] if len(days) > 1 else None,
        next_date=None, base="", is_root=True))

    archive_dir = out_dir / "archive"
    archive_dir.mkdir()
    (archive_dir / "index.html").write_text(archive_tpl.render(
        site=site, days=list(reversed(days)), base="../"))

    print(f"[build] rendered {len(days)} editions → {out_dir}")
    return out_dir


if __name__ == "__main__":
    run(*(sys.argv[1:]))
```

- [ ] **Step 4: Write templates**

`templates/base.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}{{ site.title }}{% endblock %}</title>
<link rel="stylesheet" href="{{ base }}static/style.css">
<script src="{{ base }}static/theme.js" defer></script>
</head>
<body>
<header class="masthead">
  <div class="masthead-inner">
    <a class="brand" href="{{ base }}index.html">{{ site.title }}</a>
    <p class="tagline">{{ site.tagline }}</p>
    <nav class="topnav">
      <a href="{{ base }}archive/index.html">Archive</a>
      <button id="theme-toggle" aria-label="Toggle theme">◐</button>
    </nav>
  </div>
</header>
<main>{% block content %}{% endblock %}</main>
<footer>
  <p>Generated automatically · <a href="{{ base }}archive/index.html">All editions</a></p>
</footer>
</body>
</html>
```

`templates/edition.html`:
```html
{% extends "base.html" %}
{% block title %}{{ site.title }} — {{ day.date }}{% endblock %}
{% block content %}
<div class="edition-head">
  <h1>{{ day.date | pretty_date }}</h1>
  <nav class="edition-nav">
    {% if prev_date %}<a href="{{ base }}editions/{{ prev_date }}/index.html">← {{ prev_date }}</a>{% endif %}
    {% if next_date %}<a href="{{ base }}editions/{{ next_date }}/index.html">{{ next_date }} →</a>{% endif %}
  </nav>
</div>
{% for key, heading in section_meta %}
<section class="feed-section">
  <h2>{{ heading }}</h2>
  {% if key in day.errors %}
    <p class="note">This source was unavailable today.</p>
  {% elif not day.sections.get(key) %}
    <p class="note">Nothing new today.</p>
  {% else %}
  <ol class="items">
    {% for item in day.sections[key] %}
    <li class="item">
      <a class="item-title" href="{{ item.url }}">{{ item.title }}</a>
      <div class="item-meta">
        {% if item.score_label %}<span class="score">{{ item.score_label }}</span>{% endif %}
        {% if item.author and item.author != item.score_label %}<span>{{ item.author }}</span>{% endif %}
        {% if item.extra_link %}<a href="{{ item.extra_link.url }}">{{ item.extra_link.label }}</a>{% endif %}
      </div>
      {% if item.snippet %}<p class="snippet">{{ item.snippet }}</p>{% endif %}
    </li>
    {% endfor %}
  </ol>
  {% endif %}
</section>
{% endfor %}
{% endblock %}
```

`templates/archive.html`:
```html
{% extends "base.html" %}
{% block title %}{{ site.title }} — Archive{% endblock %}
{% block content %}
<h1>Archive</h1>
<ol class="items archive-list">
  {% for day in days %}
  <li><a href="{{ base }}editions/{{ day.date }}/index.html">{{ day.date | pretty_date }}</a>
      <span class="item-meta">{{ day.sections.values() | map('length') | sum }} items</span></li>
  {% endfor %}
</ol>
{% endblock %}
```

`static/theme.js`:
```javascript
const KEY = "news-theme";
const root = document.documentElement;
const saved = localStorage.getItem(KEY);
if (saved) root.dataset.theme = saved;
document.getElementById("theme-toggle").addEventListener("click", () => {
  const dark = root.dataset.theme === "dark" ||
    (!root.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
  root.dataset.theme = dark ? "light" : "dark";
  localStorage.setItem(KEY, root.dataset.theme);
});
```

`static/style.css` — newspaper style, CSS variables for both themes (light default, `@media (prefers-color-scheme: dark)` + `[data-theme]` overrides), serif masthead, max-width 760px column, item list with score badges. (~120 lines; written at implementation time following this structure — variables `--bg --fg --muted --accent --rule`, sections separated by double rule under masthead, `.note` italic muted.)

- [ ] **Step 5: `pytest -q` → pass.**
- [ ] **Step 6: Visual check** — `python -m newsfeed.build`, serve `site/` locally, verify with browser (both themes, edition nav, archive, mobile width).
- [ ] **Step 7: Commit** — `"feat: static site builder with newspaper theme"`

---

### Task 9: GitHub Actions workflow + README

**Files:**
- Create: `.github/workflows/daily.yml`, `README.md`

**Interfaces:**
- Consumes: `python -m newsfeed.fetch`, `python -m newsfeed.build`, tests.
- Produces: daily publishing pipeline on GitHub Pages.

- [ ] **Step 1: Write workflow**

`.github/workflows/daily.yml`:
```yaml
name: Daily edition

on:
  schedule:
    - cron: "30 1 * * *"   # 07:00 IST
  workflow_dispatch:

permissions:
  contents: write
  pages: write
  id-token: write

concurrency:
  group: daily
  cancel-in-progress: false

jobs:
  publish:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -r requirements.txt
      - run: pytest -q
      - run: python -m newsfeed.fetch
      - name: Commit edition data
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/
          git diff --cached --quiet || git commit -m "data: edition $(date +%F)"
          git push
      - run: python -m newsfeed.build
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site/
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Write README** — what the site is, the four sections, how to add/remove newsletters in `sources.yml`, local dev commands (`pip install -r requirements.txt`, `pytest`, `python -m newsfeed.fetch`, `python -m newsfeed.build`, `python -m http.server -d site`), credit the two inspiration projects.
- [ ] **Step 3: Commit** — `"feat: daily publish workflow + README"`

---

### Task 10: Deploy to GitHub Pages

**Files:** none new (operations task).

- [ ] **Step 1:** Check `gh auth status`. If authenticated, create repo + push:
  `gh repo create personal-news-feed --public --source . --push`.
  If not authenticated, use the browser (user is logged into GitHub in Brave) to create the repo, then push via HTTPS.
- [ ] **Step 2:** Enable Pages with source "GitHub Actions" (via `gh api repos/{owner}/personal-news-feed/pages -X POST -f build_type=workflow` or browser Settings → Pages).
- [ ] **Step 3:** Trigger the workflow (`gh workflow run daily.yml` or Actions tab → Run workflow). Watch to completion.
- [ ] **Step 4:** Verify the live URL renders today's edition; check theme toggle and archive.
- [ ] **Step 5:** Confirm the data commit landed; `git pull` locally.

---

## Self-Review Notes

- **Spec coverage:** daily editions+archive (T8), score ranking (T3–T5), sources table (T3–T6), sources.yml tunables (T1), dedup (T7), error isolation (T6, T7, T8 note rendering), all-fail abort (T7), cron+dispatch+Pages (T9–T10), newspaper theme dark/light (T8). Spec's `scripts/fetch.py` / `scripts/build.py` became `python -m newsfeed.fetch` / `python -m newsfeed.build` — same responsibility, package layout is cleaner for testing.
- **Type consistency:** all fetchers share `fetch(cfg: dict, now: datetime) -> list[Item]`; day-file shape defined once in T7 and consumed in T8.
- **Placeholder scan:** `style.css` body is deliberately deferred to implementation with its structure specified (variables, themes, layout) — visual code, verified by the T8 visual check.
