"""Generate accessible download pages from data/downloads.json. Use --check in review."""
import html
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / 'data/downloads.json').read_text(encoding='utf-8'))
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


def page(title, description, path, body):
    before, rest = SHELL.split('<main id="main">', 1)
    after = rest.split('</main>', 1)[1]
    before = re.sub(r'<title>.*?</title>', f'<title>{esc(title)} — SWARM</title>', before)
    for key in ['description', 'og:description', 'twitter:description']:
        before = re.sub(r'((?:name|property)="' + key + r'" content=")[^"]*', lambda m: m[1] + esc(description), before)
    before = before.replace('SWARM — Support', 'SWARM — ' + esc(title)).replace('https://swarm.green/support', 'https://swarm.green' + path)
    before = before.replace('</head>', '<link rel="stylesheet" href="/css/ecosystem.css?v=2">\n<script src="/js/ecosystem.js?v=1" defer></script>\n</head>')
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


def cards():
    result = '<div class="ecosystem-grid">'
    for key, label, detail, platforms, glyph in [
        ('wallet', 'Your coins. Your wallet.', 'Hold, send and receive SWM. Choose a wallet for your computer or phone.', 'Desktop &amp; mobile', 'i-wallet'),
        ('node', 'Be part of the network.', 'Run a full node, verify the chain and mine from one app.', 'Windows · macOS · Linux', 'i-node'),
        ('messenger', 'Talk privately. Pay inside the chat.', 'End-to-end encrypted messaging between SWARM wallets, with your wallet built in.', 'Windows · macOS · Linux', 'i-message')]:
        result += f'''<article class="card ecosystem-card">
          <div class="ecosystem-card__top"><div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#{glyph}"/></svg></div><span class="ecosystem-tag">{platforms}</span></div>
          <p class="eyebrow">SWARM {key.upper()}</p><h2>{label}</h2><p>{detail}</p>
          <a class="btn btn--primary" href="/ecosystem/{key}">Explore {key}<span aria-hidden="true"> →</span></a>
        </article>'''
    return result + '</div>'


def download(entry, product_name):
    platform = entry['platform']
    if entry['status'] != 'available' or not entry.get('url'):
        # A "coming soon" card that says nothing is a dead end. When the entry
        # carries a note (why it is not here, and what is happening), print it.
        why = f'<p>{esc(entry["notes"])}</p>' if entry.get('notes') else ''
        return (f'<div class="download-empty"><span class="ecosystem-tag">Coming soon</span>'
                f'<h3>{esc(platform)}</h3><p>{esc(product_name)} is not available for {esc(platform)} yet.</p>{why}</div>')
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
    result = f'''<article class="download-file"><div class="download-file__row"><div><h3>{esc(variant + suffix)}</h3><p class="download-file__meta">{esc(entry.get('version', ''))} · {esc(entry.get('sizeShort', ''))}</p></div>
      <a class="btn btn--primary btn--sm" href="{esc(entry['url'])}">{button_label}<span class="vh"> {esc(platform + ' ' + variant)}</span><span aria-hidden="true"> ↓</span></a></div>{details}</article>'''
    if universal_mac and entry.get('role') == 'alt':
        return '<details class="dl__sum"><summary>Prefer a ZIP archive?</summary>' + result + '</details>'
    return result


def product(key):
    wallet = key == 'wallet'
    messenger = key == 'messenger'
    name = 'SWARM Wallet' if wallet else 'SWARM Messenger' if messenger else 'SWARM Node'
    intro = ('Your wallet, wherever you are. Choose your platform to get started.' if wallet
             else 'Private messages between SWARM wallets, with payments inside the chat. Choose your platform.' if messenger
             else 'Verify the chain. Support the network. Choose your platform to start mining.')
    body = hero(name, intro, True)
    if wallet and DATA['meta'].get('walletUpdate'):
        update = DATA['meta']['walletUpdate']
        body += (f'<section class="band band--cream" aria-labelledby="wallet-update-title"><div class="wrap">'
                 f'<h2 id="wallet-update-title">{esc(update["title"])}</h2><p>{esc(update["text"])}</p>'
                 f'<a class="textlink" href="{esc(update["url"])}">{esc(update["label"])} →</a></div></section>')
    groups = [('windows', 'Windows'), ('macos', 'macOS'), ('linux', 'Linux')]
    if wallet:
        groups += [('android', 'Android'), ('iphone', 'iPhone')]
    body += '<section class="band band--cream"><div class="wrap download-layout"><div class="download-main"><h2>Choose your platform</h2><p class="download-intro">Find the right download for your device.</p><div class="platform-picker" data-platform-picker hidden><span class="vh" id="platform-label">Platform</span><div class="platform-options" role="group" aria-labelledby="platform-label">'
    for slug, label in groups:
        body += f'<button type="button" class="platform-choice" data-platform="{slug}" aria-controls="platform-{slug}" aria-pressed="false">{label}</button>'
    body += '</div></div>'
    for slug, label in groups:
        entries = [e for e in DATA['entries'] if channel(e) != 'testnet' and (
                   (e['product'] == key and ((slug == 'macos' and e['platform'].startswith('macOS')) or e['platform'].lower() == slug)) or
                   (wallet and slug == 'android' and e['product'] == 'mobile-android') or
                   (wallet and slug == 'iphone' and e['product'] == 'mobile-ios'))]
        tips = {
            'windows': 'For Windows on Intel or AMD (64-bit). Windows may show a SmartScreen notice for a new publisher; check the SHA-256 below before you install.',
            'macos': ('Mac downloads and their checksums appear below. Follow the installation instructions '
                      'and signing information for the selected release.'),
            'linux': 'For Intel or AMD (64-bit). Choose .deb for Debian / Ubuntu, or AppImage for a portable download.',
            'android': ('A direct APK you install yourself; Android will ask you to allow it, and Play Protect warns that '
                        'the app is unknown because this build has never been through Play review. The Google Play '
                        'listing is pending. The APK is debug-signed, so a later Play build cannot upgrade over it.'),
            'iphone': 'The iPhone wallet is on its way to the App Store. A public download is not available yet.'}
        paused_mac = slug == 'macos' and entries and all(e['status'] != 'available' for e in entries)
        if slug == 'macos' and key == 'node' and not paused_mac:
            tips[slug] = ('One Mac app for Apple silicon and Intel. Your Mac automatically runs the right version. '
                          'Signed with Developer ID and notarized by Apple. Open the disk image, drag SWARM Node '
                          'to Applications, then open it there. macOS may ask you to confirm the first launch.')
        if slug == 'macos' and wallet and any(e.get('architecture') == 'universal' for e in entries):
            tips[slug] = ('One Mac app for Apple silicon and Intel, for macOS 12 or later. Your Mac automatically runs the right version. '
                          'Signed with Developer ID and notarized by Apple. Open the disk image, drag SWARM Wallet '
                          'to Applications, then open it there. macOS may ask you to confirm the first launch.')
        if paused_mac:
            tips[slug] = ('The macOS mainnet build is signed and notarized on the owner’s Mac, not in CI. '
                          'That signed build is in progress.')
        if messenger:
            tips['windows'] = ('For Windows 10 or 11 on Intel or AMD (64-bit). This first release is unsigned: Windows SmartScreen '
                               'will warn (More info → Run anyway). Check the SHA-256 below before you install.')
            tips['macos'] = ('For macOS 13 or later on Apple silicon (no Intel build yet). This first release is not signed by Apple: '
                             'open the disk image, drag SWARM Messenger to Applications, then run once in Terminal: '
                             'xattr -dr com.apple.quarantine "/Applications/SWARM Messenger.app". Check the SHA-256 first.')
            tips['linux'] = 'For Intel or AMD (64-bit). Choose .deb for Debian 12+ / Ubuntu 22.04+, or the AppImage for a portable download.'
        body += f'<section class="platform-panel" id="platform-{slug}" data-platform-panel="{slug}" aria-labelledby="heading-{slug}"><h2 id="heading-{slug}">{label}</h2><p class="platform-help">{esc(tips[slug])}</p>'
        body += ('<div class="download-empty"><span class="ecosystem-tag">Coming soon</span><p>Apple silicon and Intel downloads appear here, with their SHA-256, once the signed build is ready.</p></div>'
                 if paused_mac else ''.join(download(e, name) for e in entries)) + '</section>'
    other = 'node' if wallet else 'wallet'
    aside1 = ('Keep your recovery phrase backed up somewhere safe. Never share it.' if wallet
              else 'Your 24 words are your chat identity and your wallet. Write them down and keep them offline; they never leave your computer.' if messenger
              else 'Mining needs a synced node and connected peers. Allow time for the first sync.')
    aside2 = ('Mobile wallets let you send and receive. Phones do not mine.' if wallet
              else 'People find you by the username you set in Settings. There is no phone number and no phone app yet: one desktop per account.' if messenger
              else 'Have your SWARM payout address ready. You can get one from SWARM Wallet.')
    body += f'''</div><aside class="download-aside"><p class="eyebrow">BEFORE YOU START</p><h2>A little preparation.</h2>
      <p>{aside1}</p>
      <p>{aside2}</p>
      <a class="textlink" href="/support">Need a hand? Get support →</a>
      <div class="download-aside__other"><p>{'Want to mine?' if wallet else 'Need a wallet?'}</p><a class="textlink" href="/ecosystem/{other}">Explore SWARM {other.title()} →</a></div>
      </aside></div><div class="wrap"><p class="ecosystem-note">Every build includes a SHA-256 checksum. Check it before you install, and only ever download from this site or the release repository.</p></div></section>'''
    body += testnet_section(key, name)
    return page(name, intro, '/ecosystem/' + key, body)


def testnet_section(key, name):
    """The old public testnet builds, kept available and clearly marked as such.

    They connect to SwarmTestnet, whose coins have no value. They are never
    mixed into the platform panels above, so nobody can pick one up by mistake
    while looking for the mainnet download."""
    entries = [e for e in DATA['entries']
               if channel(e) == 'testnet' and e['status'] == 'available'
               and (e['product'] == key or (key == 'wallet' and e['product'].startswith('mobile-')))]
    if not entries:
        return ''
    body = ''.join(download(e, name) for e in entries)
    return f'''<section class="band band--dark2" id="testnet">
  <div class="wrap wrap--narrow">
    <p class="eyebrow">TESTNET</p>
    <h2>The public testnet is still running.</h2>
    <p>SWARM mainnet is the real network, and everything above is a mainnet build. The public testnet stays
      online for testing: it is a different chain, its addresses start <code>swarm1…</code>, and
      <strong>its coins have no value and never will</strong>. Only install one of these if you know you want
      the testnet.</p>
    <details class="dl__sum"><summary>Show the testnet downloads for {esc(name)}</summary>
      <div class="dl__sumbody">{body}</div>
    </details>
  </div>
</section>'''


def outputs():
    explorer = next(e for e in DATA['entries'] if e['product'] == 'explorer')
    # The visible text is the explorer's own hostname, so the reader sees which network it opens.
    explorer_host = explorer['url'].split('//', 1)[-1].rstrip('/')
    explorer_link = (f'<a class="textlink" href="{esc(explorer["url"])}">{esc(explorer_host)} →</a>'
                     if explorer['status'] == 'available' and explorer.get('url')
                     else '<span class="ecosystem-tag">Coming soon</span>'
                          '<p>The mainnet explorer is being brought up at <code>mainnet.explore.swarm.green</code>. '
                          'Until it opens, your own node is the authority. The public testnet explorer, '
                          '<a class="textlink" href="https://testnet.explore.swarm.green/">testnet.explore.swarm.green</a>, '
                          'is already running — it shows SwarmTestnet, not mainnet.</p>')
    overview = hero('Find your place in the swarm.', 'A wallet for your coins. A node for the network. A messenger for private conversations. Choose what you want to do.')
    overview += '<section class="band band--cream"><div class="wrap">' + cards()
    overview += f'''<div class="ecosystem-more"><div><p class="eyebrow">EXPLORE</p><h2>Follow what we’re building.</h2></div>
      <div><h3>Block explorer</h3><p>Browse blocks and network activity.</p>{explorer_link}</div>
      <div><h3>Open source</h3><p>Find releases, checksums and component links.</p><a class="textlink" href="https://github.com/Swarm-Official/swarm-releases">Explore on GitHub →</a></div></div>
      <p class="ecosystem-note">SWARM mainnet is live. SWARM Node, SWARM Wallet and SWARM Messenger are available for Windows, Linux and
      macOS today, each with its SHA-256. SWARM Messenger is a first, unsigned desktop release: sign in with your 24 words, no phone number. Both Mac apps are signed and notarized. SWARM Node and SWARM Wallet each offer one
      Mac download for Apple silicon and Intel. The Android wallet is a direct APK with its own
      SHA-256: you install it by hand while the Google Play listing is pending. The public testnet builds are still
      published, in the Testnet section of each app page.</p></div></section>'''
    yield 'ecosystem/index.html', page('Ecosystem', 'Explore SWARM Wallet, SWARM Node and SWARM Messenger. Choose your app and platform.', '/ecosystem', overview)
    for key in ['wallet', 'node', 'messenger']:
        yield f'ecosystem/{key}/index.html', product(key)


if __name__ == '__main__':
    stale = []
    for path, content in outputs():
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
