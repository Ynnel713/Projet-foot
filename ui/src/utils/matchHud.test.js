// HUD de l'écran Match (ticket v2-ecran-match/08) : `node --test` (script `npm test`).
import { test } from "node:test";
import assert from "node:assert/strict";
import { clock } from "./matchClock.js";
import { BADGES, matchBadge, revealedScore, revealedScorers, scorerText, hudName } from "./matchHud.js";

// Trace réduite : 2e période donnée par le moteur à la minute 48, 3 et 4 minutes annoncées.
const trace = { second_half_start_minute: 48, added_minutes: [3, 4] };

test("minute affichée : libellés de clock() inchangés (déplacement seul)", () => {
  assert.deepEqual(clock(trace, 0), { second: false, label: "0'", announced: null });
  assert.deepEqual(clock(trace, 12.7), { second: false, label: "12'", announced: null });
  assert.deepEqual(clock(trace, 44.99), { second: false, label: "44'", announced: null });
  assert.deepEqual(clock(trace, 45), { second: false, label: "45+1'", announced: 3 });
  assert.deepEqual(clock(trace, 46.5), { second: false, label: "45+2'", announced: 3 });
  assert.deepEqual(clock(trace, 48), { second: true, label: "45'", announced: null });
  assert.deepEqual(clock(trace, 67.2), { second: true, label: "64'", announced: null });
  assert.deepEqual(clock(trace, 93), { second: true, label: "90+1'", announced: 4 });
  assert.deepEqual(clock(trace, 96.9), { second: true, label: "90+4'", announced: 4 });
});

test("en direct, 2e période encore inconnue : on reste en 1re période, temps additionnel compris", () => {
  const live = { second_half_start_minute: null, added_minutes: [2] };
  assert.deepEqual(clock(live, 46), { second: false, label: "45+2'", announced: 2 });
});

const goals = [
  { minute: 10.5, team: "home" },
  { minute: 30, team: "away" },
  { minute: 61.25, team: "home" },
];

test("score jamais en avance sur la lecture : un but compte à partir de sa minute exacte", () => {
  for (const g of goals) {
    const before = revealedScore(goals, g.minute * 60 - 0.01);
    const at = revealedScore(goals, g.minute * 60);
    assert.equal(at[g.team], before[g.team] + 1);
  }
  assert.deepEqual(revealedScore(goals, 0), { home: 0, away: 0 });
  assert.deepEqual(revealedScore(goals, 30 * 60), { home: 1, away: 1 });
  assert.deepEqual(revealedScore(goals, 95 * 60), { home: 2, away: 1 });
  assert.deepEqual(revealedScore([], 95 * 60), { home: 0, away: 0 });
});

test("badge d'état : fin, puis mi-temps, puis chargement, sinon en direct", () => {
  assert.equal(matchBadge({ finished: true, halfBanner: true, waiting: true }), BADGES.finished);
  assert.equal(matchBadge({ finished: false, halfBanner: true, waiting: true }), BADGES.halftime);
  assert.equal(matchBadge({ finished: false, halfBanner: false, waiting: true }), BADGES.loading);
  assert.equal(matchBadge({ finished: false, halfBanner: false, waiting: false }), BADGES.live);
  assert.deepEqual(
    Object.values(BADGES).map((b) => b.label),
    ["TERMINÉ", "MI-TEMPS", "CHARGEMENT…", "EN DIRECT"],
  );
});

test("buteurs révélés (08c) : seulement les buts lus, groupés par buteur, dans l'ordre du premier but", () => {
  const label = (m) => `${Math.floor(m)}'`;
  const goals = [
    { minute: 2.04, team: "away", scorer: "Openda", own_goal: false },
    { minute: 7.2, team: "away", scorer: "Openda", own_goal: false },
    { minute: 9.66, team: "home", scorer: "Gouiri", own_goal: false },
    { minute: 16.7, team: "away", scorer: "Mata", own_goal: true },
  ];
  const at10 = revealedScorers(goals, 10 * 60, label);
  assert.deepEqual(at10.away.shown, [{ name: "Openda", ownGoal: false, minutes: ["2'", "7'"] }]);
  assert.deepEqual(at10.home.shown, [{ name: "Gouiri", ownGoal: false, minutes: ["9'"] }]);
  assert.equal(at10.away.hidden, 0);
  const at17 = revealedScorers(goals, 17 * 60, label);
  assert.equal(scorerText(at17.away.shown[1]), "Mata (csc) 16'");
  assert.deepEqual(revealedScorers(goals, 0, label).home.shown, []);
  // but lu à la seconde près, comme le score
  assert.equal(revealedScorers(goals, 2.04 * 60, label).away.shown.length, 1);
});

test("buteurs révélés (08c) : 3 lignes au plus, les 2 premiers puis « +n autres »", () => {
  const label = (m) => `${m}'`;
  const goals = ["A", "B", "C", "D", "E"].map((s, i) => ({ minute: i + 1, team: "home", scorer: s }));
  const three = revealedScorers(goals.slice(0, 3), 99 * 60, label).home;
  assert.equal(three.shown.length, 3);
  assert.equal(three.hidden, 0);
  const five = revealedScorers(goals, 99 * 60, label).home;
  assert.deepEqual(five.shown.map((r) => r.name), ["A", "B"]);
  assert.equal(five.hidden, 3);
  assert.equal(five.all.length, 5);
});

test("buteur inconnu : « But »", () => {
  const r = revealedScorers([{ minute: 5, team: "home", scorer: null }], 600, () => "5'");
  assert.equal(scorerText(r.home.shown[0]), "But 5'");
});

test("nom du HUD sans le prénom (08c)", () => {
  assert.equal(hudName("Khvicha Kvaratskhelia"), "Kvaratskhelia");
  assert.equal(hudName("Jelle Van Neck"), "Van Neck");
  assert.equal(hudName("CJ Egan-Riley"), "Egan-Riley");
  assert.equal(hudName("Abner"), "Abner");
  assert.equal(hudName("But"), "But");
});
