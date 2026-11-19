import test from "node:test";
import assert from "node:assert/strict";
import { BENCH_CARD_PX, STARTER_CARD_PX, lineupColumnHeight, lineupSubtitle } from "./lineupCards.js";

// Colonne de composition à 1366×768 : 576 px (mesure du ticket v2-ecran-match/04).
const COLUMN_1366x768_PX = 576;

test("constantes validées le 19/11/2026 : cartes de 26 et 20 px", () => {
  assert.equal(STARTER_CARD_PX, 26);
  assert.equal(BENCH_CARD_PX, 20);
});

test("11 titulaires et 9 remplaçants tiennent dans la colonne de 1366×768", () => {
  assert.ok(lineupColumnHeight(11, 9) <= COLUMN_1366x768_PX, `${lineupColumnHeight(11, 9)} px`);
});

test("sans remplaçant, la section disparaît du budget", () => {
  assert.equal(lineupColumnHeight(11, 9) - lineupColumnHeight(11, 0), 4 + 16 + 9 * BENCH_CARD_PX);
});

test("sous-titre : formation, puis entraîneur s'il est connu", () => {
  assert.equal(lineupSubtitle({ formation: "4-3-3", coach: "Dino Toppmöller" }), "4-3-3 · Dino Toppmöller");
  assert.equal(lineupSubtitle({ formation: "4-4-2", coach: null }), "4-4-2");
});
