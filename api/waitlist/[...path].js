// The only way into the waiting-list service (server/waitlist on the project's
// own server). A Vercel function on the Node runtime, no dependencies.
//
// Browser -> https://swarm.green/api/waitlist/<route> (same origin, so the
// strict CSP's connect-src 'self' is untouched) -> this function ->
// https://lwd-main.swarm.green/waitlist/api/<route>, carrying two headers the
// service trusts only together:
//   X-Waitlist-Proxy-Secret  process.env.WAITLIST_PROXY_SECRET (shared with the
//                            service; without it every route but healthz is 403)
//   X-Waitlist-Client-Ip     the visitor's address as Vercel determined it.
//
// Which header: x-forwarded-for. Vercel's request-header documentation (read
// 2026-10-03, vercel.com/docs/headers/request-headers) says Vercel overwrites
// it with the client's public IP and does not forward external values, to
// prevent spoofing. x-real-ip and x-vercel-forwarded-for carry the same
// address but the documentation makes that anti-spoofing statement for
// x-forwarded-for, so that is the one used; only its first entry is taken.
//
// Passes through the status and the JSON body. Sets no CORS headers. Never
// logs a body, a query, an address or the secret.
"use strict";

const UPSTREAM = process.env.WAITLIST_UPSTREAM || "https://lwd-main.swarm.green/waitlist/api/";
const ROUTES = new Set(["join", "stats", "leaderboard", "me", "delete", "confirm", "news", "healthz"]);
const MAX_BODY = 4096;

function send(res, status, payload, cache) {
  const body = JSON.stringify(payload);
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", cache || "no-store");
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.end(body);
}

function routeOf(req) {
  // From the address itself ("/api/waitlist/join?x=1"), which works however
  // the platform fills req.query for a catch-all file name.
  const url = new URL(req.url || "/", "http://local");
  let rest = url.pathname.replace(/^\/api\/waitlist\/?/, "").replace(/\/+$/, "");
  if (!rest || rest.includes("[")) {
    const q = req.query && req.query.path;
    rest = Array.isArray(q) ? q.join("/") : (q || "");
  }
  url.searchParams.delete("path");
  return { route: rest, search: url.search };
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY) {
        reject(Object.assign(new Error("too large"), { status: 413 }));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

function clientIp(headers) {
  const raw = headers["x-forwarded-for"];
  const first = String(Array.isArray(raw) ? raw[0] : raw || "").split(",")[0].trim();
  return /^[0-9a-fA-F:.]{2,45}$/.test(first) ? first : "";
}

async function handler(req, res) {
  const secret = process.env.WAITLIST_PROXY_SECRET || "";
  const { route, search } = routeOf(req);
  if (!ROUTES.has(route)) return send(res, 404, { error: "Not found." });
  if (!secret) return send(res, 503, { error: "The waiting list is not reachable just now." });
  const method = req.method === "HEAD" ? "GET" : req.method;
  if (method !== "GET" && method !== "POST") return send(res, 405, { error: "Not found." });

  let body;
  if (method === "POST") {
    const declared = Number(req.headers["content-length"] || 0);
    if (declared > MAX_BODY) return send(res, 413, { error: "Too large." });
    try {
      body = await readBody(req);
    } catch (err) {
      return send(res, err.status || 400, { error: err.status === 413 ? "Too large." : "Bad request." });
    }
  }

  const headers = { "X-Waitlist-Proxy-Secret": secret, Accept: "application/json" };
  const ip = clientIp(req.headers);
  if (ip) headers["X-Waitlist-Client-Ip"] = ip;
  if (req.headers["content-type"]) headers["Content-Type"] = String(req.headers["content-type"]);
  if (req.headers.origin) headers.Origin = String(req.headers.origin);

  let upstream;
  try {
    upstream = await fetch(UPSTREAM + route + (method === "GET" ? search : ""), {
      method,
      headers,
      body: method === "POST" ? body : undefined,
      redirect: "error",
      signal: AbortSignal.timeout(10000)
    });
  } catch (err) {
    console.error("waitlist proxy: upstream unreachable (" + (err && err.name) + ")");
    return send(res, 502, { error: "The waiting list could not be reached just now." });
  }
  const text = await upstream.text();
  let payload;
  try {
    payload = JSON.parse(text || "{}");
  } catch {
    console.error("waitlist proxy: upstream answered with something that is not JSON (" + upstream.status + ")");
    return send(res, 502, { error: "The waiting list could not be reached just now." });
  }
  return send(res, upstream.status, payload, upstream.headers.get("cache-control") || "no-store");
}

module.exports = handler;
module.exports.default = handler;
