import json
from pathlib import Path
import pytest
from newsfeed import build, startups
from tests.test_build import _setup

ROW = '''<div><a href="./companies/acme"><img src="https://framerusercontent.com/logo.png">Acme &amp; Co</a><p>$12.5M · Series A</p><p>Sep 2, 2026</p><a href="./investors/example">Example Capital</a><a href="https://example.com/announcement">Source</a></div>'''

def test_funding_parser_deduplicates_responsive_variants():
    records = startups.parse('<main>' + ROW * 3 + '</main>')
    assert len(records) == 1
    assert records[0]['company'] == 'Acme & Co'
    assert records[0]['amount'] == '$12.5M'
    assert records[0]['round'] == 'Series A'
    assert records[0]['date'] == '2026-09-02'
    assert records[0]['company_url'] == 'https://startups.gallery/companies/acme'
    assert records[0]['source_url'] == 'https://example.com/announcement'

def test_parser_rejects_changed_or_empty_source():
    with pytest.raises(ValueError, match='No funding records'):
        startups.parse('<html><h1>Temporarily unavailable</h1></html>')
    # An unrelated company elsewhere on the page must not borrow a funding row.
    result = startups.parse('<main><a href="./companies/other">Other</a>' + ROW + '</main>')
    assert [item['company'] for item in result] == ['Acme & Co']

def test_failed_refresh_retains_snapshot(tmp_path, monkeypatch):
    destination = tmp_path / 'data/startups/latest.json'
    destination.parent.mkdir(parents=True)
    original = '{"items": []}'
    destination.write_text(original)
    html = tmp_path / 'bad.html'
    html.write_text('<h1>Outage</h1>')
    with pytest.raises(ValueError):
        startups.run(html_path=html, root=tmp_path)
    assert destination.read_text() == original

def test_startup_page_survives_clean_build_and_escapes_content(tmp_path):
    data, site = _setup(tmp_path)
    funding = data / 'startups/latest.json'
    funding.parent.mkdir()
    item = startups.parse(ROW)[0]
    item['company'] = '<script>alert(1)</script>'
    item.update(image='', description='')
    funding.write_text(json.dumps({'source':startups.URL,'fetched_at':'2026-09-05T00:00:00Z','items':[item]}))
    build.run(data_dir=data, out_dir=site)
    build.run(data_dir=data, out_dir=site)
    html = (site/'startups.html').read_text()
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html
    assert '<script>alert(1)</script>' not in html
    assert (site/'static/startups/timeline.js').exists()
    assert 'startups.html' in (site/'index.html').read_text()
    assert 'startups.html' in (site/'editions/2026-08-01/index.html').read_text()


def test_http_decodes_framer_utf8_without_header_charset(monkeypatch):
    import requests
    response = requests.Response()
    response.status_code = 200
    response.headers['Content-Type'] = 'text/html'
    response.encoding = 'ISO-8859-1'
    response._content = ROW.replace('Acme &amp; Co', 'Naïve').encode('utf-8')
    monkeypatch.setattr(startups.requests, 'get', lambda *args, **kwargs: response)
    records = startups.parse(startups.get(startups.URL).text)
    assert records[0]['company'] == 'Naïve'
    assert records[0]['amount'] == '$12.5M'
