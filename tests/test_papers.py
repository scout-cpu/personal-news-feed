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

    assert items
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
    assert arxiv_only, "fixture should yield fresh arXiv items"
    assert all(i.score_label == "new on arXiv" for i in arxiv_only)
