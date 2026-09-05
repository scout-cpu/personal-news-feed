"""Fetch Startups Gallery's public funding table and cache its assets locally."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse

import requests

URL = 'https://startups.gallery/news'
ROOT = Path(__file__).resolve().parent.parent
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

class Node:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []
    def all(self, tag=None):
        for child in self.children:
            if isinstance(child, Node):
                if tag is None or child.tag == tag:
                    yield child
                yield from child.all(tag)
    def text(self):
        return ' '.join(c.text() if isinstance(c, Node) else c for c in self.children).strip()

class Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = self.current = Node()
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in VOID:
            self.current = node
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)
    def handle_endtag(self, tag):
        node = self.current
        while node.parent and node.tag != tag:
            node = node.parent
        if node.parent:
            self.current = node.parent
    def handle_data(self, value):
        if value.strip():
            self.current.children.append(value.strip())

def public_url(value, base=URL):
    url = urljoin(base, value)
    return url if urlparse(url).scheme == 'https' else ''

def parse(html):
    doc, result, seen = Document(html), [], set()
    for a in doc.root.all('a'):
        href = public_url(a.attrs.get('href', ''))
        if not href.startswith('https://startups.gallery/companies/'):
            continue
        row = a.parent
        # Find the smallest ancestor containing company, dated round and press.
        while row and row.parent:
            links = list(row.all('a'))
            date = re.search(r'\b([A-Z][a-z]{2} \d{1,2}, \d{4})\b', row.text())
            amount = re.search(r'(\$[\d.,]+[KMB]?)\s*·\s*(Pre-Seed|Seed|Series [A-Z]|Venture|Debt|Grant|Growth|Unknown)', row.text())
            press = next((x for x in links if x.text() == 'Source'), None)
            if date and amount and press:
                break
            row = row.parent
        else:
            continue
        # A whole-page ancestor is not a funding record.
        companies = {public_url(x.attrs.get('href','')) for x in links if '/companies/' in x.attrs.get('href','')}
        if len(companies) != 1:
            continue
        name = a.text()
        published = datetime.strptime(date[1], '%b %d, %Y').date().isoformat()
        key = (href, published, amount[0])
        if key in seen:
            continue
        seen.add(key)
        investor = next((x for x in links if '/investors/' in x.attrs.get('href','')), None)
        logo = next(a.all('img'), None)
        result.append({'id':hashlib.sha256('|'.join(key).encode()).hexdigest()[:16],
            'company':name, 'company_url':href, 'amount':amount[1], 'round':amount[2],
            'date':published, 'investor':investor.text() if investor else '',
            'investor_url':public_url(investor.attrs['href']) if investor else '',
            'source_url':public_url(press.attrs['href']),
            'logo_url':public_url(logo.attrs.get('src','')) if logo else ''})
    if not result:
        raise ValueError('No funding records found; retaining the previous snapshot')
    return sorted(result, key=lambda x:x['date'], reverse=True)

def get(url):
    response = requests.get(url, timeout=30, headers={'User-Agent':'TheSignal/1.0 (public startup funding feed)'})
    response.raise_for_status()
    if "text/html" in response.headers.get("Content-Type", ""):
        response.encoding = "utf-8"  # Framer declares UTF-8 in HTML, not always its HTTP header.
    return response

def cache_image(url, directory):
    if not url:
        return ''
    filename = hashlib.sha256(url.encode()).hexdigest()[:20]
    existing = list(directory.glob(filename + '.*'))
    if existing:
        return 'static/startups/images/' + existing[0].name
    response = get(url)
    kind = response.headers.get('Content-Type','').split(';')[0]
    extension = {'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/avif':'.avif'}.get(kind)
    if not extension or len(response.content) > 8_000_000:
        return ''
    path = directory / (filename + extension)
    path.write_bytes(response.content)
    return 'static/startups/images/' + path.name

def enrich(item, directory, previous):
    old = previous.get(item['id'], {})
    item.update({k:old[k] for k in ('image','image_url','description','image_kind') if k in old})
    try:
        item['logo'] = cache_image(item['logo_url'], directory)
        if not item.get('image') or item.get('image_kind') == 'logo':
            profile = Document(get(item['company_url']).text)
            metas = {n.attrs.get('property',n.attrs.get('name','')):n.attrs.get('content','') for n in profile.root.all('meta')}
            item['description'] = metas.get('description','')
            # Use the actual website screenshot displayed on the company profile.
            imgs = list(profile.root.all('img'))
            hero = next((n for n in imgs[:3] if str(n.attrs.get('width','')).isdigit() and str(n.attrs.get('height','')).isdigit() and int(n.attrs['width']) >= 600 and int(n.attrs['width']) > int(n.attrs['height']) * 1.3), None)
            image_url = public_url(hero.attrs.get('src','')) if hero else ''
            item['image'] = cache_image(image_url, directory)
            item['image_url'] = image_url
            item['image_kind'] = 'company artwork'
        if not item.get('image'):
            item.update(image=item.get('logo',''), image_url=item['logo_url'], image_kind='logo')
    except (requests.RequestException, ValueError) as exc:
        print(f"[startups] image unavailable for {item['company']}: {exc}")
        if not item.get('image'):
            item.update(image=item.get('logo',''), image_kind='logo')
    return item

def run(html_path=None, root=ROOT):
    destination = root / 'data/startups/latest.json'
    previous = json.loads(destination.read_text()) if destination.exists() else {'items':[]}
    items = parse(Path(html_path).read_text() if html_path else get(URL).text)
    directory = root / 'static/startups/images'
    directory.mkdir(parents=True, exist_ok=True)
    by_id = {item['id']:item for item in previous['items']}
    with ThreadPoolExecutor(max_workers=6) as pool:
        items = list(pool.map(lambda item:enrich(item,directory,by_id), items))
    snapshot = {'source':URL,'fetched_at':datetime.now(timezone.utc).isoformat(),'items':items}
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix('.tmp')
    temp.write_text(json.dumps(snapshot,indent=2,ensure_ascii=False)+'\n')
    temp.replace(destination)
    print(f'[startups] cached {len(items)} funding rounds')
    return snapshot

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', help='Import a saved funding page instead of fetching it')
    args = parser.parse_args()
    try:
        run(args.html)
    except (requests.RequestException, ValueError) as exc:
        if not (ROOT/'data/startups/latest.json').exists():
            raise
        print(f'[startups] refresh failed; keeping last successful snapshot: {exc}')
