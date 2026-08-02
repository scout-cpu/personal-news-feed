import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from newsfeed import config
from newsfeed.dedup import recent_ids
from newsfeed.fetchers import FETCHERS

DEDUP_SECTIONS = {"hackernews", "papers"}


def run(date: str | None = None, data_dir: str | Path = "data",
        config_path: str = "sources.yml") -> Path:
    cfg = config.load(config_path)
    now = datetime.now(timezone.utc)
    if date is None:
        date = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")

    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    seen = recent_ids(data_dir, before_date=date,
                      lookback=cfg.get("dedup_lookback_editions", 3))

    sections: dict[str, list[dict]] = {}
    errors: list[str] = []
    for name, fetcher in FETCHERS.items():
        try:
            items = fetcher(cfg, now)
        except Exception as exc:
            print(f"[fetch] {name} failed: {exc}", file=sys.stderr)
            sections[name] = []
            errors.append(name)
            continue
        if name in DEDUP_SECTIONS:
            items = [i for i in items if i.id not in seen]
        sections[name] = [i.to_dict() for i in items]
        print(f"[fetch] {name}: {len(sections[name])} items")

    if errors and not any(sections.values()):
        print("[fetch] all sources failed — refusing to publish empty edition",
              file=sys.stderr)
        raise SystemExit(1)

    out = data_dir / f"{date}.json"
    out.write_text(json.dumps({
        "date": date,
        "generated_at": now.isoformat(),
        "errors": errors,
        "sections": sections,
    }, indent=2, ensure_ascii=False))
    print(f"[fetch] wrote {out}")
    return out


if __name__ == "__main__":
    run(date=sys.argv[1] if len(sys.argv) > 1 else None)
