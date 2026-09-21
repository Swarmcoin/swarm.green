/* ==========================================================================
   SWARM — swarm.green
   Vanilla JS, no dependencies, no inline handlers (strict CSP friendly).
   Colour that has to come from data rides on SVG presentation attributes, so
   nothing here ever writes a style attribute.
   Sections: 1 nav · 2 reveal · 3 privacy switch · 4 data-driven rendering
   ========================================================================== */
(function () {
  "use strict";

  var SVGNS = "http://www.w3.org/2000/svg";
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  function svg(name, attrs) {
    var el = document.createElementNS(SVGNS, name);
    for (var k in attrs) { if (attrs[k] !== null && attrs[k] !== undefined) el.setAttribute(k, attrs[k]); }
    return el;
  }
  function el(name, cls, text) {
    var n = document.createElement(name);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  }
  var nf = new Intl.NumberFormat("en-GB");
  function fmt(n, dp) {
    return new Intl.NumberFormat("en-GB", { minimumFractionDigits: dp || 0, maximumFractionDigits: dp === undefined ? 4 : dp }).format(n);
  }
  /* Coin amounts: every reward is an exact binary fraction, so print all the
     significant decimals but never fewer than two. 5 -> "5.00", 0.5 -> "0.50",
     0.125 -> "0.125", 0.015625 -> "0.015625". */
  function coin(n) {
    var s = n.toFixed(8).replace(/0+$/, "").replace(/\.$/, "");
    var dot = s.indexOf(".");
    if (dot < 0) return s + ".00";
    var dec = s.length - dot - 1;
    return dec < 2 ? s + new Array(3 - dec).join("0") : s;
  }

  /* ------------------------------------------------------------------ */
  /* 1. Mobile navigation                                               */
  /* ------------------------------------------------------------------ */
  function initNav() {
    var toggle = $("[data-nav-toggle]");
    var panel = $("[data-nav-panel]");
    if (!toggle || !panel) return;

    function setOpen(open) {
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      panel.setAttribute("data-open", open ? "true" : "false");
    }
    setOpen(false);

    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    panel.addEventListener("click", function (e) {
      if (e.target.closest("a")) setOpen(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
        setOpen(false);
        toggle.focus();
      }
    });
    window.addEventListener("resize", function () {
      if (window.innerWidth > 940) setOpen(false);
    });
  }

  /* ------------------------------------------------------------------ */
  /* 2. Reveal on scroll                                                */
  /* ------------------------------------------------------------------ */
  function initReveal() {
    var items = $$("[data-reveal]");
    if (!items.length) return;
    if (reduceMotion.matches || !("IntersectionObserver" in window)) {
      items.forEach(function (n) { n.classList.add("is-in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-in");
        io.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    items.forEach(function (n) { io.observe(n); });

    // Safety net: if the observer has not reported something that is plainly on
    // screen (some headless and embedded renderers never deliver the first
    // callback), show it anyway. Content must never stay invisible.
    window.setTimeout(function () {
      items.forEach(function (n) {
        if (n.classList.contains("is-in")) return;
        var r = n.getBoundingClientRect();
        if (r.top < window.innerHeight && r.bottom > 0) {
          n.classList.add("is-in");
          io.unobserve(n);
        }
      });
    }, 1500);
  }

  /* ------------------------------------------------------------------ */
  /* 3. Privacy switch                                                   */
  /* An illustration of the two states a payment can be in. Nothing here  */
  /* is live data, and the panel says so.                                 */
  /* ------------------------------------------------------------------ */
  var SWITCH_STATES = {
    shielded: {
      title: "What the world sees: nothing.",
      body: "A shielded transaction proves it is valid without revealing who paid whom, or how much. An explorer can see that a block was mined — and that is all.",
      tag: "PRIVACY · ON",
      from: "⬢⬢⬢⬢⬢⬢⬢⬢",
      to: "⬢⬢⬢⬢⬢⬢⬢⬢",
      amount: "⬢⬢⬢.⬢⬢ SWM"
    },
    revealed: {
      title: "Or show exactly what you want.",
      body: "Send a transparent payment and its details are published like any public chain — for an audit, an exchange or a receipt. Always your call, always explicit, and never what the wallet does unless you ask.",
      tag: "PRIVACY · OFF",
      from: "visible t-address",
      to: "visible t-address",
      amount: "1,240.50 SWM"
    }
  };

  function initSwitch() {
    var box = $("[data-switchbox]");
    var btn = $("[data-switch]", box || document);
    if (!box || !btn) return;

    var parts = {
      title: $("[data-switch-title]", box),
      body: $("[data-switch-body]", box),
      tag: $("[data-switch-tag]", box),
      from: $("[data-switch-from]", box),
      to: $("[data-switch-to]", box),
      amount: $("[data-switch-amount]", box)
    };

    function apply(name) {
      var s = SWITCH_STATES[name];
      box.setAttribute("data-state", name);
      btn.setAttribute("aria-checked", name === "shielded" ? "true" : "false");
      for (var k in parts) { if (parts[k]) parts[k].textContent = s[k]; }
    }

    btn.addEventListener("click", function () {
      apply(box.getAttribute("data-state") === "shielded" ? "revealed" : "shielded");
    });
  }

  /* ------------------------------------------------------------------ */
  /* 4. Data-driven rendering                                            */
  /* ------------------------------------------------------------------ */
  function renderStats(host, data) {
    var frag = document.createDocumentFragment();
    data.stats.forEach(function (s) {
      var card = el("div", "metric" + (s.accent ? " metric--" + s.accent : ""));
      card.appendChild(el("div", "metric__k", s.label));
      var v = el("div", "metric__v", s.value);
      if (s.unit) v.appendChild(el("small", null, s.unit));
      card.appendChild(v);
      if (s.note) card.appendChild(el("div", "metric__d", s.note));
      frag.appendChild(card);
    });
    host.replaceChildren(frag);
  }

  /* Cumulative emission curve. Uses the published era table where it exists so
     the chart and the table on /network can never disagree, then extrapolates
     with further halvings if the plot window runs past the last listed era. */
  function emissionSeries(data, years) {
    var chain = data.chain;
    var perYear = 31557600 / chain.blockTimeSeconds;
    var pts = [{ y: 0, s: 0 }];
    var blocks = 0, supply = 0, reward = chain.initialBlockReward;

    (data.eras || []).forEach(function (era) {
      if (pts[pts.length - 1].y >= years) return;
      var endYear = era.toHeight / perYear;
      blocks = era.toHeight;
      supply = era.cumulative;
      reward = era.reward / 2;
      if (endYear >= years) {
        var frac = (years * perYear - pts[pts.length - 1].y * perYear) * era.reward;
        pts.push({ y: years, s: pts[pts.length - 1].s + frac });
      } else {
        pts.push({ y: endYear, s: supply, halving: true });
      }
    });

    var guard = 0;
    while (pts[pts.length - 1].y < years && guard++ < 60) {
      var endBlocks = blocks + chain.halvingIntervalBlocks;
      var ey = endBlocks / perYear;
      if (ey >= years) {
        pts.push({ y: years, s: supply + (years * perYear - blocks) * reward });
        break;
      }
      blocks = endBlocks;
      supply += chain.halvingIntervalBlocks * reward;
      reward /= 2;
      pts.push({ y: ey, s: supply, halving: true });
    }
    return pts;
  }

  function renderEmission(host, data) {
    var years = data.emission.yearsToPlot || 20;
    var pts = emissionSeries(data, years);
    var maxS = data.chain.maxSupply;

    var W = 620, H = 300, ML = 62, MR = 14, MT = 14, MB = 38;
    var iw = W - ML - MR, ih = H - MT - MB;
    var X = function (y) { return ML + (y / years) * iw; };
    var Y = function (s) { return MT + ih - (s / maxS) * ih; };

    var root = svg("svg", {
      viewBox: "0 0 " + W + " " + H,
      role: "img",
      "aria-label": "Cumulative SWARM supply over the first " + years + " years. It rises steeply to about 10.5 million SWM by the first halving, then flattens as each halving cuts the block reward, approaching the maximum of 20,999,987.3152 SWM."
    });

    var defs = svg("defs");
    var grad = svg("linearGradient", { id: "emitFill", x1: "0", y1: "0", x2: "0", y2: "1" });
    grad.appendChild(svg("stop", { offset: "0", "stop-color": "#FF8A1F", "stop-opacity": "0.42" }));
    grad.appendChild(svg("stop", { offset: "1", "stop-color": "#FF8A1F", "stop-opacity": "0" }));
    defs.appendChild(grad);
    root.appendChild(defs);

    // y grid
    var steps = 4;
    for (var i = 0; i <= steps; i++) {
      var val = (maxS / steps) * i;
      var yy = Y(val);
      root.appendChild(svg("line", {
        x1: ML, y1: yy, x2: W - MR, y2: yy,
        stroke: "#F5EFE4", "stroke-opacity": i === 0 ? "0.2" : "0.07", "stroke-width": "1"
      }));
      var lbl = svg("text", { x: ML - 10, y: yy + 4, "text-anchor": "end", fill: "#A89F92", "font-size": "11", "font-family": "JetBrains Mono, monospace" });
      lbl.textContent = val === 0 ? "0" : (val / 1e6).toFixed(0) + "M";
      root.appendChild(lbl);
    }

    // x labels
    for (var x = 0; x <= years; x += 4) {
      var tx = svg("text", { x: X(x), y: H - 14, "text-anchor": "middle", fill: "#A89F92", "font-size": "11", "font-family": "JetBrains Mono, monospace" });
      tx.textContent = x === 0 ? "0" : x + "y";
      root.appendChild(tx);
    }

    // max supply asymptote
    root.appendChild(svg("line", {
      x1: ML, y1: Y(maxS), x2: W - MR, y2: Y(maxS),
      stroke: "#FFB020", "stroke-opacity": "0.55", "stroke-width": "1", "stroke-dasharray": "5 5"
    }));
    var cap = svg("text", { x: W - MR, y: Y(maxS) - 8, "text-anchor": "end", fill: "#FFB020", "font-size": "11", "font-family": "JetBrains Mono, monospace" });
    cap.textContent = "max " + nf.format(Math.round(maxS)) + " SWM";
    root.appendChild(cap);

    // area + line
    var d = "", area = "M" + X(0) + " " + Y(0);
    pts.forEach(function (p, i) {
      d += (i === 0 ? "M" : "L") + X(p.y).toFixed(2) + " " + Y(p.s).toFixed(2) + " ";
      area += "L" + X(p.y).toFixed(2) + " " + Y(p.s).toFixed(2) + " ";
    });
    area += "L" + X(pts[pts.length - 1].y).toFixed(2) + " " + Y(0) + " Z";
    root.appendChild(svg("path", { d: area, fill: "url(#emitFill)" }));
    root.appendChild(svg("path", { d: d.trim(), fill: "none", stroke: "#FF8A1F", "stroke-width": "2.4", "stroke-linejoin": "round", "stroke-linecap": "round" }));

    // halving markers
    pts.forEach(function (p, i) {
      if (!p.halving) return;
      var cx = X(p.y), cy = Y(p.s), r = 4.2, k = 0.866 * r;
      root.appendChild(svg("path", {
        d: "M" + cx + " " + (cy - r) + " L" + (cx + k) + " " + (cy - r / 2) + " L" + (cx + k) + " " + (cy + r / 2) +
           " L" + cx + " " + (cy + r) + " L" + (cx - k) + " " + (cy + r / 2) + " L" + (cx - k) + " " + (cy - r / 2) + "Z",
        fill: "#0A0908", stroke: "#FFB020", "stroke-width": "1.6"
      }));
      if (i <= 3) {
        var t = svg("text", { x: cx, y: cy - 12, "text-anchor": "middle", fill: "#A89F92", "font-size": "10.5", "font-family": "Manrope, sans-serif" });
        t.textContent = "halving " + i;
        root.appendChild(t);
      }
    });

    host.replaceChildren(root);
  }

  function renderSplit(host, data) {
    var shares = data.rewardSplit.shares;
    var R = 92, cx = 130, cy = 132, k = 0.8660254 * R;
    var v = [
      [cx, cy - R], [cx + k, cy - R / 2], [cx + k, cy + R / 2],
      [cx, cy + R], [cx - k, cy + R / 2], [cx - k, cy - R / 2]
    ];
    var per = R * 6, gap = 6;

    function at(s) {
      s = ((s % per) + per) % per;
      var i = Math.floor(s / R) % 6, t = (s - Math.floor(s / R) * R) / R;
      var a = v[i], b = v[(i + 1) % 6];
      return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
    }
    function seg(from, to) {
      var pts = [at(from)];
      var first = Math.ceil(from / R), lastV = Math.floor(to / R);
      for (var i = first; i <= lastV; i++) pts.push(v[i % 6]);
      pts.push(at(to));
      return pts.map(function (p, i) { return (i ? "L" : "M") + p[0].toFixed(2) + " " + p[1].toFixed(2); }).join(" ");
    }

    var root = svg("svg", {
      viewBox: "0 0 260 268",
      role: "img",
      "aria-label": "Block reward split, fixed for the whole emission schedule: " + shares.map(function (s) { return s.percent + " " + s.name; }).join(", ") + "."
    });

    root.appendChild(svg("path", {
      d: seg(0, per),
      fill: "none", stroke: "#F5EFE4", "stroke-opacity": "0.07", "stroke-width": "21"
    }));

    var cursor = 0;
    shares.forEach(function (s) {
      var len = per * s.share;
      root.appendChild(svg("path", {
        d: seg(cursor + gap / 2, cursor + len - gap / 2),
        fill: "none", stroke: s.color, "stroke-width": "21",
        "stroke-linecap": "butt", "stroke-linejoin": "miter", "stroke-miterlimit": "4"
      }));
      cursor += len;
    });

    var n1 = svg("text", { x: cx, y: cy - 2, "text-anchor": "middle", fill: "#FFB020", "font-size": "34", "font-family": "JetBrains Mono, monospace", "font-weight": "500" });
    n1.textContent = String(data.rewardSplit.blockReward);
    root.appendChild(n1);
    var n2 = svg("text", { x: cx, y: cy + 20, "text-anchor": "middle", fill: "#A89F92", "font-size": "12", "font-family": "Manrope, sans-serif" });
    n2.textContent = "SWM per block";
    root.appendChild(n2);

    host.replaceChildren(root);
  }

  function renderLegend(host, data) {
    var frag = document.createDocumentFragment();
    data.rewardSplit.shares.forEach(function (s) {
      var li = el("li");
      // The swatch is an inline SVG hexagon so the colour rides on a fill
      // presentation attribute — no inline CSS, nothing for the CSP to reject.
      var sw = svg("svg", { class: "sw", viewBox: "0 0 12 13.86", "aria-hidden": "true", focusable: "false" });
      sw.appendChild(svg("path", { d: "M6 0 L12 3.465 L12 10.395 L6 13.86 L0 10.395 L0 3.465 Z", fill: s.color }));
      li.appendChild(sw);
      var nm = el("span", "nm", s.name);
      var em = el("em", null, s.desc + " " + fmt(s.perBlock, 2) + " SWM per block in era 0.");
      nm.appendChild(em);
      li.appendChild(nm);
      li.appendChild(el("span", "pc", s.percent));
      frag.appendChild(li);
    });
    host.replaceChildren(frag);
  }

  /* Per-block-by-era mini table, under the emission chart. */
  function renderLadder(host, data) {
    var rows = data.rewardSplit.perBlockByEra;
    if (!rows || !rows.length) return;
    var frag = document.createDocumentFragment();
    rows.forEach(function (r) {
      var tr = el("tr");
      var th = el("th", null, String(r.era));
      th.setAttribute("scope", "row");
      tr.appendChild(th);
      ["reward", "miner", "core", "grants", "reserve"].forEach(function (k) {
        tr.appendChild(el("td", "num", coin(r[k])));
      });
      frag.appendChild(tr);
    });
    host.replaceChildren(frag);
  }

  /* ------------------------------------------------------------------ */
  /* 5. Downloads                                                        */
  /* data/downloads.json is the source of truth. Today every entry is     */
  /* "coming-soon"; flipping one to "available" turns its card into a     */
  /* real link with a version, a size and a checksum, with no HTML edit.  */
  /* The static markup in the page says the same thing and stays as the   */
  /* no-JavaScript fallback.                                              */
  /* ------------------------------------------------------------------ */
  function buildCard(product, entries, meta) {
    var card = el("article", "card dl");
    card.appendChild(el("p", "step__app", product.name));
    card.appendChild(el("h3", null, product.tagline));
    card.appendChild(el("p", null, product.detail));

    var ready = entries.filter(function (e) { return e.status === "available" && e.url; });
    var waiting = entries.filter(function (e) { return ready.indexOf(e) < 0; });

    if (ready.length) {
      var list = el("ul", "dl__builds");
      ready.forEach(function (e) {
        var li = el("li");

        var head = el("div", "dl__head");
        head.appendChild(el("span", "dl__plat", e.platform));
        var bits = [];
        if (e.version) bits.push(e.version);
        if (e.size) bits.push(e.size);
        if (bits.length) head.appendChild(el("span", "dl__meta mono", bits.join(" · ")));
        li.appendChild(head);

        var a = el("a", "btn btn--honey btn--sm", "Download for " + e.platform);
        a.setAttribute("href", e.url);
        a.setAttribute("rel", "noopener noreferrer");
        li.appendChild(a);

        if (e.sha256) {
          var hash = el("div", "dl__hash");
          hash.appendChild(el("span", "label", "SHA-256"));
          hash.appendChild(el("code", "mono", e.sha256));
          var copy = el("button", "btn btn--ghost btn--sm", "Copy");
          copy.setAttribute("type", "button");
          copy.setAttribute("data-copy", e.sha256);
          copy.appendChild(el("span", "vh", " the SHA-256 checksum for " + product.name + " on " + e.platform));
          hash.appendChild(copy);
          li.appendChild(hash);
        }

        if (e.notes) li.appendChild(el("p", "dl__notice", e.notes));
        if (e.platform === "Windows" && meta.windowsNotice) li.appendChild(el("p", "dl__notice", meta.windowsNotice));

        list.appendChild(li);
      });
      card.appendChild(list);
      if (waiting.length) {
        card.appendChild(el("p", "dl__plats", waiting.map(function (e) { return e.platform; }).join(", ") + ": coming soon."));
      }
    } else {
      if (product.platformLine) card.appendChild(el("p", "dl__plats", product.platformLine));
      var soon = el("button", "btn btn--soon", "Coming soon");
      soon.setAttribute("type", "button");
      soon.disabled = true;
      card.appendChild(soon);
    }
    return card;
  }

  function renderDownloads(hosts, data) {
    var meta = data.meta || {};
    hosts.forEach(function (host) {
      var frag = document.createDocumentFragment();
      (data.products || []).forEach(function (p) {
        var entries = (data.entries || []).filter(function (e) { return e.product === p.key; });
        if (!entries.length) return;
        frag.appendChild(buildCard(p, entries, meta));
      });
      if (frag.childNodes.length) host.replaceChildren(frag);
    });
  }

  function initCopy() {
    document.addEventListener("click", function (e) {
      var btn = e.target.closest ? e.target.closest("[data-copy]") : null;
      if (!btn) return;
      var value = btn.getAttribute("data-copy");
      var label = btn.firstChild;
      function done(ok) {
        if (label && label.nodeType === 3) {
          label.nodeValue = ok ? "Copied" : "Copy";
          if (ok) window.setTimeout(function () { label.nodeValue = "Copy"; }, 1600);
        }
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(value).then(function () { done(true); }, function () { done(false); });
      } else {
        done(false);
      }
    });
  }

  function initDownloads() {
    var hosts = $$("[data-downloads]");
    if (!hosts.length) return;
    fetch("/data/downloads.json", { credentials: "omit" })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (data) {
        try { renderDownloads(hosts, data); } catch (err) { /* keep the static markup */ }
      })
      .catch(function () { /* keep the static markup */ });
  }

  function initData() {
    var needs = $$("[data-stats], [data-chart-emission], [data-chart-split], [data-legend-split], [data-ladder]");
    if (!needs.length) return;
    fetch("/data/network.json", { credentials: "omit" })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (data) {
        try {
          var s = $("[data-stats]"); if (s) renderStats(s, data);
          var e = $("[data-chart-emission]"); if (e) renderEmission(e, data);
          var p = $("[data-chart-split]"); if (p) renderSplit(p, data);
          var l = $("[data-legend-split]"); if (l) renderLegend(l, data);
          var k = $("[data-ladder]"); if (k) renderLadder(k, data);
        } catch (err) { /* keep the static markup */ }
      })
      .catch(function () { /* keep the static markup */ });
  }

  /* ------------------------------------------------------------------ */
  function start() {
    initNav();
    initReveal();
    initSwitch();
    initCopy();
    initDownloads();
    initData();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
