// Tests de l'interpolation courbe (ticket v2-correctifs-ecran/04b) : `node --test src/utils/v2Spline.test.js`.
import assert from "node:assert/strict";
import test from "node:test";
import { ballFromTrack, catmullRom, displayBall, playersBetween } from "./v2Spline.js";

const STEP_MIN = 0.1 / 60; // un pas du moteur
const HALF = 45;
const pt = (k, x, y, extra = {}) => ({ minute: 10 + k * STEP_MIN, x, y, mode: "sol", holder: null, dead: false, ...extra });
const close = (a, b, tol = 1e-9) => Math.abs(a - b) <= tol;

function distToSegment(p, a, b) {
  const dx = b.x - a.x, dy = b.y - a.y;
  const len2 = dx * dx + dy * dy;
  const w = len2 ? Math.min(1, Math.max(0, ((p.x - a.x) * dx + (p.y - a.y) * dy) / len2)) : 0;
  return Math.hypot(p.x - (a.x + w * dx), p.y - (a.y + w * dy));
}
const distToPolyline = (p, pts) => Math.min(...pts.slice(1).map((b, k) => distToSegment(p, pts[k], b)));

test("la courbe passe exactement par les points de la piste", () => {
  const track = [pt(0, 0, 0), pt(1, 1.5, 0.2), pt(2, 2.7, 1.1), pt(3, 3.1, 2.6), pt(4, 2.9, 4.0)];
  for (let k = 0; k < track.length; k += 1) {
    const at = ballFromTrack(track, track[k].minute, HALF);
    assert.ok(close(at.x, track[k].x) && close(at.y, track[k].y), `point ${k} : ${at.x}, ${at.y}`);
  }
  for (const f of [0, 1]) {
    const c = catmullRom({ x: -1, y: 3 }, { x: 0, y: 0 }, { x: 4, y: 1 }, { x: 5, y: 7 }, f);
    assert.ok(close(c.x, f ? 4 : 0) && close(c.y, f ? 1 : 0));
  }
});

test("virage de 90° à 15 m/s : pas de dépassement de plus de 0,3 m", () => {
  // 1,5 m par pas de 0,1 s : le ballon file vers x croissant, touche un joueur en (6, 0) et repart vers y croissant
  const track = [];
  for (let k = 0; k <= 4; k += 1) track.push(pt(k, 1.5 * k, 0));
  for (let k = 1; k <= 4; k += 1) track.push(pt(4 + k, 6, 1.5 * k));
  let worst = 0;
  const end = track.at(-1).minute;
  for (let m = track[0].minute; m <= end; m += STEP_MIN / 50) {
    const at = ballFromTrack(track, m, HALF);
    worst = Math.max(worst, distToPolyline(at, track));
  }
  assert.ok(worst <= 0.3, `dépassement ${worst.toFixed(3)} m`);
});

test("coupure nette au changement de porteur : pas de courbe tirée par le point d'après", () => {
  // tenu par A puis libre et parti vers y : entre les deux points tenus, la courbe ne doit pas se courber vers y
  const track = [pt(0, 0, 0, { holder: "A" }), pt(1, 1, 0, { holder: "A" }), pt(2, 1, 3)];
  for (let f = 0; f <= 1; f += 0.1) {
    const at = ballFromTrack(track, track[0].minute + f * STEP_MIN, HALF);
    assert.ok(close(at.y, 0), `y = ${at.y} à f = ${f}`);
  }
  // au passage du porteur au ballon libre : ligne droite sur le pas, pas de boucle
  const mid = ballFromTrack(track, track[1].minute + 0.5 * STEP_MIN, HALF);
  assert.ok(close(mid.x, 1) && close(mid.y, 1.5));
});

test("coupure nette sur une remise en jeu : le ballon saute au point de remise, sans glisser", () => {
  // sortie en touche en (40, 0), puis posé au point de remise (38, 0) mort, puis joué
  const track = [pt(0, 39, 1), pt(1, 40, 0, { dead: true }), pt(2, 38, 0, { dead: true }), pt(3, 38, 0, { holder: "B" })];
  const between = ballFromTrack(track, track[1].minute + 0.5 * STEP_MIN, HALF);
  assert.deepEqual([between.x, between.y], [40, 0]);
  const before = ballFromTrack(track, track[0].minute + 0.5 * STEP_MIN, HALF);
  assert.deepEqual([before.x, before.y], [39, 1]);
});

test("coupure nette à la mi-temps", () => {
  const a = { ...pt(0, 80, 10), minute: HALF - STEP_MIN / 2 };
  const b = { ...pt(0, 52.5, 34), minute: HALF + STEP_MIN / 2 };
  const at = ballFromTrack([a, b], HALF, HALF);
  assert.deepEqual([at.x, at.y], [80, 10]);
});

test("piste absente ou en retard : l'appelant garde l'interpolation des images", () => {
  assert.equal(ballFromTrack(undefined, 10, HALF), null);
  assert.equal(ballFromTrack([pt(0, 0, 0), pt(1, 1, 0)], 11, HALF), null);
});

test("ballon tenu : il est dessiné sur son porteur affiché", () => {
  const track = [pt(0, 5, 5, { holder: "A" }), pt(1, 6, 5, { holder: "A" })];
  const players = [{ name: "B", x: 0, y: 0 }, { name: "A", x: 5.4, y: 5.1 }];
  const ball = displayBall(track, track[0].minute + 0.5 * STEP_MIN, HALF, players, { x: 0, y: 0 }, null);
  assert.deepEqual(ball, { x: 5.4, y: 5.1, z: 0, holder: "A" }); // tenu : au pied (ticket v2-hauteur-ballon/02b)
  const free = displayBall([pt(0, 5, 5), pt(1, 6, 5)], track[0].minute + 0.5 * STEP_MIN, HALF, players, { x: 0, y: 0 }, "A");
  assert.ok(close(free.x, 5.5) && close(free.y, 5) && free.holder === null);
  const old = displayBall(undefined, 10, HALF, players, { x: 9, y: 9 }, "A");
  assert.deepEqual(old, { x: 5.4, y: 5.1, z: 0, holder: "A" });
});

test("joueurs : courbe par les images, coupure nette à la mi-temps et sur une remise en jeu", () => {
  const tick = (minute, x, dead = false) => ({ minute, ball: { dead }, players: [{ x, y: x * x }] });
  const ticks = [tick(10, 0), tick(10.01, 1), tick(10.02, 2), tick(10.03, 3)];
  const at0 = playersBetween(ticks, 1, 0, HALF)[0];
  const at1 = playersBetween(ticks, 1, 1, HALF)[0];
  assert.ok(close(at0.x, 1) && close(at0.y, 1) && close(at1.x, 2) && close(at1.y, 4));
  const mid = playersBetween(ticks, 1, 0.5, HALF)[0];
  assert.ok(mid.y < 2.5, `courbe sous la corde (y = ${mid.y})`); // la parabole passe sous la corde (1,1)-(2,4)
  // remise en jeu entre les images 1 et 2 : ligne droite (le moteur pose le preneur au point de remise)
  const dead = [tick(10, 0, true), tick(10.01, 1, true), tick(10.02, 2), tick(10.03, 3)];
  const straight = playersBetween(dead, 1, 0.5, HALF)[0];
  assert.ok(close(straight.x, 1.5) && close(straight.y, 2.5));
  const half = [tick(44.99, 0), tick(44.995, 1), tick(45.0, 2), tick(45.01, 3)];
  const cut = playersBetween(half, 1, 0.5, HALF)[0];
  assert.ok(close(cut.x, 1.5) && close(cut.y, 2.5));
});

// Hauteur du ballon (ticket v2-hauteur-ballon/02b)
test("la hauteur du ballon est interpolée en ligne droite entre deux pas, nulle au pied du porteur", () => {
  const track = [pt(0, 0, 0, { z: 0 }), pt(1, 2, 0, { z: 2 }), pt(2, 4, 0, { z: 3 }), pt(3, 6, 0, { z: 3.5 })];
  assert.ok(close(ballFromTrack(track, track[1].minute, HALF).z, 2));
  assert.ok(close(ballFromTrack(track, track[1].minute + 0.25 * STEP_MIN, HALF).z, 2.25, 1e-6));
  const free = displayBall(track, track[2].minute, HALF, [], { x: 0, y: 0 }, null);
  assert.ok(close(free.z, 3));
  const held = [pt(0, 5, 5, { holder: "A", z: 0 }), pt(1, 5, 5, { holder: "A", z: 0 })];
  assert.equal(displayBall(held, held[0].minute, HALF, [{ name: "A", x: 5, y: 5 }], { x: 0, y: 0 }, null).z, 0);
  // piste ancienne, sans hauteur : au sol
  assert.equal(ballFromTrack([pt(0, 0, 0), pt(1, 1, 0)], 10, HALF).z, 0);
});
