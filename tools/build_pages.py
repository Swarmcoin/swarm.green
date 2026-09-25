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
# Launch-day site: every page states that mainnet is live, so it must never be
# built (and therefore never deployed) with the testnet genesis in the data
# file. Local previews before launch set SWARM_ALLOW_PRELAUNCH_BUILD=1.
import os
if GENESIS.get("network") != "SwarmMainnet" and not os.environ.get("SWARM_ALLOW_PRELAUNCH_BUILD"):
    raise SystemExit("refusing to build: data/network.json genesis is %r, not SwarmMainnet. "
                     "Copy the mainnet genesis and destinations from the launch manifest first "
                     "(README: launch checklist). For a local preview only: SWARM_ALLOW_PRELAUNCH_BUILD=1."
                     % GENESIS.get("network"))


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

<p class="ribbon"><span class="dot"></span>SWARM <b>mainnet is live</b> · run a node, mine a block, send a shielded payment.</p>

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
      <a href="/roadmap">Roadmap</a>
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
        <li><a href="/roadmap">Roadmap</a></li>
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
        <p>Private, proof-of-work money run by its community. Mainnet is live.</p>
      </div>

      <nav aria-labelledby="ft-net">
        <h2 id="ft-net">Network</h2>
        <ul>
          <li><a href="/#hive">The Hive</a></li>
          <li><a href="/#honey">Honey</a></li>
          <li><a href="/#swarm">The Swarm</a></li>
          <li><a href="/network">Network &amp; supply</a></li>
          <li><a href="/roadmap">Roadmap</a></li>
        </ul>
      </nav>

      <nav aria-labelledby="ft-get">
        <h2 id="ft-get">Get started</h2>
        <ul>
          <li><a href="/join">Get SWARM</a></li>
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
      <p><strong>Open-source software, provided as is.</strong> Nothing on this site is an offer, a solicitation or financial advice. SWM has no guaranteed value and can lose value, including all of it. There is no sale and no token offering.</p>
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
    ("Code", "Proven open-source code, with consensus rules and cryptography left unmodified. Read it, build it, check it."),
    ("Ticker", "SWM"),
    ("Status", "Mainnet, live."),
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
    "Every SWARM parameter in one place: 75-second blocks, 6.25 SWM per block, halving every 1,680,000 blocks, a ceiling of 20,999,987.3152 SWM, no premine, the four-way block reward split fixed for the whole emission schedule, and the genesis block it is all fixed in.",
    "/network",
    "SWARM — Network &amp; supply",
    "75-second blocks, 6.25 coins per block, halving every 1,680,000 blocks, a ceiling of 20,999,987.3152 coins and no premine.",
) + page_head(
    "Network &amp; supply",
    "Every number, in one place.",
    "The monetary base is fixed in the code. Nothing on this page is a projection — it is arithmetic you can check yourself against the source, and against the chain in the block explorer.",
    pill="Mainnet · live",
) + f"""
  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Parameters</p>
        <h2>The rules of the hive.</h2>
      </div>
      <div class="tablewrap" data-reveal>
        <table>
          <caption>Consensus and monetary parameters, fixed in the code.</caption>
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
        <p>These are the addresses the allocations are paid to, and the genesis block they are fixed in. They are part of the network definition every node loads, so a node with different addresses rejects this chain&rsquo;s blocks and forks itself off. Compare the genesis hash below with what your node reports: if they match, you are on SWARM.</p>
        <p class="mt-s">The keys behind the three addresses were generated offline and are held under the custody policy published with the launch manifest in the <a href="{GH_SOURCE}" target="_blank" rel="noopener noreferrer">release repository{EXT}</a>.</p>
        <p class="mt-s">{esc(GENESIS["addressType"])} {esc(GENESIS["custody"])}</p>
      </div>

      <div class="tablewrap" data-reveal>
        <table>
          <caption>Allocation destinations, fixed in the genesis rules.</caption>
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
          <p>Paid block by block to its own predefined address, like the other allocations. How it is governed and spent is set out in the custody policy published with the launch manifest.</p>
        </article>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap wrap--narrow">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Next</p>
        <h2>Now run it.</h2>
        <p>Every number on this page is enforced by every node on the network. Run one and check for yourself.</p>
      </div>
      <div class="cta-row mt-l" data-reveal>
        <a class="btn btn--primary" href="/join">Get SWARM</a>
        <a class="btn btn--ghost" href="{GH}" target="_blank" rel="noopener noreferrer">Read the source{EXT}</a>
      </div>
    </div>
  </section>
""" + FOOTER
write("network/index.html", network)


# ------------------------------------------------------------------- /join
join = head(
    "Get SWARM — SWARM",
    "How to run SWARM: get the wallet, run a full node, and start CPU mining with one click. Nothing runs without your consent.",
    "/join",
    "Get SWARM",
    "Get the wallet, run a node, start foraging.",
) + page_head(
    "Get SWARM",
    "Join the swarm.",
    "Choose a wallet, run a node, and join the network. Nothing runs without you pressing the button.",
    pill="Mainnet · live",
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
          <p class="mt-s">The proof of work is Equihash and the chain started at minimum difficulty, so an ordinary computer can take part. As the network grows and difficulty rises, specialised miners can join too — nothing in the rules keeps anyone out.</p>
          <a class="btn btn--primary" href="/ecosystem/node">Start mining</a>
        </article>
      </div>

      <p class="note mt-l" data-reveal>Every app, the block explorer and the source code are listed together in <a href="/ecosystem">Ecosystem</a>.</p>

      <div class="cards cards--2 mt-l" data-reveal>
        <article class="card">
          <h3>SWARM Explorer</h3>
          <p>A block explorer, so you can watch what the chain is actually doing: blocks as they are found, the supply as it is issued, and the four-way allocation in every block.</p>
          <p class="mt-m"><a class="btn btn--ghost btn--sm" href="/ecosystem">Open the explorer{ARROW}</a></p>
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
          <p class="mt-s">Mining uses your processor and your electricity. What you earn is SWM, paid to the payout address you choose, once each reward has matured for 100 blocks.</p>
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
        <h2>Your keys, your coins.</h2>
        <p>Nobody can freeze, reverse or recover a SWARM payment for you — not us, not anyone. That is the point, and it cuts both ways: keep your recovery phrase safe, check an address before you send, and treat anyone who asks for your phrase as a thief.</p>
      </div>
      <div class="cta-row" data-reveal>
        <a class="btn btn--primary" href="/network">See the supply schedule</a>
        <a class="btn btn--ghost" href="/roadmap">What comes next</a>
      </div>
    </div>
  </section>
""" + FOOTER
write("join/index.html", join)


# ---------------------------------------------------------------- /roadmap
verify_rows = "\n".join(
    f'          <tr><th scope="row">{k}</th><td class="{cls}">{v}</td></tr>'
    for k, v, cls in [
        ("Network", esc(GENESIS["network"]), ""),
        ("Genesis block hash", esc(GENESIS["hash"]), "addr"),
        ("Genesis header time", esc(GENESIS["headerTimeUtc"]), "mono"),
        ("Spendable outputs in the genesis block", esc(GENESIS["spendableOutputs"]) + " \u2014 there is no premine", ""),
    ])

roadmap = head(
    "Roadmap — SWARM",
    "SWARM mainnet is live. What is running today, how to verify you are on the real chain, and what comes next: SWARM Market, a privacy browser and private messaging.",
    "/roadmap",
    "SWARM — Roadmap",
    "Mainnet is live. Next: SWARM Market, a privacy browser and private messaging.",
) + page_head(
    "Roadmap",
    "The money first. Then the things you do with it.",
    "SWARM mainnet is live: the coin, the chain and the apps to run them. Everything else on this page is built on top of that foundation, ships when it is finished and reviewed, and is announced here first.",
    pill="Mainnet · live",
) + f"""
  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Live today</p>
        <h2>The foundation.</h2>
      </div>
      <div class="cards" data-reveal>
        <article class="card">
          <p class="pill pill--live">Live</p>
          <h3>SWARM mainnet</h3>
          <p>Proof-of-work money with a fixed supply and shielded payments. 6.25 SWM a block, a block every 75 seconds, halving every 1,680,000 blocks, 20,999,987.3152 SWM at most. Block 1 was mined in public from a genesis block that holds nothing.</p>
        </article>
        <article class="card">
          <p class="pill pill--live">Live</p>
          <h3>SWARM Node</h3>
          <p>A full node and a miner in one app. It checks every block against the rules itself and lets you start or stop mining with one click. Windows, Linux and macOS.</p>
        </article>
        <article class="card">
          <p class="pill pill--live">Live</p>
          <h3>SWARM Wallet</h3>
          <p>Hold, send and receive SWM &mdash; shielded or transparent, your choice on every payment. Desktop and Android; the App Store and Google Play listings are next.</p>
        </article>
        <article class="card">
          <p class="pill pill--live">Live</p>
          <h3>Block explorer</h3>
          <p>Every block, every transaction, every one of the four allocations in every block reward. Public data only: it never asks for a key.</p>
        </article>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Verify it</p>
        <h2>Check you are on SWARM.</h2>
        <p>A chain is identified by its genesis block. SWARM Node compares the genesis it loads with the one below before it syncs anything; you can do the same by hand. The launch manifest, the source at the launch commit and every release with its checksum are in the <a href="{GH_SOURCE}" target="_blank" rel="noopener noreferrer">release repository{EXT}</a>.</p>
      </div>
      <div class="tablewrap" data-reveal>
        <table>
          <caption>The genesis block the rules are fixed in.</caption>
          <tbody>
{verify_rows}
          </tbody>
        </table>
      </div>
      <p class="note mt-m" data-reveal>The three destination addresses are listed with the full reward schedule on the <a href="/network">network page</a>.</p>
    </div>
  </section>

  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Next</p>
        <h2>SWARM Market.</h2>
        <p>An online marketplace where merchants list what they sell and buyers pay in SWM. Shielded by default, so a purchase is between you and the seller.</p>
      </div>
      <div class="cards" data-reveal>
        <article class="card">
          <h3>Pay from your wallet</h3>
          <p>A merchant issues an invoice: exact amount, recipient, expiry. Your wallet checks it is a real SWARM invoice for the right network before it shows you a confirmation. You pay; the seller sees the payment confirm on the chain.</p>
        </article>
        <article class="card">
          <h3>No custody</h3>
          <p>The coins go from you to the seller. The Market holds nothing on your behalf and cannot spend anything of yours. Fees, where there are any, are shown before you pay, not after.</p>
        </article>
        <article class="card">
          <h3>Nothing personal on the chain</h3>
          <p>Order details, addresses and messages between buyer and seller live off-chain, protected and deletable. The chain only ever records that a valid payment happened.</p>
        </article>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Then</p>
        <h2>A privacy browser.</h2>
        <p>A browser with the SWARM wallet built in, so paying a site is one click and no site sees more of you than it must.</p>
      </div>
      <div class="cards" data-reveal>
        <article class="card">
          <h3>Wallet built in</h3>
          <p>Pay a site or a merchant from the address bar, with the same confirmation screen as the wallet. A site can ask for a payment; it can never take one.</p>
        </article>
        <article class="card">
          <h3>Private by default</h3>
          <p>Tracking blocked, fingerprinting reduced, nothing phoning home. Each site gets only the permissions you give it, and the wallet is never one of them by default.</p>
        </article>
        <article class="card">
          <h3>Open source, like everything else</h3>
          <p>Built on a maintained open-source browser engine, with the SWARM parts published in the open. Read it, build it, check it.</p>
        </article>
      </div>
    </div>
  </section>

  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Then</p>
        <h2>Private messaging.</h2>
        <p>End-to-end encrypted messages between people who hold SWARM wallets, with payments inside the conversation.</p>
      </div>
      <div class="cards" data-reveal>
        <article class="card">
          <h3>Encrypted end to end</h3>
          <p>Only you and the person you write to can read a message. Relays carry ciphertext and the minimum needed to deliver it, and nothing is ever written to the chain.</p>
        </article>
        <article class="card">
          <h3>Pay inside the chat</h3>
          <p>Send SWM to the person you are talking to, or send them an invoice, without leaving the conversation. A message can ask for a payment; it can never spend for you.</p>
        </article>
        <article class="card">
          <h3>Keys kept apart</h3>
          <p>Your chat identity is not your spending key, and your wallet address does not publish who you talk to. You verify a contact once, and you are told if their key ever changes.</p>
        </article>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap wrap--narrow">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Always</p>
        <h2>What will never change.</h2>
      </div>
      <div class="prose" data-reveal>
        <p>No sale, presale or token offering: every SWM is mined. No premine and no hidden treasury: the 80 / 8 / 4 / 8 split is fixed in the rules and visible in every block. No promise of a price, ever. No product that takes custody of your coins behind a decentralisation claim. Nothing that runs on your machine without you pressing the button. And if this site and the code ever disagree, the code is right and the site gets fixed.</p>
      </div>
      <div class="cta-row mt-l" data-reveal>
        <a class="btn btn--primary" href="/join">Get SWARM</a>
        <a class="btn btn--ghost" href="/network">Network &amp; supply</a>
      </div>
    </div>
  </section>
""" + FOOTER
write("roadmap/index.html", roadmap)


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
          </ul>
        </article>
      </div>

    </div>
  </section>
""" + FOOTER
write("brand/index.html", brand)


# ------------------------------------------------------------------ /terms
terms = head(
    "Terms — SWARM",
    "Short, honest terms for swarm.green: an information site about open-source software and the SWARM network. Nothing here is an offer, a solicitation or financial advice.",
    "/terms",
    "SWARM — Terms",
    "An information site about open-source software and the SWARM network. Nothing here is an offer or financial advice.",
) + page_head(
    "Terms",
    "Terms.",
    "Short, and meant literally.",
) + """
  <section class="band band--cream">
    <div class="wrap wrap--narrow prose" data-reveal>
      <h2>What this site is</h2>
      <p>swarm.green is an information site about SWARM, an independent, community-run proof-of-work network. It describes software and the network. It does not host the network, run a service on your behalf, or hold anything belonging to you.</p>

      <h2>No offer, no advice</h2>
      <p>Nothing on this site is an offer or a solicitation to buy or sell anything, and nothing on it is financial, investment, legal or tax advice. There is no sale and no token offering; every SWM in existence was mined.</p>
      <p>SWM is a cryptocurrency. It has no guaranteed value, no issuer standing behind it and no price set by anyone. It can lose value, including all of it. Nobody is promising you earnings, returns or a price.</p>

      <h2>Experimental software</h2>
      <p>The node, indexer and wallet are open source, under active development, and provided as-is and without warranty of any kind. Among other things:</p>
      <ul>
        <li>The network can fork, reorganise recent blocks, or require a software upgrade. A payment is final only in the sense that the network makes it so; no fixed number of confirmations is a guarantee.</li>
        <li>Bugs may cause loss of coins, loss of data, or failure to sync.</li>
        <li>Privacy features may have defects. Shielding protects what is written to the chain; it does not protect everything about how you use a computer or a network.</li>
        <li>If you lose your recovery phrase, nobody can recover your wallet for you.</li>
      </ul>
      <p>To the fullest extent allowed by law, the SWARM contributors are not liable for any loss or damage arising from the use of this site or the software it describes.</p>

      <h2>Your own responsibility</h2>
      <p>Running a node, mining, and holding or paying with SWM use your own computer, your own electricity, your own bandwidth and your own money. Whether that is lawful, taxable and sensible where you live is yours to work out.</p>

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
