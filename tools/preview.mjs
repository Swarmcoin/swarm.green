#!/usr/bin/env node
/**
 * Zero-dependency static preview server for swarm.green.
 *
 * It mimics the Vercel settings in vercel.json so that what you see locally
 * is what you get in production:
 *   cleanUrls: true       ->  /network            serves /network/index.html
 *   trailingSlash: false  ->  /network/           redirects to /network
 *   headers for /(.*)     ->  sent on every response, so the strict
 *                             Content-Security-Policy is enforced locally too
 *                             (an inline style or script that the CSP would
 *                             drop in production is dropped here as well)
 *
 * Usage:  node tools/preview.mjs [port]      (default 4173)
 *
 * Optional, off by default: --waitlist=http://127.0.0.1:8080 runs the
 * production Vercel function api/waitlist/[...path].js for /api/waitlist/*,
 * pointed at a waiting-list service running locally (server/waitlist). Like
 * Vercel, it first replaces X-Forwarded-For with the browser's address. The
 * shared secret comes from the environment variable WAITLIST_PROXY_SECRET, as
 * on Vercel (never on the command line). --waitlist-fake-ips gives every
 * browser (by User-Agent) its own made-up public address instead, so invites
 * between two local browsers can be tested; never use it for anything but a
 * local test.
 *
 * /data/swm-price.json (the header's SWM price, js/price.js) is fetched from
 * https://fuel.army/api/swm-price like the vercel.json rewrite, passing its
 * status and Content-Type through. --swm-price=<file> serves a local file
 * instead, read again on every request (.json as JSON, anything else as
 * HTML; a missing file answers 503), so every state can be tried locally.
 */
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = resolve(fileURLToPath(new URL("../", import.meta.url)));
const ARGS = process.argv.slice(2);
const PORT = Number(ARGS.find((a) => /^\d+$/.test(a)) || 4173);
const WAITLIST = (ARGS.find((a) => a.startsWith("--waitlist=")) || "").slice("--waitlist=".length).replace(/\/+$/, "");
const FAKE_IPS = ARGS.includes("--waitlist-fake-ips");
const SWM_PRICE_FILE = (ARGS.find((a) => a.startsWith("--swm-price=")) || "").slice("--swm-price=".length);

function fakeIp(ua) {
  let h = 2166136261;
  for (const ch of ua || "") h = Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0;
  return `45.${(h >>> 16) & 255}.${(h >>> 8) & 255}.${(h & 255) || 1}`;
}

let waitlistFunction = null;
if (WAITLIST) {
  process.env.WAITLIST_UPSTREAM = `${WAITLIST}/waitlist/api/`;
  waitlistFunction = createRequire(import.meta.url)("../api/waitlist/[...path].js");
}

async function proxyWaitlist(req, res, pathname) {
  // What Vercel does before the function runs: X-Forwarded-For becomes the
  // address Vercel itself saw. Whatever the browser sent is dropped.
  req.headers["x-forwarded-for"] = FAKE_IPS ? fakeIp(req.headers["user-agent"]) : req.socket.remoteAddress;
  for (const [key, value] of Object.entries(siteHeaders(pathname))) res.setHeader(key, value);
  try {
    await waitlistFunction(req, res);
  } catch {
    if (!res.headersSent) res.writeHead(502, { "Content-Type": "application/json", "Cache-Control": "no-store" });
    res.end(JSON.stringify({ error: "The local waiting-list function failed." }));
  }
}

// The header rules from vercel.json. Every rule whose source matches the
// request path applies, in order, as on Vercel; the sources used there are
// valid regular expressions once anchored. Two of them carry the
// Content-Security-Policy: the strict one for the four Messenger link pages,
// and the one that also allows Google Analytics for every other path. Over
// plain http the browser ignores Strict-Transport-Security, and
// upgrade-insecure-requests is dropped so that http://localhost is not
// upgraded to https.
const HEADER_RULES = [];
try {
  const vercel = JSON.parse(await readFile(join(ROOT, "vercel.json"), "utf8"));
  for (const rule of vercel.headers || []) {
    HEADER_RULES.push({ match: new RegExp(`^${rule.source}$`), headers: rule.headers });
  }
} catch { /* no vercel.json: serve without the extra headers */ }

function siteHeaders(pathname) {
  const out = {};
  for (const rule of HEADER_RULES) {
    if (!rule.match.test(pathname)) continue;
    for (const { key, value } of rule.headers) {
      out[key] = key.toLowerCase() === "content-security-policy"
        ? value.replace(/;\s*upgrade-insecure-requests/, "")
        : value;
    }
  }
  return out;
}

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".ico": "image/x-icon",
  ".txt": "text/plain; charset=utf-8",
  ".xml": "application/xml; charset=utf-8",
  ".webmanifest": "application/manifest+json",
  ".woff2": "font/woff2",
  ".md": "text/markdown; charset=utf-8"
};

async function firstExisting(paths) {
  for (const p of paths) {
    try {
      const s = await stat(p);
      if (s.isFile()) return p;
    } catch { /* keep looking */ }
  }
  return null;
}

const server = createServer(async (req, res) => {
  let pathname;
  try {
    pathname = decodeURIComponent(new URL(req.url, "http://localhost").pathname);
  } catch {
    res.writeHead(400).end("Bad request");
    return;
  }

  if (WAITLIST && pathname.startsWith("/api/waitlist/")) {
    await proxyWaitlist(req, res, pathname);
    return;
  }

  // trailingSlash: false
  if (pathname === "/data/swarm-map-live.json") {
    try {
      // Same upstream as the vercel.json rewrite: the mainnet census on lwd-main.
      const upstream = await fetch("https://lwd-main.swarm.green/swarm-map-live.json", { signal: AbortSignal.timeout(12000) });
      const body = await upstream.text();
      res.writeHead(upstream.status, { ...siteHeaders(pathname), "Content-Type": "application/json", "Cache-Control": "no-store" });
      res.end(body);
    } catch {
      res.writeHead(502, { "Cache-Control": "no-store" }).end("Live map unavailable");
    }
    return;
  }

  if (pathname === "/data/swm-price.json") {
    const headers = { ...siteHeaders(pathname), "Cache-Control": "no-store" };
    try {
      if (SWM_PRICE_FILE) {
        const body = await readFile(SWM_PRICE_FILE).catch(() => null);
        if (body === null) {
          res.writeHead(503, { ...headers, "Content-Type": "application/json" }).end('{"error":"unavailable"}');
        } else {
          const json = extname(SWM_PRICE_FILE).toLowerCase() === ".json";
          res.writeHead(200, { ...headers, "Content-Type": json ? TYPES[".json"] : TYPES[".html"] }).end(body);
        }
      } else {
        // Same upstream as the vercel.json rewrite.
        const upstream = await fetch("https://fuel.army/api/swm-price", { signal: AbortSignal.timeout(12000) });
        const body = Buffer.from(await upstream.arrayBuffer());
        res.writeHead(upstream.status, { ...headers, "Content-Type": upstream.headers.get("content-type") || "application/octet-stream" });
        res.end(body);
      }
    } catch {
      res.writeHead(502, { "Cache-Control": "no-store" }).end("SWM price unavailable");
    }
    return;
  }

  if (pathname.length > 1 && pathname.endsWith("/")) {
    res.writeHead(308, { Location: pathname.replace(/\/+$/, "") }).end();
    return;
  }

  const safe = normalize(pathname).replace(/^(\.\.[/\\])+/, "");
  const target = join(ROOT, safe);
  if (!target.startsWith(ROOT)) {
    res.writeHead(403).end("Forbidden");
    return;
  }

  const candidates =
    pathname === "/"
      ? [join(ROOT, "index.html")]
      : [target, `${target}.html`, join(target, "index.html")];

  let file = await firstExisting(candidates);
  let status = 200;
  if (!file) {
    file = join(ROOT, "404.html");
    status = 404;
  }

  try {
    const body = await readFile(file);
    res.writeHead(status, {
      ...siteHeaders(pathname),
      "Content-Type": TYPES[extname(file).toLowerCase()] || "application/octet-stream",
      "Content-Length": body.length,
      "Cache-Control": "no-store"
    });
    res.end(body);
  } catch {
    res.writeHead(500).end("Server error");
  }
});

server.listen(PORT, () => {
  console.log(`swarm.green preview -> http://localhost:${PORT}`);
  if (WAITLIST) console.log(`/api/waitlist/* -> api/waitlist/[...path].js -> ${WAITLIST}/waitlist/api/*`
    + `${FAKE_IPS ? " (made-up client addresses)" : ""}${process.env.WAITLIST_PROXY_SECRET ? "" : " (WAITLIST_PROXY_SECRET is not set: the function answers 503)"}`);
});
