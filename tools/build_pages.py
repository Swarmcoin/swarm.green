# Emits the plain-HTML sub-pages for swarm.green.
# The output is ordinary static HTML committed to the repo; this generator only
# exists so the shared <head>, nav and footer are byte-identical on every page.
import html
import json
import pathlib

import seo

ROOT = pathlib.Path(__file__).resolve().parent.parent  # repository root
# Addresses and hashes must not exist in two places, so they are read from the
# data file, which is copied from the published network manifest. The
# baseline-miner payout address is operational, not consensus, and is not here.
NETWORK = json.loads((ROOT / "data" / "network.json").read_text(encoding="utf-8"))
GENESIS = NETWORK["genesis"]
# The public addresses of the live mainnet, and the address prefixes a reader
# can use to tell at a glance which network they are looking at.
ENDPOINTS = NETWORK["endpoints"]
ADDRESS_FORMATS = NETWORK["addressFormats"]["formats"]
STATUS = NETWORK["status"]
# The closed start. (data/network.json also keeps a history sentence; owner
# 2026-10-03: it is data only and is not rendered anywhere.)
CLOSED = NETWORK["closedStart"]
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


# "Public mining opens in DD days HH:MM:SS", counting to the end of the closed
# start. The markup reads correctly without JavaScript ("opens on <date>");
# js/site.js (section 5c) fills in the time left. The same element is written by
# hand into index.html.
COUNTDOWN = (f'<p class="countdown" data-countdown="{CLOSED["untilUtc"]}" role="timer">'
             f'<span class="countdown__lead">Public mining</span> '
             f'<span class="countdown__left" data-countdown-left>opens on</span> '
             f'<time datetime="{CLOSED["untilUtc"]}">{esc(CLOSED["untilLabel"]).replace(", ", ",&nbsp;").replace(" UTC", "&nbsp;UTC")}</time></p>')
EXT = ('<svg class="ext" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" '
       'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
       '<path d="M6 3h7v7M13 3 4 12"/></svg><span class="vh">(opens in a new tab)</span>')
ARROW = ('<svg class="ext" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
         '<path d="M3 8h10M9 4l4 4-4 4"/></svg>')
GH = "https://github.com/Swarmcoin"
# Nav and footer point at the GitHub account (owner 2026-10-04: "add the GitHub
# to the website"): every repository, and the front page that explains the project.
GH_SOURCE = GH
# The release repository keeps the release notes and checksum files.
GH_RELEASES = "https://github.com/Swarmcoin/swarm-releases"
# Official channels, set by the owner on 2026-09-21. index.html and data/network.json carry the same values.
X_URL = "https://x.com/swarm_coin"
X_HANDLE = "@swarm_coin"
EMAIL = "swarmofficial@atomicmail.io"


# The phase timeline, byte-identical to the one in the home page's
# #roadmap section. Used at the top of /roadmap.
PHASES = """      <ol class="phases" data-reveal>
        <li class="phase is-live">
          <span class="phase__chip phase__chip--live">Live</span>
          <span class="phase__rail"><span class="phase__node"><svg class="ico" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-coin"/></svg></span></span>
          <div class="phase__card">
            <h3>SWARM mainnet</h3>
            <p>Public testnet <b>21 September 2026</b>; mainnet live since <b>2 October 2026</b>. The coin, the chain and the apps to run them. The genesis block holds no coins; after a 30-day closed start, public mining opens on <b>1 November 2026, 15:42&nbsp;UTC</b>.</p>
            <p class="phase__you">You can</p>
            <ul class="phase__list">
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>hold, send and receive SWM, shielded or transparent, in SWARM Wallet (the current version is published for Windows, macOS and Linux; Android follows)</span></li>
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>check the genesis hash and every block for yourself &mdash; the node verifies, it never trusts</span></li>
            </ul>
          </div>
        </li>
        <li class="phase is-now">
          <span class="phase__chip phase__chip--now">Now</span>
          <span class="phase__rail"><span class="phase__node"><svg class="ico" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-growth"/></svg></span></span>
          <div class="phase__card">
            <h3>Growing the swarm</h3>
            <p>More bees, more cities, more ways in. In development: signed macOS builds, the Android and iOS mainnet wallets, a second seed node in another failure domain, custody tooling for the three published funds, and an independent security review of the code as it was launched.</p>
            <p class="phase__you">You can</p>
            <ul class="phase__list">
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>browse the chain in the mainnet block explorer</span></li>
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>tell us what breaks</span></li>
            </ul>
          </div>
        </li>
        <li class="phase">
          <span class="phase__chip">Next</span>
          <span class="phase__rail"><span class="phase__node"><svg class="ico" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-market"/></svg></span></span>
          <div class="phase__card">
            <h3>SWARM Market</h3>
            <p><b>In development.</b> An online marketplace where merchants list what they sell and buyers pay in SWM, shielded by default. The wallet checks every invoice before you confirm; the Market never holds your coins; fees are shown before you pay; order details never touch the chain. Non-custodial invoices come first &mdash; escrow, multisignature and dispute handling need their own protocol and operational review before any of it ships.</p>
            <p class="phase__you">You can</p>
            <ul class="phase__list">
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>pay for real goods and services with SWM</span></li>
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>sell to the whole swarm without a payment processor</span></li>
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>keep what you bought between you and the seller</span></li>
            </ul>
          </div>
        </li>
        <li class="phase">
          <span class="phase__chip phase__chip--now">Pre-release</span>
          <span class="phase__rail"><span class="phase__node"><svg class="ico" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-browser"/></svg></span></span>
          <div class="phase__card">
            <h3>Privacy browser</h3>
            <p>The goal: a browser with the SWARM wallet built in, where paying a site is one click with the same confirmation screen as the wallet, trackers are blocked, fingerprinting is reduced, nothing phones home, and each site gets only the permissions you give it. <strong>The first SWARM Browser pre-release for Windows is available now</strong>: Google&rsquo;s services removed, privacy defaults switched on and the wallet in the toolbar. Paying sites, tracker blocking, phishing protection, rewards that pay and builds for macOS and Linux are not in it yet. <a class="textlink" href="/ecosystem/browser">Download SWARM Browser →</a></p>
            <p class="phase__you">You can</p>
            <ul class="phase__list">
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>pay from the address bar</span></li>
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>browse without being followed</span></li>
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>give a site access to your wallet only when you choose</span></li>
            </ul>
          </div>
        </li>
        <li class="phase">
          <span class="phase__chip phase__chip--live">Live</span>
          <span class="phase__rail"><span class="phase__node"><svg class="ico" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-message"/></svg></span></span>
          <div class="phase__card">
            <h3>Private messaging</h3>
            <p>End-to-end encrypted messages between people who hold SWARM wallets, with payments inside the conversation. Your chat identity is separate from your spending key, relays see only what they need to deliver, and no message is ever written to the chain. <strong>SWARM Messenger 0.1.0 for Windows, Linux and macOS is available now</strong>: sign in with your 24 words, find people by username, and pay inside the chat. It is a first, unsigned desktop release; there is no phone app yet. <a class="textlink" href="/ecosystem/messenger">Download SWARM Messenger →</a></p>
            <p class="phase__you">You can</p>
            <ul class="phase__list">
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>message and pay in one place</span></li>
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>ask for or share a payment address inside a chat</span></li>
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>verify a contact once and be told if their key ever changes</span></li>
            </ul>
          </div>
        </li>
      </ol>

      <p class="phases__note" data-reveal>Shipped work carries the date it shipped. Nothing that has not started gets one: each product is announced here when it is finished and reviewed, and not before.</p>"""


# The shared icon sprite, byte-identical to the one in index.html and
# support/index.html. head() is an f-string, so it arrives through {SPRITE}.
SPRITE = """<!-- The SWARM icon set. One 32-grid symbol per concept, drawn once and used
     everywhere with <svg class="ico"><use href="#i-..."/></svg>. Same-document
     references, so the strict CSP is untouched. Two tones: the solid shapes
     take the cell's ink, the half-opacity shapes read as the lit inner face. -->
<svg class="sprite" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg"><defs>
<symbol id="i-coin" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M16 3.2 27.2 9.6v12.8L16 28.8 4.8 22.4V9.6Z"/><path d="M16 7.6 23.4 11.9v8.2L16 24.4 8.6 20.1v-8.2Z" stroke-width="1.6" opacity=".38"/><path d="M19.2 12.7c-.7-1.2-2-1.9-3.4-1.9-1.9 0-3.2 1-3.2 2.5 0 3.2 6.8 1.5 6.8 4.9 0 1.6-1.4 2.7-3.4 2.7-1.5 0-2.8-.7-3.5-1.8" stroke-width="2.2"/></symbol>
<symbol id="i-apps" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><rect x="9.6" y="4.4" width="18.4" height="13.4" rx="2.8" opacity=".42"/><rect x="4" y="10.4" width="18.4" height="17.2" rx="2.8"/><path d="M4 16.2h18.4" opacity=".42"/><circle cx="8.4" cy="13.4" r="1.1" fill="currentColor" stroke="none"/></symbol>
<symbol id="i-people" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="12.4" cy="10.4" r="4.4"/><path d="M4 26.8c.5-5 3.9-7.8 8.4-7.8s7.9 2.8 8.4 7.8"/><circle cx="22.8" cy="12" r="3.2" opacity=".42"/><path d="M22 19.4c3.4.5 5.5 3 6 7.4" opacity=".42"/></symbol>
<symbol id="i-shield" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M16 3.4 27.4 7.6v8.2c0 5.9-4.4 10.2-11.4 12.2C9 26 4.6 21.7 4.6 15.8V7.6Z"/><path d="M16 10.6l3 1.7v3.4l-3 1.7-3-1.7v-3.4Z" fill="currentColor" stroke="none"/><path d="M16 18v3.6" stroke-width="2.6"/></symbol>
<symbol id="i-mining" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12.6 9.2c3.6-2 8.1-1.4 11 1.5 2.9 2.9 3.5 7.4 1.5 11"/><path d="M12.6 9.2 25.1 21.7" stroke-width="1.8" opacity=".42"/><path d="M5.4 26.6 18.9 13.1"/><path d="M8 5.4l2.7 1.6v3.1L8 11.7 5.3 10.1V7Z" fill="currentColor" stroke="none" opacity=".42"/></symbol>
<symbol id="i-principles" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4.4 9.2 6.8 11.6 11.2 6.6"/><path d="M15 9.4h12.6" opacity=".42"/><path d="M4.4 17.6 6.8 20 11.2 15"/><path d="M15 17.8h12.6" opacity=".42"/><path d="M4.4 26 6.8 28.4 11.2 23.4"/><path d="M15 26.2h8.6" opacity=".42"/></symbol>
<symbol id="i-bee" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="16" cy="18.8" rx="6.2" ry="7.6"/><path d="M10 16.6h12M10.4 21.6h11.2" opacity=".42"/><path d="M13.4 12C11.3 7.9 7 6.2 5.4 8.4c-1.3 1.8.7 4.7 4.1 5.9"/><path d="M18.6 12c2.1-4.1 6.4-5.8 8-3.6 1.3 1.8-.7 4.7-4.1 5.9"/></symbol>
<symbol id="i-forager" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="13.6" cy="18" rx="5.6" ry="6.8"/><path d="M8.2 16h10.8M8.6 20.6h10" opacity=".42"/><path d="M11.4 11.6C9.5 8 5.6 6.4 4.2 8.4c-1.2 1.7.6 4.2 3.7 5.3"/><path d="M16 11.6c1.9-3.6 5.8-5.2 7.2-3.2 1.2 1.7-.6 4.2-3.7 5.3"/><circle cx="24.4" cy="19.6" r="2.4" fill="currentColor" stroke="none"/><circle cx="27" cy="24.8" r="1.7" fill="currentColor" stroke="none" opacity=".42"/><circle cx="21" cy="25.8" r="1.5" fill="currentColor" stroke="none" opacity=".42"/></symbol>
<symbol id="i-honey" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M16 3.6s8.4 9.4 8.4 14.5A8.4 8.4 0 0 1 7.6 18.1C7.6 13 16 3.6 16 3.6Z"/><path d="M12.4 18.6a3.8 3.8 0 0 0 2.8 4.8" stroke-width="2" opacity=".42"/></symbol>
<symbol id="i-comb" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M16 15.5l5.4 3.1v6.2L16 27.9l-5.4-3.1v-6.2Z" fill="currentColor" stroke="none" opacity=".2"/><path d="M10.6 3.6 16 6.7v6.2l-5.4 3.1-5.4-3.1V6.7Z"/><path d="M21.4 3.6 26.8 6.7v6.2l-5.4 3.1-5.4-3.1V6.7Z" opacity=".42"/><path d="M16 15.5l5.4 3.1v6.2L16 27.9l-5.4-3.1v-6.2Z"/></symbol>
<symbol id="i-hive" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M14.4 9.6 8.2 21M17.6 9.6 23.8 21M10 24h12" opacity=".42"/><circle cx="16" cy="6.6" r="3.4"/><circle cx="6.6" cy="24" r="3.4"/><circle cx="25.4" cy="24" r="3.4"/></symbol>
<symbol id="i-lock" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><rect x="5.6" y="13.6" width="20.8" height="14.2" rx="3.4"/><path d="M10.6 13.6V9.8a5.4 5.4 0 0 1 10.8 0v3.8"/><circle cx="16" cy="19.6" r="2.2" fill="currentColor" stroke="none" opacity=".5"/><path d="M16 21.8v2.8" opacity=".5"/></symbol>
<symbol id="i-eye-off" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 16s4.8-7.4 12-7.4S28 16 28 16s-4.8 7.4-12 7.4S4 16 4 16Z"/><circle cx="16" cy="16" r="3.4" opacity=".42"/><path d="M6.6 27 25.4 5"/></symbol>
<symbol id="i-supply" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4.6 5.2v22.2h22.8" opacity=".42"/><path d="M7 25.4h4.6v-7.6h5.2v-4.6h5.2v-2.8h5"/></symbol>
<symbol id="i-layers" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M16 3.8 28.4 10.2 16 16.6 3.6 10.2Z"/><path d="M3.6 15.8 16 22.2l12.4-6.4" opacity=".42"/><path d="M3.6 21.4 16 27.8l12.4-6.4" opacity=".42"/></symbol>
<symbol id="i-code" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M11.6 8.4 3.8 16l7.8 7.6M20.4 8.4 28.2 16l-7.8 7.6"/><path d="M18.4 5.2 13.6 26.8" opacity=".42"/></symbol>
<symbol id="i-wallet" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><rect x="3.8" y="7.4" width="24.4" height="18" rx="3.6"/><path d="M28.2 13.2h-5.8a2.8 2.8 0 0 0 0 5.6h5.8" opacity=".42"/><circle cx="22.8" cy="16" r="1.5" fill="currentColor" stroke="none"/></symbol>
<symbol id="i-node" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><rect x="4.2" y="5" width="23.6" height="9.2" rx="2.6"/><rect x="4.2" y="17.8" width="23.6" height="9.2" rx="2.6"/><circle cx="9.4" cy="9.6" r="1.5" fill="currentColor" stroke="none"/><circle cx="9.4" cy="22.4" r="1.5" fill="currentColor" stroke="none"/><path d="M14.6 9.6h8.6M14.6 22.4h8.6" opacity=".42"/></symbol>
<symbol id="i-explorer" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M13.8 4.2 22.4 9.2v9.8l-8.6 5-8.6-5V9.2Z" stroke-width="1.8" opacity=".42"/><circle cx="13.8" cy="14.2" r="6.6"/><path d="M18.6 18.9 26.6 26.9"/></symbol>
<symbol id="i-phone" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><rect x="8.8" y="3.2" width="14.4" height="25.6" rx="3.4"/><path d="M13.6 7h4.8" opacity=".42"/><path d="M14.2 24.6h3.6"/></symbol>
<symbol id="i-desktop" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><rect x="3.4" y="5.4" width="25.2" height="16.8" rx="2.8"/><path d="M3.4 18h25.2" opacity=".42"/><path d="M16 22.2v4.4M11.4 26.6h9.2"/></symbol>
<symbol id="i-market" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 11.6 6.8 5.2h18.4L28 11.6Z"/><path d="M6.2 11.6v15.2h19.6V11.6"/><path d="M12.8 26.8v-7.4h6.4v7.4" opacity=".42"/></symbol>
<symbol id="i-browser" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.6" cy="13.6" r="9.6"/><path d="M4 13.6h19.2M13.6 4c2.6 2.8 3.9 6 3.9 9.6s-1.3 6.8-3.9 9.6C11 20.4 9.7 17.2 9.7 13.6S11 6.8 13.6 4Z" opacity=".42"/><path d="M22.4 17.2 28.4 19.3v3.9c0 2.9-2.2 5-6 6-3.8-1-6-3.1-6-6v-3.9Z" fill="currentColor" stroke="none"/><path d="M19.9 23.2l1.8 1.8 3.2-3.6" stroke="#FFF8E7" stroke-width="2"/></symbol>
<symbol id="i-message" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M27.6 16.4c0 5.7-5.2 10.4-11.6 10.4-1.6 0-3.1-.3-4.5-.8l-6.9 2.4 2.2-5.6c-1.8-1.8-2.8-4-2.8-6.4C4 10.7 9.2 6 15.6 6s12 4.7 12 10.4Z"/><rect x="12.6" y="15.4" width="7" height="5.8" rx="1.2" fill="currentColor" stroke="none"/><path d="M13.8 15.4v-1.8a2.3 2.3 0 0 1 4.6 0v1.8" stroke-width="2" opacity=".5"/></symbol>
<symbol id="i-rocket" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M16 3.4c3.9 3.6 6.1 8.3 6.1 13.5l-2.5 4.5h-7.2l-2.5-4.5c0-5.2 2.2-9.9 6.1-13.5Z"/><circle cx="16" cy="12.8" r="2.6" opacity=".42"/><path d="M12.3 15.6 8.2 19.7v4.5l3.5-2.6M19.7 15.6l4.1 4.1v4.5l-3.5-2.6"/><path d="M13.9 23.6c.5 2.5 1.2 4.2 2.1 5.2.9-1 1.6-2.7 2.1-5.2" opacity=".42"/></symbol>
<symbol id="i-growth" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M16 28.4V13.6"/><path d="M16 18.2c0-4.7-3.7-8.5-8.4-8.5 0 4.7 3.7 8.5 8.4 8.5Z" opacity=".42"/><path d="M16 15.4c0-4.7 3.7-8.5 8.4-8.5 0 4.7-3.7 8.5-8.4 8.5Z"/></symbol>
<symbol id="i-check" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M16 3.2 27.2 9.6v12.8L16 28.8 4.8 22.4V9.6Z"/><path d="M10.8 16.2 14.4 19.8 21.4 12.4" stroke-width="2.6"/></symbol>
<symbol id="i-store" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4.4v13.8"/><path d="M10.2 12.6 16 18.4l5.8-5.8"/><path d="M4.8 20.2v4.2a3 3 0 0 0 3 3h16.4a3 3 0 0 0 3-3v-4.2" opacity=".42"/></symbol>
</defs></svg>"""


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
<link rel="icon" href="/favicon.ico" sizes="16x16 32x32 48x48">
<link rel="icon" href="/favicon-96.png" type="image/png" sizes="96x96">
<link rel="icon" href="/favicon.svg?v=2" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180">
<link rel="mask-icon" href="/assets/logo-mono-dark.svg?v=2" color="#F5A623">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&family=Sora:wght@600;700;800&display=swap">
<link rel="stylesheet" href="/css/site.css?v=11">
<script src="/js/boot.js?v=4"></script>
<script src="/js/site.js?v=18" defer></script>
<script src="/js/price.js?v=1" defer></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-3MDDZNCW6P"></script>
<script src="/js/analytics.js?v=2"></script>
</head>
<body>
{SPRITE}

<a class="skip" href="#main">Skip to content</a>

<p class="ribbon"><span class="dot"></span>SWARM <b>mainnet is live</b> · public mining opens 1 November 2026.</p>

<header class="nav">
  <div class="wrap nav__bar">
    <a class="brand" href="/">
      <img src="/assets/logo-mark.svg?v=2" alt="" width="56" height="27">
      <span>SWARM</span>
      <span class="vh">— home</span>
    </a>
    <div class="nav__price" data-swm-price title="SWM price on Base: not available right now">
      <span class="nav__price-line" aria-hidden="true"><span class="nav__price-dot"></span>SWM <span class="nav__price-val" data-swm-price-value>—</span></span>
      <span class="nav__price-net" aria-hidden="true">on Base</span>
      <span class="vh" data-swm-price-sr>SWM price on Base: not available right now.</span>
    </div>
    <nav class="nav__links" aria-label="Primary">
      <a href="/#mainnet">Mainnet</a>
      <a href="/waitlist">Waiting list</a>
      <a href="/#hive">The Hive</a>
      <a href="/#honey">Honey</a>
      <a href="/ecosystem">Ecosystem</a>
      <a href="/verify">Verify</a>
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
        <li><a href="/#mainnet">Mainnet</a></li>
        <li><a href="/waitlist">Waiting list</a></li>
        <li><a href="/#hive">The Hive</a></li>
        <li><a href="/#honey">Honey</a></li>
        <li><a href="/#swarm">The Swarm</a></li>
        <li><a href="/ecosystem">Ecosystem</a></li>
        <li><a href="/verify">Verify</a></li>
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
          <li><a href="/verify">Verify the chain</a></li>
          <li><a href="/roadmap">Roadmap</a></li>
        </ul>
      </nav>

      <nav aria-labelledby="ft-get">
        <h2 id="ft-get">Get started</h2>
        <ul>
          <li><a href="/what-is-swarm">What is SWARM?</a></li>
          <li><a href="/join">Get SWARM</a></li>
          <li><a href="/waitlist">Waiting list</a></li>
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
      <p><strong>Open-source software, provided as is.</strong> Nothing on this site is an offer, a solicitation or financial advice. SWM has no guaranteed value and can lose value, including all of it.</p>
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


def page_head(here, h1, lead, pill=None, extra=""):
    tag = f'<p class="pill">{pill}</p>' if pill else ""
    more = f"\n      {extra}" if extra else ""
    return f"""  <section class="band band--dark band--comb page-head">
    <div class="wrap">
      {crumbs(here)}
      {tag}
      <h1>{h1}</h1>
      <p class="page-head__lead">{lead}</p>{more}
    </div>
  </section>
"""


def write(path, body):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    # Search title, description and structured data live in tools/seo.py.
    p.write_text(seo.decorate(path, body), encoding="utf-8")
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
    ("Closed start", esc(CLOSED["summary"]) + " The genesis block itself holds no coins."),
    ("Coinbase maturity", "100 blocks"),
    ("Proof of work", "Equihash 200,9, inherited unchanged. Once mining is open to everyone, nothing in the rules keeps larger miners out."),
    ("Privacy", "Optional. Shielded transactions keep sender, receiver and amount encrypted on-chain, using zero-knowledge proofs."),
    ("Code", "Proven open-source code, with consensus rules and cryptography left unmodified. Read it, build it, check it."),
    ("Ticker", "SWM"),
    ("Status", "Mainnet, live since " + esc(STATUS["launchedLabel"]) + "."),
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
        ("Spendable outputs in the genesis block", esc(GENESIS["spendableOutputs"]), ""),
        ("Live since", esc(STATUS["launchedLabel"]), "mono"),
    ])

# The public addresses of the live network that the published apps use. Since
# 2026-10-02 (owner) the site offers no node software, so it lists no peer
# address and no node port.
endpoint_rows = "\n".join(
    f'          <tr><th scope="row">{k}</th><td class="{cls}">{v}</td></tr>'
    for k, v, cls in [
        ("Mainnet light server (TLS)", esc(ENDPOINTS["lightWallet"]), "mono"),
        ("Mainnet block explorer",
            f'<a href="{ENDPOINTS["explorerMainnet"]}" target="_blank" rel="noopener noreferrer">'
            f'mainnet.explore.swarm.green{EXT}</a> \u2014 live, showing SwarmMainnet', ""),
        ("Testnet block explorer",
            f'<a href="{ENDPOINTS["explorerTestnet"]}" target="_blank" rel="noopener noreferrer">'
            f'testnet.explore.swarm.green{EXT}</a> \u2014 the public testnet, whose coins have no value', ""),
    ])

address_rows = "\n".join(
    f'          <tr><th scope="row" class="mono">{esc(f["prefix"])}</th>'
    f'<td>{esc(f["network"])}</td><td>{esc(f["kind"])} \u2014 {esc(f["detail"])}</td></tr>'
    for f in ADDRESS_FORMATS)

network = head(
    "Network &amp; supply — SWARM",
    "Every SWARM parameter in one place: 75-second blocks, 6.25 SWM per block, halving every 1,680,000 blocks, a ceiling of 20,999,987.3152 SWM, the 30-day closed start, the four-way block reward split fixed for the whole emission schedule, and the genesis block it is all fixed in.",
    "/network",
    "SWARM — Network &amp; supply",
    "75-second blocks, 6.25 coins per block, halving every 1,680,000 blocks, a ceiling of 20,999,987.3152 coins and a genesis block that holds no coins.",
) + page_head(
    "Network &amp; supply",
    "Every number, in one place.",
    "The monetary base is fixed in the code. Nothing on this page is a projection — it is arithmetic you can check yourself against the source, and against the chain with your own node.",
    pill="Mainnet · live",
    extra=COUNTDOWN,
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
      <p class="note mt-m" data-reveal>Mining rewards mature after <strong>100 blocks</strong> before they can be spent. The genesis block contains no spendable coins, so every coin in the table above has to be mined.</p>
    </div>
  </section>

  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Reward allocation</p>
        <h2>Where every block reward goes.</h2>
        <p>Every block reward is split four ways, in the same proportions, for the whole emission schedule. Each halving reduces all four amounts together — the 80 / 8 / 4 / 8 structure never changes, all the way down to the block where the reward reaches zero. In the last eras integer rounding retires the small streams first: Grants &amp; Ecosystem rounds to zero from era 25, Core Development and the Reserve from era 26, and the miner keeps the remainder.</p>
        <p class="mt-s">The percentages are hard-coded in the genesis rules. Each allocation is paid automatically to its predefined destination address. Destinations can only be changed through a formal protocol upgrade; the percentages themselves cannot be changed. The three destinations are script addresses held by the project, and they are published together with the genesis rules.</p>
        <p class="mt-s">No coins in the genesis block, no hidden treasury — every allocation is visible in every block.</p>
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
        <p class="mt-s">The keys behind the three addresses were generated offline and are held under the custody policy published with the launch manifest in the <a href="{GH_RELEASES}" target="_blank" rel="noopener noreferrer">release repository{EXT}</a>.</p>
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

      <p class="note mt-m" data-reveal><strong>Checking the chain itself?</strong> The public endpoints, the three fund addresses with copy buttons and the address prefixes that tell mainnet from testnet are all on <a href="/verify">Verify</a>, so they live in one place and cannot drift apart. <a class="textlink" href="/verify">Check you are on the real chain &rarr;</a></p>

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
        <h2>Now use it.</h2>
        <p>Every number on this page is enforced by every node on the network.</p>
      </div>
      <div class="cta-row mt-l" data-reveal>
        <a class="btn btn--primary" href="/join">Get SWARM</a>
        <a class="btn btn--ghost" href="{GH}" target="_blank" rel="noopener noreferrer">Read the source{EXT}</a>
      </div>
    </div>
  </section>
""" + FOOTER
write("network/index.html", network)


# ----------------------------------------------------------------- /verify
# "Am I on the real chain?" answered on one page. Every value here is read from
# data/network.json, which is copied from the published launch manifest, so the
# page cannot drift from the network it describes. The home page carries only a
# short card and links here; /network links here rather than repeating the
# endpoint and address-prefix tables.
def copy_btn(value, what):
    return ('<button class="btn btn--ghost btn--sm" type="button" '
            f'data-copy="{html.escape(str(value), quote=True)}">Copy'
            f'<span class="vh"> {what}</span></button>')


def copyline(value, what):
    """A monospaced value with a Copy button beside it. The clipboard handler
    is the delegated one already in js/site.js, so nothing new runs here."""
    return (f'<span class="copyrow"><code class="mono">{esc(value)}</code>'
            f'{copy_btn(value, what)}</span>')


launch_rows = "\n".join(
    f'          <tr><th scope="row">{k}</th><td>{v}</td></tr>'
    for k, v in [
        ("Network", f'<span class="mono">{esc(GENESIS["network"])}</span>'),
        ("Live since", f'<span class="mono">{esc(STATUS["launchedLabel"])}</span>'),
        ("Genesis block hash", copyline(GENESIS["hash"], "the genesis block hash")),
        ("Genesis header time", f'<span class="mono">{esc(GENESIS["headerTimeUtc"])}</span>'),
        ("Block 1", f'<span class="mono">{esc(GENESIS["block1Utc"])}</span>'),
        ("SHA-256 of genesis.hex", copyline(GENESIS["hexSha256"], "the SHA-256 of genesis.hex")),
        ("Spendable outputs in the genesis block", esc(GENESIS["spendableOutputs"])),
        ("Closed start", esc(CLOSED["summary"])),
        ("Proof of work", esc(NETWORK["chain"]["proofOfWork"])),
        ("Ticker", esc(NETWORK["chain"]["ticker"])),
        ("Target block time", f'{esc(NETWORK["chain"]["blockTimeSeconds"])} seconds'),
    ])

fund_rows = "\n".join(
    f'          <tr><th scope="row">{esc(d["name"])}</th>'
    f'<td class="num">{esc(d["percent"])}</td>'
    f'<td>{copyline(d["address"], "the " + esc(d["name"]) + " address")}</td></tr>'
    for d in GENESIS["destinations"])

verify = head(
    "Verify the chain — SWARM",
    "Check you are on the real SWARM chain: the genesis hash, the launch time, the public endpoints, the three published fund addresses and the address prefixes that tell mainnet from testnet.",
    "/verify",
    "SWARM — Verify the chain",
    f"Genesis {GENESIS['hash'][:8]}…{GENESIS['hash'][-4:]}. Check the chain you joined is the one that was announced.",
) + page_head(
    "Verify",
    "Check you are on the real chain.",
    "A chain is identified by its genesis block. You can check it against the one below. Nothing on this page needs to be taken on trust: every value is published, and every one of them is something your own node will report back to you.",
    pill="Mainnet · live",
) + f"""
  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">The launch</p>
        <h2>The genesis block, and a closed start.</h2>
        <p>SWARM mainnet has been live since <strong>{esc(STATUS["launchedLabel"])}</strong>. The genesis block holds no spendable coins; every SWM that exists has been mined. The first 30 days are a closed start. {esc(CLOSED["summary"])}</p>
      </div>

      <div class="tablewrap" data-reveal>
        <table>
          <caption>The SWARM mainnet launch, as published in the launch manifest.</caption>
          <tbody>
{launch_rows}
          </tbody>
        </table>
      </div>

      <div class="cards cards--2 mt-l" data-reveal>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-explorer"/></svg></div>
          <h3>In the block explorer</h3>
          <p>Look up height 0 in the mainnet explorer. It shows the same hash, the same header time and an empty coinbase. The explorer is a convenience &mdash; your own node is still the authority.</p>
          <p class="mt-m"><a class="btn btn--ghost btn--sm" href="{ENDPOINTS["explorerMainnet"]}" target="_blank" rel="noopener noreferrer">mainnet.explore.swarm.green{EXT}</a></p>
        </article>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-code"/></svg></div>
          <h3>From the source</h3>
          <p>Every published release is listed with its SHA-256 in the release repository. The launch manifest and the node software are published when mining opens: from 31 October 2026, 15:42&nbsp;UTC for the waiting list, from 1 November 2026, 15:42&nbsp;UTC for everyone.</p>
          <p class="mt-m"><a class="btn btn--ghost btn--sm" href="{GH_RELEASES}" target="_blank" rel="noopener noreferrer">Release repository{EXT}</a></p>
        </article>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Where the apps connect</p>
        <h2>The public addresses of the live network.</h2>
      </div>

      <div class="tablewrap" data-reveal>
        <table>
          <caption>SWARM mainnet endpoints.</caption>
          <tbody>
{endpoint_rows}
          </tbody>
        </table>
      </div>

      <p class="note mt-m" data-reveal>These are the public addresses of the live network. Earlier wallet builds (desktop 0.1.0-mainnet.9 and older, Android 0.2.0-mainnet.4) no longer connect to it; the current version is in the <a href="/ecosystem/wallet">Ecosystem</a>. <code>explore.swarm.green</code> and <code>mainnet.explore.swarm.green</code> are the same mainnet explorer; the testnet explorer is <code>testnet.explore.swarm.green</code>.</p>
    </div>
  </section>

  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">The project&rsquo;s funds</p>
        <h2>Three addresses, published, paid block by block.</h2>
        <p>Twenty per cent of every block reward goes to these three addresses, automatically, as part of the block itself. It is not a premine and not a treasury that was filled in advance: it accumulates one block at a time, in public, and you can watch it arrive in the explorer.</p>
      </div>

      <div class="tablewrap" data-reveal>
        <table>
          <caption>The three published fund addresses, fixed in the genesis rules.</caption>
          <thead>
            <tr><th scope="col">Fund</th><th scope="col">Share</th><th scope="col">Published address</th></tr>
          </thead>
          <tbody>
{fund_rows}
          </tbody>
        </table>
      </div>

      <div class="cards cards--2 mt-l" data-reveal>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-lock"/></svg></div>
          <h3>How the keys are held</h3>
          <p>{esc(GENESIS["addressType"])} {esc(GENESIS["custody"])}</p>
          <p class="mt-s">No single person and no single machine can move these funds, and the signing procedure has been exercised end to end rather than only written down.</p>
        </article>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-eye-off"/></svg></div>
          <h3>What is deliberately not here</h3>
          <p>The project also mines; during the closed start it is the only miner. That payout goes to the project&rsquo;s own mining wallet, and its address is <strong>not</strong> published: publishing it would hand everyone a permanent view of a wallet that has no governance role.</p>
          <p class="mt-s">The three addresses above are the ones with a claim on the block reward, so those are the three that are published.</p>
        </article>
      </div>

      <p class="note mt-m" data-reveal>The percentages are fixed in the genesis rules and cannot be changed. The destinations can only be changed by a formal protocol upgrade, which every node would have to accept. The full schedule, era by era, is on the <a href="/network">network page</a>.</p>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Addresses</p>
        <h2>How to tell which network you are on.</h2>
        <p>Read the first characters of any address. Mainnet and testnet use different prefixes on purpose, so a testnet address can never be mistaken for a real one &mdash; and a payment sent to the wrong kind of address is rejected rather than lost into another chain.</p>
      </div>

      <div class="tablewrap" data-reveal>
        <table>
          <caption>SWARM address prefixes.</caption>
          <thead>
            <tr><th scope="col">Starts with</th><th scope="col">Network</th><th scope="col">What it is</th></tr>
          </thead>
          <tbody>
{address_rows}
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <section class="band band--cream">
    <div class="wrap wrap--narrow">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">If something does not match</p>
        <h2>Then stop, and tell us.</h2>
        <p>A genesis hash that differs from the one on this page means the software you are running is not on SWARM mainnet. That can be an old build, a testnet build, or something that is not ours at all. Do not send coins to it, and do not enter a recovery phrase into it.</p>
        <p class="mt-s">Download only from the links on this site, check the SHA-256 before you install, and write to <a href="mailto:{EMAIL}">{EMAIL}</a> if a published value and a running app disagree. We will never ask you for your recovery phrase, your private keys or a payment.</p>
      </div>
      <div class="cta-row mt-l" data-reveal>
        <a class="btn btn--primary" href="/ecosystem">Get the apps</a>
        <a class="btn btn--ghost" href="/network">The full supply schedule</a>
      </div>
    </div>
  </section>
""" + FOOTER
write("verify/index.html", verify)


# ------------------------------------------------------------------- /join
join = head(
    "Get SWARM — SWARM",
    "How to get started with SWARM: choose a wallet for your computer or phone and back up your recovery phrase.",
    "/join",
    "Get SWARM",
    "Get the wallet and join the swarm.",
) + page_head(
    "Get SWARM",
    "Join the swarm.",
    "Choose a wallet and join the network.",
    pill="Mainnet · live",
) + f"""
  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Step by step</p>
        <h2>Start with a wallet. Every bee counts.</h2>
      </div>
      <p class="note" data-reveal>Public mining opens on {esc(CLOSED["untilLabel"])}; until then the <a href="/waitlist">waiting list</a> is the way in. <strong>Please keep ASICs and rented hash power off the network.</strong> No coins are promised.</p>

      <div class="steps" data-reveal>
        <article class="card step">
          <div class="step__n" aria-hidden="true">1</div>
          <p class="step__app">SWARM Wallet</p>
          <h3>Get a wallet</h3>
          <p>A desktop wallet that holds your coins and sends payments — transparent or shielded, your choice on every payment. The current version, 0.1.0-mainnet.11, is published for Windows, macOS and Linux.</p>
          <p class="mt-s">On first run it will show you a recovery phrase. Write it down on paper and keep it offline. It is the only way to restore your wallet.</p>
          <a class="btn btn--primary" href="/ecosystem/wallet">Choose your wallet</a>
        </article>
      </div>

      <p class="note mt-l" data-reveal>Every app, the block explorer and the source code are listed together in <a href="/ecosystem">Ecosystem</a>.</p>

      <div class="cards cards--2 mt-l" data-reveal>
        <article class="card">
          <h3>SWARM Explorer</h3>
          <p>A block explorer, so you can watch what the chain is actually doing: blocks as they are found, the supply as it is issued, and the four-way allocation in every block. The mainnet explorer is live at mainnet.explore.swarm.green. Your own node is still the authority — the explorer just makes it easy to look.</p>
          <p class="mt-m"><a class="btn btn--ghost btn--sm" href="/ecosystem">See the ecosystem{ARROW}</a></p>
        </article>
        <article class="card">
          <h3>Read the source</h3>
          <p>The node, the indexer and the wallet are open source — read the code and check that it does what this site says it does.</p>
          <p class="mt-m"><a class="btn btn--ghost btn--sm" href="{GH}" target="_blank" rel="noopener noreferrer">Browse the source{EXT}</a></p>
        </article>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Before you start</p>
        <h2>One thing that matters.</h2>
      </div>

      <div class="cards cards--2" data-reveal>
        <article class="card">
          <div class="hexicon" aria-hidden="true">
            <svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-lock"/></svg>
          </div>
          <h3>Back up your recovery phrase offline</h3>
          <p>Write the phrase down on paper and store it somewhere safe. Do not photograph it, do not put it in a password manager you do not control, and do not type it into anything that asks you to &ldquo;verify&rdquo; it on a website.</p>
          <p class="mt-s">Anyone who has the phrase has the coins. If you lose it, nobody — including us — can recover your wallet for you.</p>
        </article>
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
# What has shipped, what is being built and what is only planned, read from
# data/network.json so the wording lives in one place and the page cannot claim
# something is live that the data file calls planned. The rule the data file
# states and this renderer enforces: only "live" rows carry a date.
DELIVERY_GROUPS = [
    ("live", "Live",
     "Shipped and public. The date is the day anyone could use it."),
    ("in-development", "In development",
     "Started, and not finished. No dates — a date on unfinished work is a guess."),
    ("planned", "Planned",
     "Not started. Named so the order is public, with nothing promised and no date."),
]


def delivery_table(state, label, blurb):
    items = [i for i in NETWORK["deliveries"]["items"] if i["state"] == state]
    if not items:
        raise SystemExit("refusing to build: no deliveries in state %r" % state)
    for i in items:
        if (state == "live") != bool(i.get("when")):
            raise SystemExit("refusing to build: %r is %r and %s a date"
                             % (i["name"], state, "has" if i.get("when") else "has no"))
    rows = "\n".join(
        f'          <tr><th scope="row">{esc(i["name"])}</th>'
        f'<td class="mono">{esc(i["when"]) if i.get("when") else "&mdash;"}</td>'
        f'<td>{esc(i["detail"])}</td></tr>'
        for i in items)
    return f"""      <div class="tablewrap mt-m" data-reveal>
        <table>
          <caption><b>{label}.</b> {blurb}</caption>
          <thead>
            <tr><th scope="col">What</th><th scope="col">Since</th><th scope="col">Detail</th></tr>
          </thead>
          <tbody>
{rows}
          </tbody>
        </table>
      </div>
"""


DELIVERIES = "\n".join(delivery_table(*g) for g in DELIVERY_GROUPS)


roadmap = head(
    "Roadmap — SWARM",
    "SWARM mainnet is live. What is running today, how to verify you are on the real chain, and what comes next: SWARM Market, a privacy browser and private messaging.",
    "/roadmap",
    "SWARM — Roadmap",
    "Mainnet is live. Next: SWARM Market, a privacy browser and private messaging.",
) + page_head(
    "Roadmap",
    "The money first. Then the things you do with it.",
    "SWARM mainnet is live: the coin, the chain and the apps to run them. Everything else on this page is built on that foundation.",
    pill="Mainnet · live",
) + f"""
  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">The plan</p>
        <h2>Five phases, in order.</h2>
        <p>The order is fixed; the calendar follows the work.</p>
      </div>
{PHASES}

      <div class="sec-head mt-l" data-reveal>
        <p class="eyebrow">Where each thing stands</p>
        <h2>Live, in development, or planned.</h2>
        <p>Three words, used strictly. <strong>Live</strong> means you can use it today and the date is the day you could. <strong>In development</strong> means the work has started and is not finished. <strong>Planned</strong> means it has not started &mdash; no date, no promise. Nothing moves up this list until it is true.</p>
      </div>

{DELIVERIES}
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap wrap--narrow">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Verify it</p>
        <h2>Check you are on SWARM.</h2>
        <p>A chain is identified by its genesis block: <span class="mono">{GENESIS["hash"][:8]}&hellip;{GENESIS["hash"][-4:]}</span>. You can check it by hand. The launch facts, the public endpoints, the three published fund addresses and the address prefixes are all on one page.</p>
      </div>
      <div class="cta-row" data-reveal>
        <a class="btn btn--primary" href="/verify">Verify the chain</a>
        <a class="btn btn--ghost" href="{GH_RELEASES}" target="_blank" rel="noopener noreferrer">Release repository{EXT}</a>
      </div>
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
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-wallet"/></svg></div>
          <h3>Pay from your wallet</h3>
          <p>A merchant issues an invoice: exact amount, recipient, expiry. Your wallet checks it is a real SWARM invoice for the right network before it shows you a confirmation. You pay; the seller sees the payment confirm on the chain.</p>
        </article>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-shield"/></svg></div>
          <h3>No custody</h3>
          <p>The coins go from you to the seller. The Market holds nothing on your behalf and cannot spend anything of yours. Fees, where there are any, are shown before you pay, not after.</p>
        </article>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-eye-off"/></svg></div>
          <h3>Nothing personal on the chain</h3>
          <p>Order details, addresses and messages between buyer and seller live off-chain, protected and deletable. The chain only ever records that a valid payment happened.</p>
        </article>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Pre-release &middot; Windows</p>
        <h2>A privacy browser.</h2>
        <p>A browser with the SWARM wallet built in, so paying a site is one click and no site sees more of you than it must.</p>
        <p>The first pre-release for Windows is out, with the wallet in the toolbar and Google&rsquo;s services removed. Paying sites and tracker blocking are not in it yet; the cards below say where it is going. <a class="textlink" href="/ecosystem/browser">Download SWARM Browser →</a></p>
      </div>
      <div class="cards" data-reveal>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-browser"/></svg></div>
          <h3>Wallet built in</h3>
          <p>Pay a site or a merchant from the address bar, with the same confirmation screen as the wallet. A site can ask for a payment; it can never take one.</p>
        </article>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-eye-off"/></svg></div>
          <h3>Private by default</h3>
          <p>Tracking blocked, fingerprinting reduced, nothing phoning home. Each site gets only the permissions you give it, and the wallet is never one of them by default.</p>
        </article>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-code"/></svg></div>
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
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-message"/></svg></div>
          <h3>Encrypted end to end</h3>
          <p>Only you and the person you write to can read a message. Relays carry ciphertext and the minimum needed to deliver it, and nothing is ever written to the chain.</p>
        </article>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-coin"/></svg></div>
          <h3>Pay inside the chat</h3>
          <p>Send SWM to the person you are talking to, or send them an invoice, without leaving the conversation. A message can ask for a payment; it can never spend for you.</p>
        </article>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-lock"/></svg></div>
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
        <p>No coins in the genesis block: every SWM that exists has been mined. No hidden treasury: the 80 / 8 / 4 / 8 split is fixed in the rules and visible in every block. No promise of a price, ever. No product that takes custody of your coins behind a decentralisation claim. Nothing that runs on your machine without you pressing the button. And if this site and the code ever disagree, the code is right and the site gets fixed.</p>
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
          <p class="sample sample--body">One bee is small. A swarm is unstoppable. A hive is just a lot of small jobs, done honestly.</p>
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


# --------------------------------------------------------------- /waitlist
# The waiting list for public mining (owner, 2026-10-03). The list itself is a
# small service on the project's own server (server/waitlist/), reached through
# the same-origin rewrite /api/waitlist/* in vercel.json; js/site.js (section
# 5d) runs the form, the counter, the leaderboard and "remove me". Without
# JavaScript the page still explains the list and shows the countdown text; the
# form needs JavaScript (the CSP's form-action 'none' blocks a plain submit).
#
# Two states, from data/network.json closedStart.opened:
#   false  the sign-up form (and, once the countdown reaches zero, a note that
#          public mining is opening, never that it is open);
#   true   the node download link instead of the form. Allowed only when
#          data/downloads.json has an available mainnet "node" row.
# What a place on the list is, in one sentence, used on the page and in /terms.
EARLY = CLOSED["projectOnlyUntilLabel"]
OPENS = CLOSED["untilLabel"]
WL_IS = (f"A place on the list gives early access: people on the list get the node download from {EARLY}, "
         f"in leaderboard order during that day, 24 hours before everyone else; mining opens to everyone on {OPENS}.")
WL_IS_NOT = "It is not a promise of coins, earnings or a price, and the list is free."
WL_RULE = ("The leaderboard counts the people who join with your invite link, each of them once, and "
           "only them: the people they invite count for them, never for you. A higher place gets the "
           "node download earlier in that day; no coins are promised.")

WL_OPEN = bool(CLOSED.get("opened"))
if WL_OPEN:
    _downloads = json.loads((ROOT / "data" / "downloads.json").read_text(encoding="utf-8"))["entries"]
    if not any(e.get("product") == "node" and e.get("status") == "available" and e.get("channel") != "testnet"
               for e in _downloads):
        raise SystemExit("refusing to build: closedStart.opened is true but data/downloads.json has no "
                         "available mainnet node row. Add the node download first, or keep opened false.")

WL_COUNT = ('<p class="wl-count js-only" data-wl-count><span class="wl-count__n" data-wl-total>&mdash;</span> '
            '<span data-wl-noun="sign-up|sign-ups">sign-ups</span> on the waiting list</p>')
WL_EARLY = (f'<p class="wl-early">Early access for the waiting list: '
            f'<time datetime="{CLOSED["projectOnlyUntilUtc"]}">{esc(EARLY).replace(", ", ",&nbsp;").replace(" UTC", "&nbsp;UTC")}</time></p>')

WL_FORM = f"""        <form class="wl-form" data-wl-form novalidate aria-labelledby="wl-form-title">
          <h2 class="wl-card__title" id="wl-form-title">Join the waiting list</h2>
          <p class="wl-card__lead">Two things: an email address, so we can reach you when it opens, and the SWARM address you would mine to.</p>
          <div class="field">
            <label for="wl-email">Email address</label>
            <input id="wl-email" name="email" type="email" inputmode="email" autocomplete="email" spellcheck="false" maxlength="254" required aria-describedby="wl-email-err">
            <p class="field__err" id="wl-email-err" data-wl-err="email" hidden></p>
          </div>
          <div class="field">
            <label for="wl-address">Your SWARM address</label>
            <input class="mono" id="wl-address" name="address" type="text" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" maxlength="512" required aria-describedby="wl-address-hint wl-address-err">
            <p class="field__hint" id="wl-address-hint">A mainnet address from SWARM Wallet: it starts with <span class="mono">swm1</span>, <span class="mono">s1</span> or <span class="mono">s3</span>. No wallet yet? <a href="/ecosystem/wallet">Get SWARM Wallet</a>.</p>
            <p class="field__err" id="wl-address-err" data-wl-err="address" hidden></p>
          </div>
          <div class="field">
            <label for="wl-invite">Invite code <span class="field__opt">(optional)</span></label>
            <input class="mono" id="wl-invite" name="invite" type="text" autocomplete="off" autocapitalize="characters" spellcheck="false" maxlength="10" aria-describedby="wl-invite-hint">
            <p class="field__hint" id="wl-invite-hint">If someone sent you a link, their code is already filled in.</p>
          </div>
          <div class="field field--check">
            <input id="wl-consent" name="consent" type="checkbox" required aria-describedby="wl-consent-err">
            <label for="wl-consent">Put me on the waiting list and tell me by email when my early access starts.</label>
            <p class="field__err" id="wl-consent-err" data-wl-err="consent" hidden></p>
          </div>
          <div class="field field--check">
            <input id="wl-news" name="news" type="checkbox">
            <label for="wl-news">Also send me SWARM project news by email. I can unsubscribe at any time. <span class="field__opt">(optional)</span></label>
          </div>
          <p class="field__hint wl-privacy-hint">What we store, and for how long, is on the <a href="/privacy#waiting-list">privacy page</a>. You can remove yourself at any time.</p>
          <div class="hp" aria-hidden="true">
            <label for="wl-trap">Do not fill this in</label>
            <input id="wl-trap" name="trap" type="text" tabindex="-1" autocomplete="off" data-1p-ignore data-lpignore="true" data-bwignore>
          </div>
          <div class="wl-actions">
            <button class="btn btn--primary" type="submit" data-wl-submit>Join the waiting list</button>
          </div>
          <p class="wl-status" role="status" aria-live="polite" data-wl-status></p>
        </form>"""

WL_ME = f"""        <div class="wl-me" data-wl-me hidden>
          <h2 class="wl-card__title" tabindex="-1" data-wl-me-title>You are on the list.</h2>
          <dl class="wl-facts">
            <div><dt>Your place</dt><dd class="mono"><span data-wl-position>&mdash;</span> <span class="wl-of">of <span data-wl-of>&mdash;</span></span></dd></div>
            <div><dt>Invites counted</dt><dd class="mono" data-wl-invites>&mdash;</dd></div>
          </dl>
          <p class="wl-me__note" data-wl-confirm-note>We will ask you to confirm your email before opening.</p>
          <p class="wl-me__label">Your invite link</p>
          <span class="copyrow"><code class="mono" data-wl-link>&mdash;</code><button class="btn btn--ghost btn--sm" type="button" data-copy="" data-wl-copy>Copy<span class="vh"> your invite link</span></button></span>
          <p class="wl-me__rule">{WL_RULE}</p>
          <p class="wl-me__note" data-wl-news-state></p>
          <p><button class="btn btn--ghost btn--sm" type="button" data-wl-news-stop hidden>Stop project news</button></p>
          <p class="wl-status" role="status" aria-live="polite" data-wl-me-status></p>
          <div class="wl-remove">
            <button class="btn btn--ghost btn--sm" type="button" data-wl-remove aria-expanded="false" aria-controls="wl-remove-confirm">Remove me from the list</button>
            <div class="wl-remove__confirm" id="wl-remove-confirm" data-wl-remove-confirm hidden>
              <p tabindex="-1" data-wl-remove-text>This deletes your email address, your SWARM address and your place, and cannot be undone.</p>
              <div class="cta-row">
                <button class="btn btn--primary btn--sm" type="button" data-wl-remove-yes>Yes, remove me</button>
                <button class="btn btn--ghost btn--sm" type="button" data-wl-remove-no>Keep me on the list</button>
              </div>
            </div>
          </div>
        </div>"""

WL_DOWNLOAD = f"""        <div class="wl-open">
          <h2 class="wl-card__title">Public mining is open.</h2>
          <p class="wl-card__lead">The node download is published. Check its SHA-256 before you install it.</p>
          <p class="mt-m"><a class="btn btn--primary" href="{esc(CLOSED.get("downloadPath", "/ecosystem/node"))}">Get the node{ARROW}</a></p>
        </div>"""

waitlist = head(
    "Waiting list for public mining — SWARM",
    "Join the waiting list for SWARM public mining. People on the list get the node download from 31 October 2026, 15:42 UTC, 24 hours before mining opens to everyone on 1 November 2026, 15:42 UTC. No coins are promised.",
    "/waitlist",
    "SWARM — Waiting list for public mining",
    "Public mining opens on 1 November 2026, 15:42 UTC. People on the waiting list get the node download 24 hours earlier.",
) + page_head(
    "Waiting list",
    "Waiting list for public mining.",
    ("Public mining is open. People on the waiting list were given the node download first."
     if WL_OPEN else
     f"SWARM is in its closed start: until {esc(EARLY)} only the project&rsquo;s own machines mine. "
     f"Put your name down now: people on the waiting list get the node download from {esc(EARLY)}, "
     f"24 hours before mining opens to everyone on {esc(OPENS)}."),
    pill="Mainnet · live" if WL_OPEN else "Closed start",
    extra=("" if WL_OPEN else COUNTDOWN + "\n      " + WL_EARLY + "\n      " + WL_COUNT),
) + f"""
  <section class="band band--cream" data-waitlist>
    <div class="wrap">
      <p class="note wl-due"><strong>Public mining is opening.</strong> The node download appears on this page as soon as it is published. Until then the list stays open.</p>
      <div class="wl-grid">
        <div class="card wl-card" data-reveal>
          <p class="wl-notice" role="status" aria-live="polite" data-wl-notice hidden></p>
{WL_DOWNLOAD if WL_OPEN else WL_FORM + chr(10) + WL_ME}
          <p class="wl-nojs nojs-only">The sign-up form needs JavaScript. Switch it on for this page, or come back in a browser that runs it; nothing else on this site needs it.</p>
        </div>

        <div class="prose wl-about" data-reveal>
          <h2>What a place on the list is</h2>
          <p>{WL_IS}</p>
          <p><strong>{WL_IS_NOT}</strong> Mining itself, once it is open, follows the same rules for everyone.</p>
          <h2>How the order is decided</h2>
          <p>{WL_RULE}</p>
          <p>Ties go to whoever joined first. One entry per person: one email address and one SWARM address. Someone who joins from the same internet connection as the person who invited them does not count as an invite.</p>
          <h2>Your email address</h2>
          <p>We send nothing yet. We will ask you to confirm your email before opening, and we will tell you when your early access starts; every message holds a link to remove yourself. Project news comes only if you tick the second box. What is stored, where and for how long is on the <a href="/privacy#waiting-list">privacy page</a>.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap wrap--narrow">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Leaderboard</p>
        <h2>Who gets the download first.</h2>
        <p>The top 50, by invites. Addresses are shortened to their first 8 and last 4 characters; email addresses are never shown.</p>
      </div>
      <div class="tablewrap wl-board" data-reveal>
        <table>
          <caption>Waiting list for public mining, top 50. <span class="js-only" data-wl-board-note></span></caption>
          <thead>
            <tr><th scope="col" class="num">Place</th><th scope="col">SWARM address</th><th scope="col" class="num">Invites</th></tr>
          </thead>
          <tbody data-wl-board>
            <tr><td colspan="3" class="wl-board__empty"><span class="nojs-only">The leaderboard is shown when JavaScript is switched on.</span><span class="js-only">Loading the leaderboard&hellip;</span></td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <section class="band band--cream">
    <div class="wrap wrap--narrow">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Before you join</p>
        <h2>Plain answers.</h2>
      </div>
      <div class="prose" data-reveal>
        <h3>Do I need a SWARM address?</h3>
        <p>Yes, a mainnet one: it is where you would mine to. <a href="/ecosystem/wallet">SWARM Wallet</a> gives you one when you create a wallet. A testnet address (it starts with <span class="mono">swarm1</span>) is not accepted.</p>
        <h3>Joined on another device, or lost the page?</h3>
        <p>Join again with the same email address and SWARM address: you get your place and your invite link back. The &ldquo;Remove me&rdquo; button works in the browser you joined with; from anywhere else, write to <a href="mailto:{EMAIL}">{EMAIL}</a> from the email address you joined with and we remove you.</p>
        <h3>Is the closed start real?</h3>
        <p>Yes. {esc(CLOSED["summary"])} The figures are on the <a href="/network">network page</a>, and you can check the chain itself on <a href="/verify">Verify</a>.</p>
      </div>
      <div class="cta-row mt-l" data-reveal>
        <a class="btn btn--ghost" href="/ecosystem/wallet">Get SWARM Wallet</a>
        <a class="btn btn--ghost" href="/privacy#waiting-list">What we store</a>
      </div>
    </div>
  </section>
""" + FOOTER
write("waitlist/index.html", waitlist)


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
      <p>Nothing on this site is an offer or a solicitation to buy or sell anything, and nothing on it is financial, investment, legal or tax advice. The genesis block holds no spendable coins; every SWM that exists has been mined.</p>
      <p>SWM is a cryptocurrency. It has no guaranteed value and no issuer standing behind it. It can lose value, including all of it. Nobody is promising you earnings, returns or a price.</p>

      <h2>Experimental software</h2>
      <p>The node, indexer and wallet are open source, under active development, and provided as-is and without warranty of any kind. Among other things:</p>
      <ul>
        <li>The network can fork, reorganise recent blocks, or require a software upgrade. A payment is final only in the sense that the network makes it so; no fixed number of confirmations is a guarantee.</li>
        <li>Bugs may cause loss of coins, loss of data, or failure to sync.</li>
        <li>Privacy features may have defects. Shielding protects what is written to the chain; it does not protect everything about how you use a computer or a network.</li>
        <li>If you lose your recovery phrase, nobody can recover your wallet for you.</li>
      </ul>
      <p>To the fullest extent allowed by law, the SWARM contributors are not liable for any loss or damage arising from the use of this site or the software it describes.</p>

      <h2>The waiting list</h2>
      <p>A place on the <a href="/waitlist">waiting list for public mining</a> gives early access to the node download, 24 hours before everyone else, and nothing else. It is not a promise of coins, earnings or a price, it is not a purchase, and it gives no claim against anyone. We may remove entries that break the list&rsquo;s rules, such as several entries for one person.</p>

      <h2>Your own responsibility</h2>
      <p>Running a node, mining, and holding or paying with SWM use your own computer, your own electricity, your own bandwidth and your own money. Whether that is lawful, taxable and sensible where you live is yours to work out.</p>

      <h2>Licences</h2>
      <p>The software is open source; each repository carries its own licence. See <a href="https://github.com/Swarmcoin/swarm-releases" target="_blank" rel="noopener noreferrer">github.com/Swarmcoin/swarm-releases</a>.</p>

      <h2>Changes</h2>
      <p>These terms may change as the project changes. The version on this page is the current one.</p>
    </div>
  </section>
""" + FOOTER
write("terms/index.html", terms)


# ---------------------------------------------------------------- /privacy
privacy = head(
    "Privacy — SWARM",
    "swarm.green counts visits with Google Analytics, which sets two cookies. The waiting list for public mining stores the email and SWARM address you give it, on the project's own server. Nothing else is collected.",
    "/privacy",
    "SWARM — Privacy",
    "Visits are counted with Google Analytics. The waiting list stores what you type into it. Nothing else is collected.",
) + page_head(
    "Privacy",
    "Visits are counted. The waiting list keeps what you give it.",
    "What this site measures, which cookies it sets, what the waiting list stores, and how to switch all of it off.",
) + f"""
  <section class="band band--cream">
    <div class="wrap wrap--narrow prose" data-reveal>
      <h2>What this site collects</h2>
      <p>This site uses Google Analytics to count visits. When you open a page, your browser loads a script from Google and sends Google the address of that page, the page you came from, your browser, device type, screen size and language, and an approximate location (country and city) that Google works out from your IP address. We see the totals: how many people visited, which pages they opened and where they came from.</p>
      <p>There is no contact form, no newsletter and no account to create. The one place on this site where you can type your email address is the <a href="/waitlist">waiting list for public mining</a>, described below.</p>

      <h2>Cookies</h2>
      <p>Google Analytics sets two cookies on swarm.green, <span class="mono">_ga</span> and <span class="mono">_ga_3MDDZNCW6P</span>. They hold a random number that tells one browser from another, and they are kept for up to two years. The site sets no other cookie.</p>

      <h2>How to switch it off</h2>
      <p>The site works the same without Google Analytics. Any content blocker stops it. So does blocking <span class="mono">googletagmanager.com</span> and <span class="mono">google-analytics.com</span> in your browser, or Google&rsquo;s own <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener noreferrer">opt-out add-on</a>. You can delete the two cookies at any time in your browser&rsquo;s settings.</p>

      <h2 id="waiting-list">The waiting list for public mining</h2>
      <p>If you join the <a href="/waitlist">waiting list</a>, we store the email address and the SWARM address you type in, the time you joined and agreed to be on the list, the invite code you used (if any) and whose code it was, your own invite code, and a salted hash of your IP address. The hash is a one-way fingerprint made with a secret key that exists only on our server; we keep it so that one connection cannot fill the list or invite itself. The IP address itself is not stored.</p>
      <p>The form has two boxes, and they are separate. The first is needed to join: with it you agree that we keep these details to run the list and write to you when your early access starts. The second is optional and not ticked unless you tick it: with it you also agree to get SWARM project news by email; we store that choice, and the time you made it, on its own.</p>
      <p>Your invite count and the time you joined decide the order in which the node download goes out from 31 October 2026, 15:42 UTC. The public leaderboard shows only the first 8 and last 4 characters of your SWARM address and your invite count, never your email address.</p>
      <p>The list is kept on the project&rsquo;s own server, not at Google and not with a mailing service. Your request reaches that server through the site&rsquo;s hosting provider, as every request to this site does (see Server logs below). We do not sell, rent or share the list with anyone. Google Analytics counts a visit to the waiting-list page like a visit to any other page, without the invite code in the page address and without anything you type into the form.</p>
      <p>How long we keep it: if you did not ask for project news, your entry is deleted within 14 days after public mining has opened on 1 November 2026. If you did, we keep your email address and your entry for project news until you remove yourself.</p>
      <p>To leave, press &ldquo;Remove me from the list&rdquo; on the waiting-list page in the browser you joined with, use the link in any email we send you, or write to <a href="mailto:{EMAIL}">{EMAIL}</a> from the email address you joined with. Your entry is removed from the list at once: email address, SWARM address, invite code and IP hash. Our backups keep it for up to 14 days. If you were counted as someone&rsquo;s invite, that invite no longer counts for them. To stop only the project news, press &ldquo;Stop project news&rdquo; on the same page.</p>
      <p>At the moment we send no email at all. Before public mining opens we will ask you to confirm your email address with a single message, which also holds a link to remove yourself.</p>

      <h2>Pages that are not measured</h2>
      <p>The pages that open a SWARM Messenger link — <span class="mono">/call</span>, <span class="mono">/u</span>, <span class="mono">/g</span> and <span class="mono">/stickers</span> — do not load Google Analytics, and their Content-Security-Policy does not allow it. The part of such a link after <span class="mono">#</span> is a key or an invitation: it stays in your browser and is handed only to SWARM Messenger.</p>

      <h2>Third parties</h2>
      <p>Two things are loaded from another origin, both from Google: the Google Analytics script described above, from <span class="mono">googletagmanager.com</span>, and the web fonts, served by Google Fonts from <span class="mono">fonts.googleapis.com</span> and <span class="mono">fonts.gstatic.com</span>. Requesting either sends your IP address and user agent to Google, as any request to any server does, and Google handles that data under its own <a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer">privacy policy</a>. No other third-party script, frame, pixel or embed is used anywhere on this site, and the site&rsquo;s Content-Security-Policy blocks them.</p>
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
      <p>If any of this ever changes, this page changes with it. Last change: 3 October 2026, when the waiting list for public mining was added. Google Analytics was added on 30 September 2026; before that day the site set no cookies and ran no analytics.</p>
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
).replace('<link rel="canonical" href="https://swarm.green/404">', '<meta name="robots" content="noindex, follow">'
# A 404 page makes no calls to outside services (Bing's 404 guidance, read
# 2026-09-30): the analytics tag stays off it; the page keeps its own CSS and JS.
).replace('<script async src="https://www.googletagmanager.com/gtag/js?id=G-3MDDZNCW6P"></script>\n'
          '<script src="/js/analytics.js?v=2"></script>\n', '') + """
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
