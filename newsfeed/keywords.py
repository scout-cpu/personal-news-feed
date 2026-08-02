import re
from typing import Callable


def matcher(keywords: list[str]) -> Callable[[str], bool]:
    parts = []
    for kw in keywords:
        if kw.endswith("*"):
            # trailing * marks a prefix keyword (e.g. "fine-tun*" matches fine-tuning)
            parts.append(rf"\b{re.escape(kw[:-1])}")
        else:
            # whole word, allowing a plural suffix (LLM matches LLMs, not Airline)
            parts.append(rf"\b{re.escape(kw)}(?:s|es)?\b")
    pattern = re.compile("|".join(parts), re.IGNORECASE)
    return lambda text: bool(pattern.search(text))
