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
 */
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(fileURLToPath(new URL("../", import.meta.url)));
const PORT = Number(process.argv[2] || 4173);

// The site-wide headers from vercel.json (the "/(.*)" rule). Over plain http
// the browser ignores Strict-Transport-Security, and upgrade-insecure-requests
// is dropped so that http://localhost is not upgraded to https.
const SITE_HEADERS = {};
try {
  const vercel = JSON.parse(await readFile(join(ROOT, "vercel.json"), "utf8"));
  for (const rule of vercel.headers || []) {
    if (rule.source !== "/(.*)") continue;
    for (const { key, value } of rule.headers) {
      SITE_HEADERS[key] = key.toLowerCase() === "content-security-policy"
        ? value.replace(/;\s*upgrade-insecure-requests/, "")
        : value;
    }
  }
} catch { /* no vercel.json: serve without the extra headers */ }

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

  // trailingSlash: false
  if (pathname === "/data/swarm-map-live.json") {
    try {
      // Same upstream as the vercel.json rewrite: the mainnet census on lwd-main.
      const upstream = await fetch("https://lwd-main.swarm.green/swarm-map-live.json", { signal: AbortSignal.timeout(12000) });
      const body = await upstream.text();
      res.writeHead(upstream.status, { ...SITE_HEADERS, "Content-Type": "application/json", "Cache-Control": "no-store" });
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
      ...SITE_HEADERS,
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
});
