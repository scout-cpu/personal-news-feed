import requests

from newsfeed import http


def test_get_retries_once_then_succeeds(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None, headers=None):
        calls.append(url)
        if len(calls) == 1:
            raise requests.ConnectionError("boom")
        resp = requests.Response()
        resp.status_code = 200
        return resp

    monkeypatch.setattr(http.requests, "get", fake_get)
    resp = http.get("https://example.com")
    assert resp.status_code == 200
    assert len(calls) == 2


def test_get_raises_after_second_failure(monkeypatch):
    def fake_get(url, params=None, timeout=None, headers=None):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(http.requests, "get", fake_get)
    try:
        http.get("https://example.com")
        assert False, "should have raised"
    except requests.ConnectionError:
        pass
