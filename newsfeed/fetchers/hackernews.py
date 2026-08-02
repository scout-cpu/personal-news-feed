from datetime import datetime, timedelta, timezone

from newsfeed import http
from newsfeed.keywords import matcher
from newsfeed.models import Item

API = "https://hn.algolia.com/api/v1/search_by_date"


def fetch(cfg: dict, now: datetime) -> list[Item]:
    c = cfg["hackernews"]
    since = int((now - timedelta(hours=c["window_hours"])).timestamp())
    resp = http.get(API, params={
        "tags": "story",
        "numericFilters": f"created_at_i>{since},points>={c['min_points']}",
        "hitsPerPage": 1000,
    })
    match = matcher(c["keywords"])
    items = []
    for hit in resp.json()["hits"]:
        title = hit.get("title") or ""
        if not match(title):
            continue
        hn_url = f"https://news.ycombinator.com/item?id={hit['objectID']}"
        published = datetime.fromtimestamp(hit["created_at_i"], tz=timezone.utc)
        items.append(Item(
            id=f"hn-{hit['objectID']}",
            section="hackernews",
            title=title,
            url=hit.get("url") or hn_url,
            score=hit.get("points", 0),
            score_label=f"{hit.get('points', 0)} points",
            author=hit.get("author", ""),
            published=published.isoformat(),
            extra_link={"label": "HN discussion", "url": hn_url},
        ))
    items.sort(key=lambda i: i.score, reverse=True)
    return items[: c["limit"]]
