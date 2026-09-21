#!/usr/bin/env node
/*
 * build_map_data.mjs — makes data/world-110m.json from the Natural Earth source.
 *
 *   node tools/build_map_data.mjs [source.json] [out.json]
 *
 * Source: world-atlas 110m "countries" TopoJSON (Natural Earth 1:110m, public
 * domain; the TopoJSON packaging by Mike Bostock is ISC). The committed copy is
 * tools/world-atlas-110m.src.json so a rebuild needs nothing from the network.
 *
 * Two things happen here so that the browser needs no clipping code at all:
 *
 *  1. Only the merged `land` object is kept. Country borders are dropped: at
 *     this size they are noise behind the heat layer, and dropping them halves
 *     the file.
 *
 *  2. Rings are cut at the antimeridian. In the source, Russia, Fiji and
 *     Antarctica each have a ring with points on both sides of ±180°. Drawn
 *     straight through a cylindrical-ish projection those rings smear a
 *     horizontal bar across the whole map. d3-geo fixes this at runtime with
 *     antimeridian clipping; we do it once, here, instead — every crossing in
 *     this dataset already sits exactly on ±180°, so splitting the ring at the
 *     wrap and closing each piece along its own meridian is exact. Antarctica,
 *     whose piece legitimately runs the full 360°, is closed over the south
 *     pole so it sits flush with the bottom of the projection.
 *
 * The output keeps the TopoJSON shape (quantised, delta-encoded arcs) so it can
 * be read by the vendored topojson-client, and so the file name still means
 * what it says. Arc sharing is not reproduced — with one object there is
 * nothing to share — and every ring becomes one arc.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..");
const SRC = process.argv[2] || path.join(HERE, "world-atlas-110m.src.json");
const OUT = process.argv[3] || path.join(ROOT, "data", "world-110m.json");

const QUANT = 20000; // grid steps across the full extent: 0.018° ≈ 0.06 px at 960 wide
const SOUTH_POLE = -90;

const src = JSON.parse(fs.readFileSync(SRC, "utf8"));
const [sx, sy] = src.transform.scale;
const [tx, ty] = src.transform.translate;

function decodeArc(i) {
  let x = 0, y = 0;
  return src.arcs[i].map((p) => { x += p[0]; y += p[1]; return [x * sx + tx, y * sy + ty]; });
}

function ringPoints(ring) {
  const out = [];
  for (const idx of ring) {
    let pts = idx < 0 ? decodeArc(~idx).slice().reverse() : decodeArc(idx);
    if (out.length) pts = pts.slice(1);
    out.push(...pts);
  }
  return out;
}

/* Split a closed ring wherever two consecutive points wrap across ±180°. */
function splitRing(pts) {
  const n = pts.length;
  const closed = n > 1 && pts[0][0] === pts[n - 1][0] && pts[0][1] === pts[n - 1][1];
  const p = closed ? pts.slice(0, n - 1) : pts.slice();
  const m = p.length;
  const wraps = [];
  for (let i = 0; i < m; i++) {
    if (Math.abs(p[(i + 1) % m][0] - p[i][0]) > 180) wraps.push(i);
  }
  if (!wraps.length) return [p];
  const pieces = [];
  for (let w = 0; w < wraps.length; w++) {
    const start = (wraps[w] + 1) % m;
    const end = wraps[(w + 1) % wraps.length];
    const piece = [];
    for (let i = start; ; i = (i + 1) % m) {
      piece.push(p[i]);
      if (i === end) break;
      if (piece.length > m) throw new Error("runaway ring walk");
    }
    pieces.push(piece);
  }
  return pieces;
}

/* A piece whose two ends sit on opposite meridians wraps the globe (Antarctica).
   Close it over the pole so the fill reaches the edge of the projection. */
function closeOverPole(piece) {
  const a = piece[0], b = piece[piece.length - 1];
  if (Math.abs(a[0] - b[0]) <= 180) return piece;
  const steps = 12;
  const out = piece.slice();
  for (let i = 1; i <= steps; i++) out.push([b[0], b[1] + (SOUTH_POLE - b[1]) * (i / steps)]);
  out.push([a[0], SOUTH_POLE]);
  for (let i = 1; i < steps; i++) out.push([a[0], SOUTH_POLE + (a[1] - SOUTH_POLE) * (i / steps)]);
  return out;
}

const polygons = [];
let ringsIn = 0, wasSplit = 0;
for (const geom of src.objects.land.geometries) {
  const list = geom.type === "MultiPolygon" ? geom.arcs : [geom.arcs];
  for (const poly of list) {
    const rings = [];
    for (const ring of poly) {
      ringsIn++;
      const pieces = splitRing(ringPoints(ring));
      if (pieces.length > 1) wasSplit++;
      for (const piece of pieces) rings.push(closeOverPole(piece));
    }
    polygons.push(rings);
  }
}

/* Quantise to an integer grid, then delta-encode, exactly as TopoJSON does. */
const bbox = [-180, -90, 180, 90];
const scale = [(bbox[2] - bbox[0]) / (QUANT - 1), (bbox[3] - bbox[1]) / (QUANT - 1)];
const translate = [bbox[0], bbox[1]];
const q = (pt) => [
  Math.round((pt[0] - translate[0]) / scale[0]),
  Math.round((pt[1] - translate[1]) / scale[1]),
];

const arcs = [];
const objectArcs = [];
let dropped = 0;
for (const rings of polygons) {
  const polyArcs = [];
  for (const ring of rings) {
    // quantise, drop points that collapse onto their neighbour, close the ring
    const grid = [];
    for (const pt of ring) {
      const g = q(pt);
      const last = grid[grid.length - 1];
      if (!last || last[0] !== g[0] || last[1] !== g[1]) grid.push(g);
    }
    const first = grid[0], last = grid[grid.length - 1];
    if (first[0] !== last[0] || first[1] !== last[1]) grid.push([first[0], first[1]]);
    if (grid.length < 4) { dropped++; continue; }
    let px = 0, py = 0;
    const delta = grid.map((g) => { const d = [g[0] - px, g[1] - py]; px = g[0]; py = g[1]; return d; });
    polyArcs.push([arcs.length]);
    arcs.push(delta);
  }
  if (polyArcs.length) objectArcs.push(polyArcs);
}

const topology = {
  type: "Topology",
  bbox,
  transform: { scale, translate },
  objects: {
    land: { type: "GeometryCollection", geometries: [{ type: "MultiPolygon", arcs: objectArcs }] },
  },
  arcs,
};

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(topology) + "\n", "utf8");

const points = arcs.reduce((n, a) => n + a.length, 0);
console.log(
  `wrote ${path.relative(ROOT, OUT)} — ${polygons.length} polygons, ${arcs.length} rings ` +
  `(${ringsIn} in source, ${wasSplit} split at the antimeridian, ${dropped} collapsed away), ` +
  `${points} points, ${fs.statSync(OUT).size} bytes`
);
