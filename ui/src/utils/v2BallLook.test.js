// Roulement et traînée du ballon (ticket v2-ecran-match/21a) : `node --test` (script `npm test`).
import { test } from "node:test";
import assert from "node:assert/strict";
import { FREEZE_SPEED, PANEL_TILE_M, TRAIL_MAX_M, TRAIL_SPEED, ballMotion, ballSpeed, patternOffset, trailLength } from "./v2BallLook.js";
import { COS } from "./v2Projection.js";

const STEP = 0.1 / 60; // un point de piste toutes les 0,1 s, en minutes
const HALF = 45;
// piste rectiligne le long de x à `speed` m/s, `n` points à partir de `x0`, minute de départ `m0`
const run = (n, speed, { x0 = 10, y = 30, m0 = 10, holder = null, dead = false } = {}) =>
  Array.from({ length: n }, (_, k) => ({ minute: m0 + k * STEP, x: x0 + k * speed * 0.1, y, holder, dead }));

test("ballon libre en ligne droite : direction, vitesse, distance depuis la coupure", () => {
  const track = run(20, 12);
  const m = ballMotion(track, 10 + 5.5 * STEP, HALF);
  assert.deepEqual(m.dir, { x: 1, y: 0 });
  assert.ok(Math.abs(m.speed - 12) < 1e-6);
  assert.ok(Math.abs(m.distance - 5.5 * 1.2) < 1e-6);
});

test("ballon tenu ou mort : ni roulement ni traînée", () => {
  const held = run(10, 12, { holder: "Joueur" });
  assert.equal(ballMotion(held, 10 + 3.5 * STEP, HALF), null);
  const dead = run(10, 0, { dead: true });
  assert.equal(ballMotion(dead, 10 + 3.5 * STEP, HALF), null);
  assert.equal(trailLength(null), 0);
});

// écart entre deux décalages d'écran ramené dans [-T/2, T/2)
const unwrap = (d) => ((((d + PANEL_TILE_M / 2) % PANEL_TILE_M) + PANEL_TILE_M) % PANEL_TILE_M) - PANEL_TILE_M / 2;
// Le décalage du motif suit la position affichée : d'une image à la suivante, il avance exactement du déplacement
// projeté du ballon, sans aucun saut au passage du carreau (rejet A1 de l'expert, 18/11/2026 : un décalage réduit le long
// de la direction sautait hors de l'axe x) ni à une réception (décision du propriétaire du 18/11/2026).
function assertSmooth(positions, speed = 8) {
  for (let k = 1; k < positions.length; k += 1) {
    const a = positions[k - 1], b = positions[k];
    const oa = patternOffset(a, speed, 1), ob = patternOffset(b, speed, 1);
    assert.ok(Math.abs(unwrap(ob.x - oa.x) - (b.x - a.x)) < 1e-9, `saut en x à l'image ${k}`);
    assert.ok(Math.abs(unwrap(ob.y - oa.y) - (b.y - a.y) * COS) < 1e-9, `saut en y à l'image ${k}`);
  }
}
// positions à 60 images/s le long de pas (m par image)
const walk = (steps, start = { x: 20, y: 20 }) => steps.reduce((pts, [dx, dy]) => [...pts, { x: pts.at(-1).x + dx, y: pts.at(-1).y + dy }], [start]);

test("roulement en diagonale à 8 m/s (direction 0,6 ; 0,8) : aucun saut au passage du carreau", () => {
  const v = 8 / 60;
  assertSmooth(walk(Array.from({ length: 120 }, () => [0.6 * v, 0.8 * v])));
});

test("changement de direction et réception (le ballon suit le porteur) : aucun saut du motif", () => {
  const steps = [...Array.from({ length: 50 }, () => [0.12, 0]), ...Array.from({ length: 50 }, () => [-0.05, 0.1]), ...Array.from({ length: 50 }, () => [0.02, -0.03])];
  assertSmooth(walk(steps));
});

test("le motif avance par rapport au ballon dans le sens du déplacement", () => {
  const a = patternOffset({ x: 10.1, y: 5 }, 6, 1), b = patternOffset({ x: 10.2, y: 5 }, 6, 1);
  assert.ok(Math.abs(unwrap(b.x - a.x) - 0.1) < 1e-9); // décalage = déplacement : le motif avance de 2 × par rapport au sol
});

test("vitesse lue sur la piste, ballon tenu compris ; nulle sur un ballon mort ou à une coupure", () => {
  const held = run(10, 6, { holder: "Joueur" });
  assert.ok(Math.abs(ballSpeed(held, 10 + 3.5 * STEP, HALF) - 6) < 1e-6);
  assert.equal(ballSpeed(run(10, 0, { dead: true }), 10 + 3.5 * STEP, HALF), 0);
  const cut = [...run(5, 6), ...run(5, 6, { m0: 10 + 5 * STEP, x0: 60, holder: "Joueur" })];
  assert.equal(ballSpeed(cut, 10 + 4.5 * STEP, HALF), 0);
});

test("même instant, même résultat (aucun état : indépendant du pas des images)", () => {
  const track = run(50, 9);
  const t = 10 + 17.3 * STEP;
  const direct = ballMotion(track, t, HALF);
  for (let k = 0; k < 40; k += 1) ballMotion(track, 10 + k * 0.37 * STEP, HALF); // autres images lues avant
  assert.deepEqual(ballMotion(track, t, HALF), direct);
});

test("motif figé au-delà du seuil de crénelage, selon la vitesse de lecture", () => {
  const g = { x: 3.3, y: 7.1 };
  assert.notDeepEqual(patternOffset(g, 10, 1), { x: 0, y: 0 }); // 10 × 1 < 15 : le motif suit la position
  assert.deepEqual(patternOffset(g, 10, 2), { x: 0, y: 0 }); // 10 × 2 ≥ 15 : figé
  assert.deepEqual(patternOffset(g, FREEZE_SPEED / 8, 8), { x: 0, y: 0 }); // x8 : figé dès 1,9 m/s
});

test("traînée : nulle sous le seuil, chemin de 0,1 s au-delà, plafonnée, jamais au-delà de la coupure", () => {
  assert.equal(trailLength({ speed: TRAIL_SPEED - 0.1, distance: 50 }), 0);
  assert.ok(Math.abs(trailLength({ speed: 25, distance: 50 }) - 2.5) < 1e-9);
  assert.equal(trailLength({ speed: 40, distance: 50 }), TRAIL_MAX_M);
  assert.equal(trailLength({ speed: 25, distance: 0.8 }), 0.8);
});

test("la distance repart de zéro après une coupure (changement de porteur, ballon mort, mi-temps)", () => {
  const before = run(10, 20, { holder: null });
  const kick = run(10, 20, { x0: before.at(-1).x, m0: before.at(-1).minute + STEP }).map((p) => ({ ...p }));
  kick[0].holder = "Tireur"; // le tireur avait le ballon : coupure entre le dernier point tenu et le premier libre
  const track = [...before, ...kick];
  const m = ballMotion(track, kick[3].minute + 0.5 * STEP, HALF);
  assert.ok(m.distance <= 2.5 * 2 + 1e-9, `distance ${m.distance}`); // au plus 2,5 pas libres depuis la coupure
  const halfTrack = run(20, 20, { m0: HALF - 10 * STEP });
  const after = ballMotion(halfTrack, HALF + 2.5 * STEP, HALF);
  assert.ok(after.distance <= 2.5 * 2 + 1e-9, `distance ${after.distance}`); // la mi-temps coupe
});
