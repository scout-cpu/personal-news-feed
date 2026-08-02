import re
from datetime import datetime

import feedparser

from newsfeed import http
from newsfeed.models import Item

HF_API = "https://huggingface.co/api/daily_papers"
ARXIV_API = "https://export.arxiv.org/api/query"


def _strip_version(arxiv_id: str) -> str:
    return re.sub(r"v\d+$", "", arxiv_id)


def _truncate(text: str, n: int = 220) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _authors_label(names: list[str]) -> str:
    label = ", ".join(n for n in names[:3] if n)
    return label + (" et al." if len(names) > 3 else "")


def fetch(cfg: dict, now: datetime) -> list[Item]:
    c = cfg["papers"]
    items: list[Item] = []
    seen: set[str] = set()

    resp = http.get(HF_API, params={"limit": 50})
    hf_items = []
    for entry in resp.json():
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
            author=_authors_label(authors),
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
            author=_authors_label([a.name for a in entry.authors]),
            published=entry.get("published", ""),
            snippet=_truncate(entry.get("summary", "")),
        ))
    items.extend(arxiv_items[: c["arxiv_limit"]])
    return items
