import json
from pathlib import Path


def recent_ids(data_dir: Path, before_date: str, lookback: int) -> set[str]:
    files = sorted(
        (p for p in Path(data_dir).glob("*.json") if p.stem < before_date),
        reverse=True,
    )[:lookback]
    ids: set[str] = set()
    for path in files:
        day = json.loads(path.read_text())
        for section_items in day.get("sections", {}).values():
            ids.update(item["id"] for item in section_items)
    return ids
