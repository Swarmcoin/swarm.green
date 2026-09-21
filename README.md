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
├── js/site.js                 Nav, reveal, hero canvas, charts (~16 KB)
├── data/network.json          ← every number on the site comes from here
│
├── assets/
│   ├── logo-mark.svg          The hex-bee on its own
│   ├── logo-full.svg          Mark + "SWARM" wordmark
│   ├── logo-mono-dark.svg     Single colour, dark ink (for light backgrounds)
│   ├── logo-mono-light.svg    Single colour, light ink (for dark backgrounds)
│   ├── comb.svg               Seamless honeycomb tile used as a CSS background
│   ├── og.svg                 Source for the social preview image
│   └── og.png                 1200×630 social preview, rendered from og.svg
├── favicon.svg                The mark on a hive-black plate, tuned for 16px
│
├── site.webmanifest
├── robots.txt
├── sitemap.xml
├── vercel.json                cleanUrls, trailingSlash, security headers
└── tools/preview.mjs          Zero-dependency local server (see below)
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
| `stats[]` | the five hexagon cells in the hero |
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
  "color": "#9AA4B2",   // the colour of this arc of the hexagon ring
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

2. **`network/index.html` tables are hand-written**, not generated. They carry
   the full era and split breakdown. Keep them consistent with the JSON.

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

## Constraints the site is built to

These are not stylistic preferences; breaking them breaks the site.

- **No inline scripts, no inline event handlers, no `style=""` attributes.**
  The Content-Security-Policy in `vercel.json` sets `script-src 'self'` and
  `style-src 'self' https://fonts.googleapis.com`, with no `'unsafe-inline'`.
  Anything inline is silently dropped by the browser. Colour that has to come
  from data is applied through SVG `fill` presentation attributes instead.
- **Only two external origins**, both Google Fonts:
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

All colours are CSS custom properties on `:root` in `css/site.css`, and the
`/brand` page renders them with their hex values. Ten are the brand palette; two
are derived:

- `--honey-ink: #8A4B03` — the only amber that is WCAG-AA legible as *text* on
  `--cream` (6.4:1). `--honey` and `--amber-deep` both come in around 2.5:1 on
  cream, so they are for fills and for text on dark, never for text on light.
- `--bark-dim: #525B69` — secondary text on cream (5.8:1).

Each colour band (`.band--dark`, `.band--dark2`, `.band--cream`) re-declares
`--fg`, `--fg-dim`, `--accent`, `--surface`, `--rule` and `--focus`, so
components inside them theme themselves without extra classes.

## Motion

The hero `<canvas>` drifts a swarm of amber particles that periodically gather
into a hexagon outline and disperse again. It caps `devicePixelRatio` at 2,
scales the particle count down on narrow screens, and stops the animation frame
loop entirely when the tab is hidden or the hero scrolls out of view.

Under `prefers-reduced-motion: reduce` the animation never starts: a single
static hexagon of dots is drawn once, and all scroll reveals and transitions are
disabled in CSS.

## The logo

The mark is an original geometric design drawn for this project — a top-down bee
made only of hexagons and straight edges: one pointy-top hexagon for the body,
two bands clipped out of it for the stripes, two smaller hexagons tilted outward
for the wings, and a triangle for the stinger.

It is deliberately unlike the Foursquare Swarm app's mark (a rounded
side-profile bee with leaf-shaped wings and a hand-script wordmark) and is not
derived from it in any way.

The wordmark in `logo-full.svg` is live `<text>` set in Sora 700, uppercase,
with `0.08em` letter-spacing and a system sans fallback stack. It is not
converted to outlines on purpose: shipping outlines of a fallback system font
would mean redistributing a licensed typeface.

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

The site is staged on the Vercel project `swarm-green` (`https://swarm-green-three.vercel.app`). The `swarm.green` domain is still attached to the older `swarm-landing` project and is switched only on the owner's explicit go-ahead.

1. Owner approves the content, the hex-bee logo and the wording of the reward allocation.
2. In `vercel.json` change `X-Robots-Tag` from `noindex, nofollow` back to `index, follow`.
3. Move the `swarm.green` and `www.swarm.green` domains from the `swarm-landing` project to `swarm-green`, then deploy with `vercel deploy --prod`.
4. Check the live headers (CSP, HSTS without `includeSubDomains`), every route, and the social preview image.
5. Keep the previous `swarm-landing` project untouched so the old page can be restored by moving the domain back.

## Regenerating the sub-pages

`/network`, `/join`, `/brand`, `/terms`, `/privacy` and `404.html` are produced by `tools/build_pages.py` (plain Python, no dependencies) so that their shared navigation and footer stay identical. `index.html` is maintained by hand. Run `python tools/build_pages.py` from anywhere; it writes into the repository root. Review the diff before committing: a regeneration must never drop reviewed wording. `tools/`, `_review/` and this README are excluded from deployment by `.vercelignore`.
