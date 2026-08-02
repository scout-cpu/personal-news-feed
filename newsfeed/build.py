import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from newsfeed import config

SECTION_META = [
    ("hackernews", "Hacker News · AI"),
    ("papers", "Papers"),
    ("models", "Trending Models"),
    ("newsletters", "Newsletters"),
]

ROOT = Path(__file__).resolve().parent.parent


def _env() -> Environment:
    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html"]))
    env.filters["pretty_date"] = (
        lambda d: datetime.strptime(d, "%Y-%m-%d").strftime("%A, %B %-d, %Y"))
    return env


def run(data_dir: str | Path = "data", out_dir: str | Path = "site",
        config_path: str | Path = "sources.yml") -> Path:
    cfg = config.load(config_path)
    data_dir, out_dir = Path(data_dir), Path(out_dir)
    days = [json.loads(p.read_text()) for p in sorted(data_dir.glob("*.json"))]
    if not days:
        raise SystemExit("no data files to build")

    env = _env()
    edition_tpl = env.get_template("edition.html")
    archive_tpl = env.get_template("archive.html")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    shutil.copytree(ROOT / "static", out_dir / "static")
    (out_dir / ".nojekyll").write_text("")

    site = cfg["site"]
    for idx, day in enumerate(days):
        prev_date = days[idx - 1]["date"] if idx > 0 else None
        next_date = days[idx + 1]["date"] if idx < len(days) - 1 else None
        page_dir = out_dir / "editions" / day["date"]
        page_dir.mkdir(parents=True)
        (page_dir / "index.html").write_text(edition_tpl.render(
            site=site, day=day, section_meta=SECTION_META,
            prev_date=prev_date, next_date=next_date,
            base="../../", is_root=False))

    latest = days[-1]
    (out_dir / "index.html").write_text(edition_tpl.render(
        site=site, day=latest, section_meta=SECTION_META,
        prev_date=days[-2]["date"] if len(days) > 1 else None,
        next_date=None, base="", is_root=True))

    archive_dir = out_dir / "archive"
    archive_dir.mkdir()
    (archive_dir / "index.html").write_text(archive_tpl.render(
        site=site, days=list(reversed(days)), base="../"))

    print(f"[build] rendered {len(days)} editions -> {out_dir}")
    return out_dir


if __name__ == "__main__":
    run(*(sys.argv[1:]))
