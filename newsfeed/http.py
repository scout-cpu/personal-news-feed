import requests

TIMEOUT = 30
HEADERS = {"User-Agent": "personal-news-feed/1.0 (personal aggregator)"}


def get(url: str, params: dict | None = None) -> requests.Response:
    last_exc = None
    for _ in range(2):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT, headers=HEADERS)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_exc = exc
    raise last_exc
