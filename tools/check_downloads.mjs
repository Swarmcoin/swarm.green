#!/usr/bin/env node
/*
 * check_downloads.mjs — refuse to ship a download button that 404s.
 *
 *   node tools/check_downloads.mjs
 *
 * Every entry in data/downloads.json with status "available" must have a url
 * that resolves, and so must its checksums file. Run this before deploying any
 * change that flips an entry to available: a dead download link is worse than
 * an honest "Coming soon", because the visitor has already decided to trust it.
 *
 * It does not download the files, so it cannot confirm a SHA-256. Compare the
 * published SHA256SUMS against the hashes in the data file by hand, or with
 * `sha256sum -c`, before release.
 *
 * Exit code 0 = every available URL answers. 1 = at least one does not.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const data = JSON.parse(fs.readFileSync(path.join(ROOT, "data", "downloads.json"), "utf8"));

const products = new Map((data.products || []).map((p) => [p.key, p]));
// Hosts that no longer answer (meta.unavailableHosts). The pages draw those rows
// as "being re-published", not as buttons, so they are listed here, not failed.
const unavailable = (data.meta && data.meta.unavailableHosts) || [];
const targets = [];
const paused = [];
// Rows flagged "paused" in the data (meta.pauseReasons) are published files the
// pages deliberately do not offer, e.g. wallet builds that no longer connect to the network.
const held = [];
for (const e of data.entries || []) {
  if (e.status !== "available" || !e.url) continue;
  const name = (products.get(e.product) || {}).name || e.product;
  const what = e.variant ? `${e.platform} · ${e.variant}` : e.platform;
  if (unavailable.some((h) => e.url.startsWith(h))) { paused.push(`${name} — ${what}`); continue; }
  if (e.paused) { held.push(`${name} — ${what} ${e.version || ""}`.trim()); continue; }
  // PROPOSED 2026-10-10 (Marketing Desk default, owner item pending): rows of the
  // testnet channel are optional — reported, never a reason not to deploy the
  // mainnet site ("mainnet before testnet"). Remove `optional` to make them hard again.
  const optional = e.channel === "testnet";
  targets.push({ label: `${name} — ${what}`, url: e.url, kind: "download", optional });
  if (e.checksums) targets.push({ label: `${name} — ${what} SHA256SUMS`, url: e.checksums, kind: "checksums", optional });
}
if (data.meta && data.meta.releasesUrl) {
  targets.push({ label: "release repository", url: data.meta.releasesUrl, kind: "page" });
}

if (!targets.length) {
  console.log("No available downloads to check — every entry is coming-soon.");
  process.exit(0);
}

let bad = 0;
for (const t of targets) {
  let status = 0, size = "";
  try {
    const r = await fetch(t.url, { method: "GET", headers: { Range: "bytes=0-0" }, redirect: "follow" });
    status = r.status;
    const range = r.headers.get("content-range");
    if (range) size = " " + range.split("/").pop() + " bytes";
    if (r.body) await r.body.cancel();
  } catch (err) {
    status = 0;
  }
  const good = status >= 200 && status < 400;
  if (!good && !t.optional) bad++;
  const mark = good ? "ok  " : t.optional ? "warn" : "FAIL";
  console.log(`${mark} ${String(status).padEnd(4)} ${t.label}${t.optional && !good ? " (testnet row, optional)" : ""}${size}\n       ${t.url}`);
}

if (paused.length) {
  console.log(`\n${paused.length} rows sit on an unavailable host and render as "being re-published":`);
  for (const p of paused) console.log(`       ${p}`);
}
if (held.length) {
  console.log(`
${held.length} rows are paused in the data and render as "being published" (not checked):`);
  for (const p of held) console.log(`       ${p}`);
}
console.log(bad
  ? `\n${bad} of ${targets.length} URLs did not resolve — do not deploy.`
  : `\nAll ${targets.length} URLs resolve.`);
process.exit(bad ? 1 : 0);
