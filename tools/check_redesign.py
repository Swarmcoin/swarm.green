"""Read-only checks for the redesigned visitor journey; no network or transactions."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import sys

import redesign_shell

ROOT = Path(__file__).resolve().parent.parent
PAGES = ['index.html', 'downloads/index.html', 'roadmap/index.html', 'trade/index.html', 'waitlist/index.html', 'get-swm/index.html', 'join/index.html', 'brand/logo-v2/index.html', 'brand/mascot/index.html', 'brand/mascot/style-sheet/index.html', 'ecosystem/index.html', 'ecosystem/wallet/index.html', 'ecosystem/messenger/index.html', 'ecosystem/browser/index.html']


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.links, self.assets = [], [], []
        self.headings = 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.append(a['id'])
        if tag == 'h1':
            self.headings += 1
        if tag == 'a' and a.get('href'):
            self.links.append(a['href'])
        if tag in ['script', 'img'] and a.get('src'):
            self.assets.append(a['src'])
        if tag == 'link' and a.get('rel') in ['stylesheet', 'icon', 'manifest']:
            self.assets.append(a.get('href', ''))


def resolve(url, current):
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc:
        return None, ''
    path = unquote(parsed.path)
    target = ROOT / path.lstrip('/') if path.startswith('/') else current.parent / path if path else current
    if target.is_dir():
        target /= 'index.html'
    elif not target.suffix and target.with_suffix('.html').exists():
        target = target.with_suffix('.html')
    return target, unquote(parsed.fragment)


errors = []
count = 0
for name in PAGES:
    file = ROOT / name
    if not file.exists():
        errors.append(name + ': missing page')
        continue
    text = file.read_text(encoding='utf-8')
    page = Page(text)
    if page.headings != 1:
        errors.append(f'{name}: expected one h1, got {page.headings}')
    if len(page.ids) != len(set(page.ids)):
        errors.append(name + ': duplicate IDs')
    for href in page.links + page.assets:
        target, fragment = resolve(href, file)
        if target is None:
            continue
        count += 1
        if not target.exists():
            errors.append(f'{name}: missing {href}')
        elif fragment and target.suffix == '.html' and fragment not in Page(target.read_text(encoding='utf-8')).ids:
            errors.append(f'{name}: missing fragment {href}')
    if name not in redesign_shell.EDITORIAL and redesign_shell.decorate(text) != text:
        errors.append(name + ': shared navigation stale')

home = (ROOT / 'index.html').read_text(encoding='utf-8')
tokens = json.loads((ROOT / 'data/token.json').read_text(encoding='utf-8'))['tokens']
for token in tokens:
    if token['address'] not in home:
        errors.append('Homepage missing canonical token address: ' + token['network'])
for host in ['app.uniswap.org', 'pancakeswap.finance', 'raydium.io']:
    if not any(urlsplit(href).netloc == host for href in Page(home).links):
        errors.append('Missing trading destination: ' + host)
if not any(href == 'https://fuel.army/staking' for href in Page(home).links):
    errors.append('Missing Fuel staking destination')
print(f'Checked {len(PAGES)} pages and {count} internal links/assets; {len(errors)} failures')
for error in errors:
    print(error)
sys.exit(bool(errors))
