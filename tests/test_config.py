from newsfeed import config


def test_load_sources_yml():
    cfg = config.load()
    assert cfg["hackernews"]["min_points"] == 20
    assert len(cfg["newsletters"]["feeds"]) == 8
    assert cfg["dedup_lookback_editions"] == 3
