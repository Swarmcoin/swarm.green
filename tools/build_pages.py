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
NETWORK = json.loads((ROOT / "data" / "network.json").read_text(encoding="utf-8"))
GENESIS = NETWORK["genesis"]
# The public addresses of the live mainnet, and the address prefixes a reader
# can use to tell at a glance which network they are looking at.
ENDPOINTS = NETWORK["endpoints"]
ADDRESS_FORMATS = NETWORK["addressFormats"]["formats"]
STATUS = NETWORK["status"]
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


# The phase timeline, byte-identical to the one in the home page's
# #roadmap section. Used at the top of /roadmap.
PHASES = """      <ol class="phases" data-reveal>
        <li class="phase is-live">
          <span class="phase__chip phase__chip--live">Live</span>
          <span class="phase__rail"><span class="phase__node"><svg class="ico" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-coin"/></svg></span></span>
          <div class="phase__card">
            <h3>SWARM mainnet</h3>
            <p>Public testnet <b>21 September 2026</b>; mainnet <b>26 September 2026</b>. The coin, the chain and the apps to run them. Block 1 was mined in public from a genesis block that holds nothing; every SWM since has been mined.</p>
            <p class="phase__you">You can</p>
            <ul class="phase__list">
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>mine with one click in SWARM Node</span></li>
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>hold, send and receive SWM, shielded or transparent, in SWARM Wallet</span></li>
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
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>run a node and light up your city on the map</span></li>
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>mine on the computer you already own</span></li>
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
          <span class="phase__chip">Then</span>
          <span class="phase__rail"><span class="phase__node"><svg class="ico" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-browser"/></svg></span></span>
          <div class="phase__card">
            <h3>Privacy browser</h3>
            <p>A browser with the SWARM wallet built in. Paying a site is one click with the same confirmation screen as the wallet; trackers are blocked, fingerprinting is reduced, nothing phones home, and each site gets only the permissions you give it.</p>
            <p class="phase__you">You can</p>
            <ul class="phase__list">
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>pay from the address bar</span></li>
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>browse without being followed</span></li>
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>give a site access to your wallet only when you choose</span></li>
            </ul>
          </div>
        </li>
        <li class="phase">
          <span class="phase__chip">Then</span>
          <span class="phase__rail"><span class="phase__node"><svg class="ico" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-message"/></svg></span></span>
          <div class="phase__card">
            <h3>Private messaging</h3>
            <p>End-to-end encrypted messages between people who hold SWARM wallets, with payments inside the conversation. Your chat identity is separate from your spending key, relays see only what they need to deliver, and no message is ever written to the chain.</p>
            <p class="phase__you">You can</p>
            <ul class="phase__list">
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>message and pay in one place</span></li>
              <li><svg class="ico ico--tick" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span>send an invoice in a chat</span></li>
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
<link rel="icon" href="/favicon.svg?v=2" type="image/svg+xml">
<link rel="mask-icon" href="/assets/logo-mono-dark.svg?v=2" color="#F5A623">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&family=Sora:wght@600;700;800&display=swap">
<link rel="stylesheet" href="/css/site.css?v=6">
<script src="/js/boot.js?v=4"></script>
<script src="/js/site.js?v=14" defer></script>
</head>
<body>
{SPRITE}

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
      <a href="/#mainnet">Mainnet</a>
      <a href="/mining">Mine</a>
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
        <li><a href="/mining">Mine</a></li>
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
          <li><a href="/join">Get SWARM</a></li>
          <li><a href="/mining">How to mine</a></li>
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
        ("Launched", esc(STATUS["launchedLabel"]), "mono"),
    ])

# The public addresses of the live network. seed-main is a peer address on the
# P2P port, not a web address: linking it as https:// reaches a web server that
# holds no certificate for it, and an audit has read that failure as a fault
# once already. It is printed, never linked.
endpoint_rows = "\n".join(
    f'          <tr><th scope="row">{k}</th><td class="{cls}">{v}</td></tr>'
    for k, v, cls in [
        ("Seed node (P2P)", esc(ENDPOINTS["seed"]), "mono"),
        ("Light-wallet server (TLS)", esc(ENDPOINTS["lightWallet"]), "mono"),
        ("Node RPC", esc(ENDPOINTS["rpcPort"]) + " \u2014 " + esc(ENDPOINTS["rpcNote"]), ""),
        ("Mainnet block explorer",
            f'<a href="{ENDPOINTS["explorerMainnet"]}" target="_blank" rel="noopener noreferrer">'
            f'mainnet.explore.swarm.green{EXT}</a> \u2014 live, showing SwarmMainnet', ""),
        ("Testnet block explorer",
            f'<a href="{ENDPOINTS["explorerTestnet"]}" target="_blank" rel="noopener noreferrer">'
            f'explore.swarm.green{EXT}</a> \u2014 the public testnet, whose coins have no value', ""),
    ])

address_rows = "\n".join(
    f'          <tr><th scope="row" class="mono">{esc(f["prefix"])}</th>'
    f'<td>{esc(f["network"])}</td><td>{esc(f["kind"])} \u2014 {esc(f["detail"])}</td></tr>'
    for f in ADDRESS_FORMATS)

network = head(
    "Network &amp; supply — SWARM",
    "Every SWARM parameter in one place: 75-second blocks, 6.25 SWM per block, halving every 1,680,000 blocks, a ceiling of 20,999,987.3152 SWM, no premine, the four-way block reward split fixed for the whole emission schedule, and the genesis block it is all fixed in.",
    "/network",
    "SWARM — Network &amp; supply",
    "75-second blocks, 6.25 coins per block, halving every 1,680,000 blocks, a ceiling of 20,999,987.3152 coins and no premine.",
) + page_head(
    "Network &amp; supply",
    "Every number, in one place.",
    "The monetary base is fixed in the code. Nothing on this page is a projection — it is arithmetic you can check yourself against the source, and against the chain with your own node.",
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
        ("Launched", f'<span class="mono">{esc(STATUS["launchedLabel"])}</span>'),
        ("Genesis block hash", copyline(GENESIS["hash"], "the genesis block hash")),
        ("Genesis header time", f'<span class="mono">{esc(GENESIS["headerTimeUtc"])}</span>'),
        ("Spendable outputs in the genesis block",
            f'{esc(GENESIS["spendableOutputs"])} &mdash; there is no premine'),
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
    "Genesis 01c34428…afdd. Check the chain you joined is the one that was announced.",
) + page_head(
    "Verify",
    "Check you are on the real chain.",
    "A chain is identified by its genesis block. SWARM Node compares the genesis it loads against the one below before it syncs anything &mdash; and so can you. Nothing on this page needs to be taken on trust: every value is published, and every one of them is something your own node will report back to you.",
    pill="Mainnet · live",
) + f"""
  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">The launch</p>
        <h2>One block, published in advance.</h2>
        <p>SWARM mainnet started on <strong>{esc(STATUS["launchedLabel"])}</strong>. The rules, the genesis block and the three destination addresses were published before block 1 was mined, so there was no window in which anyone could mine in private. The genesis block holds no spendable coins: there is no premine, no sale and no head start.</p>
      </div>

      <div class="tablewrap" data-reveal>
        <table>
          <caption>The SWARM mainnet launch, as published in the launch manifest.</caption>
          <tbody>
{launch_rows}
          </tbody>
        </table>
      </div>

      <div class="cards mt-l" data-reveal>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-node"/></svg></div>
          <h3>In SWARM Node</h3>
          <p>Open <em>Settings &rarr; Network</em>. It prints the chain, the genesis hash and the ports the app is using. If the genesis hash there is not the one above, you are not on SWARM mainnet.</p>
          <p class="mt-m"><a class="btn btn--ghost btn--sm" href="/ecosystem/node">Get SWARM Node{ARROW}</a></p>
        </article>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-explorer"/></svg></div>
          <h3>In the block explorer</h3>
          <p>Look up height 0 in the mainnet explorer. It shows the same hash, the same header time and an empty coinbase. The explorer is a convenience &mdash; your own node is still the authority.</p>
          <p class="mt-m"><a class="btn btn--ghost btn--sm" href="{ENDPOINTS["explorerMainnet"]}" target="_blank" rel="noopener noreferrer">Open the explorer{EXT}</a></p>
        </article>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-code"/></svg></div>
          <h3>From the source</h3>
          <p>The launch manifest, the source at the launch commit and every release with its SHA-256 are in the release repository. Build the node yourself and it will derive the same genesis.</p>
          <p class="mt-m"><a class="btn btn--ghost btn--sm" href="{GH_SOURCE}" target="_blank" rel="noopener noreferrer">Release repository{EXT}</a></p>
        </article>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Where the apps connect</p>
        <h2>The public addresses of the live network.</h2>
        <p><code>seed-main.swarm.green</code> is a <strong>peer address on the P2P port</strong>, not a web address. Opening it as <code>https://</code> reaches a web server that holds no certificate for it; that refusal is correct behaviour, not a fault.</p>
      </div>

      <div class="tablewrap" data-reveal>
        <table>
          <caption>SWARM mainnet endpoints.</caption>
          <tbody>
{endpoint_rows}
          </tbody>
        </table>
      </div>

      <p class="note mt-m" data-reveal>You do not have to use any of them. A node with no seed configured will still find peers, and a node you build yourself connects to whichever peers you point it at. These are the addresses the published apps use by default.</p>
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
          <p>The project also mines, like anyone else. That payout goes to an ordinary private wallet, and it is <strong>not</strong> published: publishing it would hand everyone a permanent view of a wallet that has no governance role.</p>
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


# ----------------------------------------------------------------- /mining
# How to mine, written against the shipped app rather than against the spec:
# every screen name, button label, engine name and caution below is the wording
# SWARM Node 0.2.0-mainnet.5 itself uses, so a reader can follow this page with
# the app open beside it. The live figures come from the seed's own status.json
# through the /data/status.json rewrite in vercel.json (the strict CSP allows
# same-origin fetches only), and the static markup is the no-JavaScript state.
mining = head(
    "How to mine SWARM — SWARM",
    "Mine SWARM on an ordinary computer: Equihash 200,9 on your CPU, no pool, a block every 75 seconds and 5 SWM plus fees to whoever finds it. Download SWARM Node, paste a payout address, press Start.",
    "/mining",
    "How to mine SWARM",
    "CPU mining, no pool, one button. 5 SWM plus fees to whoever finds the block.",
) + page_head(
    "Mining",
    "Mine on the computer you already own.",
    "SWARM&rsquo;s proof of work is <strong>Equihash 200,9</strong>, inherited unchanged, and the chain started at minimum difficulty. There is no pool and no account: your machine looks for blocks, and the protocol pays whoever finds one straight to an address you chose. One app does all of it, and it only ever runs while you have pressed Start.",
    pill="Mainnet · live",
) + f"""
  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">How it works</p>
        <h2>Find a block, keep the reward.</h2>
        <p>Mining is a race to find a valid next block. Every machine on the network is working on the same problem; the first to solve it publishes the block, everyone else verifies it and starts on the next one. Nothing is shared out and nothing is owed to you &mdash; the reward belongs to the block you found.</p>
      </div>

      <div class="cards" data-reveal>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-mining"/></svg></div>
          <h3>Equihash 200,9, on your CPU</h3>
          <p>The proof of work is inherited unchanged. The chain started at minimum difficulty, so an ordinary computer can find blocks from the first one. Nothing in the rules keeps larger miners out later, and we do not pretend otherwise.</p>
        </article>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-coin"/></svg></div>
          <h3>5 SWM plus fees, not 6.25</h3>
          <p>A block pays <strong>6.25 SWM</strong> in the first era, and the miner&rsquo;s share is <strong>80%</strong>. So a block you find pays you <strong>5.00 SWM</strong> plus that block&rsquo;s transaction fees. The other 20% goes to the three project funds, block by block, in public.</p>
        </article>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-honey"/></svg></div>
          <h3>100 blocks before you can spend it</h3>
          <p>A transparent mining reward needs <strong>100 confirmations</strong> &mdash; about two hours at target spacing &mdash; before it can be spent. That rule is inherited and it applies to every miner equally. Shielded rewards have no coinbase maturity countdown; your wallet tells you what is spendable.</p>
        </article>
        <article class="card">
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-layers"/></svg></div>
          <h3>Difficulty moves every block</h3>
          <p>The target is a block every <strong>75 seconds</strong>. Difficulty is recomputed at every block from a 17-block mean and 11-block median times, damped and bounded to roughly +16% / &minus;32% per block, so it follows the hash power on the network instead of waiting for a fortnightly reset.</p>
        </article>
      </div>

      <div class="panel mt-l" data-reveal>
        <h3>You mine alone &mdash; there is no pool.</h3>
        <p>Whichever machine finds the next valid block first gets that block&rsquo;s full reward, paid by the protocol straight to your payout address. A machine that just started can win several blocks in a row &mdash; that is luck on a small number of blocks, not a preference. Over time every miner earns in proportion to its share of the network&rsquo;s total hash power.</p>
        <p class="mt-s">That is the same sentence SWARM Node prints on its own Mining screen. There is no pool protocol yet, no payout smoothing and no minimum withdrawal, because there is nothing to withdraw: the protocol pays the address you pasted.</p>
      </div>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">The network right now</p>
        <h2>What you would be mining against.</h2>
        <p>Read live from the seed server&rsquo;s public status file. These are the only network-wide figures the project publishes, and they are the same ones your own node will report once it has caught up.</p>
      </div>

      <div class="stats" data-netstatus>
        <div class="stat"><div class="stat__in"><div class="stat__v" data-net="height">&mdash;</div><div class="stat__l">Block height</div></div></div>
        <div class="stat"><div class="stat__in"><div class="stat__v" data-net="difficulty">&mdash;</div><div class="stat__l">Difficulty</div></div></div>
        <div class="stat"><div class="stat__in"><div class="stat__v" data-net="interval">&mdash;</div><div class="stat__l">Mean block time, last 100</div></div></div>
        <div class="stat"><div class="stat__in"><div class="stat__v">75<small>s</small></div><div class="stat__l">Target block time</div></div></div>
      </div>

      <p class="note mt-l" data-reveal><span data-net="foot">Live figures load from the seed server. With JavaScript off, or if the seed cannot be reached, the dashes stay &mdash; the page never guesses a number.</span></p>

      <p class="note mt-m" data-reveal><strong>No projections, here or in the app.</strong> We do not publish an expected-earnings calculator, a per-day figure or a fiat value, because any such number would be an invention: it depends on hash power that changes block by block. What you can check is the arithmetic &mdash; your share of the network&rsquo;s hash power is your expected share of the blocks. SWARM Node&rsquo;s <em>Node</em> screen shows <strong>Network hash rate</strong> and <strong>Difficulty</strong> as measured by your own node, with the caveat the app prints itself: a dash means it has not measured that yet, and the hash rate needs a few blocks before it means anything.</p>
    </div>
  </section>

  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Step by step</p>
        <h2>From download to first block.</h2>
        <p>One app is all of it: SWARM Node is a full node and a miner together. It never mines without you pressing the button, and closing the window stops everything.</p>
      </div>

      <div class="steps" data-reveal>
        <article class="card step">
          <div class="step__n" aria-hidden="true">1</div>
          <p class="step__app">SWARM Node</p>
          <h3>Download it</h3>
          <p>Windows installer or portable zip; Debian/Ubuntu <span class="mono">.deb</span> or a portable AppImage for Linux. Check the SHA-256 on the download page before you install.</p>
          <p class="mt-s">No build is code-signed yet. Windows SmartScreen will warn you: <em>More info</em> &rarr; <em>Run anyway</em>. macOS blocks the first open: right-click the app in Applications and choose <em>Open</em>. Both are expected, and the SHA-256 is what actually tells you the file is the published one.</p>
          <a class="btn btn--primary" href="/ecosystem/node">Get SWARM Node</a>
        </article>

        <article class="card step">
          <div class="step__n" aria-hidden="true">2</div>
          <p class="step__app">First run</p>
          <h3>Agree to what will run</h3>
          <p>On first run the app asks you to tick, one line at a time, exactly what it is about to do: run a full node, use your CPU <em>only</em> while you have pressed Start, store nothing about you but a payout address, and stop completely when you close it.</p>
          <p class="mt-s">It then checks this machine and prints what it found: processor, memory, free disk, and whether port <span class="mono">28233</span> is free. It never uploads any of that.</p>
        </article>

        <article class="card step">
          <div class="step__n" aria-hidden="true">3</div>
          <p class="step__app">Payout</p>
          <h3>Paste a payout address</h3>
          <p>Open SWARM Wallet, copy a receive address, paste it in. The app checks the format offline and then asks your own node to confirm it. The protocol pays rewards straight to that address &mdash; SWARM Node never holds your coins, so there is nothing to withdraw later.</p>
          <p class="mt-s">Which address you paste decides how you mine. That is the next section.</p>
          <a class="btn btn--ghost btn--sm" href="/ecosystem/wallet">Get SWARM Wallet{ARROW}</a>
        </article>

        <article class="card step">
          <div class="step__n" aria-hidden="true">4</div>
          <p class="step__app">Mining</p>
          <h3>Press Start mining</h3>
          <p>One button. It starts your node, waits for it to catch up, and begins mining on its own. The line under the button says where it has got to, and the same button stops it again.</p>
          <p class="mt-s">It will hold back until your node has at least one peer and is level with the network &mdash; mining on a node that cannot see the network builds a private fork that everybody else throws away. Press it and walk away; mining begins by itself.</p>
        </article>

        <article class="card step">
          <div class="step__n" aria-hidden="true">5</div>
          <p class="step__app">Honey</p>
          <h3>Watch the Honey page</h3>
          <p>Every block this machine finds appears there the moment the network accepts it, with its height, whether it was paid transparently or shielded, and how many confirmations it still needs.</p>
          <p class="mt-s">There is nothing to claim. Open your wallet to spend it.</p>
        </article>
      </div>

      <p class="note mt-l" data-reveal>The installer for SWARM mainnet starts on <strong>SWARM Mainnet</strong> by itself, on a fresh machine or over an old testnet install. The band across the top of every screen says which chain you are on: <span class="mono">SwarmMainnet &middot; SWARM mainnet &middot; chain swarm-mainnet &middot; genesis 01c34428&hellip;</span> &mdash; and <em>Settings &rarr; Network</em> has the full genesis, the ports and the switcher. If that band ever says anything else, stop and check <a href="/verify">Verify</a>.</p>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">The one real choice</p>
        <h2>Shielded on one core, or transparent on many.</h2>
        <p>SWARM Node has two mining engines, and the address you paste decides which one you get. Both pay you directly; neither is a pool. The app states the trade-off on the Mining screen under <em>How you mine</em>, and it is worth understanding before you paste.</p>
      </div>

      <div class="cards cards--2" data-reveal>
        <article class="card">
          <p class="pill">Shielded &middot; 1 core</p>
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-shield"/></svg></div>
          <h3>Paste a <span class="mono">swm1&hellip;</span> address</h3>
          <p>A unified address. <strong>Rewards paid to it are private.</strong> It works with shielded mining, which runs on one core inside the node and pays into your unified address where nobody can see the amount.</p>
          <p class="mt-s">Slower, because it is one core. There is no coinbase maturity countdown on a shielded reward, and the app cannot read the amount either &mdash; your wallet is what tells you the balance.</p>
        </article>
        <article class="card">
          <p class="pill">Standard &middot; many cores</p>
          <div class="hexicon" aria-hidden="true"><svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-desktop"/></svg></div>
          <h3>Paste an <span class="mono">s1&hellip;</span> address</h3>
          <p>A transparent address. <strong>Rewards paid to it are visible on the explorer.</strong> It works with standard mining, which uses as many processor cores as you choose.</p>
          <p class="mt-s">Faster, because it is every core you allow. Anyone can see what that address has been paid, and a transparent reward needs 100 confirmations before it can be spent.</p>
        </article>
      </div>

      <p class="note mt-m" data-reveal>You cannot have both at once, and the app will not pretend you can: it greys out whichever engine your address does not fit and says why. Change your mind by pasting the other kind of address in <em>Settings</em>. Switching shielded mining on or off restarts the node, because that is the only moment the node reads that setting. Mainnet payout addresses start <span class="mono">s1&hellip;</span> or <span class="mono">swm1&hellip;</span>; a testnet address, or an upstream Zcash address, is refused before your node is even asked. See <a href="/verify">the address prefixes</a>.</p>
    </div>
  </section>

  <section class="band band--cream">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">What the screens show</p>
        <h2>Four numbers, and what each one is not.</h2>
        <p>Every figure on the Mining screen comes from the chain, from the miner&rsquo;s own output, or from this machine. Anything unknown renders as a dash rather than a zero.</p>
      </div>

      <div class="tablewrap" data-reveal>
        <table>
          <caption>The Mining screen, tile by tile.</caption>
          <thead>
            <tr><th scope="col">Tile</th><th scope="col">What it is</th><th scope="col">What it is not</th></tr>
          </thead>
          <tbody>
            <tr><th scope="row">Hash rate</th><td>Solutions per second from your own machine, in <span class="mono">Sol/s</span>, measured by the solver that is actually running.</td><td>Not the network&rsquo;s rate, and not an estimate. A dash means nothing has reported a rate yet.</td></tr>
            <tr><th scope="row">Blocks found</th><td>Blocks <em>this machine</em> found and the network accepted, split into transparent and shielded once both exist.</td><td>Not your wallet history, and not blocks found by your other machines.</td></tr>
            <tr><th scope="row">Mature rewards</th><td>Mining income past 100 confirmations. On a shielded payout the tile is called <em>Shielded subsidy</em> instead.</td><td>Not your wallet balance. The app never holds coins and cannot see what else is in your wallet.</td></tr>
            <tr><th scope="row">Honey maturing</th><td>Rewards still counting down, with the number of blocks until the next one unlocks.</td><td>Not applicable to shielded rewards, which have no coinbase maturity rule.</td></tr>
          </tbody>
        </table>
      </div>

      <p class="note mt-m" data-reveal>The <em>Node</em> screen adds the chain-wide view: block height, newest block, peers, disk used, and &mdash; once your node has measured them &mdash; <strong>Network hash rate</strong> and <strong>Difficulty</strong>. The <em>Log</em> screen shows every line tagged <strong>node</strong>, <strong>miner</strong> or <strong>app</strong>, so you can see which part of the system said what.</p>
    </div>
  </section>

  <section class="band band--dark2">
    <div class="wrap">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Living with it</p>
        <h2>Keeping the machine usable.</h2>
      </div>

      <div class="cards" data-reveal>
        <article class="card">
          <h3>Leave yourself a core</h3>
          <p>The core slider reads <em>How many cores to use</em>, and the maximum it offers is one fewer than your machine has: <strong>one core is always left free so the machine stays usable</strong>. Turn it down further any time; it takes effect without a restart.</p>
        </article>
        <article class="card">
          <h3>Pause while you are at the keyboard</h3>
          <p>There is a switch labelled <em>Pause while I am using this machine (starts again after two minutes of no keyboard or mouse)</em>. With it on, the miner steps aside the moment you touch the machine and picks up again two minutes after you stop.</p>
        </article>
        <article class="card">
          <h3>Heat, fans and electricity</h3>
          <p>Mining runs your processor at full load for as long as it is on. That means heat, fan noise and a real electricity bill. On a laptop, expect it to get hot and to drain on battery. Nothing about SWARM makes that cheaper, and we will not tell you it pays for itself.</p>
        </article>
        <article class="card">
          <h3>More than one machine</h3>
          <p>Run SWARM Node on as many machines as you like, each with its own full node, and point them all at the same payout address if you want the rewards in one place. They do not need to know about each other &mdash; they are simply more of the swarm.</p>
          <p class="mt-s">Each machine keeps its own copy of the chain, so budget the disk on each of them.</p>
        </article>
      </div>

      <div class="cards cards--2 mt-l" data-reveal>
        <article class="card">
          <h3>Linux</h3>
          <p>The <span class="mono">.deb</span> installs on Debian and Ubuntu; the AppImage runs anywhere without installing &mdash; mark it executable and run it. Both are built from the same commit as the Windows package and carry their own SHA-256.</p>
          <p class="mt-s"><strong>Stated plainly:</strong> the Linux packages have not been run on a Linux machine by the project. Same source, same pipeline as Windows; nothing more is claimed.</p>
        </article>
        <article class="card">
          <h3>macOS</h3>
          <p>Disk image or portable zip, for Apple silicon and for Intel, each with its SHA-256. <strong>These builds are not code-signed</strong>, so the first open is blocked: right-click <em>SWARM Node</em> in Applications and choose <em>Open</em>, or run <span class="mono">xattr -d com.apple.quarantine</span> on it in Terminal.</p>
          <p class="mt-s">Signing and notarization happen on the owner&rsquo;s Mac, never in CI. A signed build follows, and it is on the <a href="/roadmap">roadmap</a> as in development.</p>
        </article>
      </div>

      <div class="note mt-l" data-reveal>
        <strong>What the machine check looks for.</strong> These are the app&rsquo;s own thresholds, measured locally and never uploaded.
        <ul class="note__list">
          <li><strong>2 CPU cores or more.</strong></li>
          <li><strong>4 GB of memory or more.</strong></li>
          <li><strong>10 GB of free disk</strong> where the chain is stored. Mainnet started on 26 September 2026, so the chain is still small &mdash; leave room for it to grow.</li>
          <li><strong>64-bit Windows 10 or newer</strong>, or Linux.</li>
          <li><strong>Port 28233 free</strong> on this machine. Whether your router lets other nodes in cannot be tested from here, and mining works either way.</li>
        </ul>
      </div>
    </div>
  </section>

  <section class="band band--cream">
    <div class="wrap wrap--narrow">
      <div class="sec-head" data-reveal>
        <p class="eyebrow">Questions</p>
        <h2>The ones that actually come up.</h2>
      </div>

      <div class="faq" data-reveal>
        <details>
          <summary>Why do blocks come in bursts, then nothing for ages?<span class="ind" aria-hidden="true"></span></summary>
          <div class="answer"><p>Because finding a block is a lottery draw, not a queue. Every attempt is independent, so the gaps between blocks follow a random distribution around the 75-second target: several in a minute, then a long quiet stretch, is exactly what that looks like. It is not a fault and it is not the network favouring anyone.</p><p>Difficulty only recalculates when a block arrives, and it is bounded to roughly +16% / &minus;32% per block. So when a large miner leaves, the first blocks at the raised difficulty genuinely do take a long time, and recovery is measured in slow blocks rather than in minutes.</p></div>
        </details>
        <details>
          <summary>Why do rewards have to mature?<span class="ind" aria-hidden="true"></span></summary>
          <div class="answer"><p>Because a block at the tip of the chain can still be replaced. If a competing chain turns out to have more work behind it, the block you found &mdash; and its reward &mdash; goes away with it. The 100-block wait means a coinbase reward cannot be spent until it is buried deep enough that reversing it is impractical, which protects whoever you would have paid with it.</p><p>It is an inherited rule and it applies to every miner equally. Shielded rewards have no coinbase maturity countdown; your wallet shows what is spendable.</p></div>
        </details>
        <details>
          <summary>Why is there no pool?<span class="ind" aria-hidden="true"></span></summary>
          <div class="answer"><p>Because nobody has built one for SWARM yet. A pool needs a protocol for handing out work, a way of measuring each miner&rsquo;s contribution and an operator who takes custody of rewards before paying them out &mdash; and that last part is exactly the kind of thing we want reviewed before it exists, not bolted on.</p><p>A pool protocol is on the <a href="/roadmap">roadmap</a> as planned, with no date. Until then every miner is solo: whoever finds the block keeps it, and the protocol pays your address directly.</p></div>
        </details>
        <details>
          <summary>The network is small. Is that good or bad for me?<span class="ind" aria-hidden="true"></span></summary>
          <div class="answer"><p>Both, honestly. A small network means your machine is a large share of the total hash power, so you find blocks far more often than you would on an established chain. It also means the chain has less accumulated work behind it, fewer nodes checking it, and a single large miner arriving would change your share overnight.</p><p>Equihash hardware already exists and hash power for it can be rented. A single current-generation ASIC out-hashes thousands of home PCs, so from the moment one joins, home mining stops being competitive at the difficulty it sets. That is a consequence of keeping the rules open rather than inventing a hardware gate, and we would rather write it here than let you discover it.</p></div>
        </details>
        <details>
          <summary>What will I earn?<span class="ind" aria-hidden="true"></span></summary>
          <div class="answer"><p>Your share of the network&rsquo;s hash power is your expected share of the blocks, and each block you find pays 5.00 SWM plus that block&rsquo;s fees. We will not turn that into a number for you: it depends on hash power that changes block by block, on your electricity price, and on a market price that SWARM does not set, promise or have any say in.</p><p>SWM can lose value, including all of it. Mine because you want to run a piece of the network, not because a website told you what it pays.</p></div>
        </details>
        <details>
          <summary>Why will it not start mining?<span class="ind" aria-hidden="true"></span></summary>
          <div class="answer"><p>The app tells you, in one line under the button. The usual reasons: your node is still downloading the chain; it has no peers yet, so it cannot tell whether it is on the real chain; or there is no payout address saved. In every case the button stays pressable &mdash; press it and mining starts by itself the moment the node is ready.</p><p>If it has been waiting far longer than it should, the app offers <em>Start anyway</em> beside the main button and explains the risk: your node may not be on the network&rsquo;s best chain, and blocks you find could be discarded.</p></div>
        </details>
        <details>
          <summary>Does it mine when I am not looking?<span class="ind" aria-hidden="true"></span></summary>
          <div class="answer"><p>No. Mining starts when you press Start and stops when you press Stop, when you close the window, or when the node loses the network. There is no silent mode, no background service and no setting that starts it at boot. Closing the window stops the node and the miner too.</p></div>
        </details>
      </div>

      <div class="cta-row mt-l" data-reveal>
        <a class="btn btn--primary" href="/ecosystem/node">Get SWARM Node</a>
        <a class="btn btn--ghost" href="/verify">Check you are on the real chain</a>
      </div>
    </div>
  </section>
""" + FOOTER
write("mining/index.html", mining)


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
          <a class="btn btn--primary" href="/mining">How to mine</a>
        </article>
      </div>

      <p class="note mt-l" data-reveal>Mining has a page of its own: <a href="/mining">how mining works on SWARM</a>, which engine your payout address picks, what each number on the screen means, and what it costs you in heat and electricity. Every app, the block explorer and the source code are listed together in <a href="/ecosystem">Ecosystem</a>.</p>

      <div class="cards cards--2 mt-l" data-reveal>
        <article class="card">
          <h3>SWARM Explorer</h3>
          <p>A block explorer, so you can watch what the chain is actually doing: blocks as they are found, the supply as it is issued, and the four-way allocation in every block. The mainnet explorer is live at mainnet.explore.swarm.green. Your own node is still the authority — the explorer just makes it easy to look.</p>
          <p class="mt-m"><a class="btn btn--ghost btn--sm" href="/ecosystem">See the ecosystem{ARROW}</a></p>
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
            <svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-lock"/></svg>
          </div>
          <h3>Back up your recovery phrase offline</h3>
          <p>Write the phrase down on paper and store it somewhere safe. Do not photograph it, do not put it in a password manager you do not control, and do not type it into anything that asks you to &ldquo;verify&rdquo; it on a website.</p>
          <p class="mt-s">Anyone who has the phrase has the coins. If you lose it, nobody — including us — can recover your wallet for you.</p>
        </article>
        <article class="card">
          <div class="hexicon" aria-hidden="true">
            <svg class="ico" viewBox="0 0 32 32" focusable="false"><use href="#i-mining"/></svg>
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
          <li><strong>10 GB of free disk</strong> for the chain. Mainnet started on 26 September 2026, so the chain is still small; leave room for it to grow.</li>
          <li><strong>An internet connection.</strong></li>
          <li><strong>Port 28233 open &mdash; only if you want other nodes to be able to connect to you.</strong> Mining and syncing work without it.</li>
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
        <p>A chain is identified by its genesis block: <span class="mono">{GENESIS["hash"][:8]}&hellip;{GENESIS["hash"][-4:]}</span>. SWARM Node compares the genesis it loads with that one before it syncs anything, and you can do the same by hand. The launch facts, the public endpoints, the three published fund addresses and the address prefixes are all on one page.</p>
      </div>
      <div class="cta-row" data-reveal>
        <a class="btn btn--primary" href="/verify">Verify the chain</a>
        <a class="btn btn--ghost" href="{GH_SOURCE}" target="_blank" rel="noopener noreferrer">Release repository{EXT}</a>
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
        <p class="eyebrow">Then</p>
        <h2>A privacy browser.</h2>
        <p>A browser with the SWARM wallet built in, so paying a site is one click and no site sees more of you than it must.</p>
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
