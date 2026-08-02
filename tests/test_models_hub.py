import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from newsfeed import config
from newsfeed.fetchers import models_hub

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "hf_models.json").read_text())


@patch("newsfeed.fetchers.models_hub.http.get")
def test_fetch_trending_models(mock_get):
    mock_get.return_value = Mock(json=lambda: FIXTURE)
    cfg = config.load()
    items = models_hub.fetch(cfg, now=datetime.now(timezone.utc))

    assert 0 < len(items) <= cfg["models"]["limit"]
    for item in items:
        assert item.section == "models"
        assert item.id.startswith("model-")
        assert item.url.startswith("https://huggingface.co/")
        assert "likes" in item.score_label
