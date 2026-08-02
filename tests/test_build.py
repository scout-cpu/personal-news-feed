import json

from newsfeed import build

DAY = {
    "date": "2026-08-02", "generated_at": "2026-08-02T02:00:00+00:00",
    "errors": ["models"],
    "sections": {
        "hackernews": [{"id": "hn-1", "section": "hackernews", "title": "Big AI Story",
                        "url": "https://ex.com/a", "score": 100,
                        "score_label": "100 points", "author": "pg",
                        "published": "2026-08-02T00:00:00+00:00", "snippet": "",
                        "extra_link": {"label": "HN discussion",
                                       "url": "https://news.ycombinator.com/item?id=1"}}],
        "papers": [], "models": [],
        "newsletters": [{"id": "nl-1", "section": "newsletters", "title": "Post",
                         "url": "https://ex.com/p", "score": None,
                         "score_label": "Import AI", "author": "Import AI",
                         "published": "2026-08-01T00:00:00+00:00",
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
