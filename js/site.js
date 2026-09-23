/* ==========================================================================
   SWARM — swarm.green
   Vanilla JS, no dependencies, no inline handlers (strict CSP friendly).
   Sections: 1 nav · 2 reveal · 3 hero swarm canvas · 4 data-driven charts
             5 downloads · 6 pointer tilt for the 3D hex cells
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
      if (window.innerWidth > 860) setOpen(false);
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
        var node = entry.target;
        var delay = parseInt(node.getAttribute("data-reveal-delay") || "0", 10);
        if (delay) {
          window.setTimeout(function () { node.classList.add("is-in"); }, delay);
        } else {
          node.classList.add("is-in");
        }
        io.unobserve(node);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    items.forEach(function (n) { io.observe(n); });

    // Safety net: if the observer has not reported anything that is plainly on
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
  /* 3. Hero swarm canvas                                               */
  /* ------------------------------------------------------------------ */
  function initSwarm() {
    var canvas = $("[data-swarm]");
    if (!canvas) return;
    var ctx = canvas.getContext("2d");
    if (!ctx) return;

    var host = canvas.parentElement;
    var w = 0, h = 0, dpr = 1;
    var bees = [], targets = [];
    var raf = 0, visible = true, onScreen = true, last = 0, clock = 0;

    // phase machine: drift -> gather -> hold -> scatter -> drift
    var PHASES = [
      { name: "drift", ms: 6400 },
      { name: "gather", ms: 2600 },
      { name: "hold", ms: 2600 },
      { name: "scatter", ms: 1800 }
    ];
    var phase = 0, phaseT = 0;

    function count() {
      var n = Math.round(w / 15);
      if (w < 520) n = Math.round(w / 11);
      return Math.max(28, Math.min(118, n));
    }

    function hexPoints(n) {
      // n points spread evenly along the outline of a pointy-top hexagon
      var R = Math.min(w, h) * (w < 620 ? 0.3 : 0.26);
      var cx = w / 2, cy = h * 0.47;
      var k = 0.8660254 * R;
      var v = [
        [cx, cy - R], [cx + k, cy - R / 2], [cx + k, cy + R / 2],
        [cx, cy + R], [cx - k, cy + R / 2], [cx - k, cy - R / 2]
      ];
      var out = [];
      for (var i = 0; i < n; i++) {
        var s = (i / n) * 6;
        var e = Math.floor(s) % 6;
        var t = s - Math.floor(s);
        out.push([
          v[e][0] + (v[(e + 1) % 6][0] - v[e][0]) * t,
          v[e][1] + (v[(e + 1) % 6][1] - v[e][1]) * t
        ]);
      }
      out.outline = v;
      return out;
    }

    function seed() {
      var n = count();
      bees = [];
      for (var i = 0; i < n; i++) {
        bees.push({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.5,
          vy: (Math.random() - 0.5) * 0.5,
          a: Math.random() * Math.PI * 2,
          da: (Math.random() - 0.5) * 0.018,
          r: 1.1 + Math.random() * 1.7,
          o: 0.35 + Math.random() * 0.5
        });
      }
      targets = hexPoints(n);
    }

    function resize() {
      var rect = host.getBoundingClientRect();
      dpr = Math.min(2, window.devicePixelRatio || 1);
      w = Math.max(1, Math.round(rect.width));
      h = Math.max(1, Math.round(rect.height));
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (!bees.length || bees.length !== count()) seed();
      else targets = hexPoints(bees.length);
      if (reduceMotion.matches) drawStatic();
    }

    function cohesion() {
      var p = PHASES[phase], t = phaseT / p.ms;
      if (p.name === "gather") return easeInOut(t);
      if (p.name === "hold") return 1;
      if (p.name === "scatter") return 1 - easeInOut(t);
      return 0;
    }
    function easeInOut(t) { return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; }

    function step(dt) {
      phaseT += dt;
      if (phaseT >= PHASES[phase].ms) { phaseT = 0; phase = (phase + 1) % PHASES.length; }
      var c = cohesion();
      var cx = w / 2, cy = h * 0.47;

      for (var i = 0; i < bees.length; i++) {
        var b = bees[i], tg = targets[i];
        b.a += b.da;
        // wander
        b.vx += Math.cos(b.a) * 0.018 * (1 - c);
        b.vy += Math.sin(b.a) * 0.018 * (1 - c);
        // loose cohesion toward the middle so the swarm stays on screen
        b.vx += (cx - b.x) * 0.00016 * (1 - c);
        b.vy += (cy - b.y) * 0.00016 * (1 - c);
        // pull to the hexagon
        if (c > 0.001) {
          b.vx += (tg[0] - b.x) * 0.0062 * c;
          b.vy += (tg[1] - b.y) * 0.0062 * c;
        }
        var damp = 0.965 - 0.045 * c;
        b.vx *= damp; b.vy *= damp;
        b.x += b.vx * dt * 0.06;
        b.y += b.vy * dt * 0.06;
        // soft bounds
        if (b.x < -20) b.x = w + 20; else if (b.x > w + 20) b.x = -20;
        if (b.y < -20) b.y = h + 20; else if (b.y > h + 20) b.y = -20;
      }
      return c;
    }

    function paint(c) {
      ctx.clearRect(0, 0, w, h);

      // hexagon outline fades in with cohesion
      if (c > 0.02 && targets.outline) {
        var v = targets.outline;
        ctx.beginPath();
        ctx.moveTo(v[0][0], v[0][1]);
        for (var k = 1; k < 6; k++) ctx.lineTo(v[k][0], v[k][1]);
        ctx.closePath();
        ctx.strokeStyle = "rgba(245,166,35," + (c * 0.3).toFixed(3) + ")";
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }

      // links
      ctx.lineWidth = 1;
      var lim = w < 620 ? 68 : 86;
      for (var i = 0; i < bees.length; i++) {
        for (var j = i + 1; j < bees.length; j++) {
          var dx = bees[i].x - bees[j].x, dy = bees[i].y - bees[j].y;
          var d2 = dx * dx + dy * dy;
          if (d2 > lim * lim) continue;
          var a = (1 - Math.sqrt(d2) / lim) * 0.16;
          ctx.strokeStyle = "rgba(255,201,77," + a.toFixed(3) + ")";
          ctx.beginPath();
          ctx.moveTo(bees[i].x, bees[i].y);
          ctx.lineTo(bees[j].x, bees[j].y);
          ctx.stroke();
        }
      }

      // bees
      ctx.globalCompositeOperation = "lighter";
      for (var m = 0; m < bees.length; m++) {
        var b = bees[m];
        ctx.beginPath();
        ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(245,166,35," + (b.o * (0.55 + 0.45 * c)).toFixed(3) + ")";
        ctx.fill();
      }
      ctx.globalCompositeOperation = "source-over";
    }

    function drawStatic() {
      // prefers-reduced-motion: one still hexagon of bees, drawn once
      ctx.clearRect(0, 0, w, h);
      var pts = targets.length ? targets : hexPoints(count());
      var v = pts.outline;
      if (v) {
        ctx.beginPath();
        ctx.moveTo(v[0][0], v[0][1]);
        for (var k = 1; k < 6; k++) ctx.lineTo(v[k][0], v[k][1]);
        ctx.closePath();
        ctx.strokeStyle = "rgba(245,166,35,0.28)";
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }
      for (var i = 0; i < pts.length; i++) {
        ctx.beginPath();
        ctx.arc(pts[i][0], pts[i][1], 2, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(245,166,35,0.75)";
        ctx.fill();
      }
    }

    function frame(ts) {
      raf = 0;
      var dt = Math.min(48, ts - (last || ts));
      last = ts;
      clock += dt;
      paint(step(dt));
      schedule();
    }
    function schedule() {
      if (raf || reduceMotion.matches || !visible || !onScreen) return;
      raf = window.requestAnimationFrame(frame);
    }
    function stop() {
      if (raf) { window.cancelAnimationFrame(raf); raf = 0; }
      last = 0;
    }

    resize();
    if (reduceMotion.matches) { drawStatic(); } else { schedule(); }

    if ("ResizeObserver" in window) {
      new ResizeObserver(function () { resize(); }).observe(host);
    } else {
      window.addEventListener("resize", resize);
    }
    document.addEventListener("visibilitychange", function () {
      visible = !document.hidden;
      if (visible) schedule(); else stop();
    });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        onScreen = entries[0].isIntersecting;
        if (onScreen) schedule(); else stop();
      }, { threshold: 0 }).observe(host);
    }
    if (reduceMotion.addEventListener) {
      reduceMotion.addEventListener("change", function () {
        stop();
        if (reduceMotion.matches) drawStatic(); else schedule();
      });
    }
  }

  /* ------------------------------------------------------------------ */
  /* 4. Data-driven rendering                                            */
  /* ------------------------------------------------------------------ */
  function renderStats(host, data) {
    var current = $$(".stat", host);
    var same = current.length === data.stats.length && data.stats.every(function (s, i) {
      return current[i].textContent.replace(/\s+/g, " ").trim() ===
        (String(s.value) + (s.unit || "") + s.label).replace(/\s+/g, " ").trim();
    });
    if (same) return; // the static markup already matches the data
    var frag = document.createDocumentFragment();
    data.stats.forEach(function (s) {
      var cell = el("div", "stat");
      var inner = el("div", "stat__in");
      var v = el("div", "stat__v", s.value);
      if (s.unit) { var u = el("small", null, s.unit); v.appendChild(u); }
      inner.appendChild(v);
      inner.appendChild(el("div", "stat__l", s.label));
      cell.appendChild(inner);
      frag.appendChild(cell);
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
      "aria-label": "Cumulative SWARM supply over the first " + years + " years. It rises steeply to about 10.5 million coins by the first halving, then flattens as each halving cuts the block reward, approaching the maximum of 20,999,987.3152 coins."
    });

    var defs = svg("defs");
    var grad = svg("linearGradient", { id: "emitFill", x1: "0", y1: "0", x2: "0", y2: "1" });
    grad.appendChild(svg("stop", { offset: "0", "stop-color": "#F5A623", "stop-opacity": "0.34" }));
    grad.appendChild(svg("stop", { offset: "1", "stop-color": "#F5A623", "stop-opacity": "0" }));
    defs.appendChild(grad);
    root.appendChild(defs);

    // y grid
    var steps = 4;
    for (var i = 0; i <= steps; i++) {
      var val = (maxS / steps) * i;
      var yy = Y(val);
      root.appendChild(svg("line", {
        x1: ML, y1: yy, x2: W - MR, y2: yy,
        stroke: "#E6EDF3", "stroke-opacity": i === 0 ? "0.22" : "0.08", "stroke-width": "1"
      }));
      var lbl = svg("text", { x: ML - 10, y: yy + 4, "text-anchor": "end", fill: "#9AA4B2", "font-size": "11", "font-family": "JetBrains Mono, monospace" });
      lbl.textContent = val === 0 ? "0" : (val / 1e6).toFixed(0) + "M";
      root.appendChild(lbl);
    }

    // x labels
    for (var x = 0; x <= years; x += 4) {
      var tx = svg("text", { x: X(x), y: H - 14, "text-anchor": "middle", fill: "#9AA4B2", "font-size": "11", "font-family": "JetBrains Mono, monospace" });
      tx.textContent = x === 0 ? "0" : x + "y";
      root.appendChild(tx);
    }

    // max supply asymptote
    root.appendChild(svg("line", {
      x1: ML, y1: Y(maxS), x2: W - MR, y2: Y(maxS),
      stroke: "#FFC94D", "stroke-opacity": "0.55", "stroke-width": "1", "stroke-dasharray": "5 5"
    }));
    var cap = svg("text", { x: W - MR, y: Y(maxS) - 8, "text-anchor": "end", fill: "#FFC94D", "font-size": "11", "font-family": "JetBrains Mono, monospace" });
    cap.textContent = "max " + nf.format(Math.round(maxS));
    root.appendChild(cap);

    // area + line
    var d = "", area = "M" + X(0) + " " + Y(0);
    pts.forEach(function (p, i) {
      d += (i === 0 ? "M" : "L") + X(p.y).toFixed(2) + " " + Y(p.s).toFixed(2) + " ";
      area += "L" + X(p.y).toFixed(2) + " " + Y(p.s).toFixed(2) + " ";
    });
    area += "L" + X(pts[pts.length - 1].y).toFixed(2) + " " + Y(0) + " Z";
    root.appendChild(svg("path", { d: area, fill: "url(#emitFill)" }));
    root.appendChild(svg("path", { d: d.trim(), fill: "none", stroke: "#F5A623", "stroke-width": "2.5", "stroke-linejoin": "round", "stroke-linecap": "round" }));

    // halving markers
    pts.forEach(function (p, i) {
      if (!p.halving) return;
      var cx = X(p.y), cy = Y(p.s), r = 4.2, k = 0.866 * r;
      root.appendChild(svg("path", {
        d: "M" + cx + " " + (cy - r) + " L" + (cx + k) + " " + (cy - r / 2) + " L" + (cx + k) + " " + (cy + r / 2) +
           " L" + cx + " " + (cy + r) + " L" + (cx - k) + " " + (cy + r / 2) + " L" + (cx - k) + " " + (cy - r / 2) + "Z",
        fill: "#0E1116", stroke: "#FFC94D", "stroke-width": "1.6"
      }));
      if (i <= 3) {
        var t = svg("text", { x: cx, y: cy - 12, "text-anchor": "middle", fill: "#9AA4B2", "font-size": "10.5", "font-family": "Inter, sans-serif" });
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
      fill: "none", stroke: "#E6EDF3", "stroke-opacity": "0.07", "stroke-width": "21"
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

    var n1 = svg("text", { x: cx, y: cy - 2, "text-anchor": "middle", fill: "#FFC94D", "font-size": "34", "font-family": "JetBrains Mono, monospace", "font-weight": "500" });
    n1.textContent = String(data.rewardSplit.blockReward);
    root.appendChild(n1);
    var n2 = svg("text", { x: cx, y: cy + 20, "text-anchor": "middle", fill: "#9AA4B2", "font-size": "12", "font-family": "Inter, sans-serif" });
    n2.textContent = "coins per block";
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
      var em = el("em", null, s.desc + " " + fmt(s.perBlock, 2) + " coins per block.");
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
  /* ------------------------------------------------------------------ */
  /* 5. Downloads                                                        */
  /* data/downloads.json is the source of truth. Today every app entry is */
  /* "coming-soon" and renders the same disabled button as the static     */
  /* markup. Setting one to "available" turns its row into a real link    */
  /* with a version, a size and a checksum — a data change, not an HTML   */
  /* edit. The static markup stays as the no-JavaScript fallback.         */
  /* ------------------------------------------------------------------ */
  /* Generic glyphs, drawn here. Deliberately not Apple's or Google's store
     badges: their guidelines do not allow badge artwork for an app that is not
     published yet, so the store names are plain text instead. */
  var DL_GLYPHS = {
    desktop: ["M3 5.5h18v11H3z", "M9 20h6", "M12 16.5V20"],
    phone: ["M7.6 2.6h8.8v18.8H7.6z", "M10.6 5.4h2.8"],
    explorer: ["M11 4.2a6.8 6.8 0 1 0 0 13.6 6.8 6.8 0 0 0 0-13.6z", "M16 16l4.4 4.4"],
    code: ["M8.6 7 3.4 12l5.2 5", "M15.4 7l5.2 5-5.2 5", "M13.6 4.4l-3.2 15.2"]
  };

  function dlGlyph(name) {
    var paths = DL_GLYPHS[name];
    if (!paths) return null;
    var box = el("div", "hexicon");
    box.setAttribute("aria-hidden", "true");
    var s = svg("svg", { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor",
      "stroke-width": "1.8", "stroke-linecap": "round", "stroke-linejoin": "round", focusable: "false" });
    paths.forEach(function (d) { s.appendChild(svg("path", { d: d })); });
    box.appendChild(s);
    return box;
  }

  function dlSoonPill() {
    var b = el("button", "btn btn--soon btn--sm dl__cta", "Coming soon");
    b.setAttribute("type", "button");
    b.disabled = true;
    return b;
  }

  /* One card shape for everything in the grid, so the icon, the title, the
     spec line, the button and the footer all sit at the same height whether or
     not the card has anything to download yet. */
  function dlCard(product, entries, meta) {
    var card = el("article", "card dl");
    var glyph = dlGlyph(product.glyph);
    if (glyph) card.appendChild(glyph);
    card.appendChild(el("p", "step__app", product.tagline));
    card.appendChild(el("h3", null, product.name));
    card.appendChild(el("p", "dl__desc", product.detail));

    var available = entries.filter(function (e) { return e.status === "available" && e.url; });
    var primary = available.filter(function (e) { return e.role !== "alt"; })[0];
    var alts = available.filter(function (e) { return e !== primary; });
    var waiting = entries.filter(function (e) { return e.status !== "available" || !e.url; });

    var build = el("div", "dl__build");

    // spec: platform, version and size on one line
    var spec = [];
    if (primary) {
      spec.push(primary.platform);
      if (primary.version) spec.push(primary.version);
      if (primary.sizeShort) spec.push(primary.sizeShort);
    }
    build.appendChild(el("p", "dl__spec", spec.length ? spec.join(" · ") : (product.soonSpec || "")));

    if (primary) {
      var label = product.kind === "link" ? "Open"
        : primary.platform === "Android" ? "Download APK"
        : "Download for " + primary.platform;
      var a = el("a", "btn btn--primary btn--sm dl__cta", label);
      a.setAttribute("href", primary.url);
      a.setAttribute("rel", "noopener noreferrer");
      if (product.kind === "link") {
        a.setAttribute("target", "_blank");
        a.appendChild(el("span", "vh", " " + product.name + " (opens in a new tab)"));
      }
      build.appendChild(a);
    } else {
      build.appendChild(dlSoonPill());
    }

    // an alternate build is a small link, not a second box
    alts.forEach(function (e) {
      var p = el("p", "dl__alt");
      var link = el("a", "textlink", (e.platform !== primary.platform ? e.platform + " · " : "") + (e.label || (e.variant + " (" + e.sizeShort + ")")));
      link.setAttribute("href", e.url);
      link.setAttribute("rel", "noopener noreferrer");
      p.appendChild(link);
      build.appendChild(p);
    });

    // exactly one small line, never two
    var notice = "";
    if (primary) {
      notice = primary.notes
        || (primary.platform === "Windows" ? meta.windowsNotice : meta.unsignedNotice)
        || "";
    } else if (product.key === "mobile-ios" || product.key === "mobile-android") {
      notice = meta.mobileNotice || "";
    }
    if (notice) build.appendChild(el("p", "dl__notice", notice));

    // the 64-character hash lives behind a disclosure so it stops dominating
    if (primary && primary.sha256) {
      var d = document.createElement("details");
      d.className = "dl__sum";
      var sum = document.createElement("summary");
      sum.textContent = "Checksum";
      d.appendChild(sum);
      var body = el("div", "dl__sumbody");
      body.appendChild(el("code", "dl__hashline", primary.sha256));
      var row = el("p", "dl__sumrow");
      var copy = el("button", "btn btn--ghost btn--sm", "Copy");
      copy.setAttribute("type", "button");
      copy.setAttribute("data-copy", primary.sha256);
      copy.appendChild(el("span", "vh", " the SHA-256 checksum for " + product.name));
      row.appendChild(copy);
      if (primary.checksums) {
        var sa = el("a", "textlink", "SHA256SUMS");
        sa.setAttribute("href", primary.checksums);
        sa.setAttribute("target", "_blank");
        sa.setAttribute("rel", "noopener noreferrer");
        sa.appendChild(el("span", "vh", " for this release (opens in a new tab)"));
        row.appendChild(sa);
      }
      body.appendChild(row);
      if (primary.sizeBytes) body.appendChild(el("p", "dl__bytes", nf.format(primary.sizeBytes) + " bytes"));
      d.appendChild(body);
      build.appendChild(d);
    }

    card.appendChild(build);

    // footer, pushed to the bottom of every card by CSS
    var foot = waiting.map(function (e) { return e.platform; }).join(", ");
    card.appendChild(el("p", "dl__foot", foot ? foot + ": coming soon." : ""));
    return card;
  }

  function renderDownloads(hosts, data) {
    var meta = data.meta || {};
    var products = data.products || [];
    var entries = data.entries || [];
    hosts.forEach(function (host) {
      var frag = document.createDocumentFragment();
      products.forEach(function (p) {
        var mine = entries.filter(function (e) { return e.product === p.key; });
        if (!mine.length) return;
        frag.appendChild(dlCard(p, mine, meta));
      });
      if (frag.childNodes.length) host.replaceChildren(frag);
    });
    if (meta.releasesUrl && meta.releasesLabel) {
      $$("[data-downloads-releases]").forEach(function (node) {
        var a = el("a", "textlink", meta.releasesLabel);
        a.setAttribute("href", meta.releasesUrl);
        a.setAttribute("target", "_blank");
        a.setAttribute("rel", "noopener noreferrer");
        a.appendChild(el("span", "vh", " (opens in a new tab)"));
        node.replaceChildren(a);
      });
    }
    products.forEach(function (p) {
      if (p.key !== "explorer") return;
      addExplorerLinks(p, entries.filter(function (e) { return e.product === p.key; })[0]);
    });
  }

  function initCopy() {
    document.addEventListener("click", function (e) {
      var btn = e.target.closest ? e.target.closest("[data-copy]") : null;
      if (!btn) return;
      var label = btn.firstChild;
      function done(ok) {
        if (label && label.nodeType === 3) {
          label.nodeValue = ok ? "Copied" : "Copy";
          if (ok) window.setTimeout(function () { label.nodeValue = "Copy"; }, 1600);
        }
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(btn.getAttribute("data-copy")).then(function () { done(true); }, function () { done(false); });
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

  /* ------------------------------------------------------------------ */
  /* 6. Pointer tilt for the 3D hex cells                                */
  /* The cells are drawn entirely in CSS (css/site.css, sections 7, 8,   */
  /* 10). This feeds them two custom properties, --rx and --ry, through   */
  /* the CSSOM, which the strict CSP permits (it forbids style="" markup, */
  /* not element.style.setProperty). One delegated listener on the        */
  /* document covers cells rendered later (stats, downloads) without any  */
  /* hook in their renderers. Mouse only: touch has no hover, and         */
  /* prefers-reduced-motion leaves the cells at rest.                    */
  /* ------------------------------------------------------------------ */
  var TILT_MAX = 14;

  function initTilt() {
    if (reduceMotion.matches) return;
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;

    var active = null; // { cell, rest } for the cell under the pointer
    var raf = 0, rx = 0, ry = 0;

    function clamp(v) { return Math.max(-1, Math.min(1, v)); }
    function apply() {
      raf = 0;
      if (!active) return;
      active.cell.style.setProperty("--rx", rx.toFixed(2) + "deg");
      active.cell.style.setProperty("--ry", ry.toFixed(2) + "deg");
    }
    function release() {
      if (raf) { window.cancelAnimationFrame(raf); raf = 0; }
      if (active) {
        active.cell.style.removeProperty("--rx");
        active.cell.style.removeProperty("--ry");
        active = null;
      }
    }

    document.addEventListener("pointermove", function (e) {
      if (e.pointerType && e.pointerType !== "mouse") return;
      var t = e.target;
      var area = t && t.closest ? t.closest(".stat, .card, .why > li") : null;
      var cell = null;
      if (area) cell = area.classList.contains("stat") ? area : area.querySelector(".hexicon, .step__n");
      if (!cell) { if (active) release(); return; }
      if (!active || active.cell !== cell) {
        release();
        // the resting pose comes from the stylesheet (6deg for icons, 5deg for stat cells)
        active = { cell: cell, rest: parseFloat(window.getComputedStyle(cell).getPropertyValue("--rx")) || 0 };
      }
      var r = cell.getBoundingClientRect();
      if (!r.width || !r.height) return;
      // Offset of the pointer from the cell's centre, in cell sizes, clamped
      // so a pointer at the far end of a wide card still gives a gentle tilt.
      var dx = clamp((e.clientX - (r.left + r.width / 2)) / (r.width * 1.6));
      var dy = clamp((e.clientY - (r.top + r.height / 2)) / (r.height * 1.6));
      ry = dx * TILT_MAX;
      rx = active.rest - dy * TILT_MAX;
      if (!raf) raf = window.requestAnimationFrame(apply);
    }, { passive: true });
    // Leaving the window, or the tab going to the background, lets go.
    document.addEventListener("pointerleave", release);
    document.addEventListener("visibilitychange", function () { if (document.hidden) release(); });
  }

  function start() {
    initNav();
    initReveal();
    initSwarm();
    initData();
    initCopy();
    initDownloads();
    initTilt();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
