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
    newest = max(datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
                 for e in feed.entries)
    return newest + timedelta(hours=1)


@patch("newsfeed.fetchers.newsletters.http.get")
def test_window_and_ordering(mock_get):
    mock_get.return_value = Mock(text=FIXTURE_TEXT)
    cfg = config.load()
    cfg["newsletters"]["feeds"] = [{"name": "Interconnects", "url": "https://x/feed"}]
    now = _now_from_fixture()
    items = newsletters.fetch(cfg, now=now)

    assert items
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
