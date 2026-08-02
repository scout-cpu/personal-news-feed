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
