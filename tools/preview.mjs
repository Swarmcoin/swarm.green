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
 * Optional, off by default: --waitlist=http://127.0.0.1:8080 forwards
 * /api/waitlist/* to a waiting-list service running locally (server/waitlist),
 * the way the vercel.json rewrite forwards it to the server in production
 * (/api/waitlist/X -> <upstream>/waitlist/api/X), with the browser's address
 * in X-Forwarded-For. --waitlist-fake-ips gives every browser (by User-Agent)
 * its own made-up public address instead, so invites between two local
 * browsers can be tested; never use it for anything but a local test.
 */
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(fileURLToPath(new URL("../", import.meta.url)));
const ARGS = process.argv.slice(2);
const PORT = Number(ARGS.find((a) => /^\d+$/.test(a)) || 4173);
const WAITLIST = (ARGS.find((a) => a.startsWith("--waitlist=")) || "").slice("--waitlist=".length).replace(/\/+$/, "");
const FAKE_IPS = ARGS.includes("--waitlist-fake-ips");

function fakeIp(ua) {
  let h = 2166136261;
  for (const ch of ua || "") h = Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0;
  return `45.${(h >>> 16) & 255}.${(h >>> 8) & 255}.${(h & 255) || 1}`;
}

async function proxyWaitlist(req, res, pathname, search) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > 65536) { res.writeHead(413).end(); return; }
    chunks.push(chunk);
  }
  const headers = { "X-Forwarded-For": FAKE_IPS ? fakeIp(req.headers["user-agent"]) : req.socket.remoteAddress };
  for (const name of ["content-type", "accept", "origin"]) {
    if (req.headers[name]) headers[name] = req.headers[name];
  }
  try {
    const upstream = await fetch(`${WAITLIST}/waitlist/api/${pathname.slice("/api/waitlist/".length)}${search}`, {
      method: req.method,
      headers,
      body: ["GET", "HEAD"].includes(req.method) ? undefined : Buffer.concat(chunks),
      signal: AbortSignal.timeout(12000)
    });
    const body = Buffer.from(await upstream.arrayBuffer());
    res.writeHead(upstream.status, {
      ...siteHeaders(pathname),
      "Content-Type": upstream.headers.get("content-type") || "application/json",
      "Cache-Control": upstream.headers.get("cache-control") || "no-store"
    });
    res.end(body);
  } catch {
    res.writeHead(502, { "Content-Type": "application/json", "Cache-Control": "no-store" });
    res.end(JSON.stringify({ error: "The local waiting-list service is not reachable." }));
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
    await proxyWaitlist(req, res, pathname, new URL(req.url, "http://localhost").search);
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
  if (WAITLIST) console.log(`/api/waitlist/* -> ${WAITLIST}/waitlist/api/*${FAKE_IPS ? " (made-up client addresses)" : ""}`);
});
