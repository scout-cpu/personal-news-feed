from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Item:
    id: str
    section: str
    title: str
    url: str
    score: int | None = None
    score_label: str = ""
    author: str = ""
    published: str = ""
    snippet: str = ""
    extra_link: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Item":
        return cls(**d)
