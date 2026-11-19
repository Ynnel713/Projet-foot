import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { eventStats, holderTeams, matchStats, possessionAt, possessionPrefix } from "./matchStats.js";

// Trace réelle réduite (OM–OL 6-3, `em11-om-ol`) : événements utiles aux statistiques et équipe du porteur par image.
const fx = JSON.parse(readFileSync(new URL("./fixtures/stats-om-ol.json", import.meta.url)));
const teams = [...fx.holders].map((c) => (c === "h" ? "home" : c === "a" ? "away" : null));
const prefix = possessionPrefix(teams);
const at = (minute) => matchStats({ events: fx.events, prefix, minute, tickSeconds: fx.tick_seconds });
const END = 104;

test("définitions (14a) : tirs, cadrés (but ou arrêt), corners, fautes, hors-jeu, par équipe", () => {
  const ev = [
    { id: 0, minute: 1, kind: "tir", team: "home", cause: null },
    { id: 1, minute: 1.01, kind: "arrêt", team: "away", cause: 0, detail: "capté" }, // cadré pour le tireur (domicile)
    { id: 2, minute: 2, kind: "tir", team: "home", cause: 1 },
    { id: 3, minute: 2.01, kind: "contre", team: "away", cause: 2 }, // contré : tir non cadré
    { id: 4, minute: 3, kind: "tir", team: "away", cause: 3 },
    { id: 5, minute: 3.01, kind: "but", team: "away", cause: 4 },
    { id: 6, minute: 4, kind: "remise", team: "home", cause: 5, detail: "corner" },
    { id: 7, minute: 4.5, kind: "remise", team: "home", cause: 6, detail: "touche" },
    { id: 8, minute: 5, kind: "faute", team: "away", cause: 7, detail: "avantage" },
    { id: 9, minute: 6, kind: "hors-jeu", team: "home", cause: 8 },
  ];
  const s = eventStats(ev, 10);
  assert.deepEqual(s.shots, { home: 2, away: 1 });
  assert.deepEqual(s.onTarget, { home: 1, away: 1 });
  assert.deepEqual(s.corners, { home: 1, away: 0 });
  assert.deepEqual(s.fouls, { home: 0, away: 1 });
  assert.deepEqual(s.offsides, { home: 1, away: 0 });
  // tir lu mais issue pas encore lue : pas encore cadré
  assert.deepEqual(eventStats(ev, 1.005).onTarget, { home: 0, away: 0 });
  assert.deepEqual(eventStats(ev, 1.005).shots, { home: 1, away: 0 });
});

test("jamais de futur : chaque valeur = événements lus, et ne recule pas quand le temps lu avance (trace réelle)", () => {
  let previous = null;
  for (let m = 0; m <= END; m += 0.25) {
    const s = at(m);
    const seen = fx.events.filter((e) => e.minute <= m);
    for (const side of ["home", "away"]) {
      assert.equal(s.shots[side], seen.filter((e) => e.kind === "tir" && e.team === side).length);
      assert.equal(s.fouls[side], seen.filter((e) => e.kind === "faute" && e.team === side).length);
      assert.ok(s.onTarget[side] <= s.shots[side]);
      const goals = fx.goals.filter((g) => g.team === side && g.minute <= m).length;
      assert.ok(goals <= s.onTarget[side], `buts ≤ cadrés à ${m}'`);
      if (previous) {
        for (const k of ["shots", "onTarget", "corners", "fouls", "offsides"]) assert.ok(s[k][side] >= previous[k][side]);
      }
    }
    if (s.possession) assert.equal(s.possession.home + s.possession.away, 100);
    previous = s;
  }
});

test("fin du match OM–OL : valeurs de la trace", () => {
  const s = at(END);
  const count = (kind, side, detail) =>
    fx.events.filter((e) => e.kind === kind && e.team === side && (detail === undefined || e.detail === detail)).length;
  assert.deepEqual(s.shots, { home: count("tir", "home"), away: count("tir", "away") });
  assert.deepEqual(s.corners, { home: count("remise", "home", "corner"), away: count("remise", "away", "corner") });
  assert.equal(s.onTarget.home + s.onTarget.away, 18); // 9 buts + 9 arrêts, tous issus d'un tir
  assert.equal(s.cards, null);
});

test("possession « dernier porteur » : sans porteur, l'équipe du dernier porteur garde le ballon", () => {
  const p = possessionPrefix([null, "home", null, null, "away", null]);
  assert.equal(possessionAt(p, 0), null); // personne n'a encore eu le ballon
  assert.deepEqual(possessionAt(p, 3), { home: 100, away: 0 }); // images 1 à 3 : domicile
  assert.deepEqual(possessionAt(p, 5), { home: 60, away: 40 }); // 3 images domicile, 2 extérieur
  assert.deepEqual(possessionAt(p, 99), { home: 60, away: 40 }); // au-delà : bornée à la dernière image
});

test("équipe du porteur lue dans les images de la trace", () => {
  const ticks = [
    { ball: { holder: null }, players: [] },
    { ball: { holder: "A" }, players: [{ name: "A", team: "away" }, { name: "B", team: "home" }] },
  ];
  assert.deepEqual(holderTeams(ticks), [null, "away"]);
});
