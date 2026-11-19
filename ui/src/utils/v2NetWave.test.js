// Filet qui ondule sur un but (ticket v2-ecran-match/21b) : `node --test` (script `npm test`).
import { test } from "node:test";
import assert from "node:assert/strict";
import { WAVE_DECAY_S, WAVE_DURATION_S, netWave } from "./v2NetWave.js";

const L = 105;
const HALF = 52;
const goals = [
  { minute: 10, team: "home" },
  { minute: 30, team: "away" },
  { minute: 60, team: "home" },
  { minute: 80, team: "away" },
];
const at = (m, s) => m + s / 60;

test("recul maximal à l'instant du but, puis amorti", () => {
  assert.equal(netWave(goals, 10, HALF, L).k, 1);
  const k = (s) => Math.abs(netWave(goals, at(10, s), HALF, L).k);
  assert.ok(k(0.5) <= Math.exp(-0.5 / WAVE_DECAY_S) + 1e-12);
  assert.ok(k(1.5) <= Math.exp(-1.5 / WAVE_DECAY_S) + 1e-12); // borne tirée de la constante (A2 de l'expert)
});

test("rien avant le but ni à partir de la fin de l'ondulation", () => {
  assert.equal(netWave(goals, at(10, -0.01), HALF, L), null);
  // juste après la borne : (minute − but) × 60 n'est exact qu'à 1e-14 près en flottant
  assert.equal(netWave(goals, at(10, WAVE_DURATION_S + 1e-9), HALF, L), null);
  assert.notEqual(netWave(goals, at(10, WAVE_DURATION_S - 0.01), HALF, L), null);
  assert.equal(netWave(goals, 20, HALF, L), null);
  assert.equal(netWave([], 10, HALF, L), null);
});

test("le filet de la vue, dans chaque période", () => {
  assert.equal(netWave(goals, at(10, 0.1), HALF, L).x, L); // 1re période, domicile : but en x = L
  assert.equal(netWave(goals, at(30, 0.1), HALF, L).x, 0); // 1re période, extérieur : x = 0
  assert.equal(netWave(goals, at(60, 0.1), HALF, L).x, 0); // 2e période (scène retournée), domicile : x = 0
  assert.equal(netWave(goals, at(80, 0.1), HALF, L).x, L); // 2e période, extérieur : x = L
});

test("temps additionnel de la 1re période en direct (2e période encore inconnue) : filet de la 1re période", () => {
  // réserve A1 de l'expert : sans début de 2e période connu, la scène n'est pas retournée, l'ondulation non plus
  assert.equal(netWave([{ minute: 46, team: "home" }], at(46, 0.1), Infinity, L).x, L);
  assert.equal(netWave([{ minute: 46, team: "away" }], at(46, 0.1), Infinity, L).x, 0);
});

test("deux buts rapprochés : le plus récent l'emporte", () => {
  const close = [{ minute: 10, team: "home" }, { minute: at(10, 1), team: "away" }];
  assert.equal(netWave(close, at(10, 1.2), HALF, L).x, 0);
});
