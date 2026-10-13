"""Keep the redesigned header/footer consistent on generated information pages.

The homepage, downloads hub and roadmap own their editorial layouts. Existing
product and information pages retain their functional markup and data generators.
Run this after a legacy generator, or use --check for a read-only consistency check.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
EDITORIAL = {'index.html', 'downloads/index.html', 'roadmap/index.html', 'get-swm/index.html', 'join/index.html', 'trade/index.html', 'waitlist/index.html', 'brand/logo-v2/index.html', 'brand/mascot/index.html', 'brand/mascot/style-sheet/index.html'}
EXCLUDED = {'call', 'u', 'g', 'stickers', 'wallet', 'components', 'assets'}


def decorate(content):
    if not re.search(r'<html\b', content, re.I):
        return content
    home = (ROOT / 'index.html').read_text(encoding='utf-8')
    header = re.search(r'<header\b[^>]*class="rd-header"[^>]*>.*?</header>', home, re.S)
    footer = re.search(r'<footer\b[^>]*class="rd-footer"[^>]*>.*?</footer>', home, re.S)
    if not header or not footer:
        return content
    if not re.search(r'<header\b', content):
        return content
    nav = header.group().replace('href="#', 'href="/#')
    foot = footer.group().replace('href="#', 'href="/#')
    content = re.sub(r'<p class="ribbon">.*?</p>\s*', '', content, flags=re.S)
    content = re.sub(r'<header\b[^>]*>.*?</header>', lambda _: nav, content, count=1, flags=re.S)
    content = re.sub(r'<footer\b[^>]*>.*?</footer>', lambda _: foot, content, count=1, flags=re.S)
    def body(match):
        tag = match.group()
        if 'rd-legacy' in tag:
            return tag
        if 'class="' in tag:
            return tag.replace('class="', 'class="redesign rd-legacy ', 1)
        return tag[:-1] + ' class="redesign rd-legacy">'
    content = re.sub(r'<body\b[^>]*>', body, content, count=1)
    content = re.sub(r'<(?:link|script)\b[^>]*(?:/css/(?:redesign(?:-legacy)?|mobile-v2|presentation-v5|motion-v5|refinement-v6|bee-pointer)\.css|/js/(?:redesign|status-v2|price|presentation-v5|page-swarm|bee-pointer)\.js)[^>]*>(?:</script>)?\s*', '', content)
    content = re.sub(r'<link\b[^>]*href="https://fonts.googleapis.com/css2[^>]*>\s*', '', content)
    includes = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&amp;family=Manrope:wght@400;500;600;700&amp;family=JetBrains+Mono:wght@400;500&amp;display=swap">\n<link rel="stylesheet" href="/css/redesign.css?v=6">\n<link rel="stylesheet" href="/css/redesign-legacy.css?v=2">\n<link rel="stylesheet" href="/css/mobile-v2.css?v=1">\n<link rel="stylesheet" href="/css/presentation-v5.css?v=6">\n<link rel="stylesheet" href="/css/motion-v5.css?v=8">\n<link rel="stylesheet" href="/css/refinement-v6.css?v=10">\n<script src="/js/page-swarm.js?v=10" defer></script>\n<script src="/js/presentation-v5.js?v=6" defer></script>\n<script src="/js/redesign.js?v=2" defer></script>\n<script src="/js/price.js?v=2" defer></script>\n<script src="/js/status-v2.js?v=2" defer></script>\n'
    includes += '<link rel="stylesheet" href="/css/bee-pointer.css?v=10">\n<script type="module" src="/js/bee-pointer.js?v=10"></script>\n'
    anchor = '<!-- seo:start -->' if '<!-- seo:start -->' in content else '</head>'
    return content.replace(anchor, includes + anchor, 1)


def main():
    stale = []
    for page in ROOT.rglob('*.html'):
        rel = page.relative_to(ROOT).as_posix()
        if rel in EDITORIAL or rel.split('/')[0] in EXCLUDED or rel.startswith('.'):
            continue
        current = page.read_text(encoding='utf-8')
        updated = decorate(current)
        if current != updated:
            stale.append(rel)
            if '--check' not in sys.argv:
                page.write_text(updated, encoding='utf-8')
    if '--check' in sys.argv and stale:
        sys.exit('Refresh shared navigation: ' + ', '.join(stale))
    print(('Checked' if '--check' in sys.argv else 'Updated') + ' shared site shell: ' + str(len(stale)) + ' pages')


if __name__ == '__main__':
    main()
