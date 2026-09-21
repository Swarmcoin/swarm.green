/* ==========================================================================
   SWARM — "The swarm" world heat map.

   Reads data/swarm-map.json, which lists only the nodes that share a
   city-level location. It is not a count of the network, and the page says so.

   Everything here is same-origin: the geometry is data/world-110m.json, the
   projection is js/vendor/geo-natural-earth1.js and the TopoJSON decoder is
   js/vendor/topojson-client.min.js. Those three are fetched only when the
   section scrolls into view, so a visitor who never reaches it pays nothing.

   No inline styles anywhere: everything that has to be positioned or coloured
   from data rides on an SVG presentation attribute, and states are classes.
   ========================================================================== */
(function () {
  "use strict";

  var SVGNS = "http://www.w3.org/2000/svg";
  var W = 960, H = 500;
  var SCALE = 174, CENTRE = [480, 250];
  /* Radius scale. The domain floor keeps a young swarm honest: one node is a
     small glow, not a continent-sized bloom, and the scale grows with the
     data as real hotspots appear. */
  var R_MIN = 7, R_MAX = 46, R_REF = 12;

  var root = document.querySelector("[data-map-root]");
  if (!root) return;
  var plot = root.querySelector("[data-map]");
  if (!plot) return;

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var started = false;

  function svg(name, attrs) {
    var el = document.createElementNS(SVGNS, name);
    for (var k in attrs) { if (attrs[k] !== null && attrs[k] !== undefined) el.setAttribute(k, attrs[k]); }
    return el;
  }
  var numberFormat = new Intl.NumberFormat("en-GB");
  function nf(n) { return numberFormat.format(n); }

  function text(attrs, value) {
    var t = svg("text", attrs);
    t.textContent = value;
    return t;
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = function () { reject(new Error("failed to load " + src)); };
      document.head.appendChild(s);
    });
  }
  function loadJson(url) {
    return fetch(url, { credentials: "omit" }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status + " for " + url);
      return r.json();
    });
  }

  function start() {
    if (started) return;
    started = true;
    Promise.all([
      loadScript("/js/vendor/topojson-client.min.js"),
      loadScript("/js/vendor/geo-natural-earth1.js")
    ])
      .then(function () { return Promise.all([loadJson("/data/world-110m.json"), loadJson("/data/swarm-map.json")]); })
      .then(function (res) { draw(res[0], res[1]); })
      .catch(function () { /* the visually hidden table is already the answer */ });
  }

  /* ---------------------------------------------------------------- draw */
  function draw(topo, data) {
    var G = window.SwarmGeo, topojson = window.topojson;
    if (!G || !topojson) return;

    var project = G.naturalEarth1(SCALE, CENTRE);
    var land = topojson.feature(topo, topo.objects.land);
    var nodes = (data.nodes || []).filter(function (n) {
      return typeof n.lon === "number" && typeof n.lat === "number" && n.count > 0;
    });

    var frag = document.createDocumentFragment();

    /* defs: the heat gradient and the soft blur that makes it a glow */
    var defs = svg("defs");
    var grad = svg("radialGradient", { id: "swarm-heat" });
    grad.appendChild(svg("stop", { offset: "0%", "stop-color": "#FFB020", "stop-opacity": ".95" }));
    grad.appendChild(svg("stop", { offset: "35%", "stop-color": "#FF8A1F", "stop-opacity": ".55" }));
    grad.appendChild(svg("stop", { offset: "100%", "stop-color": "#FF8A1F", "stop-opacity": "0" }));
    defs.appendChild(grad);
    var filter = svg("filter", { id: "swarm-soft", x: "-50%", y: "-50%", width: "200%", height: "200%" });
    filter.appendChild(svg("feGaussianBlur", { stdDeviation: "1.2" }));
    defs.appendChild(filter);
    frag.appendChild(defs);

    /* graticule, globe outline, land */
    frag.appendChild(svg("path", {
      d: G.path(G.graticule(30), project),
      fill: "none", stroke: "#FFFFFF", "stroke-opacity": ".05", "stroke-width": ".6"
    }));
    frag.appendChild(svg("path", {
      d: G.path(G.sphere(), project),
      fill: "none", stroke: "#FF8A1F", "stroke-opacity": ".18", "stroke-width": ".8"
    }));
    frag.appendChild(svg("path", {
      d: G.path(land, project),
      fill: "#171411", "fill-rule": "evenodd",
      stroke: "#FFFFFF", "stroke-opacity": ".09", "stroke-width": ".5"
    }));

    if (!nodes.length) {
      plot.replaceChildren(frag);
      return;
    }

    var max = nodes.reduce(function (m, n) { return Math.max(m, n.count); }, 0);
    var ref = Math.max(max, R_REF);
    function radius(n) { return R_MIN + (R_MAX - R_MIN) * Math.sqrt(Math.min(n, ref) / ref); }

    var points = nodes.map(function (n) {
      var xy = project([n.lon, n.lat]);
      return { node: n, x: xy[0], y: xy[1], r: radius(n.count) };
    });

    /* heat, screen-blended through a class so no style attribute is needed */
    var heat = svg("g", { class: "swarmmap__heat" });
    points.forEach(function (p) {
      heat.appendChild(svg("circle", {
        cx: p.x.toFixed(1), cy: p.y.toFixed(1), r: p.r.toFixed(1),
        fill: "url(#swarm-heat)", filter: "url(#swarm-soft)",
        opacity: (0.55 + 0.45 * Math.min(1, p.node.count / ref)).toFixed(2)
      }));
    });
    frag.appendChild(heat);

    /* pulsing rings on the biggest hotspots — never under reduced motion */
    if (!reduceMotion.matches) {
      var top = points.filter(function (p) { return p.node.count >= max * 0.6; });
      var rings = svg("g");
      top.forEach(function (p) {
        rings.appendChild(svg("circle", {
          class: "ring-pulse", cx: p.x.toFixed(1), cy: p.y.toFixed(1), r: "10",
          fill: "none", stroke: "#FFB020", "stroke-width": "1"
        }));
      });
      frag.appendChild(rings);
    }

    /* the markers themselves */
    var dots = svg("g");
    points.forEach(function (p) {
      dots.appendChild(svg("circle", {
        cx: p.x.toFixed(1), cy: p.y.toFixed(1),
        r: p.node.count >= max * 0.6 ? "2.6" : "1.6",
        fill: "#FFE0B0", opacity: ".95"
      }));
    });
    frag.appendChild(dots);

    /* tooltip, built once and moved by transform */
    var tip = svg("g", { class: "map__tip", "aria-hidden": "true", visibility: "hidden" });
    var tipBox = svg("rect", { x: "0", y: "0", rx: "8", ry: "8", height: "40", fill: "#100E0C", "fill-opacity": ".96", stroke: "#FF8A1F", "stroke-opacity": ".4" });
    var tipCity = text({ x: "10", y: "17", fill: "#FFB020", "font-family": "JetBrains Mono, monospace", "font-size": "11.5" }, "");
    var tipCount = text({ x: "10", y: "31", fill: "#D9D1C4", "font-family": "JetBrains Mono, monospace", "font-size": "11" }, "");
    tip.appendChild(tipBox);
    tip.appendChild(tipCity);
    tip.appendChild(tipCount);

    /* hit areas: focusable, so the hotspots work from the keyboard */
    var hits = svg("g");
    points.forEach(function (p) {
      var n = p.node;
      var where = n.city + (n.country ? ", " + n.country : "");
      var howMany = nf(n.count) + (n.count === 1 ? " node" : " nodes");
      var g = svg("g", {
        class: "hot", tabindex: "0", role: "button",
        "aria-label": where + " — " + howMany + " sharing a city-level location"
      });
      g.appendChild(svg("circle", {
        class: "hot__halo",
        cx: p.x.toFixed(1), cy: p.y.toFixed(1), r: Math.max(9, p.r * 0.55).toFixed(1)
      }));
      g.appendChild(svg("circle", {
        cx: p.x.toFixed(1), cy: p.y.toFixed(1), r: Math.max(14, p.r * 0.8).toFixed(1),
        fill: "none", "pointer-events": "all"
      }));

      function show() {
        tipCity.textContent = where;
        tipCount.textContent = howMany;
        var width = Math.max(where.length, howMany.length) * 6.6 + 20;
        tipBox.setAttribute("width", width.toFixed(0));
        var tx = Math.min(Math.max(p.x + 14, 4), W - width - 4);
        var ty = p.y - 50 < 4 ? p.y + 16 : p.y - 50;
        tip.setAttribute("transform", "translate(" + tx.toFixed(1) + "," + ty.toFixed(1) + ")");
        tip.setAttribute("visibility", "visible");
      }
      function hide() { tip.setAttribute("visibility", "hidden"); }

      g.addEventListener("mouseenter", show);
      g.addEventListener("mouseleave", hide);
      g.addEventListener("focus", show);
      g.addEventListener("blur", hide);
      hits.appendChild(g);
    });
    frag.appendChild(hits);
    frag.appendChild(tip);

    plot.replaceChildren(frag);

    /* the figures around the map come from the same file */
    var cities = nodes.length;
    var total = nodes.reduce(function (s, n) { return s + n.count; }, 0);
    var biggest = nodes.slice().sort(function (a, b) { return b.count - a.count; })[0];

    /* Fixed three-letter months: toLocaleDateString gives "SEPT" in en-GB and
       something else again in another locale, and this pill has to read the
       same everywhere. */
    var MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
    var when = new Date(data.updated);
    var stamp = isNaN(when) ? ""
      : when.getUTCDate() + " " + MONTHS[when.getUTCMonth()] + " " + when.getUTCFullYear();

    setText("[data-map-total]", nf(total));
    setText("[data-map-cities]", nf(cities));
    setText("[data-map-top]", biggest.city + (biggest.country ? ", " + biggest.country : ""));
    // Pill reads straight from the data: how many nodes, and when it was last
    // checked. Never "members", never "live" — this is a list, not a census.
    setText("[data-map-badge]",
      nf(total) + (total === 1 ? " NODE" : " NODES") + (stamp ? " · UPDATED " + stamp : ""));
    if (data.source) setText("[data-map-source]", data.source);
    if (data.updated && !isNaN(when)) {
      var el = root.querySelector("[data-map-updated]") || document.querySelector("[data-map-updated]");
      if (el) {
        el.setAttribute("datetime", data.updated.slice(0, 10));
        el.textContent = when.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
      }
    }
    renderTable(nodes);
  }

  function setText(sel, value) {
    var el = root.querySelector(sel) || document.querySelector(sel);
    if (el) el.textContent = value;
  }

  function renderTable(nodes) {
    var table = root.querySelector("[data-map-table]");
    if (!table) return;
    var body = table.querySelector("tbody");
    if (!body) return;
    var frag = document.createDocumentFragment();
    nodes.slice().sort(function (a, b) { return b.count - a.count; }).forEach(function (n) {
      var tr = document.createElement("tr");
      var th = document.createElement("th");
      th.setAttribute("scope", "row");
      th.textContent = n.city;
      tr.appendChild(th);
      var td = document.createElement("td");
      td.textContent = n.country || "";
      tr.appendChild(td);
      var num = document.createElement("td");
      num.className = "num";
      num.textContent = String(n.count);
      tr.appendChild(num);
      frag.appendChild(tr);
    });
    body.replaceChildren(frag);
  }

  /* -------------------------------------------------------- lazy trigger */
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.disconnect();
        start();
      });
    }, { rootMargin: "300px 0px" });
    io.observe(root);
    // Belt and braces for renderers that never deliver the first callback.
    window.setTimeout(function () {
      var r = root.getBoundingClientRect();
      if (r.top < window.innerHeight * 2) start();
    }, 2500);
  } else {
    start();
  }
})();
