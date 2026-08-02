from datetime import datetime

from newsfeed import http
from newsfeed.models import Item

API = "https://huggingface.co/api/models"


def fetch(cfg: dict, now: datetime) -> list[Item]:
    c = cfg["models"]
    resp = http.get(API, params={"sort": "trendingScore", "limit": c["limit"]})
    items = []
    for m in resp.json():
        model_id = m.get("modelId") or m.get("id") or ""
        if not model_id:
            continue
        likes = m.get("likes", 0)
        downloads = m.get("downloads", 0)
        bits = [b for b in [m.get("pipeline_tag"), m.get("library_name")] if b]
        items.append(Item(
            id=f"model-{model_id}",
            section="models",
            title=model_id,
            url=f"https://huggingface.co/{model_id}",
            score=likes,
            score_label=f"{likes:,} likes · {downloads:,} downloads",
            author=model_id.split("/")[0],
            published=m.get("createdAt", ""),
            snippet=" · ".join(bits),
        ))
    return items[: c["limit"]]
