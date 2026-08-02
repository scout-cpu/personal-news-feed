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
