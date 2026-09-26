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

  /* The live census supersedes the opt-in list: the seed publishes, every 30 s,
     which nodes are connected to it right now, at city level. A fixed Vercel
     rewrite serves the census from this site under its existing security policy. If it cannot answer, the page falls back to the published
     opt-in list and says so rather than inventing a count.
     The rewrite points at the mainnet seed (lwd-main.swarm.green); the
     engineering testnet keeps its own census at lwd.swarm.green.
     TODO: lwd-main.swarm.green/nodes.json is not published yet (checked
     2026-09-26 16:20 UTC). When it exists, prefer it over
     swarm-map-live.json and add the matching /data/nodes.json rewrite
     to vercel.json. */
  var MAP_URL = "/data/swarm-map.json";
  var LIVE_URL = "/data/swarm-map-live.json";
  var LIVE_STALE_MS = 3 * 60 * 1000;

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

  function toMapData(live) {
    var generated = Number(live.generated_unix) * 1000;
    if (!isFinite(generated) || generated <= 0 || generated > Date.now() + 60000) {
      throw new Error("the live map has no valid generation time");
    }
    var nodes = (live.places || []).map(function (p) {
      return {
        city: typeof p.city === "string" ? p.city : "",
        country: typeof p.country === "string" ? p.country : "",
        lon: Number(p.lon), lat: Number(p.lat), count: Number(p.count),
        seed: !!p.seed
      };
    }).filter(function (n) {
      return n.city && isFinite(n.lon) && isFinite(n.lat) && n.count > 0;
    });
    return {
      nodes: nodes,
      updated: typeof live.updated === "string" ? live.updated : null,
      source: "Live: connected to the seed right now",
      note: typeof live.note === "string" ? live.note : null,
      live: true,
      liveAgeMs: Math.max(0, Date.now() - generated),
      nodesOnline: Number.isInteger(live.nodes_online) && live.nodes_online >= 0 ? live.nodes_online : null
    };
  }

  /* Try the live census first; fall back to the opt-in list if it is unusable. */
  function loadMapData() {
    return fetch(LIVE_URL, { credentials: "omit", cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (live) {
        if (!live || live.live !== true || !Array.isArray(live.places) || !live.places.length) {
          throw new Error("the live map has no places");
        }
        return toMapData(live);
      })
      .catch(function () {
        return loadJson(MAP_URL).then(function (s) {
          return {
            nodes: (s && s.nodes) || [], updated: s && s.updated || null,
            source: s && s.source || null, note: s && s.note || null, live: false
          };
        });
      });
  }

  function start() {
    if (started) return;
    started = true;
    Promise.all([
      loadScript("/js/vendor/topojson-client.min.js"),
      loadScript("/js/vendor/geo-natural-earth1.js")
    ])
      .then(function () { return Promise.all([loadJson("/data/world-110m.json"), loadMapData()]); })
      .then(function (res) {
        draw(res[0], res[1]);
        function refresh() {
          loadMapData().then(function (data) { draw(res[0], data); })
            .catch(function () { setText("[data-map-badge]", "MAP UNAVAILABLE · RETRYING"); })
            .finally(function () { window.setTimeout(refresh, 30000); });
        }
        window.setTimeout(refresh, 30000);
      })
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

    /* Every place is NAMED on the map, not only on hover.
       The owner reported on 2026-09-23 that "the heatmap locations are still not
       showing up": a single 2.6 px dot on a world map is easy to look straight
       past, and a tooltip needs a pointer to find. With few places the names fit,
       so they are drawn while there are at most eight of them and the map stays a
       heat map rather than a wall of text as the swarm grows. */
    if (points.length <= 8) {
      var names = svg("g");
      points.forEach(function (p) {
        var where = p.node.city + (p.node.country ? ", " + p.node.country : "");
        var atEnd = p.x > W - 120;
        names.appendChild(text({
          x: (p.x + (atEnd ? -8 : 8)).toFixed(1), y: (p.y + 3.2).toFixed(1),
          "text-anchor": atEnd ? "end" : "start",
          fill: "#D9D1C4", "font-family": "JetBrains Mono, monospace", "font-size": "10",
          "paint-order": "stroke", stroke: "#0A0908", "stroke-width": "3", "stroke-opacity": ".85"
        }, where));
      });
      frag.appendChild(names);
    }

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

    var online = data.nodesOnline == null ? total : data.nodesOnline;
    setText("[data-map-total]", nf(online));
    setText("[data-map-cities]", nf(cities));
    setText("[data-map-top]", biggest.city + (biggest.country ? ", " + biggest.country : ""));
    // Pill reads straight from the data: how many nodes, and when it was last
    // checked. Never "members", never "live" — this is a list, not a census.
    var badgeEl = root.querySelector("[data-map-badge]") || document.querySelector("[data-map-badge]");
    var liveStale = data.live && data.liveAgeMs != null && data.liveAgeMs > LIVE_STALE_MS;
    setText("[data-map-badge]",
      data.live
        ? nf(online) + (online === 1 ? " NODE ONLINE" : " NODES ONLINE") + (liveStale ? " · LIVE (STALE)" : " · LIVE")
        : nf(total) + (total === 1 ? " NODE" : " NODES") + (stamp ? " · UPDATED " + stamp : ""));
    if (badgeEl) {
      badgeEl.classList.toggle("is-live", !!data.live && !liveStale);
      badgeEl.classList.toggle("is-stale", !!liveStale);
    }
    if (data.source) setText("[data-map-source]", data.source);
    if (data.updated && !isNaN(when)) {
      var el = root.querySelector("[data-map-updated]") || document.querySelector("[data-map-updated]");
      if (el) {
        el.setAttribute("datetime", data.updated.slice(0, 20));
        el.textContent = data.live
          ? "checked continuously"
          : when.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
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
  // Draw as soon as the page has settled, and once more if the figure is
  // scrolled to. Whichever comes first, and only ever once.
  //
  // This used to wait for the figure to come within 300 px of the viewport, with
  // a fallback that fired only when it was within two screens. Measured against
  // the live site on 2026-09-23: at every width from 390 to 1440 the figure sat
  // at opacity 0 with ZERO children drawn — no world, no markers — until it was
  // scrolled to, which is what the owner reported as "the heatmap locations are
  // still not showing up". The two files it needs are 65 KB, so waiting is not
  // worth an empty map.
  // The flag here is deliberately NOT `started`: that one belongs to start(),
  // which sets it and returns early on a second call. Reusing it made the
  // trigger below set the guard before start() could do its work, so the map
  // silently drew nothing at all — measured on the local copy, 2026-09-23.
  var triggered = false;
  var io = null;
  function startOnce() {
    if (triggered) return;
    triggered = true;
    if (io) io.disconnect();
    start();
  }
  if ("IntersectionObserver" in window) {
    io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) startOnce();
      });
    }, { rootMargin: "300px 0px" });
    io.observe(root);
  }
  window.setTimeout(startOnce, 2500);
  window.addEventListener("load", function () { window.setTimeout(startOnce, 200); });
})();
