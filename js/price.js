/* ==========================================================================
   SWARM — SWM price in the header.

   Fills the small "SWM $0.60 · on Base" reading that sits in the header of
   every page (markup: .nav__price in index.html, tools/build_pages.py,
   support/index.html and the four Messenger link pages).

   The number is FUEL's price of the SWM token on Base, in US dollars. It is
   read from /data/swm-price.json, which a fixed Vercel rewrite in vercel.json
   serves from https://fuel.army/api/swm-price. Same origin, so the page's
   Content-Security-Policy stays as it is and the visitor's browser talks to
   nobody but swarm.green. Expected answer:

     { "swmUsd": "0.60", "ethUsd": "2703.05", "source": "live" | "stored",
       "updatedAt": <ms epoch>, "ageSeconds": <n>, "paused": null | "CODE" }

   Anything else (a network error, a 503, HTML instead of JSON, a paused
   price, a price older than 30 minutes, a value that is not a positive
   number) shows a quiet "—" and never an error. The reading refreshes every
   60 seconds, and only while the tab is visible.

   No inline styles: states are classes (.is-live, .is-stored), the rest is
   in css/site.css section 5b.
   ========================================================================== */
(function () {
  "use strict";

  var URL_PRICE = "/data/swm-price.json";
  var REFRESH_MS = 60 * 1000;
  var MAX_AGE_S = 30 * 60;
  var TIMEOUT_MS = 8000;
  var DASH = "—";

  var roots = document.querySelectorAll("[data-swm-price]");
  if (!roots.length || typeof window.fetch !== "function") return;

  var timer = null;
  var lastFetch = null;
  var inFlight = false;
  /* The last good reading: the value text, where it came from, how old it was
     when it arrived and when it arrived (performance clock, so a wrong
     computer clock cannot make a fresh price look stale or the reverse). */
  var reading = null;

  function ago(seconds) {
    if (seconds < 45) return "just now";
    var m = Math.max(1, Math.round(seconds / 60));
    return m === 1 ? "1 min ago" : m + " min ago";
  }

  function money(n) {
    if (n >= 1000) return n.toLocaleString("en-US", { maximumFractionDigits: 0 });
    if (n >= 0.1) return n.toFixed(2);
    /* Small prices keep three significant figures: 0.0123, not 0.01. */
    var s = n.toPrecision(3);
    return s.indexOf("e") === -1 ? s : n.toFixed(8).replace(/0+$/, "");
  }

  function nowS() {
    return (window.performance && performance.now ? performance.now() : Date.now()) / 1000;
  }

  /* Seconds since FUEL took the price: what the answer said, plus the time
     since it arrived here. */
  function ageNow() {
    return reading ? reading.age + (nowS() - reading.at) : Infinity;
  }

  function paint() {
    var ok = reading && ageNow() <= MAX_AGE_S;
    var value = ok ? "$" + reading.text : DASH;
    var title = ok
      ? "SWM in US dollars on Base, from FUEL · updated " + ago(ageNow())
      : "SWM price on Base: not available right now";
    var spoken = ok
      ? "SWM price: " + reading.text + " US dollars on Base, updated " + ago(ageNow()) + "."
      : "SWM price on Base: not available right now.";
    for (var i = 0; i < roots.length; i++) {
      var root = roots[i];
      var v = root.querySelector("[data-swm-price-value]");
      var sr = root.querySelector("[data-swm-price-sr]");
      if (v && v.textContent !== value) v.textContent = value;
      if (sr && sr.textContent !== spoken) sr.textContent = spoken;
      root.title = title;
      root.classList.toggle("is-live", !!ok && reading.source === "live");
      root.classList.toggle("is-stored", !!ok && reading.source !== "live");
    }
  }

  /* Returns a reading or null. Never throws. */
  function parse(body) {
    var d;
    try { d = JSON.parse(body); } catch (e) { return null; }
    if (!d || typeof d !== "object" || d.paused) return null;
    var n = typeof d.swmUsd === "number" ? d.swmUsd : parseFloat(String(d.swmUsd));
    if (!isFinite(n) || n <= 0 || n > 1e9) return null;
    var age = Number(d.ageSeconds);
    if (!isFinite(age) || age < 0) {
      /* No server age: fall back to the timestamp against this computer's
         clock. A future timestamp (clock skew) counts as just now. */
      var t = Number(d.updatedAt);
      if (!isFinite(t) || t <= 0) return null;
      age = Math.max(0, (Date.now() - t) / 1000);
    }
    if (age > MAX_AGE_S) return null;
    return { text: money(n), source: d.source === "live" ? "live" : "stored", age: age, at: nowS() };
  }

  function load() {
    if (inFlight) return;
    inFlight = true;
    lastFetch = nowS();
    var ctrl = typeof AbortController === "function" ? new AbortController() : null;
    var cut = ctrl ? setTimeout(function () { ctrl.abort(); }, TIMEOUT_MS) : null;
    fetch(URL_PRICE, {
      cache: "no-store",
      credentials: "omit",
      headers: { "Accept": "application/json" },
      signal: ctrl ? ctrl.signal : undefined
    })
      .then(function (r) { return r.ok ? r.text() : ""; })
      .then(function (body) { reading = body ? parse(body) : null; })
      .catch(function () { reading = null; })
      .then(function () {
        if (cut) clearTimeout(cut);
        inFlight = false;
        paint();
      });
  }

  function schedule() {
    clearTimeout(timer);
    timer = null;
    if (document.visibilityState === "hidden") return;
    var wait = lastFetch === null ? 0 : Math.max(0, REFRESH_MS - (nowS() - lastFetch) * 1000);
    timer = setTimeout(function () { load(); schedule(); }, wait);
  }

  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") {
      clearTimeout(timer);
      timer = null;
    } else {
      paint();
      schedule();
    }
  });

  paint();
  if (document.visibilityState !== "hidden") load();
  schedule();
})();
