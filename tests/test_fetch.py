import json
from unittest.mock import patch

import pytest

from newsfeed import fetch
from newsfeed.models import Item


def _item(id, section, score=1):
    return Item(id=id, section=section, title=id, url="https://x", score=score)


def test_run_writes_edition_and_dedupes(tmp_path):
    fetchers = {
        "hackernews": lambda cfg, now: [_item("hn-1", "hackernews"),
                                        _item("hn-2", "hackernews")],
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
