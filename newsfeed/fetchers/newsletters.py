import re
import sys
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
        except Exception as exc:
            print(f"[newsletters] {feed_cfg['name']} failed: {exc}", file=sys.stderr)
            continue
    items.sort(key=lambda i: i.published, reverse=True)
    return items[: c["limit"]]
