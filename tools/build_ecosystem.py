"""Generate every download surface from data/downloads.json. Use --check in review.

Outputs:
  index.html            the Ecosystem block on the home page (between the two
                        ecosystem markers; the rest of the file stays hand-made)
  ecosystem/index.html  the hub: the four app cards with their downloads, every
                        file with its checksum, the testnet builds
  ecosystem/<app>/      one page per app with a platform picker and install notes

Downloads live in the Ecosystem and nowhere else: no other page carries a
download link, only links to /ecosystem. Rows whose URL sits on a host listed in
meta.unavailableHosts render as "being re-published" instead of a dead button.
Owner rule 2026-09-28: files are served from SWARM's own server; github.com is
never linked for a download (meta.sourceUrl is the code, not the files).
"""
import html
import json
import os
from pathlib import Path
import re
import sys

import seo

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / 'data/downloads.json').read_text(encoding='utf-8'))
META = DATA['meta']
PRODUCTS = {p['key']: p for p in DATA['products']}
ECO_CSS = '/css/ecosystem.css?v=4'
ECO_JS = '/js/ecosystem.js?v=1'
MARK_START = '<!-- ecosystem:start -->'
MARK_END = '<!-- ecosystem:end -->'
UNAVAILABLE = tuple(META.get('unavailableHosts', []))


# Launch-day site: the pages say mainnet is live, so a testnet build must never
# be offered as if it were the mainnet download. Testnet builds are still
# published, but only in an entry that says so: channel == "testnet". Those are
# rendered in their own clearly labelled Testnet section, never in the main
# platform panels. Anything that smells of testnet without that label is a bug,
# and the build refuses. Local previews before launch set
# SWARM_ALLOW_PRELAUNCH_BUILD=1.
def channel(entry):
    return entry.get('channel', 'mainnet')


_test = [e for e in DATA['entries']
         if e['status'] == 'available' and channel(e) != 'testnet'
         and 'testnet' in (e.get('version', '') + e.get('url', '') + e.get('notes', '')).lower()]
if _test and not os.environ.get('SWARM_ALLOW_PRELAUNCH_BUILD'):
    sys.exit('refusing to build: %d available download entries are testnet builds but are not marked '
             '"channel": "testnet" (e.g. %s %s). Either point them at the mainnet releases or mark them '
             'as testnet so they render in the Testnet section (README: launch checklist).'
             % (len(_test), _test[0]['product'], _test[0].get('version') or _test[0]['url']))

SHELL = (ROOT / 'support/index.html').read_text(encoding='utf-8')
esc = lambda value: html.escape(str(value), quote=True)


def reachable(entry):
    return not entry.get('url', '').startswith(UNAVAILABLE)


def available(entry):
    """A button may be drawn: the file is published and its host answers."""
    return entry['status'] == 'available' and bool(entry.get('url')) and reachable(entry)


def paused(entry):
    """Published once, but its host is gone: say so instead of drawing a dead button."""
    return entry['status'] == 'available' and bool(entry.get('url')) and not reachable(entry)


NAMES = {'wallet': 'SWARM Wallet', 'node': 'SWARM Node', 'messenger': 'SWARM Messenger', 'browser': 'SWARM Browser'}
GROUPS = {'wallet': [('windows', 'Windows'), ('macos', 'macOS'), ('linux', 'Linux'), ('android', 'Android'), ('iphone', 'iPhone')],
          'node': [('windows', 'Windows'), ('macos', 'macOS'), ('linux', 'Linux')],
          'messenger': [('windows', 'Windows'), ('macos', 'macOS'), ('linux', 'Linux')],
          'browser': [('windows', 'Windows')]}


def group_entries(key, slug, chan='mainnet'):
    def match(e):
        if channel(e) != chan:
            return False
        if slug == 'android':
            return key == 'wallet' and e['product'] == 'mobile-android'
        if slug == 'iphone':
            return key == 'wallet' and e['product'] == 'mobile-ios'
        if e['product'] != key:
            return False
        return e['platform'].startswith('macOS') if slug == 'macos' else e['platform'].lower() == slug
    return [e for e in DATA['entries'] if match(e)]


def version_of(key):
    for slug, _ in GROUPS[key]:
        for e in group_entries(key, slug):
            if available(e) and e.get('version'):
                return e['version']
    return ''


def page(title, description, path, body):
    before, rest = SHELL.split('<main id="main">', 1)
    after = rest.split('</main>', 1)[1]
    before = re.sub(r'<title>.*?</title>', f'<title>{esc(title)} — SWARM</title>', before)
    for key in ['description', 'og:description', 'twitter:description']:
        before = re.sub(r'((?:name|property)="' + key + r'" content=")[^"]*', lambda m: m[1] + esc(description), before)
    before = before.replace('SWARM — Support', 'SWARM — ' + esc(title)).replace('https://swarm.green/support', 'https://swarm.green' + path)
    before = before.replace('</head>', f'<link rel="stylesheet" href="{ECO_CSS}">\n<script src="{ECO_JS}" defer></script>\n</head>')
    return before + '<main id="main">\n' + body + '\n</main>' + after


def hero(title, lead, product=False):
    crumbs = '<a href="/">Home</a><span aria-hidden="true">/</span>'
    crumbs += '<a href="/ecosystem">Ecosystem</a><span aria-hidden="true">/</span>' + esc(title) if product else 'Ecosystem'
    return f'''<section class="band band--dark band--comb page-head">
  <div class="wrap"><p class="crumbs">{crumbs}</p>
    <p class="eyebrow">THE SWARM ECOSYSTEM</p><h1>{title}</h1>
    <p class="page-head__lead">{lead}</p>
  </div>
</section>'''


# ---------------------------------------------------------------------------
# The app cards, each with its downloads. Drawn on the home page and on /ecosystem.
# ---------------------------------------------------------------------------
CARDS = [
    ('wallet', 'Your coins. Your wallet.', 'Hold, send and receive SWM, shielded or transparent. The same wallet for your computer and your phone.', 'i-wallet'),
    ('node', 'Be part of the network.', 'Run a full node, verify the chain and mine with one click, all from one app.', 'i-node'),
    ('messenger', 'Talk privately. Pay inside the chat.', 'End-to-end encrypted messaging between SWARM wallets, with your wallet built in. Sign in with your 24 words, no phone number.', 'i-message'),
    ('browser', 'Browse with your wallet built in.', 'A Windows browser without Google’s services, with the SWARM wallet in the toolbar. Its keys stay on your computer, never in the browser.', 'i-browser'),
]


def short_variant(entry, slug):
    variant = entry.get('variant') or 'Download'
    role = entry.get('role', 'primary')
    if slug == 'android':
        return 'Direct APK'
    if slug == 'macos':
        return 'Disk image (.dmg)' if role == 'primary' or variant == 'Installer' else 'ZIP archive'
    if slug == 'linux':
        return 'Debian / Ubuntu (.deb)' if 'Installer' in variant else 'AppImage'
    if slug == 'windows':
        return 'Installer (.exe)' if variant == 'Installer' else 'Portable zip'
    return variant


def mac_flavour(entry):
    platform = entry['platform']
    if entry.get('architecture') == 'universal':
        return 'Apple silicon and Intel'
    if 'Apple silicon' in platform:
        return 'Apple silicon'
    if 'Intel' in platform:
        return 'Intel'
    return ''


def home_row(key, slug, label, entries):
    name = NAMES[key]
    live = [e for e in entries if available(e)]
    primary = next((e for e in live if e.get('role') != 'alt'), live[0] if live else None)
    if primary:
        alts = [e for e in live if e is not primary]
        flavour = mac_flavour(primary) if slug == 'macos' else ''
        # A Mac group with one build per architecture: the row offers the first
        # architecture's disk image and names the other one; the ZIPs are on the app's page.
        per_arch = slug == 'macos' and len({mac_flavour(e) for e in live if mac_flavour(e)}) > 1
        if per_arch:
            alts = [e for e in alts if e.get('role') != 'alt']
        meta = ' · '.join(x for x in [short_variant(primary, slug), flavour, primary.get('version', ''), primary.get('sizeShort', '')] if x)
        get = (f'<a class="btn btn--primary btn--sm" href="{esc(primary["url"])}">Download'
               f'<span class="vh"> {esc(name)} {esc(primary.get("version", ""))} for {esc(label)}, {esc(short_variant(primary, slug))}, {esc(primary.get("sizeShort", ""))}</span>'
               f'<span aria-hidden="true"> ↓</span></a>')
        for alt in alts:
            alt_text = f'{mac_flavour(alt)} (.dmg)' if per_arch else short_variant(alt, slug)
            get += (f'<a class="textlink" href="{esc(alt["url"])}">{esc(alt_text)}'
                    f'<span class="vh"> for {esc(label)}, {esc(alt.get("sizeShort", ""))}</span></a>')
        return (f'<li class="dl-row"><span class="dl-row__os">{esc(label)}</span>'
                f'<span class="dl-row__get">{get}</span><span class="dl-row__meta">{esc(meta)}</span></li>')
    if any(paused(e) for e in entries):
        why = f'{name} for {label} is being moved to the new release repository and returns here, with the same SHA-256, as soon as it is uploaded.'
        return (f'<li class="dl-row"><span class="dl-row__os">{esc(label)}</span>'
                f'<span class="dl-row__get"><span class="pill pill--soon">Being re-published</span></span>'
                f'<span class="dl-row__note">{esc(why)}</span></li>')
    detail = next((e.get('notes') for e in entries if e.get('notes')), '')
    if slug == 'iphone':
        detail = 'On its way to the App Store.'
    return (f'<li class="dl-row"><span class="dl-row__os">{esc(label)}</span>'
            f'<span class="dl-row__get"><span class="pill pill--soon">Coming soon</span></span>'
            + (f'<span class="dl-row__note">{esc(detail)}</span>' if detail else '') + '</li>')


def card(key, title, detail, glyph):
    name = NAMES[key]
    rows = ''
    platforms = []
    for slug, label in GROUPS[key]:
        entries = group_entries(key, slug)
        if not entries:
            continue
        rows += home_row(key, slug, label, entries)
        if any(available(e) for e in entries):
            platforms.append(label)
    version = version_of(key)
    eyebrow = f'{name.upper()} · {esc(version)}' if version else name.upper()
    return f'''<article class="card ecosystem-card ecosystem-card--dl" id="get-{key}">
          <div class="ecosystem-card__top"><div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#{glyph}"/></svg></div><span class="ecosystem-tag">{esc(' · '.join(platforms))}</span></div>
          <p class="eyebrow">{eyebrow}</p><h2>{esc(title)}</h2><p>{esc(detail)}</p>
          <ul class="dl-list" aria-label="{esc(name)} downloads">{rows}</ul>
          <a class="textlink ecosystem-card__more" href="/ecosystem/{key}">Install notes and every checksum<span class="vh"> for {esc(name)}</span><span aria-hidden="true"> →</span></a>
        </article>'''


def cards():
    return ('<div class="ecosystem-grid ecosystem-grid--4" data-reveal>'
            + ''.join(card(*c) for c in CARDS) + '</div>')


def explorer_link():
    explorer = next(e for e in DATA['entries'] if e['product'] == 'explorer' and channel(e) != 'testnet')
    # The visible text is the explorer's own hostname, so the reader sees which network it opens.
    host = explorer['url'].split('//', 1)[-1].rstrip('/')
    if available(explorer):
        return f'<a class="textlink" href="{esc(explorer["url"])}">{esc(host)}<span class="vh"> (SWARM mainnet explorer)</span><span aria-hidden="true"> →</span></a>'
    return ('<span class="ecosystem-tag">Coming soon</span>'
            '<p>The mainnet explorer is being brought up at <code>mainnet.explore.swarm.green</code>. '
            'Until it opens, your own node is the authority. The public testnet explorer, '
            '<a class="textlink" href="https://testnet.explore.swarm.green/">testnet.explore.swarm.green</a>, '
            'is already running — it shows SwarmTestnet, not mainnet.</p>')


def more_links(hub):
    all_link = ('<a class="textlink" href="#downloads">Every file and checksum<span aria-hidden="true"> ↓</span></a>' if hub
                else '<a class="textlink" href="/ecosystem#downloads">Every file and checksum<span aria-hidden="true"> →</span></a>')
    return f'''<div class="ecosystem-more">
      <div><p class="eyebrow">EXPLORE</p><h2>Follow what we’re building.</h2><p class="mt-s">{all_link}</p></div>
      <div><h3>Block explorer (mainnet)</h3><p>Browse blocks and network activity on SWARM mainnet.</p>{explorer_link()}</div>
      <div><h3>Our own server</h3><p>Every file is served from SWARM’s own infrastructure, with its SHA256SUMS beside it. No third party in between.</p><a class="textlink" href="{esc(META['sourceUrl'])}" target="_blank" rel="noopener noreferrer">Source code<svg class="ext" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M6 3h7v7M13 3 4 12"/></svg><span class="vh">(opens in a new tab)</span></a></div>
    </div>'''


def signing_note():
    return ('<p class="note mt-m" data-reveal><strong>Check the SHA-256 before you install.</strong> The Windows and Linux builds are not '
            'code-signed, so Windows SmartScreen will warn: <em>More info</em> &rarr; <em>Run anyway</em>. The Mac builds of SWARM Wallet and SWARM Messenger are '
            'not signed with an Apple Developer ID: macOS asks you to allow them once under <em>System Settings</em> &rarr; '
            '<em>Privacy &amp; Security</em> &rarr; <em>Open Anyway</em>. SWARM Messenger is a first, unsigned release on every '
            'platform. SWARM Browser is an unsigned pre-release for Windows only. <strong>Android is a direct APK</strong>, debug-signed and installed by hand while the Google Play listing is '
            'pending; phones do not mine.</p>')


def testnet_note(hub):
    where = '<a href="#testnet">the Testnet section below</a>' if hub else '<a href="/ecosystem#testnet">the Testnet section of the ecosystem page</a>'
    return (f'<p class="note mt-m" data-reveal><strong>Testnet.</strong> The public testnet is still running and its builds are published in {where}. '
            'It is a different chain, its addresses start <span class="mono">swarm1…</span>, and its coins have no value.</p>')


def home_block():
    genesis = '<span class="mono">01c34428…afdd</span>'
    return f'''{MARK_START}
  <!-- Generated by tools/build_ecosystem.py from data/downloads.json. Edit the data or the tool, not this block. -->
  <section class="band band--cream" id="downloads">
    <div class="wrap"><div class="sec-head"><p class="eyebrow">THE ECOSYSTEM</p><h2>Your way into SWARM.</h2><p>Every SWARM app and every download, in one place. A wallet for your coins, a node for the network, a messenger for private conversations, a browser with the wallet built in. All builds connect to SWARM mainnet, genesis {genesis}, and every file carries a SHA-256 checksum.</p></div>
{cards()}
{more_links(False)}
{signing_note()}
{testnet_note(False)}
    </div>
  </section>
  {MARK_END}'''


# ---------------------------------------------------------------------------
# One file, with its checksum. Used on the hub, the product pages and the
# testnet sections.
# ---------------------------------------------------------------------------
def download(entry, product_name, level='h3'):
    """level is the heading tag of the file name, so the outline stays in order wherever the row is drawn."""
    platform = entry['platform']
    if paused(entry):
        return (f'<div class="download-empty"><span class="pill pill--soon">Being re-published</span>'
                f'<{level}>{esc(platform)}</{level}><p>{esc(product_name)} {esc(entry.get("version", ""))} for {esc(platform)} is being moved to the new '
                f'release repository. It returns here, with the same SHA-256, as soon as it is uploaded.</p></div>')
    if entry['status'] != 'available' or not entry.get('url'):
        # A "coming soon" card that says nothing is a dead end. When the entry
        # carries a note (why it is not here, and what is happening), print it.
        why = f'<p>{esc(entry["notes"])}</p>' if entry.get('notes') else ''
        return (f'<div class="download-empty"><span class="ecosystem-tag">Coming soon</span>'
                f'<{level}>{esc(platform)}</{level}><p>{esc(product_name)} is not available for {esc(platform)} yet.</p>{why}</div>')
    variant = entry.get('variant') or 'Download'
    suffix = ' · Apple silicon' if 'Apple silicon' in platform else ' · Intel' if 'Intel' in platform else ''
    if platform == 'Linux' and 'Installer' in variant:
        variant = 'Debian / Ubuntu (.deb)'
    if variant == 'Installer' and platform.startswith('macOS'):
        variant = 'Disk image (.dmg)'
    universal_mac = platform == 'macOS' and entry.get('architecture') == 'universal'
    if universal_mac:
        variant = 'Mac download (.dmg)' if entry.get('role') == 'primary' else 'ZIP archive (optional)'
    sha = entry.get('sha256', '')
    details = ''
    if sha:
        details = f'''<details class="dl__sum"><summary>Verify download</summary><div class="dl__sumbody">
          <p>SHA-256</p><code class="dl__hashline">{esc(sha)}</code>
          <div class="dl__sumrow"><button class="btn btn--ghost btn--sm" type="button" data-copy="{esc(sha)}">Copy<span class="vh"> checksum for {esc(variant + suffix)}</span></button>
          <a class="textlink" href="{esc(entry['checksums'])}">SHA256SUMS</a><span class="dl__bytes">{entry['sizeBytes']:,} bytes</span></div></div></details>'''
    button_label = 'Download for Mac' if universal_mac and entry.get('role') == 'primary' else 'Download'
    result = f'''<article class="download-file"><div class="download-file__row"><div><{level}>{esc(variant + suffix)}</{level}><p class="download-file__meta">{esc(entry.get('version', ''))} · {esc(entry.get('sizeShort', ''))}</p></div>
      <a class="btn btn--primary btn--sm" href="{esc(entry['url'])}">{button_label}<span class="vh"> {esc(product_name + ' ' + platform + ' ' + variant)}</span><span aria-hidden="true"> ↓</span></a></div>{details}</article>'''
    if universal_mac and entry.get('role') == 'alt':
        return '<details class="dl__sum"><summary>Prefer a ZIP archive?</summary>' + result + '</details>'
    return result


def group_block(name, entries, level='h3'):
    """The files of one platform group, or one honest panel when none can be offered."""
    if entries and not any(available(e) for e in entries) and any(paused(e) for e in entries):
        return download(next(e for e in entries if paused(e)), name, level)
    return ''.join(download(e, name, level) for e in entries if not paused(e))


# ---------------------------------------------------------------------------
# SWARM Browser: what it is, what this pre-release does not do yet, and how to
# install it. Every sentence here is checked against the build's own record
# (docs/SWARM-BROWSER-PLAN.md, docs/BROWSER-PRIVACY-AUDIT-2026-09-26.md, the
# swarm-privacy-defaults patch); a claim that cannot be checked stays out.
# ---------------------------------------------------------------------------
def browser_sections():
    def cell(glyph, title, text):
        return (f'<article class="card"><div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false">'
                f'<use href="#{glyph}"/></svg></div><h3>{title}</h3><p>{text}</p></article>')

    def step(n, app, title, text):
        return (f'<article class="card step"><div class="step__n" aria-hidden="true">{n}</div>'
                f'<p class="step__app">{app}</p><h3>{title}</h3>{text}</article>')

    what = ''.join([
        cell('i-wallet', 'The wallet is in the toolbar',
             'See your balance, receive and send SWM from the toolbar, and your history in the side panel. The keys never live '
             'in the browser: the wallet talks to a small wallet host that is installed with the browser on your computer.'),
        cell('i-eye-off', 'Google’s services taken out',
             'It is built on Chromium 153 from the ungoogled-chromium code base, which removes Google’s services: no Google API '
             'keys, no Safe Browsing lookups, no usage reports and no remote feature switches.'),
        cell('i-shield', 'Privacy defaults switched on',
             'Other sites are not told which page you came from. Client hints are not sent, and less about your system is '
             'reported to sites. WebRTC does not reveal your local network address. Link-tracking pings are off, sites are '
             'not added as search engines automatically, and <em>Always use secure connections</em> is on.'),
    ])
    limits = ''.join(f'<li><strong>{head}</strong> {text}</li>' for head, text in [
        ('Pre-release.', 'This is the first public build. Expect rough edges, and tell us what breaks.'),
        ('Unsigned.', 'Windows SmartScreen warns before the first start: choose <em>More info</em>, then <em>Run anyway</em>. '
                      'Check the SHA-256 first.'),
        ('Windows only.', '64-bit Windows on Intel or AMD. There is no macOS or Linux build yet.'),
        ('No automatic updates yet.', 'A new version is a new download from this page. Chromium publishes security fixes '
                                      'often, so check back.'),
        ('No ad or tracker blocking yet, and no phishing lists.', 'Google Safe Browsing is removed with the other Google '
                                                                  'services, so nothing warns you about a dangerous site. '
                                                                  'Be careful with links, most of all near your wallet.'),
        ('Search.', 'The default search engine is DuckDuckGo, with search suggestions off, so nothing is sent while you type. '
                    'You can choose another engine in Settings.'),
        ('Rewards.', 'A rewards page is included, but it pays nothing yet.'),
        ('Paying websites.', 'Websites cannot reach the wallet in this pre-release, so paying a site from the browser is not '
                             'part of it.'),
        ('Built by the project.', 'This build was made on the project’s own build machine.'),
    ])
    steps = ''.join([
        step(1, 'Installer or portable zip', 'Download and check',
             '<p>Download the installer or the portable zip from this page. Then compare its SHA-256 with the one under '
             '<em>Verify download</em>.</p><p class="mt-s">In Windows PowerShell, <code>Get-FileHash</code> followed by the '
             'file name shows it.</p>'),
        step(2, 'Installer or portable zip', 'Install, or unpack',
             '<p><strong>Installer:</strong> run it. When SmartScreen warns, choose <em>More info</em>, then <em>Run anyway</em>.</p>'
             '<p class="mt-s"><strong>Portable zip:</strong> unpack it to a folder of your own and start <code>chrome.exe</code> '
             'inside it; the file keeps the name it has in Chromium. The wallet host comes inside the folder.</p>'),
        step(3, 'SWARM Wallet', 'Open your wallet',
             '<p>The SWARM Wallet button is pinned beside the address bar (if it is not, pin it from the puzzle-piece icon). '
             'Create a new wallet, or restore one from its 24-word recovery phrase.</p><p class="mt-s">Write the words down on paper and keep them offline. '
             'Anyone who has them has the coins.</p>'),
    ])
    return f'''<section class="band band--dark2" aria-labelledby="browser-what">
  <div class="wrap">
    <div class="sec-head" data-reveal><p class="eyebrow">WHAT IT IS</p><h2 id="browser-what">A browser with the SWARM wallet built in.</h2>
      <p>SWARM Browser is a web browser for Windows in SWARM’s colours. The wallet inside it connects to SWARM mainnet.</p>
      <p class="mt-s"><strong>New in build 153.0.8010.52-4:</strong> DuckDuckGo is the default search engine (change it in Settings); the search box on SWARM Start and the address bar use it. Since build -3: a SWARM welcome page on the first start; SWARM Start on every new tab, with a search box, the SWARM shortcuts and tiles that ask no server anything until you switch the network tile on; the SWARM Navigator, a side panel opened from the SWARM mark beside the address bar; and SWARM’s own icons, colours and names throughout the settings and the internal pages.</p></div>
    <div class="cards" data-reveal>{what}</div>
  </div>
</section>
<section class="band band--cream" aria-labelledby="browser-limits">
  <div class="wrap wrap--narrow">
    <div class="sec-head" data-reveal><p class="eyebrow">KNOW BEFORE YOU INSTALL</p><h2 id="browser-limits">What this pre-release does not do yet.</h2>
      <p>It is useful today, and it is not finished. This is exactly where it stands.</p></div>
    <div class="prose" data-reveal><ul>{limits}</ul></div>
  </div>
</section>
<section class="band band--dark2" aria-labelledby="browser-install">
  <div class="wrap">
    <div class="sec-head" data-reveal><p class="eyebrow">INSTALL</p><h2 id="browser-install">Three steps.</h2></div>
    <div class="steps" data-reveal>{steps}</div>
  </div>
</section>'''


# ---------------------------------------------------------------------------
# The product pages: a platform picker, install notes, every file.
# ---------------------------------------------------------------------------
def product(key):
    wallet = key == 'wallet'
    messenger = key == 'messenger'
    browser = key == 'browser'
    name = NAMES[key]
    intro = ('Your wallet, wherever you are. Choose your platform to get started.' if wallet
             else 'SWARM Messenger 0.1.3 pre-release. Private messages between SWARM wallets, with payments inside the chat. Choose your platform.' if messenger
             else f'SWARM Browser {version_of(key)} pre-release for Windows. A web browser without Google’s services, with the SWARM wallet built in.' if browser
             else 'Verify the chain. Support the network. Choose your platform to start mining.')
    body = hero(name, intro, True)
    if wallet and META.get('walletUpdate'):
        update = META['walletUpdate']
        link = (f'<a class="textlink" href="{esc(update["url"])}">{esc(update["label"])} →</a>'
                if update.get('url') else '')
        body += (f'<section class="band band--cream" aria-labelledby="wallet-update-title"><div class="wrap">'
                 f'<h2 id="wallet-update-title">{esc(update["title"])}</h2><p>{esc(update["text"])}</p>'
                 f'{link}</div></section>')
    groups = GROUPS[key]
    body += '<section class="band band--cream"><div class="wrap download-layout"><div class="download-main">'
    if len(groups) > 1:
        body += '<h2>Choose your platform</h2><p class="download-intro">Find the right download for your device.</p><div class="platform-picker" data-platform-picker hidden><span class="vh" id="platform-label">Platform</span><div class="platform-options" role="group" aria-labelledby="platform-label">'
        for slug, label in groups:
            body += f'<button type="button" class="platform-choice" data-platform="{slug}" aria-controls="platform-{slug}" aria-pressed="false">{label}</button>'
        body += '</div></div>'
    else:
        # One platform: no picker, the single panel is simply shown.
        body += '<h2>Download</h2><p class="download-intro">Two ways to get the same build: an installer, or a portable zip you unpack and run.</p>'
    for slug, label in groups:
        entries = group_entries(key, slug)
        tips = {
            'windows': 'For Windows on Intel or AMD (64-bit). Windows may show a SmartScreen notice for a new publisher; check the SHA-256 below before you install.',
            'macos': ('Mac downloads and their checksums appear below. Follow the installation instructions '
                      'and signing information for the selected release.'),
            'linux': 'For Intel or AMD (64-bit). Choose .deb for Debian / Ubuntu, or AppImage for a portable download.',
            'android': ('A direct APK you install yourself; Android will ask you to allow it, and Play Protect warns that '
                        'the app is unknown because this build has never been through Play review. The Google Play '
                        'listing is pending. The APK is debug-signed, so a later Play build cannot upgrade over it.'),
            'iphone': 'The iPhone wallet is on its way to the App Store. A public download is not available yet.'}
        paused_mac = slug == 'macos' and entries and not any(available(e) for e in entries)
        if slug == 'macos' and key == 'node' and not paused_mac:
            tips[slug] = ('One Mac app for Apple silicon and Intel. Your Mac automatically runs the right version. '
                          'Signed with Developer ID and notarized by Apple. Open the disk image, drag SWARM Node '
                          'to Applications, then open it there. macOS may ask you to confirm the first launch.')
        if slug == 'macos' and wallet and any(e.get('architecture') == 'universal' for e in entries) and not paused_mac:
            tips[slug] = ('One Mac app for Apple silicon and Intel, for macOS 12 or later. Your Mac automatically runs the right version. '
                          'Signed with Developer ID and notarized by Apple. Open the disk image, drag SWARM Wallet '
                          'to Applications, then open it there. macOS may ask you to confirm the first launch.')
        if slug == 'macos' and wallet and not paused_mac and not any(e.get('architecture') == 'universal' for e in entries):
            tips[slug] = ('For macOS 12 or later. Choose Apple silicon (M1 and later) or Intel. These builds are not signed with an '
                          'Apple Developer ID and not notarized: open the disk image, drag SWARM Wallet to Applications and open it '
                          'once; macOS refuses, then allow it under System Settings → Privacy & Security → Open Anyway. '
                          'Check the SHA-256 first.')
        if paused_mac:
            tips[slug] = (f'The signed Mac build of {name} (one app for Apple silicon and Intel) is being moved to the new '
                          'release repository. It returns here, with the same SHA-256, as soon as it is uploaded.'
                          if any(paused(e) for e in entries) else
                          'The macOS mainnet build is signed and notarized on the owner’s Mac, not in CI. '
                          'That signed build is in progress.')
        if messenger:
            tips['windows'] = ('For Windows 10 or 11 on Intel or AMD (64-bit). This first release is unsigned: Windows SmartScreen '
                               'will warn (More info → Run anyway). Check the SHA-256 below before you install.')
            tips['macos'] = ('For macOS 13 or later on Apple silicon (no Intel build yet). This first release is not signed by Apple: '
                             'open the disk image, drag SWARM Messenger to Applications, then run once in Terminal: '
                             'xattr -dr com.apple.quarantine "/Applications/SWARM Messenger.app". Check the SHA-256 first.')
            tips['linux'] = 'For Intel or AMD (64-bit). Choose .deb for Debian 12+ / Ubuntu 22.04+, or the AppImage for a portable download.'
        if browser:
            tips['windows'] = ('For Windows on Intel or AMD (64-bit). This pre-release is unsigned: Windows SmartScreen '
                               'will warn (More info → Run anyway). Check the SHA-256 below before you install.')
        body += f'<section class="platform-panel" id="platform-{slug}" data-platform-panel="{slug}" aria-labelledby="heading-{slug}"><h2 id="heading-{slug}">{label}</h2><p class="platform-help">{esc(tips[slug])}</p>'
        body += group_block(name, entries) + '</section>'
    other = 'node' if wallet else 'wallet'
    aside1 = ('Keep your recovery phrase backed up somewhere safe. Never share it.' if wallet
              else 'Your 24 words are your chat identity and your wallet. Write them down and keep them offline; they never leave your computer.' if messenger
              else 'Keep the recovery phrase of the wallet in your browser backed up somewhere safe. Never share it, and never type it into a website.' if browser
              else 'Mining needs a synced node and connected peers. Allow time for the first sync.')
    aside2 = ('Mobile wallets let you send and receive. Phones do not mine.' if wallet
              else 'People find you by the username you set in Settings. There is no phone number and no phone app yet: one desktop per account.' if messenger
              else 'There are no automatic updates yet. A new version appears on this page as a new download.' if browser
              else 'Have your SWARM payout address ready. You can get one from SWARM Wallet.')
    other_q = 'Want to mine?' if wallet else 'Prefer a separate wallet app?' if browser else 'Need a wallet?'
    body += f'''</div><aside class="download-aside"><p class="eyebrow">BEFORE YOU START</p><h2>A little preparation.</h2>
      <p>{aside1}</p>
      <p>{aside2}</p>
      <a class="textlink" href="/support">Need a hand? Get support →</a>
      <div class="download-aside__other"><p>{other_q}</p><a class="textlink" href="/ecosystem/{other}">Explore SWARM {other.title()} →</a></div>
      <div class="download-aside__other"><p>Looking for another app?</p><a class="textlink" href="/ecosystem#downloads">Every SWARM download →</a></div>
      </aside></div><div class="wrap"><p class="ecosystem-note">Every build includes a SHA-256 checksum. Check it before you install, and only ever download from this site.</p></div></section>'''
    if browser:
        body += browser_sections()
    body += testnet_section([key], name)
    return page(name, intro, '/ecosystem/' + key, body)


# ---------------------------------------------------------------------------
# Testnet builds: still published, clearly labelled, never mixed with mainnet.
# ---------------------------------------------------------------------------
TESTNET_PRODUCTS = [('wallet', 'SWARM Wallet'), ('node', 'SWARM Node'), ('mobile-android', 'SWARM Wallet for Android')]


def testnet_rows(product_key):
    entries = [e for e in DATA['entries'] if channel(e) == 'testnet' and e['status'] == 'available' and e['product'] == product_key]
    live = [e for e in entries if available(e)]
    gone = [e for e in entries if paused(e)]
    name = dict(TESTNET_PRODUCTS).get(product_key)
    if not entries or not name:
        return ''
    version = next((e.get('version') for e in live if e.get('version')), next((e.get('version') for e in entries if e.get('version')), ''))
    out = f'<h3 class="testnet__app">{esc(name)} <span class="dl-all__ver">{esc(version)}</span></h3>'
    out += ''.join(download(e, name, 'h4') for e in live)
    if gone:
        platforms = sorted({e['platform'] for e in gone})
        versions = sorted({e.get('version', '') for e in gone})
        out += (f'<p class="dl-all__note">Not available at the moment: {esc(name)} {esc(", ".join(versions))} for '
                f'{esc(", ".join(platforms))}. Those testnet files were not re-published.</p>')
    return out


def testnet_section(product_keys, label):
    """The old public testnet builds, kept available and clearly marked as such.

    They connect to SwarmTestnet, whose coins have no value. They are never
    mixed into the platform panels above, so nobody can pick one up by mistake
    while looking for the mainnet download."""
    keys = []
    for key in product_keys:
        keys.append(key)
        if key == 'wallet':
            keys.append('mobile-android')
    body = ''.join(testnet_rows(k) for k in keys)
    if not body:
        return ''
    explorer = next((e for e in DATA['entries'] if e['product'] == 'explorer' and channel(e) == 'testnet'), None)
    if explorer and available(explorer):
        host = explorer['url'].split('//', 1)[-1].rstrip('/')
        body += (f'<p class="dl-all__note">Testnet explorer: <a class="textlink" href="{esc(explorer["url"])}">{esc(host)}</a> '
                 '(it shows SwarmTestnet, not mainnet).</p>')
    return f'''<section class="band band--dark2" id="testnet">
  <div class="wrap wrap--narrow">
    <p class="eyebrow">TESTNET</p>
    <h2>The public testnet is still running.</h2>
    <p>SWARM mainnet is the real network, and everything above is a mainnet build. The public testnet stays
      online for testing: it is a different chain, its addresses start <code>swarm1…</code>, and
      <strong>its coins have no value and never will</strong>. Only install one of these if you know you want
      the testnet.</p>
    <details class="dl__sum"><summary>Show the testnet downloads for {esc(label)}</summary>
      <div class="dl__sumbody">{body}</div>
    </details>
  </div>
</section>'''


# ---------------------------------------------------------------------------
# The hub: /ecosystem
# ---------------------------------------------------------------------------
def every_download():
    out = ''
    for key, title, detail, glyph in CARDS:
        name = NAMES[key]
        version = version_of(key)
        platforms = ''
        for slug, label in GROUPS[key]:
            entries = group_entries(key, slug)
            if not entries:
                continue
            platforms += f'<div class="dl-all__platform"><h4>{esc(label)}</h4>{group_block(name, entries, "h5")}</div>'
        out += f'''<section class="dl-all__product" id="downloads-{key}" aria-labelledby="dl-{key}">
      <h3 id="dl-{key}">{esc(name)} <span class="dl-all__ver">{esc(version)}</span></h3>
      <div class="dl-all__platforms">{platforms}</div>
      <a class="textlink" href="/ecosystem/{key}">Install notes for {esc(name)}<span aria-hidden="true"> →</span></a>
    </section>'''
    return out


def hub():
    body = hero('Find your place in the swarm.',
                'A wallet for your coins. A node for the network. A messenger for private conversations. A browser with the wallet built in. Every SWARM download lives here, with its checksum.')
    body += '<section class="band band--cream"><div class="wrap">' + cards() + more_links(True) + signing_note() + testnet_note(True) + '</div></section>'
    body += f'''<section class="band band--dark2" id="downloads">
  <div class="wrap">
    <div class="sec-head"><p class="eyebrow">EVERY DOWNLOAD</p><h2>Every file, with its checksum.</h2>
      <p>All mainnet builds of every SWARM app, for every platform, in one list. Open <em>Verify download</em> for the SHA-256 of a file and the release’s SHA256SUMS. The app pages add install notes and a platform picker.</p></div>
    <div class="dl-all">{every_download()}</div>
    <p class="ecosystem-note">Every build includes a SHA-256 checksum. Check it before you install, and only ever download from this site.</p>
  </div>
</section>'''
    body += testnet_section(['wallet', 'node'], 'SWARM Wallet and SWARM Node')
    return page('Ecosystem', 'Every SWARM download in one place: SWARM Wallet, SWARM Node, SWARM Messenger and SWARM Browser for Windows, macOS, Linux and Android, each with its SHA-256.', '/ecosystem', body)


def outputs():
    index = (ROOT / 'index.html').read_text(encoding='utf-8')
    if index.count(MARK_START) != 1 or index.count(MARK_END) != 1:
        sys.exit('index.html must carry exactly one ' + MARK_START + ' and one ' + MARK_END)
    head, rest = index.split(MARK_START, 1)
    tail = rest.split(MARK_END, 1)[1]
    yield 'index.html', head + home_block() + tail
    yield 'ecosystem/index.html', hub()
    for key in ['wallet', 'node', 'messenger', 'browser']:
        yield f'ecosystem/{key}/index.html', product(key)


if __name__ == '__main__':
    stale = []
    for path, content in outputs():
        content = seo.decorate(path, content)  # search title, description, structured data
        target = ROOT / path
        if '--check' in sys.argv:
            if not target.exists() or target.read_text(encoding='utf-8') != content:
                stale.append(path)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
            print(path)
    if stale:
        sys.exit('Regenerate with python tools/build_ecosystem.py: ' + ', '.join(stale))
