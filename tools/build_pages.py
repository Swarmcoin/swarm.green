# Emits the plain-HTML sub-pages for swarm.green.
# The output is ordinary static HTML committed to the repo; this generator only
# exists so the shared <head>, nav and footer are byte-identical on every page.
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent  # repository root
# Addresses and hashes must not exist in two places, so they are read from the
# data file, which is copied from the published network manifest. The
# baseline-miner payout address is operational, not consensus, and is not here.
GENESIS = json.loads((ROOT / "data" / "network.json").read_text(encoding="utf-8"))["genesis"]


def esc(value):
    return html.escape(str(value), quote=False)
EXT = ('<svg class="ext" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" '
       'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
       '<path d="M6 3h7v7M13 3 4 12"/></svg><span class="vh">(opens in a new tab)</span>')
ARROW = ('<svg class="ext" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
         '<path d="M3 8h10M9 4l4 4-4 4"/></svg>')
GH = "https://github.com/Swarm-Official"
# Nav and footer point at the release repository: its README lists every
# component and what it is based on. Prose references keep GH.
GH_SOURCE = "https://github.com/Swarm-Official/swarm-releases"
# Official channels, set by the owner on 2026-09-21. index.html and data/network.json carry the same values.
X_URL = "https://x.com/swarm_coin"
X_HANDLE = "@swarm_coin"
EMAIL = "swarmofficial@atomicmail.io"


def head(title, desc, path, og_title, og_desc):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://swarm.green{path}">
<meta name="theme-color" content="#0E1116">
<meta property="og:type" content="website">
<meta property="og:site_name" content="SWARM">
<meta property="og:locale" content="en">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:url" content="https://swarm.green{path}">
<meta property="og:image" content="https://swarm.green/assets/og.png?v=2">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="SWARM — Together we are strong. Private, proof-of-work money run by its community.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="{X_HANDLE}">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{og_desc}">
<meta name="twitter:image" content="https://swarm.green/assets/og.png?v=2">
<link rel="icon" href="/favicon.svg?v=2" type="image/svg+xml">
<link rel="mask-icon" href="/assets/logo-mono-dark.svg?v=2" color="#F5A623">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&family=Sora:wght@600;700;800&display=swap">
<link rel="stylesheet" href="/css/site.css?v=4">
<script src="/js/boot.js?v=4"></script>
<script src="/js/site.js?v=4" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<p class="ribbon"><span class="dot"></span><b>Mainnet</b> in preparation · the public testnet is live — test coins have no value.</p>

<header class="nav">
  <div class="wrap nav__bar">
    <a class="brand" href="/">
      <img src="/assets/logo-mark.svg?v=2" alt="" width="56" height="27">
      <span>SWARM</span>
      <span class="vh">— home</span>
    </a>
    <nav class="nav__links" aria-label="Primary">
      <a href="/#hive">The Hive</a>
      <a href="/#honey">Honey</a>
      <a href="/#swarm">The Swarm</a>
      <a href="/ecosystem">Ecosystem</a>
      <a href="/#join">Join</a>
      <a href="/mainnet">Mainnet</a>
      <a href="/#faq">FAQ</a>
      <a href="{GH_SOURCE}" target="_blank" rel="noopener noreferrer">GitHub{EXT}</a>
    </nav>
    <button class="nav__toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="navpanel">
      <span class="bars" aria-hidden="true"><i></i><i></i><i></i></span>
      <span class="vh">Menu</span>
    </button>
  </div>
  <div class="nav__panel" id="navpanel" data-nav-panel>
    <nav aria-label="Primary, compact">
      <ul>
        <li><a href="/#hive">The Hive</a></li>
        <li><a href="/#honey">Honey</a></li>
        <li><a href="/#swarm">The Swarm</a></li>
        <li><a href="/ecosystem">Ecosystem</a></li>
        <li><a href="/#join">Join</a></li>
        <li><a href="/mainnet">Mainnet</a></li>
        <li><a href="/#faq">FAQ</a></li>
        <li><a href="/network">Network &amp; supply</a></li>
        <li><a href="{GH_SOURCE}" target="_blank" rel="noopener noreferrer">GitHub</a></li>
      </ul>
    </nav>
  </div>
</header>

<main id="main">
"""


FOOTER = f"""</main>

<footer class="footer">
  <div class="wrap">
    <div class="footer__top">
      <div class="footer__brand">
        <a class="brand" href="/">
          <img src="/assets/logo-mark.svg?v=2" alt="" width="56" height="27">
          <span>SWARM</span>
        </a>
        <p>Private, proof-of-work money run by its community. Mainnet in preparation; the public testnet is live and test coins have no value.</p>
      </div>

      <nav aria-labelledby="ft-net">
        <h2 id="ft-net">Network</h2>
        <ul>
          <li><a href="/#hive">The Hive</a></li>
          <li><a href="/#honey">Honey</a></li>
          <li><a href="/#swarm">The Swarm</a></li>
          <li><a href="/network">Network &amp; supply</a></li>
          <li><a href="/#roadmap">The road to mainnet</a></li>
          <li><a href="/mainnet">Mainnet</a></li>
        </ul>
      </nav>

      <nav aria-labelledby="ft-get">
        <h2 id="ft-get">Get started</h2>
        <ul>
          <li><a href="/join">Join the swarm</a></li>
          <li><a href="/ecosystem">Ecosystem</a></li>
          <li><a href="/#faq">FAQ</a></li>
          <li><a href="{GH_SOURCE}" target="_blank" rel="noopener noreferrer">GitHub{EXT}</a></li>
        </ul>
      </nav>

      <nav aria-labelledby="ft-more">
        <h2 id="ft-more">More</h2>
        <ul>
          <li><a href="/brand">Brand</a></li>
          <li><a href="/terms">Terms</a></li>
          <li><a href="/privacy">Privacy</a></li>
        </ul>
      </nav>

      <nav aria-labelledby="ft-contact">
        <h2 id="ft-contact">Contact</h2>
        <ul>
          <li><a href="{X_URL}" target="_blank" rel="noopener noreferrer">X (Twitter){EXT}</a></li>
          <li><a href="mailto:{EMAIL}">Email</a></li>
        </ul>
      </nav>
    </div>

    <div class="footer__bottom">
      <p><strong>Experimental software. Mainnet has not launched.</strong> Today&rsquo;s downloads run on the public testnet and test coins have no value. Nothing on this site is an offer, a solicitation or financial advice; there is no sale, no token offering and no launch date. SWARM is not affiliated with or endorsed by the Electric Coin Company, the Zcash Foundation, Zingo Labs, Foursquare&rsquo;s Swarm app, or the Ethereum Swarm (BZZ) project.</p>
      <div class="row">
        <p>© 2026 SWARM contributors. Open source.</p>
        <p>swarm.green</p>
      </div>
    </div>
  </div>
</footer>

</body>
</html>
"""


def crumbs(here):
    return f'<p class="crumbs"><a href="/">Home</a><span aria-hidden="true">/</span>{here}</p>'


def page_head(here, h1, lead, pill=None):
    tag = f'<p class="pill">{pill}</p>' if pill else ""
    return f"""  <section class="band band--dark band--comb page-head">
    <div class="wrap">
      {crumbs(here)}
      {tag}
      <h1>{h1}</h1>
      <p class="page-head__lead">{lead}</p>
    </div>
  </section>
"""


def write(path, body):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    print("wrote", path)


# ---------------------------------------------------------------- /network
eras = [
    (0, "1 – 1,679,998", "6.25", "10,499,987.5", "10,499,987.5"),
    (1, "1,679,999 – 3,359,998", "3.125", "5,250,000", "15,749,987.5"),
    (2, "3,359,999 – 5,039,998", "1.5625", "2,625,000", "18,374,987.5"),
    (3, "5,039,999 – 6,719,998", "0.78125", "1,312,500", "19,687,487.5"),
    (4, "6,719,999 – 8,399,998", "0.390625", "656,250", "20,343,737.5"),
]
era_rows = "\n".join(
    f'          <tr><th scope="row" class="num">{e}</th><td class="num">{h}</td>'
    f'<td class="num">{r}</td><td class="num">{i}</td><td class="num">{c}</td></tr>'
    for e, h, r, i, c in eras)

params = [
    ("Target block time", "75 seconds"),
    ("Block reward (era 0)", "6.25 coins"),
    ("Halving interval", "1,680,000 blocks — about 4 years"),
    ("Maximum supply", "20,999,987.3152 coins"),
    ("Premine", "None. The genesis block contains no spendable coins."),
    ("Coinbase maturity", "100 blocks"),
    ("Proof of work", "Equihash 200,9, inherited unchanged. The chain starts at minimum difficulty, so it is CPU-mineable from the first block; nothing in the rules keeps larger miners out later."),
    ("Privacy", "Optional. Shielded transactions keep sender, receiver and amount encrypted on-chain, using zero-knowledge proofs."),
    ("Lineage", "Forked from open-source Zcash software — the Zebra full node, the Zaino indexer and the Zingo desktop wallet — with consensus rules and cryptography left unmodified."),
    ("Ticker", "SWM"),
    ("Status", "Mainnet in preparation. The public testnet has run these rules unchanged since 21 September 2026; test coins have no monetary value and do not carry over."),
]
param_rows = "\n".join(
    f'          <tr><th scope="row">{k}</th><td>{v}</td></tr>' for k, v in params)

split_rows = "\n".join(
    f'          <tr><th scope="row">{n}</th><td class="num">{s}</td>'
    f'<td class="num">{pb}</td><td class="num">{tot}</td></tr>'
    for n, s, pb, tot in [
        ("Miner", "80%", "5.00", "8,399,990"),
        ("Core Development", "8%", "0.50", "839,999"),
        ("Grants &amp; Ecosystem", "4%", "0.25", "419,999.5"),
        ("Community &amp; Development Reserve", "8%", "0.50", "839,999"),
    ])

# Per block, by era. Every halving halves all four amounts together.
per_block_by_era = [
    ("0", "6.25",     "5.00",   "0.50",    "0.25",     "0.50"),
    ("1", "3.125",    "2.50",   "0.25",    "0.125",    "0.25"),
    ("2", "1.5625",   "1.25",   "0.125",   "0.0625",   "0.125"),
    ("3", "0.78125",  "0.625",  "0.0625",  "0.03125",  "0.0625"),
    ("4", "0.390625", "0.3125", "0.03125", "0.015625", "0.03125"),
]
per_block_rows = "\n".join(
    f'          <tr><th scope="row" class="num">{e}</th><td class="num">{r}</td>'
    f'<td class="num">{m}</td><td class="num">{c}</td><td class="num">{g}</td>'
    f'<td class="num">{v}</td></tr>'
    for e, r, m, c, g, v in per_block_by_era)

lifetime_totals = [
    ("Miners", "16,799,990.4872"),
    ("Core Development", "1,679,998.7648"),
    ("Grants &amp; Ecosystem", "839,999.2984"),
    ("Community &amp; Development Reserve", "1,679,998.7648"),
]
lifetime_rows = "\n".join(
    f'          <tr><th scope="row">{n}</th><td class="num">{v}</td></tr>'
    for n, v in lifetime_totals)

destination_rows = "\n".join(
    f'          <tr><th scope="row">{esc(d["name"])}</th><td class="num">{esc(d["percent"])}</td>'
    f'<td class="addr">{esc(d["address"])}</td></tr>'
    for d in GENESIS["destinations"])

genesis_rows = "\n".join(
    f'          <tr><th scope="row">{k}</th><td class="{cls}">{v}</td></tr>'
    for k, v, cls in [
        ("Network", esc(GENESIS["network"]), ""),
        ("Genesis block hash", esc(GENESIS["hash"]), "addr"),
        ("Genesis header time", esc(GENESIS["headerTimeUtc"]), "mono"),
        ("Spendable outputs in the genesis block",
            esc(GENESIS["spendableOutputs"]) + " \u2014 there is no premine", ""),
    ])

network = head(
    "Network &amp; supply — SWARM",
    "Every SWARM mainnet parameter in one place: 75-second blocks, 6.25 SWM per block, halving every 1,680,000 blocks, a ceiling of 20,999,987.3152 SWM, no premine, and the four-way block reward split fixed for the whole emission schedule. Already running on the public testnet.",
    "/network",
    "SWARM — Network &amp; supply",
    "75-second blocks, 6.25 coins per block, halving every 1,680,000 blocks, a ceiling of 20,999,987.3152 coins and no premine.",
) + page_head(
    "Network &amp; supply",
    "Every number, in one place.",
    "These are the mainnet rules. The monetary base is inherited from the Zcash design and fixed in the code, and the public testnet has been running it unchanged since 21 September 2026. Nothing on this page is a projection — it is arithmetic you can check yourself against the source.",
    pill="Mainnet rules · live on the public testnet",
) + f"""
  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Parameters</p>
        <h2>The rules of the hive.</h2>
      </div>
      <div class="tablewrap" data-reveal>
        <table>
          <caption>Consensus and monetary parameters. Inherited from the upstream Zcash design and left unmodified.</caption>
          <tbody>
{param_rows}
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Emission</p>
        <h2>The first five eras.</h2>
        <p>An era is the stretch between two halvings: 1,680,000 blocks, or roughly four years at a 75-second target block time. In each era the block reward is half of what it was in the era before, which is why the total supply approaches 20,999,987.3152 coins without ever reaching it.</p>
      </div>
      <div class="tablewrap" data-reveal>
        <table>
          <caption>Coins issued per era and the running total.</caption>
          <thead>
            <tr><th scope="col" class="num">Era</th><th scope="col">Block heights</th><th scope="col">Block reward</th><th scope="col">Issued in era</th><th scope="col">Cumulative supply</th></tr>
          </thead>
          <tbody>
{era_rows}
          </tbody>
        </table>
      </div>
      <p class="note mt-m" data-reveal>Mining rewards mature after <strong>100 blocks</strong> before they can be spent. There is no premine: the genesis block contains no spendable coins, so every coin in the table above has to be mined.</p>
    </div>
  </section>

  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Reward allocation</p>
        <h2>Where every block reward goes.</h2>
        <p>Every block reward is split four ways, in the same proportions, for the whole emission schedule. Each halving reduces all four amounts together — the 80 / 8 / 4 / 8 structure never changes, all the way down to the block where the reward reaches zero. In the last eras integer rounding retires the small streams first: Grants &amp; Ecosystem rounds to zero from era 25, Core Development and the Reserve from era 26, and the miner keeps the remainder.</p>
        <p class="mt-s">The percentages are hard-coded in the genesis rules. Each allocation is paid automatically to its predefined destination address. Destinations can only be changed through a formal protocol upgrade; the percentages themselves cannot be changed. The three destinations are script addresses held by the project, and they are published together with the genesis rules.</p>
        <p class="mt-s">No premine, no hidden treasury — every allocation is visible in every block.</p>
      </div>

      <p class="rule-tag" data-reveal><b>Fixed in the genesis rules</b> for the whole emission schedule. Paid block by block as part of each block reward — not a premine.</p>

      <div class="tablewrap mt-m" data-reveal>
        <table>
          <caption>Per block in era 0 — block heights 1 – 1,679,998, at 6.25 coins per block.</caption>
          <thead>
            <tr><th scope="col">Recipient</th><th scope="col">Share</th><th scope="col">Per block (era 0)</th><th scope="col">Total in era 0</th></tr>
          </thead>
          <tbody>
{split_rows}
            <tr><th scope="row">Total</th><td class="num">100%</td><td class="num">6.25</td><td class="num">10,499,987.5</td></tr>
          </tbody>
        </table>
      </div>

      <div class="tablewrap mt-m" data-reveal>
        <table>
          <caption>Per block, by era. Every halving halves all four amounts together, so the shares stay at 80 / 8 / 4 / 8.</caption>
          <thead>
            <tr><th scope="col" class="num">Era</th><th scope="col" class="num">Block reward</th><th scope="col" class="num">Miner</th><th scope="col" class="num">Core Development</th><th scope="col" class="num">Grants &amp; Ecosystem</th><th scope="col" class="num">Reserve</th></tr>
          </thead>
          <tbody>
{per_block_rows}
          </tbody>
        </table>
      </div>

      <div class="tablewrap mt-m" data-reveal>
        <table>
          <caption>Lifetime totals (exact), across the whole emission schedule.</caption>
          <thead>
            <tr><th scope="col">Recipient</th><th scope="col">Coins</th></tr>
          </thead>
          <tbody>
{lifetime_rows}
            <tr><th scope="row">Total</th><td class="num">20,999,987.3152</td></tr>
          </tbody>
        </table>
      </div>

      <p class="note mt-m" data-reveal>Amounts are exact to the smallest unit for the first seven eras (about 28 years). After that the inherited rounding rule rounds each allocation down to a whole unit and the miner receives the remainder, which is why the lifetime miner share is fractionally above 80%.</p>

      <div class="sec-head mt-l" data-reveal>
        <p class="eyebrow">Genesis rules</p>
        <h2>The three destinations, in full.</h2>
        <p>These are the addresses the allocations are paid to on the SWARM <strong>public testnet</strong>, and the genesis block they are fixed in. They are part of the network definition every node loads, so a node with different addresses rejects this chain&rsquo;s blocks and forks itself off.</p>
        <p class="mt-s">Mainnet gets its own genesis block and fresh destination addresses, generated offline under a published custody policy and fixed into the launch rules before block 1. They will be listed here, in the same form, when they exist. <a class="textlink" href="/mainnet">What changes at mainnet</a></p>
        <p class="mt-s">{esc(GENESIS["addressType"])} {esc(GENESIS["custody"])}</p>
      </div>

      <div class="tablewrap" data-reveal>
        <table>
          <caption>Allocation destinations on the SWARM testnet. Test coins have no monetary value.</caption>
          <thead>
            <tr><th scope="col">Allocation</th><th scope="col">Share</th><th scope="col">Destination address</th></tr>
          </thead>
          <tbody>
{destination_rows}
          </tbody>
        </table>
      </div>

      <div class="tablewrap mt-m" data-reveal>
        <table>
          <caption>The genesis block these rules are fixed in.</caption>
          <tbody>
{genesis_rows}
          </tbody>
        </table>
      </div>

      <div class="cards cards--2 mt-l" data-reveal>
        <article class="card">
          <h3>At every halving</h3>
          <p>The block reward halves and the 80 / 8 / 4 / 8 split stays exactly the same. The percentages are fixed in the genesis rules and cannot be changed.</p>
          <p class="mt-s">Over the whole life of the chain that is <strong>80% to miners</strong>, <strong>8% to Core Development</strong>, <strong>4% to Grants &amp; Ecosystem</strong> and <strong>8% to the Community &amp; Development Reserve</strong>.</p>
        </article>
        <article class="card">
          <h3>The reserve</h3>
          <p>Paid block by block to its own predefined address, like the other allocations. How it is governed and spent will be defined separately and published before mainnet launches.</p>
        </article>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap wrap--narrow">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Precedent</p>
        <h2>How Zcash did it.</h2>
        <p>SWARM did not invent the idea of funding development out of the block reward. The upstream project has run three different arrangements, in public, over nearly a decade. SWARM&rsquo;s arrangement is simpler than any of them: one fixed split for the whole emission schedule.</p>
      </div>
      <div class="tablewrap" data-reveal>
        <table>
          <caption>Zcash block reward arrangements over time, for context.</caption>
          <thead>
            <tr><th scope="col">Period</th><th scope="col">Split</th></tr>
          </thead>
          <tbody>
            <tr><th scope="row">2016 – 2020</th><td>80% miners / 20% Founders&rsquo; Reward</td></tr>
            <tr><th scope="row">2020 – 2024</th><td>80% miners / 7% / 5% / 8% development fund</td></tr>
            <tr><th scope="row">2024 onward</th><td>80% miners / 8% grants / 12% lockbox</td></tr>
          </tbody>
        </table>
      </div>
      <div class="cta-row mt-l" data-reveal>
        <a class="btn btn--primary" href="/join">Join the public testnet</a>
        <a class="btn btn--ghost" href="{GH}" target="_blank" rel="noopener noreferrer">Read the source{EXT}</a>
      </div>
    </div>
  </section>
""" + FOOTER
write("network/index.html", network)


# ------------------------------------------------------------------- /join
join = head(
    "Join the swarm — SWARM",
    "How to run SWARM: get the wallet, run a full node, and start CPU mining with one click on the public testnet. The same apps carry you to mainnet. Nothing runs without your consent.",
    "/join",
    "Join the SWARM public testnet",
    "Get the wallet, run a node, start foraging. Public testnet downloads are live; test coins have no value.",
) + page_head(
    "Join",
    "Join the swarm.",
    "Choose a wallet, run a node, and join the public testnet today. Everything you learn here carries over to mainnet; the test coins do not. Nothing runs without you pressing the button.",
    pill="Public testnet · downloads live",
) + f"""
  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Step by step</p>
        <h2>Three steps. Every bee counts.</h2>
      </div>

      <div class="steps" data-reveal>
        <article class="card step">
          <div class="step__n" aria-hidden="true">1</div>
          <p class="step__app">SWARM Wallet</p>
          <h3>Get a wallet</h3>
          <p>A desktop wallet that holds your coins and sends payments — transparent or shielded, your choice on every payment.</p>
          <p class="mt-s">On first run it will show you a recovery phrase. Write it down on paper and keep it offline. It is the only way to restore your wallet.</p>
          <a class="btn btn--primary" href="/ecosystem/wallet">Choose your wallet</a>
        </article>

        <article class="card step">
          <div class="step__n" aria-hidden="true">2</div>
          <p class="step__app">SWARM Node</p>
          <h3>Run a node</h3>
          <p>One app that runs a full node: it downloads the chain, checks every block against the rules itself, and relays to its peers.</p>
          <p class="mt-s">Running a node is what makes you part of the hive. You are not trusting anyone&rsquo;s word about what the chain says — you are checking it.</p>
          <a class="btn btn--primary" href="/ecosystem/node">Get SWARM Node</a>
        </article>

        <article class="card step">
          <div class="step__n" aria-hidden="true">3</div>
          <p class="step__app">SWARM Node</p>
          <h3>Start foraging</h3>
          <p>The same app has a mining switch. Press <strong>Start</strong> and your CPU begins looking for blocks; press <strong>Stop</strong> and it stops. That is the whole interface.</p>
          <p class="mt-s">The proof of work is Equihash and the chain starts at minimum difficulty, so an ordinary computer can take part from the first block — on the testnet today and on mainnet at launch. As the network grows and difficulty rises, specialised miners can join too — nothing in the rules keeps anyone out.</p>
          <a class="btn btn--primary" href="/ecosystem/node">Start mining</a>
        </article>
      </div>

      <p class="note mt-l" data-reveal>Every app, the block explorer and the source code are listed together in <a href="/ecosystem">Ecosystem</a>.</p>

      <div class="cards cards--2 mt-l" data-reveal>
        <article class="card">
          <h3>SWARM Explorer</h3>
          <p>A block explorer, so you can watch what the chain is actually doing: blocks as they are found, the supply as it is issued, and the four-way allocation in every block. Live for the public testnet.</p>
          <p class="mt-m"><a class="btn btn--ghost btn--sm" href="https://lwd.swarm.green:8443">Open the explorer{EXT}</a></p>
        </article>
        <article class="card">
          <h3>Build it yourself</h3>
          <p>You do not have to wait for a download. The node, the indexer and the wallet are open source — read the code, build it, and check that it does what this site says it does.</p>
          <p class="mt-m"><a class="btn btn--ghost btn--sm" href="{GH}" target="_blank" rel="noopener noreferrer">Browse the source{EXT}</a></p>
        </article>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Before you start</p>
        <h2>Two things that matter.</h2>
      </div>

      <div class="cards cards--2" data-reveal>
        <article class="card">
          <div class="hexicon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" focusable="false"><rect x="4.4" y="10.4" width="15.2" height="10.2" rx="2"/><path d="M8.2 10.4V7.6a3.8 3.8 0 0 1 7.6 0v2.8"/></svg>
          </div>
          <h3>Back up your recovery phrase offline</h3>
          <p>Write the phrase down on paper and store it somewhere safe. Do not photograph it, do not put it in a password manager you do not control, and do not type it into anything that asks you to &ldquo;verify&rdquo; it on a website.</p>
          <p class="mt-s">Anyone who has the phrase has the coins. If you lose it, nobody — including us — can recover your wallet for you.</p>
        </article>
        <article class="card">
          <div class="hexicon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" focusable="false"><circle cx="12" cy="12" r="8.6"/><path d="M12 7.4v5.2l3.2 2"/></svg>
          </div>
          <h3>Mining only runs when you say so</h3>
          <p>Mining starts when you press <strong>Start</strong> and stops when you press <strong>Stop</strong>. It never starts by itself, it never runs hidden in the background, and there is no &ldquo;silent&rdquo; mode.</p>
          <p class="mt-s">Mining uses your processor and your electricity. On the testnet what you earn is test coins, which have no monetary value and do not carry over to mainnet.</p>
        </article>
      </div>

      <div class="note mt-l" data-reveal>
        <strong>What you need.</strong> These are the figures the mining app&rsquo;s own machine check looks for.
        <ul class="note__list">
          <li><strong>Windows 10 or 11, Linux or macOS, 64-bit.</strong> See <a href="/ecosystem/node">SWARM Node</a> for the builds available today.</li>
          <li><strong>2 CPU cores or more.</strong></li>
          <li><strong>4 GB of memory or more.</strong></li>
          <li><strong>10 GB of free disk</strong> for the chain. The seed node was using about 6.4 GB after its first day.</li>
          <li><strong>An internet connection.</strong></li>
          <li><strong>Port 18233 open &mdash; only if you want other nodes to be able to connect to you.</strong> Mining and syncing work without it.</li>
        </ul>
      </div>
    </div>
  </section>

  <section class="band band--cream">
    <div class="wrap wrap--narrow">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Reminder</p>
        <h2>Testnet today, mainnet next.</h2>
        <p>Test coins have no monetary value and are not converted into mainnet coins. The testnet chain may be reset without warning while the software is being built. Mainnet launches only after the gates on the road to mainnet are passed; there is no sale, no token offering and no launch date. When mainnet launches, create a fresh wallet for it rather than reusing a testnet recovery phrase.</p>
      </div>
      <div class="cta-row" data-reveal>
        <a class="btn btn--primary" href="/mainnet">The road to mainnet</a>
        <a class="btn btn--ghost" href="/network">See the supply schedule</a>
      </div>
    </div>
  </section>
""" + FOOTER
write("join/index.html", join)


# ---------------------------------------------------------------- /mainnet
same_rows = "\n".join(
    f'          <tr><th scope="row">{k}</th><td>{v}</td></tr>' for k, v in [
        ("Block reward", "6.25 SWM per block at launch, halving every 1,680,000 blocks"),
        ("Block time", "75-second target"),
        ("Maximum supply", "20,999,987.3152 SWM, fixed by the halving arithmetic"),
        ("Allocation", "80% miner · 8% Core Development · 4% Grants &amp; Ecosystem · 8% Community &amp; Development Reserve, in every block, for the whole schedule"),
        ("Premine", "None. Block 1 is the first SWM ever issued."),
        ("Coinbase maturity", "100 blocks"),
        ("Proof of work", "Equihash 200,9 with the inherited per-block difficulty rule, unchanged"),
        ("Privacy", "Shielded (Orchard) and transparent payments, chosen per payment"),
        ("Software", "The same SWARM Node and SWARM Wallet, in mainnet releases of their own"),
    ])

change_rows = "\n".join(
    f'          <tr><th scope="row">{k}</th><td>{t}</td><td>{m}</td></tr>' for k, t, m in [
        ("Genesis block", "<span class=\"mono\">045993f5&hellip;</span>, header time 21 September 2026 12:00 UTC", "A new block, derived at launch from a public, unpredictable input. Zero spendable outputs."),
        ("Balances", "Test coins, no value", "Starts empty. No testnet balance, key or address is copied across; no airdrop, no conversion."),
        ("Network identity", "SwarmTestnet: its own network magic and ports", "Its own name, magic and ports. A node on one network rejects blocks from the other."),
        ("Addresses", "Begin with <span class=\"mono\">swarm1</span>", "A distinct mainnet prefix, so a wallet can tell the two apart and refuses a cross-network payment. Testnet keeps its prefix."),
        ("Transactions", "Signed for the testnet only", "Signed for mainnet only. A transaction from one network is invalid on the other by construction, not by luck."),
        ("The three destinations", "One key each, held by the project", "Fresh keys generated offline, held on separate devices under a threshold policy, with spending and recovery tested on disposable funds. Addresses published before block 1."),
        ("Servers", "One seed server, shared by node, indexer and explorer", "Separate production hosts, more than one, with backups and monitoring. The testnet server stays as it is."),
        ("Releases", "Test builds, versioned <span class=\"mono\">-testnet.N</span>", "Separate mainnet builds with checksums and a published launch manifest. A mainnet wallet will not connect to the testnet by mistake."),
        ("The testnet itself", "Live", "Stays online after launch as the place to rehearse upgrades."),
    ])

gate_rows = "\n".join(
    f'          <tr><th scope="row" class="num">{n}</th><td>{k}</td><td>{w}</td><td>{st}</td></tr>' for n, k, w, st in [
        ("1", "One source tree", "Every platform&rsquo;s wallet and node built from one reviewed source, with the fixes from each platform merged both ways.", "In progress"),
        ("2", "Production identity", "Own genesis, network magic, ports and address prefix implemented in the node, the wallet SDK, the indexer and the apps. Negative tests: wrong network, testnet address, testnet transaction all rejected.", "In progress"),
        ("3", "Economics and mining", "Exact issuance and allocation replayed against the implementation. Difficulty behaviour measured with miners entering and leaving. On the public testnet the inherited rule reached the 75-second target in about ten hours from genesis; the remaining scenarios run on a disposable network.", "In progress"),
        ("4", "Treasury custody", "Build, sign, shield and recover a payment from each of the three destinations, with disposable keys, on a clean machine, before any real key exists.", "In progress"),
        ("5", "Services and miners", "Two production hosts in separate places, tested failover, off-site backups, alerting, and miners that restart themselves after every kind of failure we can cause.", "In progress"),
        ("6", "Independent review and soak", "External review of every change on top of upstream Zcash software, then weeks of the integrated launch candidate under normal and failure workloads.", "Not started"),
        ("7", "Keys and release ceremony", "Offline key generation for the three destinations, public addresses verified independently, recovery rehearsed, signed releases and launch manifest published.", "Not started"),
        ("8", "Launch decision", "An evidence packet for every gate above, then an explicit go. Then block 1, mined in public.", "Not started"),
    ])

mainnet = head(
    "Mainnet — SWARM",
    "The road to SWARM mainnet: what stays the same (the money), what changes (the network), how the launch is kept fair, the gates that must pass first, and what you can do now. Mainnet is in preparation; there is no launch date.",
    "/mainnet",
    "SWARM — The road to mainnet",
    "What stays the same, what changes, how the launch is kept fair, and the gates that must pass first. In preparation; no launch date.",
) + page_head(
    "Mainnet",
    "The road to mainnet.",
    "Mainnet is the SWARM network whose coins are the real SWM. It has not launched. It is being built on the code that runs the public testnet today, and everything it will run on &mdash; the rules, the addresses, the launch input &mdash; is published before block 1. This page is the whole plan, in the order it happens.",
    pill="In preparation · no launch date",
) + f"""
  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Where things stand</p>
        <h2>Testnet today. Mainnet when the gates pass.</h2>
      </div>
      <div class="cards" data-reveal>
        <article class="card">
          <p class="pill pill--live">Live</p>
          <h3>Public testnet</h3>
          <p>Running since 21 September 2026 with the final economic rules: 6.25 SWM a block, 75-second target, the 80 / 8 / 4 / 8 split paid in every block. Wallets, the one-click mining app, an Android wallet and the block explorer are public. Anyone can mine, send shielded payments, and try to break it.</p>
        </article>
        <article class="card">
          <p class="pill">Now</p>
          <h3>Mainnet engineering</h3>
          <p>Giving the production network an identity of its own so it can never be confused with the testnet, building the custody tooling for the three project destinations, preparing separate production hosts, and reconciling every platform&rsquo;s app into one reviewed source tree.</p>
        </article>
        <article class="card">
          <p class="pill pill--soon">Not yet</p>
          <h3>Review, ceremony, launch</h3>
          <p>An independent review of the changes on top of upstream Zcash software, a soak of the launch candidate under normal and failure conditions, the offline key ceremony, signed releases, a published launch manifest &mdash; and only then block 1.</p>
        </article>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">What stays the same</p>
        <h2>The money does not change.</h2>
        <p>The economic rules were settled before the public testnet launched and they carry over to mainnet unchanged. They have been running in public, block by block, since 21 September 2026 &mdash; you can check every one of them in the <a href="https://lwd.swarm.green:8443">block explorer</a> today.</p>
      </div>
      <div class="tablewrap" data-reveal>
        <table>
          <caption>Rules that are identical on the public testnet and on mainnet.</caption>
          <tbody>
{same_rows}
          </tbody>
        </table>
      </div>
      <p class="note mt-m" data-reveal>The full schedule &mdash; every era, every per-block amount, the lifetime totals and the rounding rule &mdash; is on the <a href="/network">network page</a>.</p>
    </div>
  </section>

  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">What changes</p>
        <h2>The network does.</h2>
        <p>Mainnet is a fresh network, not a renamed testnet. Nothing that exists on the testnet today is carried across, and the two are built so that they cannot be mistaken for each other by a wallet, a node or a person.</p>
      </div>
      <div class="tablewrap" data-reveal>
        <table>
          <caption>Testnet today versus mainnet at launch.</caption>
          <thead>
            <tr><th scope="col">What</th><th scope="col">Public testnet (today)</th><th scope="col">Mainnet (at launch)</th></tr>
          </thead>
          <tbody>
{change_rows}
          </tbody>
        </table>
      </div>
      <p class="note mt-m" data-reveal><strong>About the address prefix.</strong> Testnet addresses begin with <span class="mono">swarm1</span>. Mainnet uses a different, distinct prefix, which will be published with the launch manifest; the exact spelling is one of the last things fixed, so that it is never printed here and then changed. What is settled is that the two can never overlap.</p>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap wrap--narrow">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">A fair launch</p>
        <h2>How nobody gets a head start &mdash; including us.</h2>
      </div>
      <div class="prose" data-reveal>
        <h3>Genesis holds nothing</h3>
        <p>The genesis block contains no spendable coins. Block 1 is the first SWM ever issued, and it is mined by whoever is running SWARM Node at that moment. There is no allocation at genesis, no founders&rsquo; balance, no reserved supply. The 20% of every block reward that goes to the three project destinations is paid block by block, in public, and only for blocks that are actually mined.</p>

        <h3>Genesis comes from a public, unpredictable input</h3>
        <p>The genesis block is derived from an input that nobody can know in advance and everybody can check afterwards, fixed only at launch. That is what makes a private head start impossible: blocks cannot be mined before an input that does not exist yet. The exact source of that input, how it is encoded and the fallback if it fails are published with the launch procedure, and the procedure is rehearsed beforehand with substitute inputs.</p>

        <h3>Everything is published before block 1</h3>
        <p>The rules, the three destination addresses, the network identity, the source code at the launch commit, the builds with their checksums and a launch manifest that ties all of it together are public before the first block. Anyone who syncs a node checks the genesis hash against the manifest; a node that disagrees does not join the network.</p>

        <h3>You can verify it, not just read it</h3>
        <p>The block explorer shows every block and the four-way split in each one. SWARM Node checks the network&rsquo;s genesis and rules for itself before it syncs a single block. The source is open, and the numbers on this site are arithmetic you can redo against it.</p>

        <h3>What will not happen</h3>
        <p>No sale, presale or token offering. No private mining before the public launch. No airdrop or conversion of testnet coins. No exchange or listing arrangement made before launch. No promise of a price, ever. Anything presented as SWARM that offers one of these is not SWARM.</p>
      </div>
    </div>
  </section>

  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">The gates</p>
        <h2>Eight things that must be true first.</h2>
        <p>These run mostly in this order, each with evidence that is written down. Status as of 25 September 2026; this table is updated as gates pass.</p>
      </div>
      <div class="tablewrap" data-reveal>
        <table>
          <caption>The gates on the road to mainnet, and where each stands.</caption>
          <thead>
            <tr><th scope="col" class="num">#</th><th scope="col">Gate</th><th scope="col">What must be true</th><th scope="col">Status</th></tr>
          </thead>
          <tbody>
{gate_rows}
          </tbody>
        </table>
      </div>
      <p class="note mt-m" data-reveal>Weeks of soak are not proof by themselves; the scenario results are. A finding late in the list sends the affected gate back, not the whole list &mdash; but nothing launches while a critical finding is open. There is no date until gate 8, and the date follows the evidence.</p>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">What you can do now</p>
        <h2>The testnet is the rehearsal. Rehearse.</h2>
      </div>
      <div class="cards cards--2" data-reveal>
        <article class="card">
          <h3>Run it</h3>
          <p>Install <a href="/ecosystem/wallet">SWARM Wallet</a> and <a href="/ecosystem/node">SWARM Node</a>, mine a few blocks, send yourself a shielded payment, restore your wallet from its recovery phrase. Everything you learn carries over to mainnet.</p>
        </article>
        <article class="card">
          <h3>Break it</h3>
          <p>If something fails, that is what the testnet is for. Write to <a href="mailto:{EMAIL}">{EMAIL}</a> with the app version, your system and what happened. Every bug found now is one that does not touch real money later.</p>
        </article>
        <article class="card">
          <h3>Read the rules</h3>
          <p>The <a href="/network">network page</a> has every number. The specifications and the source are on <a href="{GH}" target="_blank" rel="noopener noreferrer">GitHub{EXT}</a>. If this site and the code ever disagree, the code is right and the site gets fixed.</p>
        </article>
        <article class="card">
          <h3>Follow the official channels only</h3>
          <p>This site, <a href="{GH}" target="_blank" rel="noopener noreferrer">github.com/Swarm-Official{EXT}</a>, <a href="{X_URL}" target="_blank" rel="noopener noreferrer">{X_HANDLE} on X{EXT}</a> and <a href="mailto:{EMAIL}">{EMAIL}</a>. A launch date, when there is one, appears here first. We never ask for your recovery words, your keys or a payment.</p>
        </article>
      </div>
      <div class="cta-row mt-l" data-reveal>
        <a class="btn btn--primary" href="/join">Join the public testnet</a>
        <a class="btn btn--ghost" href="/network">Network &amp; supply</a>
      </div>
    </div>
  </section>
""" + FOOTER
write("mainnet/index.html", mainnet)


# ------------------------------------------------------------------ /brand
swatches = [
    ("Honey", "#F5A623", "chip-honey", "Primary. Buttons, marks, accents on dark."),
    ("Amber deep", "#E8890C", "chip-amber", "Gradient end, deep tones."),
    ("Comb", "#FFC94D", "chip-comb", "Highlights, numbers on dark."),
    ("Pollen", "#FFE9A8", "chip-pollen", "Soft fills and notices."),
    ("Cream", "#FFF8E7", "chip-cream", "Light band background."),
    ("Hive black", "#0E1116", "chip-hive", "Dark band background."),
    ("Bark", "#161A21", "chip-bark", "Second dark band."),
    ("Wax", "#252A33", "chip-wax", "Dark surfaces and cards."),
    ("Ink", "#E6EDF3", "chip-ink", "Body text on dark."),
    ("Ink dim", "#9AA4B2", "chip-inkdim", "Secondary text on dark."),
    ("Leaf", "#3FB950", "chip-leaf", "Live and OK states, used sparingly."),
    ("Honey ink", "#8A4B03", "chip-honeyink", "The only amber that is AA-legible as text on cream."),
]
swatch_html = "\n".join(
    f"""        <div class="swatch">
          <div class="chip {cls}"></div>
          <div class="meta"><div class="nm">{name}</div><div class="hx">{hexv}</div></div>
        </div>""" for name, hexv, cls, _ in swatches)

assets = [
    ("Mark", "/assets/logo-mark.svg?v=2", "stage--light", "The mark on its own. Use at 24px wide and up."),
    ("Mark on dark", "/assets/logo-mark.svg?v=2", "stage--dark", "The same file. It works on cream and on hive black."),
    ("Full lockup", "/assets/logo-full.svg?v=2", "stage--light", "Mark plus wordmark, for headers and documents."),
    ("Mono — dark ink", "/assets/logo-mono-dark.svg?v=2", "stage--light", "One colour, for light backgrounds, print and engraving."),
    ("Mono — light ink", "/assets/logo-mono-light.svg?v=2", "stage--dark", "One colour, for dark backgrounds."),
    ("Favicon", "/favicon.svg?v=2", "stage--light", "The mark on a hive-black plate, tuned for 16px."),
]
SIZES = {"/assets/logo-full.svg?v=2": (327, 70)}
_rows = []
for name, src, stage, desc in assets:
    w, h = SIZES.get(src, (80, 80))
    _rows.append(f"""        <div class="asset">
          <div class="stage {stage}"><img src="{src}" alt="{name} logo" width="{w}" height="{h}"></div>
          <div class="nm">{name}</div>
          <p class="dc">{desc}</p>
          <p><a class="btn btn--ghost btn--sm" href="{src}" download>Download SVG</a></p>
        </div>""")
asset_html = "\n".join(_rows)

brand = head(
    "Brand — SWARM",
    "SWARM logo files, colour tokens with hex values, typography and usage rules. The SWARM mark is original artwork.",
    "/brand",
    "SWARM brand",
    "Logo files, colour tokens, typography and usage rules for the SWARM mark.",
) + page_head(
    "Brand",
    "The mark.",
    "A chevron over two eyes, in two tones of honey: the light chevron (#FBC241) and the deep amber eyes (#DB7C04). It is original artwork, drawn for this project; the vector files are traced from the original and will be refined.",
) + f"""
  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Logo files</p>
        <h2>Downloads.</h2>
        <p>All SVG, all under 2 KB. The mono names describe the ink colour, not the background: <strong>mono&nbsp;dark</strong> is dark ink for light backgrounds, <strong>mono&nbsp;light</strong> is light ink for dark ones.</p>
      </div>
      <div class="assetgrid" data-reveal>
{asset_html}
      </div>
      <p class="note mt-l" data-reveal>The wordmark in <strong>logo-full.svg</strong> is live text set in Sora 700, uppercase, with 0.08em letter-spacing, and a system sans fallback stack so the file still renders correctly where Sora is not installed. Shipping the letterforms as outlines would mean redistributing a licensed font, so the text stays text.</p>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Colour</p>
        <h2>Twelve tokens.</h2>
        <p>Ten brand colours plus two derived ones. Every value is declared as a CSS custom property on <span class="mono">:root</span> in <span class="mono">css/site.css</span>.</p>
      </div>
      <div class="swatches" data-reveal>
{swatch_html}
      </div>
      <p class="note mt-l" data-reveal><strong>Contrast.</strong> Amber is not legible as text on cream: <span class="mono">--honey</span> reaches only 2.5:1 and <span class="mono">--amber-deep</span> 2.5:1, both below the 4.5:1 that WCAG AA asks for. Use <span class="mono">--honey-ink</span> (6.4:1) for any amber text on a light background, and keep <span class="mono">--honey</span> for fills, marks and text on dark.</p>
    </div>
  </section>

  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Typography</p>
        <h2>Three faces, one job each.</h2>
      </div>
      <div class="typespec" data-reveal>
        <div>
          <p class="sample sample--display">Together we are strong.</p>
          <p class="meta">Sora — 600 / 700 / 800 — headlines, the wordmark, card titles</p>
        </div>
        <div>
          <p class="sample sample--body">One bee is small. A swarm is unstoppable. Every computer that joins makes the hive stronger.</p>
          <p class="meta">Inter — 400 / 500 / 600 — body copy, navigation, buttons</p>
        </div>
        <div>
          <p class="sample sample--mono">6.25 · 1,680,000 · 20,999,987.3152</p>
          <p class="meta">JetBrains Mono — 500 — every figure, so digits line up</p>
        </div>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Usage</p>
        <h2>Do and don&rsquo;t.</h2>
      </div>
      <div class="dodont" data-reveal>
        <article class="card">
          <h3><span class="mk mk--do" aria-hidden="true">✓</span>Do</h3>
          <ul class="prose">
            <li>Keep clear space around the mark of at least half its width.</li>
            <li>Use the mark at 24px or larger; use the favicon below that.</li>
            <li>Put the colour mark on cream or on hive black, nothing in between.</li>
            <li>Use the mono files for print, engraving and single-colour work.</li>
            <li>Say &ldquo;SWARM&rdquo; in capitals when you mean the network.</li>
          </ul>
        </article>
        <article class="card">
          <h3><span class="mk mk--dont" aria-hidden="true">✕</span>Don&rsquo;t</h3>
          <ul class="prose">
            <li>Don&rsquo;t rotate, skew, outline or add effects to the mark.</li>
            <li>Don&rsquo;t recolour it — the honey, comb and amber are the mark.</li>
            <li>Don&rsquo;t place it on a mid-tone or a busy photograph.</li>
            <li>Don&rsquo;t redraw the mark, and don&rsquo;t set the wordmark in a script face.</li>
            <li>Don&rsquo;t imply endorsement by Zcash, the Zcash Foundation, Zingo Labs, Foursquare or Ethereum Swarm.</li>
          </ul>
        </article>
      </div>

      <div class="note mt-l" data-reveal>
        <strong>On the name.</strong> SWARM has no connection to the Ethereum Swarm (BZZ) project or to Foursquare&rsquo;s Swarm app. The SWARM mark is original artwork: a chevron over two eyes in two tones of honey, with the wordmark set in Sora.
      </div>
    </div>
  </section>
""" + FOOTER
write("brand/index.html", brand)


# ------------------------------------------------------------------ /terms
terms = head(
    "Terms — SWARM",
    "Short, honest terms for swarm.green: an information site about experimental software and a network whose mainnet has not launched. Nothing here is an offer, a solicitation or financial advice.",
    "/terms",
    "SWARM — Terms",
    "An information site about experimental software. Mainnet has not launched. Nothing here is an offer or financial advice.",
) + page_head(
    "Terms",
    "Terms.",
    "Short, and meant literally.",
) + """
  <section class="band band--cream">
    <div class="wrap wrap--narrow prose" data-reveal>
      <h2>What this site is</h2>
      <p>swarm.green is an information site about SWARM, an independent, community-run proof-of-work network. It describes software, the public testnet that runs today and the mainnet that is being prepared. It does not host the network, run a service on your behalf, or hold anything belonging to you.</p>

      <h2>No offer, no advice</h2>
      <p>Nothing on this site is an offer or a solicitation to buy or sell anything, and nothing on it is financial, investment, legal or tax advice. There is no sale, no token offering and no launch date.</p>
      <p>SWARM&rsquo;s mainnet has not launched. The software available today runs on a public testnet; test coins have no monetary value, are not intended to have any, and are not converted into mainnet coins. Nobody is promising you earnings, returns, a price, or a date on which the mainnet will launch.</p>

      <h2>Experimental software</h2>
      <p>The node, indexer and wallet are experimental and under active development. They are provided as open source, as-is and without warranty of any kind. Among other things:</p>
      <ul>
        <li>The testnet chain may be reset, restarted or abandoned without notice. Mainnet launches only after the published gates are passed, and may be postponed while findings remain.</li>
        <li>Bugs may cause loss of test coins, loss of data, or failure to sync.</li>
        <li>Privacy features may have defects. Shielding protects what is written to the chain; it does not protect everything about how you use a computer or a network.</li>
        <li>If you lose your recovery phrase, nobody can recover your wallet for you.</li>
      </ul>
      <p>To the fullest extent allowed by law, the SWARM contributors are not liable for any loss or damage arising from the use of this site or the software it describes.</p>

      <h2>Your own responsibility</h2>
      <p>Running a node and mining use your own computer, your own electricity and your own bandwidth. Whether that is lawful and sensible where you live is yours to work out.</p>

      <h2>Trade marks and independence</h2>
      <p>SWARM is not affiliated with or endorsed by the Electric Coin Company, the Zcash Foundation, Zingo Labs, Foursquare&rsquo;s Swarm app, or the Ethereum Swarm (BZZ) project. Names and marks mentioned on this site belong to their respective owners and are used only to describe what SWARM is built from.</p>

      <h2>Licences</h2>
      <p>The software is open source; each repository carries its own licence. See <a href="https://github.com/Swarm-Official" target="_blank" rel="noopener noreferrer">github.com/Swarm-Official</a>.</p>

      <h2>Changes</h2>
      <p>These terms may change as the project changes. The version on this page is the current one.</p>
    </div>
  </section>
""" + FOOTER
write("terms/index.html", terms)


# ---------------------------------------------------------------- /privacy
privacy = head(
    "Privacy — SWARM",
    "swarm.green sets no cookies, runs no analytics and collects no personal data. There are no forms and no third-party scripts.",
    "/privacy",
    "SWARM — Privacy",
    "No cookies, no analytics, no personal data, no forms, no third-party scripts.",
) + page_head(
    "Privacy",
    "No cookies. No analytics. No data.",
    "This is the shortest page on the site, because there is very little to say.",
) + f"""
  <section class="band band--cream">
    <div class="wrap wrap--narrow prose" data-reveal>
      <h2>What this site collects</h2>
      <p>Nothing. This site sets no cookies, runs no analytics, uses no tracking pixels and collects no personal data. There is no contact form, no newsletter sign-up and no account to create — there is nowhere on this site to type your email address, because we did not build one.</p>

      <h2>Third parties</h2>
      <p>The only thing loaded from another origin is the web fonts, served by Google Fonts from <span class="mono">fonts.googleapis.com</span> and <span class="mono">fonts.gstatic.com</span>. Requesting a font file sends your IP address and user agent to Google, as any request to any server does. No other third-party script, frame, pixel or embed is used anywhere on this site, and the site&rsquo;s Content-Security-Policy blocks them.</p>
      <p>If you would rather not contact Google at all, the site is fully readable without the web fonts — it falls back to the fonts already on your computer.</p>

      <h2>Server logs</h2>
      <p>The site is served by a hosting provider, which may keep standard server logs — typically the requested URL, a timestamp, an IP address, a user agent and a response code — for operational and security purposes. We do not analyse them, join them to anything, or use them to build a profile of you.</p>

      <h2>If you contact us</h2>
      <p>The footer links to our X account, <a href="{X_URL}" target="_blank" rel="noopener noreferrer">{X_HANDLE}</a>, and to an email address, <a href="mailto:{EMAIL}">{EMAIL}</a>. Both are services run by other companies, outside this site. If you write to us, we receive your email address and whatever you choose to send. If you open X, X&rsquo;s own terms and privacy policy apply. Following either link is your choice, and this site passes nothing about you to them.</p>
      <p>We will never ask for your recovery words, private keys or a payment — not by email, not on X, not anywhere.</p>

      <h2>The network is separate</h2>
      <p>This is a website. It is not the SWARM network, and using it tells the network nothing about you.</p>
      <p>Separately, when you run node or wallet software on your own computer, that software talks to peers over the internet and your own network connection is visible to them in the usual way. Shielded transactions keep sender, receiver and amount encrypted on-chain, using zero-knowledge proofs — that is about what is written to the chain, and it is not a claim about your network connection or your computer.</p>

      <h2>Changes</h2>
      <p>If any of this ever changes, this page changes with it.</p>
    </div>
  </section>
""" + FOOTER
write("privacy/index.html", privacy)


# ------------------------------------------------------------------- 404
notfound = head(
    "Page not found — SWARM",
    "That page is not here. Head back to swarm.green.",
    "/404",
    "SWARM — Page not found",
    "That cell is empty.",
).replace('<link rel="canonical" href="https://swarm.green/404">', '<meta name="robots" content="noindex, follow">') + """
  <section class="band band--dark band--comb page-head">
    <div class="wrap wrap--narrow center">
      <p class="pill">Error 404</p>
      <h1>This cell is empty.</h1>
      <p class="page-head__lead mt-s">There is no block at that height. The page you asked for does not exist, or it moved while you were looking the other way.</p>
      <div class="cta-row mt-m center" data-reveal>
        <a class="btn btn--primary" href="/">Back to the hive</a>
        <a class="btn btn--ghost" href="/network">Network &amp; supply</a>
      </div>
    </div>
  </section>
""" + FOOTER
write("404.html", notfound)
