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
const targets = [];
for (const e of data.entries || []) {
  if ((e.state || e.status) !== "available" || !e.url) continue;
  const name = (products.get(e.product) || {}).name || e.product;
  const what = e.variant ? `${e.platform} · ${e.variant}` : e.platform;
  targets.push({ label: `${name} — ${what}`, url: e.url, kind: "download" });
  if (e.checksums) targets.push({ label: `${name} — ${what} SHA256SUMS`, url: e.checksums, kind: "checksums" });
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
  if (!good) bad++;
  console.log(`${good ? "ok  " : "FAIL"} ${String(status).padEnd(4)} ${t.label}${size}\n       ${t.url}`);
}

console.log(bad
  ? `\n${bad} of ${targets.length} URLs did not resolve — do not deploy.`
  : `\nAll ${targets.length} URLs resolve.`);
process.exit(bad ? 1 : 0);
