# swarm.green

The marketing site for **SWARM** — an independent, community-run, proof-of-work
cryptocurrency network with optional shielded transactions, built by forking
open-source Zcash software (the Zebra full node, the Zaino indexer and the Zingo
desktop wallet) with consensus rules and cryptography left unmodified.

**Status: testnet only. Test coins have no monetary value.**

---

## What this is

Plain HTML, CSS and vanilla JavaScript. No build step, no bundler, no npm
dependencies, no framework. What is in the repository is exactly what gets
served. Deployed as a static site on Vercel.

There is no analytics, no cookie banner, no tracking pixel and no form that
collects anything. The only third-party origin used anywhere is Google Fonts.

## File tree

```
.
├── index.html                 Home
├── network/index.html         Parameters, era table, reward allocation
├── join/index.html            Step-by-step guide (apps are "coming soon")
├── brand/index.html           Logo downloads, colour, type, do/don't
├── terms/index.html
├── privacy/index.html
├── 404.html
│
├── css/site.css               All styling. Design tokens live at the top.
├── js/boot.js                 3 lines: marks <html class="js"> before paint
├── js/site.js                 Nav, reveal, privacy switch, downloads, charts
├── js/map.js                  "The swarm" heat map, lazily initialised
├── js/vendor/                 Two third-party files, with their licences
│   ├── topojson-client.min.js topojson-client 3.1.0 (ISC, Mike Bostock)
│   ├── geo-natural-earth1.js  Natural Earth projection, derived from d3-geo
│   ├── topojson-client.LICENSE
│   └── d3-geo.LICENSE
│
├── data/network.json          ← every number on the site comes from here
├── data/downloads.json        ← the download area, product by product
├── data/swarm-map.json        ← the nodes that appear on the map
├── data/world-110m.json       Land geometry for the map (built, see below)
│
├── assets/
│   ├── logo-mark.svg          The hive bee on its own
│   ├── logo-full.svg          Mark + "SWARM" wordmark
│   ├── logo-mono-dark.svg     Single colour, dark ink (for light backgrounds)
│   ├── logo-mono-light.svg    Single colour, light ink (for dark backgrounds)
│   ├── comb.svg               Hexagon tile used as a CSS background
│   ├── og.svg                 Source for the social preview image
│   └── og.png                 1200×630 social preview, rendered from og.svg
├── favicon.svg                The mark on a warm-black plate, tuned for 16px
│
├── site.webmanifest
├── robots.txt
├── sitemap.xml
├── vercel.json                cleanUrls, trailingSlash, security headers
└── tools/
    ├── preview.mjs            Zero-dependency local server (see below)
    ├── build_pages.py         Generates the sub-pages (see below)
    ├── build_map_data.mjs     Generates data/world-110m.json (see below)
    └── world-atlas-110m.src.json   Natural Earth source for that build
```

## Preview locally

The site uses clean folder URLs (`/network`, not `/network/index.html`), so a
naive static server will 404 on internal links. `tools/preview.mjs` mirrors the
two Vercel settings in `vercel.json` exactly:

```bash
node tools/preview.mjs          # http://localhost:4173
node tools/preview.mjs 8080     # or pick your own port
```

It has no dependencies — it is a single file using only `node:http` and
`node:fs`. `npx --yes serve -l 4173 .` also works, but it redirects
`/network/` rather than serving `/network` directly.

## Editing the numbers — `data/network.json`

`data/network.json` is the single source of truth for every figure on the site
and for the reward split. `js/site.js` fetches it and renders:

| What | Rendered into |
|---|---|
| `stats[]` | the five metric cards in the hero |
| `chain` + `eras[]` | the emission curve on the home page |
| `rewardSplit.shares[]` | the hexagon split ring **and** its legend |
| `rewardSplit.perBlockByEra[]` | the "Per block, by era" mini table under the emission chart |
| `rewardSplit.lifetimeTotals` | the lifetime totals table on `/network` (static there) |

Each entry in `rewardSplit.shares[]` looks like this:

```jsonc
{
  "key": "reserve",
  "name": "Community & Development Reserve",
  "share": 0.08,        // fraction of the block reward; the ring is drawn from this
  "percent": "8%",      // the label shown in the legend
  "perBlock": 0.5,      // coins per block in era 0, shown in the legend
  "era0Total": 839999,  // coins over the whole of era 0
  "color": "#A89F92",   // the colour of this arc of the hexagon ring
  "desc": "..."         // one sentence under the name in the legend
}
```

The `share` values should add up to `1`. The ring is drawn by walking the
perimeter of a hexagon, so any set of shares works.

`rewardSplit.perBlockByEra[]` holds one row per era with `reward`, `miner`,
`core`, `grants` and `reserve`. Each row must add up to that era's `reward`, and
each value must be exactly its `share` of it. `rewardSplit.lifetimeTotals` holds
the exact lifetime figures; they must add up to `chain.maxSupply`.

### Two things to keep in step

1. **Static fallbacks.** Every JSON-driven block is also written out as plain
   HTML inside its container, so the page is complete and correct with
   JavaScript disabled and for crawlers that do not run scripts. JavaScript
   replaces those elements when it loads. If you change a number in the JSON,
   change the matching static text too:
   - hero stat cells — `index.html`, `<div class="stats" data-stats>`
   - split legend — `index.html`, `<ul class="legend" data-legend-split>`
   - per-era mini table — `index.html`, `<tbody data-ladder>`
   - era figures — `index.html` (`.chart-fallback`) and the tables in
     `network/index.html`
   - download cards — `index.html` and `tools/build_pages.py`, `[data-downloads]`
   - the map's figures and its table — `index.html`, `[data-map-root]`

2. **`network/index.html` tables are hand-written**, not generated. They carry
   the full era and split breakdown. Keep them consistent with the JSON. The
   one exception is the "The genesis rules" block, which `tools/build_pages.py`
   reads straight out of `data/network.json` — see below.

### The genesis rules block

`network.genesis` in `data/network.json` is copied from
`network/swarm-testnet/manifest.json`, the published network definition. It
holds the genesis block hash, the header time, the funding range and the three
destination addresses. `tools/build_pages.py` loads the JSON and renders the two
tables on `/network` from it, so no address or hash is ever typed into HTML by
hand. To change one, edit the JSON and regenerate.

The destinations are described exactly this way, and no further:

> The three destinations are script addresses held by the project, and they are
> published together with the genesis rules.

On the testnet each of those scripts is a pay-to-script-hash address whose
redeem script needs **one** key, held by the project — so the site says "script
addresses", never "multisignature". How keys are generated, held and used is not
decided; the page says it will be written down and published before any mainnet.

### `data/downloads.json` — the download area

One `products[]` entry per app and one `entries[]` row per app-and-platform,
with `status` (`coming-soon` or `available`), `version`, `platform`, `url`,
`sha256`, `size` and `notes`. `js/site.js` renders it into every
`[data-downloads]` block, on the home page and on `/join`.

While every row for a product is `coming-soon` the card shows the platform line
and one disabled **Coming soon** button. Flip a row to `available` and give it a
`url`, and that row becomes a real download link with its version, its size and
its SHA-256 with a copy button — plus, for Windows, the standing notice from
`meta.windowsNotice` that the testnet build is not code-signed. **Going live is
a data change, not an HTML edit.** The static markup in `index.html` and in
`tools/build_pages.py` is the no-JavaScript fallback and must say the same thing
as the data.

### `data/swarm-map.json` — the map

```jsonc
{
  "updated": "2026-09-21T00:00:00Z",
  "source":  "Operated by the SWARM project",
  "note":    "...",
  "nodes": [ { "city": "Dallas", "country": "US", "lon": -96.80, "lat": 32.78, "count": 1 } ]
}
```

This file is **not a census of the network**. It lists only nodes that share a
location, never finer than a city, and sharing will be opt-in in SWARM Node,
which is not published yet. The page says all of that in plain words, and the
map's own caption says so too. Today there is exactly one entry: the project's
own public seed node. Never put a figure in here that nobody can check.

### `network.live` in `data/network.json` — the running testnet

The endpoints that are actually up: the seed node, the wallet server and the
date the first blocks were mined. `tools/build_pages.py` renders them into
"Connecting" on `/network` and into step 2 and 3 of "Test it yourself" on
`/join`.

Two rules for this block:

- **No block height, ever.** A height on a static page is wrong within seconds.
  Dates and endpoints stay true; counters do not.
- **The explorer is not deployed.** `explore.swarm.green` points elsewhere
  today, so nothing on the site links to it. It is named in plain text as
  *planned*, never as an anchor, and `/network` says so in the same table.

### Wording the allocation is committed to

The four-way allocation is **decided**, and it runs for the **whole emission
schedule** — not for the first four years, and it does not end at the first
halving:

> 80% Miner · 8% Core Development · 4% Grants & Ecosystem · 8% Community &
> Development Reserve

The percentages are hard-coded. Every halving reduces all four amounts
proportionally and keeps the same 80 / 8 / 4 / 8 structure, until block rewards
reach zero. Each allocation is paid automatically to its own predefined
destination address; destinations can only be changed by a formal protocol
upgrade, and the percentages themselves cannot be changed at all.

Wherever the split appears it carries the label **"Fixed in the genesis rules
for the whole emission schedule. Paid block by block as part of each block
reward — not a premine."** (`.rule-tag`). Keep it.

Three things the site must never say:

- Do **not** say the split applies only until the first halving, only for the
  first four years, that it "ends", or that 100% goes to miners afterwards.
  Older drafts said this and it is wrong.
- Do **not** describe the Community & Development Reserve as keyless, held by
  the protocol with no keys, unspendable, or releasable only by a network
  upgrade. How it is governed and spent is not decided yet. The one approved
  description is: *"Paid block by block to its own predefined address, like the
  other allocations. How it is governed and spent will be defined separately and
  published before any mainnet."*
  It **is** accurate and approved to say that all three destinations are
  multisignature addresses held by the project and that they will be published
  with the genesis rules; that sentence is on `/network`. Do not go beyond it into
  custody details, which are not decided.
- The word *lockbox* appears on this site in exactly one place: the Zcash
  history table on `/network`, where it is Zcash's own term for Zcash's own
  arrangement. Do not use it for SWARM.

Mining wording is also deliberate: SWARM is open to ordinary computers from the
first block, and on the testnet the proof of work is CPU-mineable — but the site
does not promise that home computers stay competitive forever, and it says
plainly that specialised miners can join as difficulty rises.

## Official channels

Set by the owner on 2026-09-21. The site links out to exactly three places:

| Channel | Address |
| --- | --- |
| X (Twitter) | https://x.com/swarm_coin (`@swarm_coin`) |
| Email | `swarmofficial@atomicmail.io` |
| Source | https://github.com/brs-holding |

The values live in three places that must stay in step: the constants `X_URL`,
`X_HANDLE` and `EMAIL` at the top of `tools/build_pages.py` (shared footer,
`twitter:site` meta tag and the "If you contact us" section of `/privacy`),
`index.html` by hand (same footer column, the meta tag and the FAQ entry "How
do I reach the project?"), and `links` in `data/network.json`.

These are plain links, not embeds: no X widget, no follow button script and no
contact form, all of which the CSP would block anyway. External links carry
`rel="noopener noreferrer"`, so the site passes nothing to X. The footer label
for the mailbox is the word "Email" because the full address does not fit the
footer column; the address is printed in full in the FAQ and on `/privacy`.

Wording that goes with the channels and should stay: *"We will never ask for
your recovery words, private keys or a payment — not by email, not on X, not
anywhere."*

## Constraints the site is built to

These are not stylistic preferences; breaking them breaks the site.

- **No inline scripts, no inline event handlers, no `style=""` attributes.**
  The Content-Security-Policy in `vercel.json` sets `script-src 'self'` and
  `style-src 'self' https://fonts.googleapis.com`, with no `'unsafe-inline'`.
  Anything inline is silently dropped by the browser. Colour that has to come
  from data is applied through SVG `fill` presentation attributes instead.
- **Only two external origins**, both Google Fonts (Sora, Manrope and JetBrains Mono):
  `fonts.googleapis.com` (the stylesheet) and `fonts.gstatic.com` (the font
  files). Nothing else is allowed by the CSP.
- **No raster images in the design.** Every mark, icon, chart and background
  pattern is SVG or canvas. `assets/og.png` is the one exception and it is only
  ever fetched by social-media crawlers, never by the page.
- **No claims about money.** No earnings, returns, price, "fair launch", or
  privacy absolutes. Privacy is described exactly one way: *"shielded
  transactions keep sender, receiver and amount encrypted on-chain, using
  zero-knowledge proofs."*
- **Downloads are disabled buttons**, never links to nothing.

## Design tokens

The site follows the **SWARM Style Guide v2**. All colours are CSS custom
properties on `:root` in `css/site.css`, and the `/brand` page renders them with
their hex values.

| Group | Tokens |
|---|---|
| Surfaces | `--void #0A0908`, `--base #100E0C`, `--surface #171411`, `--surface2 #1F1B17`, `--flat #0C0B09` |
| Text | `--text #F5EFE4`, `--text-2 #D9D1C4`, `--text-3 #A89F92`, `--text-4 #7D746A`, `--text-5 #6B645A`, `--text-6 #544E45` |
| Accents | `--orange #FF8A1F` (brand + shielded), `--honey #FFB020`, `--honey-lt #FFD08A`, `--blue #6FB6FF` (transparent/revealed **only**), `--green #3DD68C`, `--red #FF5C5C` |

There is one dark theme. The old cream band is gone, so nothing re-declares
`--fg`; `.band--tint` is a slightly lighter panel and `.band--line` adds a
hairline above a section.

**Contrast rule.** On `--void`, `--text` is 17.4:1, `--text-2` 13.1:1 and
`--text-3` 7.6:1; `--orange` is 8.4:1 and `--honey` 10.9:1, so both are legible
as text on dark. The two dimmest tones in the guide, `--text-4` (4.3:1) and
`--text-5` (3.2:1), are **below** the 4.5:1 WCAG AA asks for at body sizes.
They are kept as tokens for hairlines, dividers, icon ghosts and disabled
controls, and are never used for prose, labels or numbers. `--text-3` is the
dimmest tone allowed to carry meaning. `/brand` states this in public.

Clear Blue is reserved: it appears only where privacy is switched off, so a
visible transaction never looks like a normal one.

## Motion

Motion comes from the guide's three verbs: **hover** (the bee floats, its wings
beat), **shield** (values fold into hex masks) and **flow** (light runs along
the top edge of a metric card, and around the map frame, when something lands).
All of it is CSS keyframes — there is no animation JavaScript.

Under `prefers-reduced-motion: reduce` every animation and transition is
switched off in one block at the bottom of `css/site.css`, scroll reveals are
forced visible, the shimmering headline falls back to solid Hive Orange, and
`js/map.js` never draws the pulsing ring. The wings keep their resting angle
because it rides on an SVG `transform` presentation attribute, which the CSS
animation overrides only while it is running.

## The logo

The mark is the guide's **hive bee**: a hexagonal body — one cell of the hive —
with two stripes and two honey elliptical wings. Symmetric, frontal, geometric.
The guide's don'ts are load-bearing: no tilt, no face, no gradients inside the
mark, and SWARM is only ever set in Sora.

The stripes are **cut out** of the body with the even-odd fill rule rather than
painted in the background colour, so a single file works on warm black, on wax,
on orange or on a photograph, and the mono variants fall out of the same
geometry.

It is deliberately unlike the Foursquare Swarm app's mark (a rounded
side-profile bee with leaf-shaped wings and a hand-script wordmark) and is not
derived from it in any way.

The wordmark in `logo-full.svg` is live `<text>` set in Sora 700, uppercase,
with a system sans fallback stack and a pinned `textLength` so the lockup is the
same width either way. It is not converted to outlines on purpose: shipping
outlines of a fallback system font would mean redistributing a licensed
typeface.

## "The swarm" map

`js/map.js` draws the heat map in `#swarm` on the home page. It is lazily
initialised: an `IntersectionObserver` waits until the section is within 300px
of the viewport, then injects the two vendor scripts and fetches the geometry.
A visitor who never scrolls that far downloads none of it.

- **Projection.** `js/vendor/geo-natural-earth1.js` is a small module with the
  Natural Earth polynomial, a path builder, a graticule and a sphere outline. It
  is derived from d3-geo (ISC) and credits it; d3-geo plus d3-array would be
  about 46 KB minified to reach one projection, which is most of the site's
  whole JavaScript budget.
- **Geometry.** `data/world-110m.json` is built by `tools/build_map_data.mjs`
  from the committed Natural Earth source. It keeps only the merged `land`
  object and **cuts the three rings that cross the antimeridian** — Russia, Fiji
  and Antarctica — so the browser needs no clipping code at all. Drawn without
  that cut, those rings smear a bar across the whole map. Rebuild with
  `node tools/build_map_data.mjs`.
- **Accessibility.** Hotspots are focusable `<g role="button">` elements with an
  `aria-label`; the tooltip is built from SVG and positioned with a `transform`
  attribute, so no style attribute is ever written. The same data is in a table
  under the map, visually hidden when JavaScript is running and plainly visible
  when it is not.

## Verifying a change

Beyond the checks in "Constraints" below, two are easy to get wrong:

- **Phone widths.** Headless Chrome's `--window-size` cannot go below about
  500px on Windows and produces misleading clipped screenshots. Measure with
  CDP `Emulation.setDeviceMetricsOverride`, or assert
  `documentElement.scrollWidth === documentElement.clientWidth` at 360, 390,
  768, 1280 and 1920.
- **Regeneration.** `python tools/build_pages.py` must reproduce the committed
  sub-pages byte for byte. Run it twice and diff before committing.

Total JavaScript, including the vendored map code, is about **45 KB**. Treat
120 KB as the ceiling.

`assets/og.png` is rendered from `assets/og.svg` by a headless browser. To
regenerate it after editing the SVG:

```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new \
  --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
  --screenshot=assets/og.png --window-size=1200,630 \
  "file:///absolute/path/to/assets/og.svg"
```

## Deploying

Vercel, as a static site. No framework preset, no build command, no output
directory — the repository root is the site. `vercel.json` supplies
`cleanUrls`, `trailingSlash: false` and the security headers (CSP, nosniff,
referrer policy, `X-Frame-Options: DENY`, and a `Permissions-Policy` that turns
off camera, microphone and geolocation).

## Independence

SWARM is not affiliated with or endorsed by the Electric Coin Company, the Zcash
Foundation, Zingo Labs, Foursquare's Swarm app, or the Ethereum Swarm (BZZ)
project.

## Go-live checklist (swarm.green production)

swarm.green is **live**, served from `main`, and `vercel.json` already sets
`X-Robots-Tag: index, follow`. Do not change that header.

Anything that is not yet approved goes on a branch and is shown to the owner as
a Vercel **preview** deployment:

```bash
npx --yes vercel@latest deploy --yes     # never --prod
```

Before a branch is merged into `main`:

1. Owner approves the content, the logo and the wording of the reward allocation.
2. Every internal link and asset returns 200 through `node tools/preview.mjs`.
3. No inline script, style block or `style=""` in any HTML or SVG.
4. Every `data/*.json` parses, and the allocation arithmetic still adds up.
5. `python tools/build_pages.py` reproduces the committed sub-pages with no diff.
6. `scrollWidth === clientWidth` at 360, 390, 768, 1280 and 1920.
7. The no-JavaScript and `prefers-reduced-motion` paths both render the full page.
8. Check the live headers (CSP, HSTS without `includeSubDomains`), every route,
   and the social preview image.

## Regenerating the sub-pages

`/network`, `/join`, `/brand`, `/terms`, `/privacy` and `404.html` are produced by `tools/build_pages.py` (plain Python, no dependencies) so that their shared navigation and footer stay identical. `index.html` is maintained by hand. Run `python tools/build_pages.py` from anywhere; it writes into the repository root. Review the diff before committing: a regeneration must never drop reviewed wording. `tools/`, `_review/` and this README are excluded from deployment by `.vercelignore`.
