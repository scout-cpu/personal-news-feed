from pathlib import Path

import yaml


def load(path: str | Path = "sources.yml") -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
