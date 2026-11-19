import test from "node:test";
import assert from "node:assert/strict";
import { AXIS_Y, BARS_BOTTOM_Y, FRISE_PX, LABEL_ROW_PX, barBox, domainMinutes, minuteX, ticks } from "./momentumLayout.js";

test("hauteurs validées le 19/11/2026 : frise de 72 px, axe à 30 px, barres jusqu'à 52 px", () => {
  assert.equal(FRISE_PX, 72);
  assert.equal(AXIS_Y, 30);
  assert.equal(BARS_BOTTOM_Y, 52);
  assert.equal(BARS_BOTTOM_Y + 8 + LABEL_ROW_PX, FRISE_PX);
});

test("domaine fixe de 105 minutes, plus seulement si le match dure davantage", () => {
  assert.equal(domainMinutes(undefined), 105);
  assert.equal(domainMinutes(12.4), 105);
  assert.equal(domainMinutes(104.2), 105);
  assert.equal(domainMinutes(105.0), 105);
  assert.equal(domainMinutes(107.3), 108);
});

test("une barre ne bouge pas quand le match avance (même domaine de la 10e minute à la fin)", () => {
  const d10 = domainMinutes(10), dFin = domainMinutes(98.7);
  assert.deepEqual(barBox(5, 1346, d10), barBox(5, 1346, dFin));
});

test("barres : écart de 2 px, 1 px de large au moins, contiguës d'une minute à l'autre", () => {
  const a = barBox(0, 1050, 105), b = barBox(1, 1050, 105);
  assert.equal(a.x, 1);
  assert.equal(a.width, 8);
  assert.equal(b.x - (a.x + a.width), 2);
  assert.equal(barBox(0, 50, 105).width, 1);
});

test("abscisse proportionnelle à l'instant", () => {
  assert.equal(minuteX(52.5, 1050, 105), 525);
});

test("repères : 2e période placée sur son début réel seulement une fois atteinte", () => {
  const avant = ticks(47, false), apres = ticks(47, true);
  assert.equal(avant.halfLine, null);
  assert.deepEqual(avant.labels.map((t) => t.minute), [0, 15, 30, 45, 60, 75, 90]);
  assert.equal(apres.halfLine, 47);
  assert.deepEqual(apres.labels.map((t) => t.minute), [0, 15, 30, 45, 62, 77, 92]);
  assert.deepEqual(apres.labels.map((t) => t.label), ["0'", "15'", "30'", "45'", "60'", "75'", "90'"]);
});

test("début de 2e période inconnu : repères à 45'", () => {
  assert.equal(ticks(null, true).labels.at(-1).minute, 90);
});

test("fin de match en milieu de minute : la dernière barre s'arrête au curseur (réserve A1 de 11b)", () => {
  const W = 1346, D = 105;
  for (const end of [96.3, 96.95, 96.02, 103.99]) {
    const m = Math.floor(end);
    const b = barBox(m, W, D, end);
    assert.ok(b.x + b.width <= minuteX(end, W, D) + 1e-9, `fin ${end}`);
    assert.ok(b.width >= 1);
    // les barres précédentes ne bougent pas
    assert.deepEqual(barBox(m - 1, W, D, end), barBox(m - 1, W, D));
  }
  // 96,3' sur 1346 px : créneau de 12,82 px, barre bornée à 0,3 × 12,82 − 1 ≈ 2,85 px
  assert.ok(Math.abs(barBox(96, W, D, 96.3).width - (0.3 * W / D - 1)) < 1e-9);
});
