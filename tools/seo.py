"""Search-engine and AI-assistant discovery for swarm.green. Use --check in review.

One module owns everything a crawler reads that a visitor does not:

  decorate(path, html)  called by build_pages.py and build_ecosystem.py on every
                        page they write: the search title and description from
                        PAGES, and the structured-data block (JSON-LD) between
                        the two seo markers at the end of <head>
  python tools/seo.py   writes what-is-swarm/index.html (the facts page),
                        llms.txt and llms-full.txt (the same facts as Markdown,
                        for AI assistants), robots.txt, sitemap.xml, the IndexNow
                        key file, and decorates the hand-made pages (index.html,
                        support/, wallet/*)
  --check               exits non-zero when any of those files is stale
  --indexnow            after a deploy: tells the IndexNow search engines which
                        URLs changed (one POST, the public URL list only)

Run order after an edit: build_pages.py, build_ecosystem.py, then seo.py.

Every figure comes from data/network.json and data/downloads.json, and every
sentence on the facts page restates something the site already says elsewhere.
Rules for the copy: no price, no promise, no other project named, "shielded"
(never "anonymous" or "untraceable"), and nothing that reads as an invitation to
buy. A page that carries <meta name="robots" content="noindex"> is left alone
and stays out of the sitemap (the Messenger link pages, the 404 page).
"""
import datetime
import hashlib
import html
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://swarm.green'
NETWORK = json.loads((ROOT / 'data/network.json').read_text(encoding='utf-8'))
DOWNLOADS = json.loads((ROOT / 'data/downloads.json').read_text(encoding='utf-8'))
CHAIN = NETWORK['chain']
GENESIS = NETWORK['genesis']
STATUS = NETWORK['status']
ENDPOINTS = NETWORK['endpoints']
SHARES = NETWORK['rewardSplit']['shares']

X_URL = NETWORK['links']['x']
X_HANDLE = '@' + X_URL.rsplit('/', 1)[-1]
EMAIL = NETWORK['links']['email']
EXPLORER = ENDPOINTS['explorerMainnet']
EXPLORER_HOST = EXPLORER.split('//', 1)[-1].rstrip('/')
# The release repository: its README lists every component. Same value as
# GH_SOURCE in build_pages.py.
SOURCE = DOWNLOADS['meta']['releasesUrl']

STATE = ROOT / 'tools/seo-state.json'
START = '<!-- seo:start -->'
END = '<!-- seo:end -->'
# IndexNow proves ownership with a key that is published on the site itself, so
# it is not a secret: the file /<key>.txt holds the key.
INDEXNOW_KEY = 'eba4807cf40d07eb436609728fe08be3'
INDEXNOW_ENDPOINT = 'https://api.indexnow.org/indexnow'

esc = lambda value: html.escape(str(value), quote=True)


def number(value):
    """20999987.3152 -> '20,999,987.3152'; 1680000 -> '1,680,000'; 6.25 -> '6.25'."""
    text = f'{value:,.4f}'.rstrip('0').rstrip('.')
    return text


def listing(items):
    items = list(items)
    if len(items) < 2:
        return ''.join(items)
    return ', '.join(items[:-1]) + ' and ' + items[-1]


MAX_SUPPLY = number(CHAIN['maxSupply'])
REWARD = number(CHAIN['initialBlockReward'])
HALVING = number(CHAIN['halvingIntervalBlocks'])
BLOCK_TIME = CHAIN['blockTimeSeconds']
POW = CHAIN['proofOfWork']
MATURITY = CHAIN['coinbaseMaturityBlocks']
LAUNCHED = STATUS['launchedLabel']
LAUNCH_DAY = LAUNCHED.split(',')[0]
# The restart of 2 October 2026: a 30-day closed start (29 days in which only
# the project mines, then 24 hours for the waiting list), and one sentence of
# history about the first chain.
CLOSED = NETWORK['closedStart']
OPENS = CLOSED['untilLabel']
PROJECT_ONLY = CLOSED['projectOnlyUntilLabel']
HISTORY = NETWORK['history']['sentence']
SPLIT = ' · '.join(f'{s["percent"]} {s["name"]}' for s in SHARES)
PROJECT_SHARE = number(100 * sum(s['share'] for s in SHARES if s['key'] != 'miner'))
MINER_SHARE = next(s['percent'] for s in SHARES if s['key'] == 'miner')

# The one-paragraph answer to "what is SWARM?". The home page description, the
# facts page, llms.txt and the structured data all carry this same sentence, so
# a search engine and an assistant read the same definition everywhere.
DEFINITION = (f'SWARM (ticker SWM) is a privacy coin: a cryptocurrency with its own proof-of-work blockchain, '
              f'on which payments can be shielded so that sender, receiver and amount stay encrypted on-chain. '
              f'Its supply is capped at {MAX_SUPPLY} SWM and there was no sale. Its mainnet was restarted from a new '
              f'genesis block on {LAUNCH_DAY}; until {PROJECT_ONLY} only the project’s own machines mine, for the '
              f'next 24 hours the people on its waiting list can mine too, and from {OPENS} mining is open to '
              f'everyone.')


# ---------------------------------------------------------------------------
# Downloads: which platforms an app is published for today, read from the same
# data file the Ecosystem pages are generated from.
# ---------------------------------------------------------------------------
UNAVAILABLE = tuple(DOWNLOADS['meta'].get('unavailableHosts', []))


def published(entry, held=False):
    """Offered for download today. held=True also counts builds that are paused in the data
    (published, but not offered until a new version replaces them)."""
    return (entry.get('channel', 'mainnet') == 'mainnet' and entry.get('status') == 'available'
            and bool(entry.get('url')) and not (UNAVAILABLE and entry['url'].startswith(UNAVAILABLE))
            and (held or not entry.get('paused')))


def platforms(*products, held=False):
    seen = {('macOS' if e['platform'].startswith('macOS') else e['platform'])
            for e in DOWNLOADS['entries'] if e.get('product') in products and published(e, held)}
    return [p for p in ['Windows', 'macOS', 'Linux', 'Android'] if p in seen]


def version_of(*products):
    return next((e['version'] for e in DOWNLOADS['entries']
                 if e.get('product') in products and published(e) and e.get('version')), '')


APPS = {
    '/ecosystem/wallet': {
        'name': 'SWARM Wallet', 'products': ('wallet', 'mobile-android'), 'category': 'FinanceApplication',
        'what': 'holds, sends and receives SWM, shielded or transparent'},
    '/ecosystem/messenger': {
        'name': 'SWARM Messenger', 'products': ('messenger',), 'category': 'CommunicationApplication',
        'what': 'is end-to-end encrypted messaging between SWARM wallets, with payments inside the chat'},
    '/ecosystem/browser': {
        'name': 'SWARM Browser', 'products': ('browser',), 'category': 'BrowserApplication',
        'what': 'is a web browser with the SWARM wallet built in'},
}
for _app in APPS.values():
    _app['platforms'] = platforms(*_app['products'])
    _app['version'] = version_of(*_app['products'])
    # Nothing offered today, but builds paused in the data: the app still exists
    # for those platforms, and a new version is being published.
    _app['held'] = not _app['platforms'] and bool(platforms(*_app['products'], held=True))
    if _app['held']:
        _app['platforms'] = platforms(*_app['products'], held=True)

HELD_NOTE = 'a new version for the restarted network is being published'


def app_line(path):
    app = APPS[path]
    if app['held']:
        return f'{app["name"]} {app["what"]}, for {listing(app["platforms"])}. {HELD_NOTE[0].upper() + HELD_NOTE[1:]}.'
    return f'{app["name"]} {app["what"]}. Free downloads for {listing(app["platforms"])}, each with its SHA-256 checksum.'


# ---------------------------------------------------------------------------
# The pages a search engine should know, in sitemap order. "name" is the
# breadcrumb label; "title" and "desc" replace what the page generator wrote,
# and a page without them keeps its own. Titles lead with what a person types
# into a search box: the name with its ticker, then the subject.
# ---------------------------------------------------------------------------
PAGES = {
    '/': {
        'name': 'SWARM',
        'title': 'SWARM (SWM) — Privacy coin: private, proof-of-work money run by its community',
        'desc': 'SWARM (SWM) is a privacy coin: proof-of-work money with shielded payments that keep sender, receiver and amount encrypted. 21 million cap, no sale. Public mining opens 1 November 2026.'},
    '/what-is-swarm': {'name': 'What is SWARM?', 'desc': 'SWARM (SWM) in plain facts: a proof-of-work privacy coin with shielded payments, a 21 million cap and no sale. Mainnet restarted 2 October 2026; public mining opens 1 November 2026.'},
    '/network': {'name': 'Network & supply', 'title': 'SWM supply, halving schedule and network rules — SWARM',
                 'desc': 'Every SWARM (SWM) parameter: 75-second blocks, 6.25 SWM per block, halving every 1,680,000 blocks, a 20,999,987.3152 SWM cap, the 30-day closed start, the 80/8/4/8 split.'},
    '/verify': {'name': 'Verify', 'title': 'Verify the SWARM mainnet: genesis hash, endpoints, addresses — SWARM',
                'desc': 'Check you are on the real SWARM chain: the genesis hash, the launch time, the public endpoints, the three published fund addresses and the address prefixes.'},
    '/join': {'name': 'Get SWARM', 'title': 'Get started with SWARM (SWM): choose a wallet — SWARM'},
    '/waitlist': {'name': 'Waiting list', 'title': 'Waiting list for SWARM (SWM) public mining — SWARM',
                  'desc': 'Join the waiting list for SWARM (SWM) public mining: the node download from 31 October 2026, 15:42 UTC, 24 hours before mining opens to everyone, in leaderboard order. No coins are promised.'},
    '/ecosystem': {'name': 'Ecosystem', 'title': 'Download the SWARM apps: every file with its checksum — SWARM'},
    '/ecosystem/wallet': {
        'name': 'SWARM Wallet',
        'title': f'SWARM Wallet: SWM wallet for {listing(APPS["/ecosystem/wallet"]["platforms"])}',
        'desc': app_line('/ecosystem/wallet')},
    '/ecosystem/messenger': {
        'name': 'SWARM Messenger',
        'title': 'SWARM Messenger: private messaging with a built-in SWM wallet'},
    '/ecosystem/browser': {
        'name': 'SWARM Browser',
        'title': 'SWARM Browser: a web browser with the SWM wallet built in'},
    '/roadmap': {'name': 'Roadmap', 'title': 'SWARM (SWM) roadmap: what is live and what comes next — SWARM',
                 'desc': 'SWARM (SWM) roadmap: what is live today, what is being built and what is only planned, from the mainnet and the apps to SWARM Market.'},
    '/support': {'name': 'Support', 'title': 'SWARM support: help with the wallet and downloads'},
    '/brand': {'name': 'Brand'},
    '/terms': {'name': 'Terms', 'desc': 'Terms for swarm.green, an information site about open-source software and the SWARM network. Nothing here is an offer, a solicitation or financial advice.'},
    '/privacy': {'name': 'Privacy'},
}

NOINDEX = re.compile(r'<meta name="robots" content="[^"]*noindex')
SKIP_DIRS = {'tools', 'assets', 'css', 'js', 'data', 'node_modules', '_review'}


def url_of(path):
    """'network/index.html' -> '/network'; 'index.html' -> '/'; anything else is not a page."""
    path = str(path).replace('\\', '/')
    if path == 'index.html':
        return '/'
    return '/' + path[:-len('/index.html')] if path.endswith('/index.html') else None


def file_of(url):
    return 'index.html' if url == '/' else url.strip('/') + '/index.html'


# ---------------------------------------------------------------------------
# Structured data. One JSON-LD graph per page: who publishes the site, what the
# page is, where it sits, and the questions it answers. A JSON-LD block is data,
# not a script, so the site's Content-Security-Policy does not apply to it.
# ---------------------------------------------------------------------------
ORG_ID = SITE + '/#organization'
WEBSITE_ID = SITE + '/#website'
COIN_ID = SITE + '/#swm'
# Wikidata's item for "cryptocurrency"; schema.org has no type of its own for one.
CRYPTOCURRENCY = 'https://www.wikidata.org/wiki/Q13479982'

FAQ_RE = re.compile(r'<details>\s*<summary>(.*?)<span class="ind"[^>]*></span></summary>\s*'
                    r'<div class="answer">(.*?)</div>\s*</details>', re.S)


def plain(fragment):
    """Visible text of an HTML fragment, on one line."""
    fragment = re.sub(r'<span class="vh">.*?</span>', '', fragment, flags=re.S)
    fragment = re.sub(r'<svg.*?</svg>', '', fragment, flags=re.S)
    fragment = re.sub(r'</p>\s*<p[^>]*>', ' ', fragment)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', fragment))).strip()


def questions(text):
    return [(plain(q), plain(a)) for q, a in FAQ_RE.findall(text)]


def meta_of(text):
    title = re.search(r'<title>(.*?)</title>', text, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', text)
    return html.unescape(title[1]) if title else '', html.unescape(desc[1]) if desc else ''


def crumb_name(url, title):
    if url in PAGES:
        return PAGES[url]['name']
    return re.split(r' — | \| ', title)[0]


def graph(url, text):
    title, desc = meta_of(text)
    here = SITE + url
    full = url in ('/', '/what-is-swarm')
    org = {'@type': 'Organization', '@id': ORG_ID, 'name': 'SWARM', 'url': SITE + '/',
           'logo': SITE + '/assets/logo-mark.svg'}
    site = {'@type': 'WebSite', '@id': WEBSITE_ID, 'url': SITE + '/', 'name': 'SWARM',
            'publisher': {'@id': ORG_ID}}
    coin = {'@type': 'Thing', '@id': COIN_ID, 'name': 'SWARM (SWM)'}
    if full:
        org.update({'alternateName': ['SWARM (SWM)', 'SWARM Network'],
                    'description': 'The open-source project behind SWARM (SWM), a proof-of-work privacy coin.',
                    'email': EMAIL, 'sameAs': [X_URL, SOURCE]})
        site.update({'alternateName': 'swarm.green', 'description': DEFINITION, 'inLanguage': 'en'})
        coin.update({'alternateName': ['SWM', 'SWARM coin'], 'additionalType': CRYPTOCURRENCY,
                     'description': DEFINITION, 'url': SITE + '/what-is-swarm'})
    page = {'@type': 'AboutPage' if url == '/what-is-swarm' else 'WebPage', '@id': here, 'url': here,
            'name': title, 'description': desc, 'inLanguage': 'en',
            'isPartOf': {'@id': WEBSITE_ID}, 'about': {'@id': COIN_ID}}
    nodes = [org, site, coin, page]

    if url != '/':
        trail = [('Home', SITE + '/')]
        parts = url.strip('/').split('/')
        for depth in range(1, len(parts)):
            parent = '/' + '/'.join(parts[:depth])
            if parent in PAGES:
                trail.append((PAGES[parent]['name'], SITE + parent))
        trail.append((crumb_name(url, title), here))
        page['breadcrumb'] = {'@id': here + '#breadcrumb'}
        nodes.append({'@type': 'BreadcrumbList', '@id': here + '#breadcrumb', 'itemListElement': [
            {'@type': 'ListItem', 'position': n, 'name': name, 'item': item}
            for n, (name, item) in enumerate(trail, 1)]})

    if url in APPS:
        app = APPS[url]
        node = {'@type': 'SoftwareApplication', '@id': here + '#app', 'name': app['name'], 'url': here,
                'description': f'{app["name"]} {app["what"]}.',
                'applicationCategory': app['category'], 'operatingSystem': ', '.join(app['platforms']),
                'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
                'isAccessibleForFree': True, 'publisher': {'@id': ORG_ID}}
        if app['version']:
            node['softwareVersion'] = app['version']
        nodes.append(node)

    faq = questions(text)
    if faq:
        nodes.append({'@type': 'FAQPage', '@id': here + '#faq', 'isPartOf': {'@id': here}, 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]})
    return {'@context': 'https://schema.org', '@graph': nodes}


def decorate(path, text):
    """The page as it should be served: search title, description, structured data. Idempotent."""
    url = url_of(path)
    if url is None or NOINDEX.search(text):
        return text
    over = PAGES.get(url, {})
    if 'title' in over:
        text = re.sub(r'<title>.*?</title>', lambda m: '<title>' + esc(over['title']) + '</title>', text, 1, re.S)
    if 'desc' in over:
        text = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m[1] + esc(over['desc']), text, 1)
    data = json.dumps(graph(url, text), ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    block = f'{START}\n<script type="application/ld+json">{data}</script>\n{END}'
    # Always the last thing in <head>, whatever a generator appended after an
    # earlier block, so every route to a page gives the same bytes.
    text = re.sub(re.escape(START) + r'.*?' + re.escape(END) + r'\n?', '', text, 1, re.S)
    return text.replace('</head>', block + '\n</head>', 1)


# ---------------------------------------------------------------------------
# The facts page, /what-is-swarm, and its Markdown twins. One set of rows,
# paragraphs and questions feeds all three, so they cannot drift apart.
# ---------------------------------------------------------------------------
def link(href, label):
    if href.startswith('/') or href.startswith('mailto:'):
        return f'<a href="{href}">{label}</a>'
    return (f'<a href="{href}" target="_blank" rel="noopener noreferrer">{label}'
            '<span class="vh"> (opens in a new tab)</span></a>')


def app_list():
    out = []
    for path, app in APPS.items():
        if app['platforms']:
            note = '; ' + HELD_NOTE if app['held'] else ''
            out.append(f'{link(path, app["name"])} ({listing(app["platforms"])}{note})')
    return out


ADDRESSES = ', '.join(f'<code>{esc(f["prefix"])}</code> {f["kind"].lower()}'
                      for f in NETWORK['addressFormats']['formats'] if f['network'] == 'Mainnet')

FACTS = [
    ('Name', 'SWARM'),
    ('Ticker', 'SWM'),
    ('What it is', 'A privacy coin: a cryptocurrency with its own proof-of-work blockchain and shielded payments.'),
    ('Status', f'Mainnet live; restarted from a new genesis block on {LAUNCHED}.'),
    ('Genesis block hash', f'<code>{GENESIS["hash"]}</code>'),
    ('Consensus', f'Proof of work, {POW}.'),
    ('Target block time', f'{BLOCK_TIME} seconds'),
    ('Block reward', f'{REWARD} SWM, halving every {HALVING} blocks (about {CHAIN["halvingApproxYears"]} years).'),
    ('Maximum supply', f'{MAX_SUPPLY} SWM'),
    ('Genesis and sale', 'The genesis block holds no spendable coins, and there was no sale, no presale '
                         'and no token offering. Every SWM is mined.'),
    ('Closed start', CLOSED['summary']),
    ('First chain', HISTORY),
    ('Block reward split', f'{SPLIT}. Fixed in the genesis rules for the whole emission schedule.'),
    ('Privacy', 'Shielded payments keep sender, receiver and amount encrypted on-chain, using zero-knowledge '
                'proofs. Transparent payments exist too.'),
    ('Mainnet addresses', ADDRESSES),
    ('Apps', '; '.join(app_list()) + '.'),
    ('Block explorer', link(EXPLORER, EXPLORER_HOST)),
    ('Source code', f'Open source: {link(SOURCE, SOURCE.split("//", 1)[-1])}'),
    ('Official channels', f'{link("/", "swarm.green")}, {link(X_URL, X_HANDLE + " on X")}, '
                          f'{link("mailto:" + EMAIL, EMAIL)}'),
]

SECTIONS = [
    ('How SWARM keeps a payment private', [
        'SWARM has two kinds of payment. A <strong>shielded</strong> payment uses zero-knowledge proofs: the chain '
        'records that a valid payment happened without recording who paid whom or how much, so sender, receiver '
        'and amount stay encrypted on-chain. A <strong>transparent</strong> payment is public, as on most '
        'blockchains.',
        'SWARM Wallet gives you a shielded address by default and tells you which kind of payment you are about '
        'to make. Shielding protects what is written to the chain. It does not protect everything about how you '
        'use the network: your own network connection, for example, is a separate matter.',
    ]),
    ('How SWM is issued', [
        f'SWM is issued only by mining. A block is found about every {BLOCK_TIME} seconds and pays {REWARD} SWM; '
        f'the reward halves every {HALVING} blocks, about every {CHAIN["halvingApproxYears"]} years, so the supply '
        f'approaches {MAX_SUPPLY} SWM and never exceeds it. The genesis block holds no spendable coins and there was '
        'no sale. The first 30 days are a closed start. ' + CLOSED['summary'],
        f'Every block reward is split the same way for the whole schedule: {MINER_SHARE} to the miner who found '
        f'the block and {PROJECT_SHARE}% to three published project addresses ('
        + listing(f'{s["percent"]} {s["name"]}' for s in SHARES if s['key'] != 'miner') +
        '). Those shares are paid block by block, in public, and the percentages cannot be changed. '
        f'The full schedule is on the {link("/network", "network page")}; the three addresses and how their keys '
        f'are held are on the {link("/verify", "verify page")}.',
    ]),
    ('Proof of work', [
        f'SWARM is secured by proof of work, {POW}, left unchanged from the open-source code it builds on. '
        'Specialised hardware for this proof of work exists and nothing in the rules keeps larger miners out.',
    ]),
    ('What it is built on', [
        'SWARM is built on proven, open-source code that has secured real money for years. The consensus rules '
        'and the cryptography are left unmodified; SWARM adds its own network, its economics and its apps. '
        f'The code is public at {link(SOURCE, SOURCE.split("//", 1)[-1])}: read it, build it, check it.',
    ]),
    ('The software', [
        'Everything you need is published with its SHA-256 checksum in the '
        f'{link("/ecosystem", "Ecosystem")}: ' + listing(app_list()) + '. '
        f'The mainnet block explorer is at {link(EXPLORER, EXPLORER_HOST)}. The '
        f'{link("/roadmap", "roadmap")} separates what is live from what is only planned.',
    ]),
]

QUESTIONS = [
    ('Is SWARM a privacy coin?',
     ['Yes. SWARM is a cryptocurrency whose payments can be shielded: sender, receiver and amount stay encrypted '
      'on-chain, using zero-knowledge proofs. It runs on its own proof-of-work blockchain, and its ticker is SWM.']),
    ('When did SWARM launch?',
     [f'SWARM mainnet was restarted on {LAUNCHED} from a new genesis block that holds no spendable coins. '
      + HISTORY + ' ' + CLOSED['summary']]),
    ('How many SWM will there be?',
     [f'At most {MAX_SUPPLY} SWM. Each block pays {REWARD} SWM, and the reward halves every {HALVING} blocks, '
      f'about every {CHAIN["halvingApproxYears"]} years.']),
    ('Was there a premine, a sale or an airdrop?',
     ['There was no sale, no presale and no token offering, and the genesis block holds no spendable coins; every '
      'SWM in existence was mined. There is a closed start. ' + CLOSED['summary'] + ' '
      'Anything claiming to be a SWARM sale, presale or airdrop is not the project.']),
    ('What does a shielded payment hide?',
     ['The sender, the receiver and the amount. The chain records that a valid payment happened, not who paid '
      'whom or how much.']),
    ('Is every SWARM payment private?',
     ['No. Privacy is a choice you make per payment: shielded payments are encrypted on-chain, transparent '
      'payments are public, and the wallet tells you which kind you are about to make.']),
    ('How do I get SWM?',
     [f'SWM is issued only by mining; until {PROJECT_ONLY} only the project’s own machines mine, and public mining opens on {OPENS}. You can receive it from someone who already has it. The project does not sell SWM, does not set a price and does not run an exchange. '
      'SWM has no guaranteed value and can lose value, including all of it.']),
    ('Where do block rewards go?',
     [f'{SPLIT}. The split is fixed in the genesis rules for the whole emission schedule and is visible in every '
      'block.']),
    ('Who runs SWARM?',
     ['A founding team builds the software in the open. Until ' + PROJECT_ONLY + ' the project alone mines; the '
      'people on the waiting list follow 24 hours before public mining opens on ' + OPENS + ', and from then on '
      'anyone can run a node and mine, with no account to apply for. There is no admin key, '
      'and the rules every node enforces are the same for the founders as for anyone else.']),
    ('How do I check that I am on the real SWARM chain?',
     [f'A chain is identified by its genesis block. SWARM mainnet&rsquo;s genesis hash is '
      f'<code>{GENESIS["hash"]}</code>. '
      f'The {link("/verify", "verify page")} lists the launch facts, the public endpoints and the published '
      'addresses.']),
    ('Which sources are official?',
     [f'This site, {link(X_URL, X_HANDLE + " on X")}, the email address {link("mailto:" + EMAIL, EMAIL)} and the '
      f'code at {link(SOURCE, SOURCE.split("//", 1)[-1])}. The project will never ask for your recovery words, '
      'private keys or a payment.']),
]

WHAT_TITLE = 'What is SWARM (SWM)? The privacy coin in plain facts — SWARM'
WHAT_DESC = DEFINITION


def what_body():
    rows = '\n'.join(f'          <tr><th scope="row">{label}</th><td>{value}</td></tr>' for label, value in FACTS)
    prose = ''
    for heading, paragraphs in SECTIONS:
        prose += f'      <h2>{heading}</h2>\n' + ''.join(f'      <p>{p}</p>\n' for p in paragraphs)
    faq = ''
    for question, paragraphs in QUESTIONS:
        answer = ''.join(f'<p>{p}</p>' for p in paragraphs)
        faq += (f'        <details>\n          <summary>{question}<span class="ind" aria-hidden="true"></span></summary>\n'
                f'          <div class="answer">{answer}</div>\n        </details>\n')
    return f'''  <section class="band band--dark band--comb page-head">
    <div class="wrap">
      <p class="crumbs"><a href="/">Home</a><span aria-hidden="true">/</span>What is SWARM?</p>
      <p class="pill">{esc(STATUS["short"])}</p>
      <h1>What is SWARM (SWM)?</h1>
      <p class="page-head__lead">{DEFINITION}</p>
    </div>
  </section>

  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head">
        <p class="eyebrow">Key facts</p>
        <h2>SWARM in one table.</h2>
        <p>Fixed rules and published facts only. Live figures such as the block height come from the chain itself: see the <a href="/#mainnet">home page</a> or the block explorer.</p>
      </div>
      <div class="tablewrap">
        <table>
          <caption>SWARM (SWM) at a glance.</caption>
          <tbody>
{rows}
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap wrap--narrow prose">
{prose}    </div>
  </section>

  <section class="band band--cream" id="faq">
    <div class="wrap wrap--narrow">
      <div class="sec-head">
        <p class="eyebrow">Questions</p>
        <h2>Short answers.</h2>
      </div>
      <div class="faq">
{faq}      </div>
      <p class="note mt-l">Nothing on this page is an offer, a solicitation or financial advice. More questions are answered in the <a href="/#faq">FAQ</a>.</p>
    </div>
  </section>'''


def what_page():
    """The facts page in the site's own shell (head, nav and footer come from support/index.html)."""
    shell = (ROOT / 'support/index.html').read_text(encoding='utf-8')
    before, rest = shell.split('<main id="main">', 1)
    after = rest.split('</main>', 1)[1]
    before = re.sub(r'<title>.*?</title>', lambda m: '<title>' + esc(WHAT_TITLE) + '</title>', before, 1, re.S)
    for key in ['description', 'og:description', 'twitter:description']:
        before = re.sub(r'((?:name|property)="' + key + r'" content=")[^"]*', lambda m: m[1] + esc(WHAT_DESC), before)
    before = before.replace('SWARM — Support', 'SWARM — What is SWARM?').replace(SITE + '/support', SITE + '/what-is-swarm')
    return decorate('what-is-swarm/index.html', before + '<main id="main">\n' + what_body() + '\n</main>' + after)


def markdown(fragment):
    """The few tags used above, as Markdown with absolute links."""
    fragment = re.sub(r'<span class="vh">.*?</span>', '', fragment, flags=re.S)

    def anchor(m):
        href = m[1] if not m[1].startswith('/') else SITE + m[1]
        return m[2] if href.startswith('mailto:') else f'[{m[2]}]({href})'
    fragment = re.sub(r'<a href="([^"]+)"[^>]*>(.*?)</a>', anchor, fragment, flags=re.S)
    fragment = re.sub(r'</?strong>', '**', fragment)
    fragment = re.sub(r'</?code>', '`', fragment)
    return html.unescape(re.sub(r'<[^>]+>', '', fragment))


def page_links():
    """(title, url, one line) for the pages an assistant should read first."""
    return [
        ('What is SWARM (SWM)?', '/what-is-swarm', 'the facts on one page: definition, key figures, privacy, issuance, official sources'),
        ('Network and supply', '/network', f'every consensus and monetary parameter, the era table and the {SPLIT.replace(" · ", " / ")} block reward split'),
        ('Verify the chain', '/verify', 'genesis hash, launch time, public endpoints, the three published fund addresses, address prefixes'),
        ('Get started', '/join', 'choosing a wallet, step by step'),
        ('Waiting list for public mining', '/waitlist', 'join the list to get the node download from 31 October 2026, 15:42 UTC, 24 hours before public mining opens on 1 November 2026; one level of invites decides the order; no coins are promised'),
        ('Roadmap', '/roadmap', 'what is live, what is being built and what is only planned'),
        ('Frequently asked questions', '/#faq', 'launch, supply, mining, privacy, custody of the project share'),
    ]


def llms_txt():
    lines = ['# SWARM (SWM)', '', '> ' + DEFINITION, '',
             'Identify this project by its ticker SWM, its website swarm.green and its mainnet genesis block hash '
             f'`{GENESIS["hash"]}`. Everything below is published by the project itself. Text on swarm.green may be '
             'quoted with a link to the page it comes from.', '',
             f'- Ticker: SWM. Own blockchain, proof of work ({POW}), target block time {BLOCK_TIME} seconds.',
             f'- Supply: at most {MAX_SUPPLY} SWM; {REWARD} SWM per block, halving every {HALVING} blocks (about {CHAIN["halvingApproxYears"]} years).',
             '- The genesis block holds no coins; no sale, no presale, no token offering: every SWM is mined.',
             '- Closed start. ' + CLOSED['summary'],
             f'- Block reward split, fixed for the whole schedule: {SPLIT}.',
             '- Privacy: shielded payments keep sender, receiver and amount encrypted on-chain, using zero-knowledge proofs; transparent payments exist too.',
             f'- Mainnet restarted from a new genesis block on {LAUNCHED}. ' + HISTORY,
             '- The project does not sell SWM, does not set a price and does not run an exchange.', '',
             '## Start here', '']
    lines += [f'- [{title}]({SITE}{url}): {note}' for title, url, note in page_links()]
    lines += ['', '## Apps', '',
              f'- [Ecosystem]({SITE}/ecosystem): every download with its SHA-256 checksum']
    lines += [f'- [{app["name"]}]({SITE}{path}): {app["name"]} {app["what"]}. {listing(app["platforms"])}'
              + ('; ' + HELD_NOTE if app['held'] else '') + '.'
              for path, app in APPS.items() if app['platforms']]
    lines += ['', '## Live data', '',
              f'- [Network status (JSON)]({SITE}/data/status.json): block height, difficulty and mean block time, refreshed every 30 seconds by the SWARM mainnet server',
              f'- [Network parameters (JSON)]({SITE}/data/network.json): the fixed figures every page of the site is built from',
              f'- [Block explorer]({EXPLORER}): SWARM mainnet blocks and transactions',
              '', '## Official channels', '',
              f'- [X: {X_HANDLE}]({X_URL})',
              f'- [Source code and releases]({SOURCE})',
              f'- Email: {EMAIL}',
              '', '## Optional', '',
              f'- [Everything above in one file]({SITE}/llms-full.txt): the facts, the schedule and the questions and answers as plain Markdown',
              f'- [Support]({SITE}/support): help with the wallet',
              f'- [Brand]({SITE}/brand): logo files, colours and usage rules',
              f'- [Terms]({SITE}/terms) and [Privacy]({SITE}/privacy)', '']
    return '\n'.join(lines)


def llms_full(home):
    out = ['# SWARM (SWM)', '', '> ' + DEFINITION, '',
           f'Source: {SITE}/what-is-swarm and the pages linked below. Published by the SWARM project. '
           'Fixed rules and published facts only; for live figures read '
           f'{SITE}/data/status.json or the block explorer at {EXPLORER}.', '',
           '## Key facts', '', '| | |', '| --- | --- |']
    out += [f'| {label} | {markdown(value)} |' for label, value in FACTS]
    for heading, paragraphs in SECTIONS:
        out += ['', '## ' + heading, ''] + [markdown(p) + '\n' for p in paragraphs]
        out[-1] = out[-1].rstrip('\n')
    out += ['', '## Emission schedule', '',
            'An era is the stretch between two halvings. Later eras continue the same halving.', '',
            '| Era | Block heights | Block reward (SWM) | Issued in era (SWM) | Cumulative supply (SWM) |',
            '| --- | --- | --- | --- | --- |']
    out += [f'| {e["era"]} | {number(e["fromHeight"])} – {number(e["toHeight"])} | {number(e["reward"])} | '
            f'{number(e["issuance"])} | {number(e["cumulative"])} |' for e in NETWORK['eras']]
    out += ['', f'Mining rewards mature after {MATURITY} blocks before they can be spent.', '',
            '## Block reward split', '',
            NETWORK['rewardSplit']['appliesFor'] + ' ' + NETWORK['rewardSplit']['destinations'], '',
            '| Recipient | Share | Per block in era 0 (SWM) | Published address |', '| --- | --- | --- | --- |']
    addresses = {d['name']: d['address'] for d in GENESIS['destinations']}
    out += [f'| {s["name"]} | {s["percent"]} | {number(s["perBlock"])} | '
            + (f'`{addresses[s["name"]]}`' if s['name'] in addresses else 'the address the miner chose') + ' |'
            for s in SHARES]
    out += ['', f'Custody of the three project addresses: {GENESIS["addressType"]} {GENESIS["custody"]}', '',
            '## Network endpoints', '',
            f'- Light-wallet server (TLS): `{ENDPOINTS["lightWallet"]}`',
            f'- Block explorer: {EXPLORER}',
            f'- Network name: `{GENESIS["network"]}`; light-wallet chain label: `{CHAIN["lightWalletChainLabel"]}`',
            '', '## Address formats', '']
    out += [f'- `{f["prefix"]}` — {f["network"]}, {f["kind"].lower()}. {f["detail"]}'
            for f in NETWORK['addressFormats']['formats']]
    out += ['', '## Apps', '']
    out += [f'- {app["name"]} {app["what"]}. ' + (f'For {listing(app["platforms"])}; {HELD_NOTE}.' if app['held']
            else f'Published for {listing(app["platforms"])}.') + f' Download page: {SITE}{path}'
            for path, app in APPS.items() if app['platforms']]
    out += [f'- Every file and its SHA-256 checksum: {SITE}/ecosystem', '',
            '## Questions and answers', '']
    seen = set()
    for question, answer in [(q, ' '.join(markdown(p) for p in ps)) for q, ps in QUESTIONS] + questions(home):
        if question not in seen:
            seen.add(question)
            out += ['### ' + question, '', answer, '']
    out += ['## Pages', '']
    out += [f'- [{title}]({SITE}{url}): {note}' for title, url, note in page_links()]
    out += ['', '## Official channels', '',
            f'- Website: {SITE}', f'- X: {X_URL} ({X_HANDLE})', f'- Source code and releases: {SOURCE}',
            f'- Email: {EMAIL}', '',
            'The project will never ask for recovery words, private keys or a payment. Nothing here is an offer, '
            'a solicitation or financial advice. SWM has no guaranteed value and can lose value, including all of it.', '']
    return '\n'.join(out)


# ---------------------------------------------------------------------------
# robots.txt. Everything on the site is public. The named agents are the search
# and AI crawlers that publish a robots.txt token; naming them changes nothing a
# crawler may do (the first group already allows all of it) and states in the
# file itself that answering questions from these pages is welcome.
# ---------------------------------------------------------------------------
# Tokens read at each vendor's own crawler page on 2026-09-30. Brave's crawler
# has no token of its own and follows the Googlebot rules.
AI_AGENTS = [
    ('OpenAI (ChatGPT)', ['OAI-SearchBot', 'GPTBot', 'ChatGPT-User']),
    ('Anthropic (Claude)', ['ClaudeBot', 'Claude-SearchBot', 'Claude-User']),
    ('Perplexity', ['PerplexityBot', 'Perplexity-User']),
    ('Google (Search, Gemini)', ['Googlebot', 'Google-Extended']),
    ('Microsoft (Bing, Copilot)', ['bingbot']),
    ('Apple', ['Applebot', 'Applebot-Extended']),
    ('Meta', ['meta-externalagent', 'meta-webindexer', 'meta-externalfetcher']),
    ('Amazon', ['Amazonbot', 'Amzn-SearchBot']),
    ('DuckDuckGo', ['DuckDuckBot', 'DuckAssistBot']),
    ('Mistral', ['MistralAI-Index', 'MistralAI-User']),
    ('You.com', ['YouBot']),
    ('Common Crawl', ['CCBot']),
]


def robots_txt():
    lines = ['# swarm.green: every page here is public. It may be crawled, indexed, quoted',
             '# and used to answer questions, by search engines and by AI assistants alike.',
             f'# A plain-text summary for assistants: {SITE}/llms.txt',
             '', 'User-agent: *', 'Allow: /', '']
    for owner, agents in AI_AGENTS:
        lines += ['# ' + owner] + ['User-agent: ' + agent for agent in agents] + ['Allow: /', '']
    lines += [f'Sitemap: {SITE}/sitemap.xml', '']
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# sitemap.xml. Every page that may be indexed, with the day its content last
# changed. tools/seo-state.json remembers a hash per page, so lastmod moves only
# when the page really changed (search engines stop trusting a lastmod that
# moves on every deploy).
# ---------------------------------------------------------------------------
def indexable():
    """url -> decorated page text, PAGES first, then whatever else is on disk."""
    found = {}
    for file in sorted(ROOT.rglob('index.html')):
        rel = file.relative_to(ROOT).as_posix()
        if rel.split('/')[0] in SKIP_DIRS or rel.startswith('.'):
            continue
        text = file.read_text(encoding='utf-8')
        if not NOINDEX.search(text):
            found[url_of(rel)] = text
    found['/what-is-swarm'] = what_page()
    ordered = {url: found.pop(url) for url in PAGES if url in found}
    ordered.update(found)
    return {url: decorate(file_of(url), text) for url, text in ordered.items()}


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def sitemap_xml(state):
    rows = ''.join(f'  <url><loc>{SITE}{"/" if url == "/" else url}</loc><lastmod>{entry["lastmod"]}</lastmod></url>\n'
                   for url, entry in state.items())
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + '</urlset>\n')


def outputs(today):
    """path -> content for every file this module owns, and whether the sitemap state is current."""
    pages = indexable()
    old = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    state, current = {}, True
    for url, text in pages.items():
        sha = digest(text)
        if old.get(url, {}).get('sha256') == sha:
            state[url] = old[url]
        else:
            state[url] = {'sha256': sha, 'lastmod': today}
            current = False
    files = {file_of(url): text for url, text in pages.items()}
    files['llms.txt'] = llms_txt()
    files['llms-full.txt'] = llms_full(pages['/'])
    files['robots.txt'] = robots_txt()
    files['sitemap.xml'] = sitemap_xml(state)
    files[INDEXNOW_KEY + '.txt'] = INDEXNOW_KEY
    files['tools/seo-state.json'] = json.dumps(state, indent=1) + '\n'
    return files, current


def indexnow():
    """Tell the IndexNow engines which URLs exist. Only after the deploy that carries the key file."""
    import urllib.request
    key_url = f'{SITE}/{INDEXNOW_KEY}.txt'
    request = urllib.request.Request(key_url, headers={'User-Agent': 'swarm.green seo.py'})
    with urllib.request.urlopen(request, timeout=20) as reply:
        if reply.read().decode('utf-8').strip() != INDEXNOW_KEY:
            sys.exit('the key file is not live at ' + key_url + ': deploy first')
    state = json.loads(STATE.read_text(encoding='utf-8'))
    body = json.dumps({'host': SITE.split('//', 1)[1], 'key': INDEXNOW_KEY, 'keyLocation': key_url,
                       'urlList': [SITE + ('/' if url == '/' else url) for url in state]}).encode('utf-8')
    request = urllib.request.Request(INDEXNOW_ENDPOINT, data=body, method='POST',
                                     headers={'Content-Type': 'application/json; charset=utf-8'})
    with urllib.request.urlopen(request, timeout=20) as reply:
        print('IndexNow answered', reply.status, 'for', len(state), 'URLs')


if __name__ == '__main__':
    if '--indexnow' in sys.argv:
        indexnow()
        sys.exit()
    files, current = outputs(datetime.date.today().isoformat())
    stale = []
    for path, content in files.items():
        target = ROOT / path
        if '--check' in sys.argv:
            if not target.exists() or target.read_text(encoding='utf-8') != content:
                stale.append(path)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.read_text(encoding='utf-8') != content:
                target.write_text(content, encoding='utf-8')
                print(path)
    if '--check' in sys.argv and (stale or not current):
        sys.exit('Regenerate with python tools/seo.py: ' + (', '.join(stale) or 'sitemap state'))
