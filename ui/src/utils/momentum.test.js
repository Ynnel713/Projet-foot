import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { FULL_SCALE, LABEL, MIN_BAR_PX, barHeight, completedMinutes, momentumByMinute } from "./momentum.js";

// Trace réelle tronquée (OM–OL, `em11-om-ol`, 3 min 15 s, joueurs réduits au porteur du ballon).
const fixture = JSON.parse(readFileSync(new URL("./fixtures/momentum-om-ol-3min.json", import.meta.url)));
const { ticks, length } = fixture;

// Ancienne formule (`Momentum.jsx` avant 11a, b0c7490), recopiée comme référence : toutes les images reçues comptent.
function oldMomentumByMinute(trace, n) {
  const sums = new Array(n).fill(0);
  const counts = new Array(n).fill(0);
  for (const t of trace.ticks) {
    const m = Math.min(n - 1, Math.floor(t.minute));
    const dx = (t.ball.x - length / 2) / (length / 2);
    const holderTeam = t.ball.holder && t.players.find((p) => p.name === t.ball.holder)?.team;
    sums[m] += dx * Math.abs(dx) + (holderTeam === "home" ? 0.15 : holderTeam === "away" ? -0.15 : 0);
    counts[m] += 1;
  }
  return sums.map((v, m) => (counts[m] ? v / counts[m] : null));
}

test("constantes validées le 19/11/2026 : échelle fixe 0,6, 1 px au moins, libellé", () => {
  assert.equal(FULL_SCALE, 0.6);
  assert.equal(MIN_BAR_PX, 1);
  assert.equal(LABEL, "Pression territoriale");
});

test("minutes terminées seulement : la minute en cours n'a pas de barre", () => {
  assert.equal(completedMinutes(0, 3.24, false), 0);
  assert.equal(completedMinutes(2.99, 3.24, false), 2);
  assert.equal(completedMinutes(3, 3.24, false), 3);
  assert.equal(completedMinutes(3.24, 3.24, false), 3); // calcul pas fini : la minute 3 reste ouverte
  assert.equal(completedMinutes(51.5, 103.99, true), 51);
});

test("fin du match lue jusqu'au bout : la dernière minute compte", () => {
  assert.equal(completedMinutes(103.99, 103.99, true), 104);
  assert.equal(completedMinutes(103.98, 103.99, true), 103);
});

test("mêmes valeurs que l'ancienne formule sur les minutes terminées", () => {
  const old = oldMomentumByMinute({ ticks }, 4);
  const now = momentumByMinute(ticks, 3, length);
  assert.equal(now.length, 3);
  for (let m = 0; m < 3; m += 1) assert.ok(Math.abs(now[m] - old[m]) < 1e-12, `minute ${m}`);
});

test("la minute en cours ne moyenne aucune image : seules les minutes terminées sont calculées", () => {
  // lu à 2,5', images reçues jusqu'à 3,24' : la minute 2 est entamée, et sa moyenne dépend des images non vues
  const vues = ticks.filter((t) => t.minute < 2.5);
  assert.notDeepEqual(momentumByMinute(vues, 3, length)[2], momentumByMinute(ticks, 3, length)[2]);
  // la frise ne calcule que les minutes terminées : même résultat avec les images vues ou toutes les images reçues
  const complete = completedMinutes(2.5, 3.24, false);
  assert.equal(complete, 2);
  assert.deepEqual(momentumByMinute(vues, complete, length), momentumByMinute(ticks, complete, length));
});

test("une barre déjà affichée ne change plus de hauteur quand le match avance", () => {
  const h = (complete) => momentumByMinute(ticks, complete, length).map((v) => barHeight(v, 22));
  assert.deepEqual(h(3).slice(0, 1), h(1));
  assert.deepEqual(h(3).slice(0, 2), h(2));
});

test("échelle fixe : 0,6 en pleine hauteur, écrêtée au-delà, 1 px au moins, signe ignoré", () => {
  assert.equal(barHeight(0.6, 22), 22);
  assert.equal(barHeight(-0.9, 22), 22);
  assert.equal(barHeight(0.3, 22), 11);
  assert.equal(barHeight(-0.3, 22), 11);
  assert.equal(barHeight(0.001, 22), 1);
  assert.equal(barHeight(0, 22), 1);
});

test("minute sans image : pas de valeur", () => {
  assert.deepEqual(momentumByMinute([], 2, length), [null, null]);
});
