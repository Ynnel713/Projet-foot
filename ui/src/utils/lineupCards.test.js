import test from "node:test";
import assert from "node:assert/strict";
import { BENCH_CARD_PX, STARTER_CARD_PX, lineupColumnHeight, lineupDensity, lineupSubtitle, goalsByPlayer } from "./lineupCards.js";

// Hauteurs de colonne mesurées (tickets v2-ecran-match/10a et 10b, trace em10a) : 1366×768 570 px (HUD de 89 px),
// 1280×720 522, 1100×700 502, 960×600 402 ; tiroirs 844×390 288, 915×412 310.
const COLUMN_1366x768_PX = 570;

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

test("budgets des trois niveaux (10b) : 562, 500 et 280 px pour les titulaires seuls en serré", () => {
  assert.equal(lineupColumnHeight(11, 9, "complet"), 562);
  assert.equal(lineupColumnHeight(11, 9, "compact"), 500);
  assert.equal(lineupColumnHeight(11, 0, "serre"), 280);
});

test("niveau choisi selon la hauteur mesurée de la colonne", () => {
  const cas = [[882, "complet"], [570, "complet"], [562, "complet"], [561, "compact"], [522, "compact"],
    [502, "compact"], [500, "compact"], [499, "serre"], [402, "serre"], [310, "serre"], [288, "serre"], [0, "serre"]];
  for (const [h, attendu] of cas) assert.equal(lineupDensity(h, 11, 9), attendu, `${h} px`);
});

test("en serré, les 11 titulaires tiennent dans le plus petit tiroir (844×390 : 288 px)", () => {
  assert.ok(lineupColumnHeight(11, 0, "serre") <= 288);
});

test("banc vide : le niveau complet tient plus tôt", () => {
  assert.equal(lineupDensity(400, 11, 0), "complet"); // 12 + 44 + 4 + 16 + 286 = 362
});

test("sous-titre : formation, puis entraîneur s'il est connu", () => {
  assert.equal(lineupSubtitle({ formation: "4-3-3", coach: "Dino Toppmöller" }), "4-3-3 · Dino Toppmöller");
  assert.equal(lineupSubtitle({ formation: "4-4-2", coach: null }), "4-4-2");
});

test("buts par joueur (10c) : buts et csc comptés à part, buteur inconnu ignoré", () => {
  const goals = [
    { minute: 2, team: "away", scorer: "Loïs Openda", own_goal: false },
    { minute: 7, team: "away", scorer: "Loïs Openda", own_goal: false },
    { minute: 9, team: "home", scorer: "Amine Gouiri", own_goal: false },
    { minute: 30, team: "away", scorer: "Amine Gouiri", own_goal: true },
    { minute: 40, team: "home", scorer: null, own_goal: false },
  ];
  assert.deepEqual(goalsByPlayer(goals), {
    "Loïs Openda": { goals: 2, ownGoals: 0 },
    "Amine Gouiri": { goals: 1, ownGoals: 1 },
  });
  assert.deepEqual(goalsByPlayer([]), {});
});
