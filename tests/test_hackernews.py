import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from newsfeed import config
from newsfeed.fetchers import hackernews
from newsfeed.keywords import matcher

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "hn.json").read_text())


@patch("newsfeed.fetchers.hackernews.http.get")
def test_fetch_filters_and_ranks(mock_get):
    mock_get.return_value = Mock(json=lambda: FIXTURE)
    cfg = config.load()
    items = hackernews.fetch(cfg, now=datetime.now(timezone.utc))

    assert items, "fixture should contain at least one AI story"
    assert len(items) <= cfg["hackernews"]["limit"]
    match = matcher(cfg["hackernews"]["keywords"])
    for item in items:
        assert item.section == "hackernews"
        assert item.score >= cfg["hackernews"]["min_points"]
        assert match(item.title)
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
