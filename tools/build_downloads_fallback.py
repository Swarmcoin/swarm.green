#!/usr/bin/env python3
"""Writes the no-JavaScript fallback for the Downloads section into index.html
from data/downloads.json.

    python tools/build_downloads_fallback.py

js/site.js renders the same data as tabs, one platform at a time. Without
JavaScript there are no tabs to click, so this fallback lists every platform in
full, stacked, inside each card. Running this after any edit to
data/downloads.json is what keeps the two in step; nothing here is written by
hand.
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "downloads.json").read_text(encoding="utf-8"))
INDEX = ROOT / "index.html"

OS_LABEL = {"windows": "Windows", "macos": "macOS", "linux": "Linux",
            "android": "Android", "ios": "iPhone", "web": "Web", "source": "GitHub"}
GLYPHS = {
    "desktop": ['M3 5.5h18v11H3z', 'M9 20h6', 'M12 16.5V20'],
    "phone": ['M7.6 2.6h8.8v18.8H7.6z', 'M10.6 5.4h2.8'],
    "explorer": ['M11 4.2a6.8 6.8 0 1 0 0 13.6 6.8 6.8 0 0 0 0-13.6z', 'M16 16l4.4 4.4'],
    "code": ['M8.6 7 3.4 12l5.2 5', 'M15.4 7l5.2 5-5.2 5', 'M13.6 4.4l-3.2 15.2'],
}
META = DATA["meta"]
ORDER = META.get("osOrder", [])


def esc(v):
    return html.escape(str(v), quote=False)


def glyph(name):
    paths = GLYPHS.get(name)
    if not paths:
        return ""
    body = "".join('<path d="%s"/>' % p for p in paths)
    return ('          <div class="hexicon" aria-hidden="true">\n'
            '            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round" focusable="false">%s</svg>\n'
            '          </div>\n' % body)


def notice_for(os_key, primary):
    if primary is not None:
        if primary.get("notes"):
            return primary["notes"]
        return {"windows": META.get("windowsNotice", ""),
                "macos": META.get("macosNotice", ""),
                "linux": META.get("linuxNotice", "")}.get(os_key, META.get("unsignedNotice", ""))
    if os_key in ("ios", "android"):
        return META.get("mobileNotice", "")
    return ""


def pane(product, os_key, entries, tabbed):
    label = OS_LABEL.get(os_key, os_key)
    ready = [e for e in entries if e["state"] == "available" and e.get("url")]
    primaries = [e for e in ready if e.get("role") != "alt"]
    primary = primaries[0] if primaries else None
    alts = [e for e in ready if e.get("role") == "alt"]
    out = []

    if tabbed:
        out.append('            <p class="dl__osname">%s</p>' % esc(label))

    # two explicit lines: platform, then version and size
    if primary:
        line1 = primary["platform"] if len(primaries) > 1 else " · ".join(
            [x for x in (primary["platform"], primary.get("sizeShort")) if x])
        line2 = primary.get("version", "")
    else:
        pending = entries[0] if entries else {}
        line1 = label
        line2 = pending.get("plannedVersion") or product.get("soonMeta", "")
    out.append('            <p class="dl__spec"><span class="dl__specos">%s</span>'
               '<span class="dl__specmeta">%s</span></p>' % (esc(line1), esc(line2)))

    if primaries:
        for i, e in enumerate(primaries):
            if product.get("kind") == "link":
                text, extra = "Open", ' target="_blank"'
                vh = '<span class="vh"> %s (opens in a new tab)</span>' % esc(product["name"])
            elif e["os"] == "android":
                text, extra, vh = "Download APK", "", ""
            elif e.get("arch"):
                text, extra = "Download for %s" % e["arch"], ""
                vh = '<span class="vh"> of %s for %s</span>' % (esc(product["name"]), esc(label))
            else:
                text, extra, vh = "Download for %s" % label, "", ""
            kind = "btn--primary" if i == 0 else "btn--ghost"
            out.append('            <a class="btn %s btn--sm dl__cta" href="%s"%s rel="noopener noreferrer">%s%s</a>'
                       % (kind, esc(e["url"]), extra, esc(text), vh))
    else:
        out.append('            <button class="btn btn--soon btn--sm dl__cta" type="button" disabled>Coming soon</button>')

    for e in entries:
        if e["state"] != "available" and primary is not None and e["platform"] != primary["platform"]:
            out.append('            <p class="dl__alt dl__alt--soon">%s: coming soon.</p>' % esc(e["platform"]))

    for a in alts:
        text = a.get("label") or (a.get("variant", "") + (" (%s)" % a["sizeShort"] if a.get("sizeShort") else ""))
        out.append('            <p class="dl__alt"><a class="textlink" href="%s" rel="noopener noreferrer">%s</a></p>'
                   % (esc(a["url"]), esc(text)))

    note = notice_for(os_key, primary)
    if note:
        out.append('            <p class="dl__notice">%s</p>' % esc(note))

    if len(primaries) > 1:
        out.append('            <details class="dl__sum">')
        out.append('              <summary>Checksums</summary>')
        out.append('              <div class="dl__sumbody">')
        for e in primaries:
            if not e.get("sha256"):
                continue
            tag = (e.get("arch") or e["platform"]) + (" · " + e["sizeShort"] if e.get("sizeShort") else "")
            out.append('                <p class="dl__sumlabel">%s</p>' % esc(tag))
            out.append('                <code class="dl__hashline">%s</code>' % esc(e["sha256"]))
            out.append('                <p class="dl__sumrow"><button class="btn btn--ghost btn--sm" type="button" data-copy="%s">Copy<span class="vh"> the SHA-256 checksum for %s %s</span></button></p>'
                       % (esc(e["sha256"]), esc(product["name"]), esc(e.get("arch") or label)))
        if primary.get("checksums"):
            out.append('                <p class="dl__sumrow"><a class="textlink" href="%s" target="_blank" rel="noopener noreferrer">SHA256SUMS<span class="vh"> for this release (opens in a new tab)</span></a></p>'
                       % esc(primary["checksums"]))
        out.append('              </div>')
        out.append('            </details>')
    elif primary and primary.get("sha256"):
        sha = esc(primary["sha256"])
        out.append('            <details class="dl__sum">')
        out.append('              <summary>Checksum</summary>')
        out.append('              <div class="dl__sumbody">')
        out.append('                <code class="dl__hashline">%s</code>' % sha)
        out.append('                <p class="dl__sumrow"><button class="btn btn--ghost btn--sm" type="button" data-copy="%s">Copy<span class="vh"> the SHA-256 checksum for %s on %s</span></button>'
                   % (sha, esc(product["name"]), esc(label)))
        if primary.get("checksums"):
            out.append('                <a class="textlink" href="%s" target="_blank" rel="noopener noreferrer">SHA256SUMS<span class="vh"> for this release (opens in a new tab)</span></a>'
                       % esc(primary["checksums"]))
        out.append('                </p>')
        if primary.get("sizeBytes"):
            out.append('                <p class="dl__bytes">%s bytes</p>' % "{:,}".format(primary["sizeBytes"]))
        out.append('              </div>')
        out.append('            </details>')

    return ('          <div class="dl__pane">\n' + "\n".join(out) + '\n          </div>')


def card(product, entries):
    groups, order = {}, []
    for e in entries:
        k = e.get("os", "other")
        if k not in groups:
            groups[k] = []
            order.append(k)
    for e in entries:
        groups[e.get("os", "other")].append(e)
    order.sort(key=lambda k: ORDER.index(k) if k in ORDER else 99)
    tabbed = len(order) > 1

    out = ['        <article class="card dl">']
    g = glyph(product.get("glyph", ""))
    if g:
        out.append(g.rstrip("\n"))
    out.append('          <p class="step__app">%s</p>' % esc(product["tagline"]))
    out.append('          <h3>%s</h3>' % esc(product["name"]))
    out.append('          <p class="dl__desc">%s</p>' % esc(product["detail"]))
    out.append('          <div class="dl__build%s">' % ("" if tabbed else " dl__build--plain"))
    for k in order:
        out.append(pane(product, k, groups[k], tabbed))
    out.append('          </div>')

    out.append('          <p class="dl__foot"></p>')
    out.append('        </article>')
    return "\n".join(out)


cards = []
for product in DATA["products"]:
    mine = [e for e in DATA["entries"] if e["product"] == product["key"]]
    if mine:
        cards.append(card(product, mine))
body = "\n\n".join(cards)

src = INDEX.read_text(encoding="utf-8")
opener = '<div class="dlgrid" data-downloads data-reveal>'
i = src.index(opener) + len(opener)
j = src.index("\n      </div>", i)
INDEX.write_text(src[:i] + "\n" + body + src[j:], encoding="utf-8")
print("wrote the no-JS fallback: %d cards, %d chars" % (len(cards), len(body)))
