// Raccourcis clavier de la lecture (ticket v2-ecran-match/09) : `node --test` (script `npm test`).
import { test } from "node:test";
import assert from "node:assert/strict";
import { playbackKey, speedLabel } from "./playbackKeys.js";

const SPEEDS = [1, 1.5, 2, 8, 32];
const key = (k, extra = {}) => playbackKey({ key: k, target: { tagName: "BODY" }, ...extra }, SPEEDS);

test("barre d'espace : lecture/pause, y compris depuis un bouton", () => {
  assert.deepEqual(key(" "), { type: "toggle" });
  assert.deepEqual(playbackKey({ key: " ", target: { tagName: "BUTTON" } }, SPEEDS), { type: "toggle" });
});

test("touches 1 à 5 : les vitesses dans l'ordre", () => {
  assert.deepEqual(["1", "2", "3", "4", "5"].map((k) => key(k).speed), SPEEDS);
  assert.equal(key("6"), null);
  assert.equal(key("0"), null);
  assert.equal(key("Enter"), null);
});

test("clavier AZERTY et pavé numérique : la position de la touche compte (réserve A1)", () => {
  const azerty = [["&", "Digit1"], ["é", "Digit2"], ['"', "Digit3"], ["'", "Digit4"], ["(", "Digit5"]];
  assert.deepEqual(azerty.map(([k, code]) => key(k, { code }).speed), SPEEDS);
  assert.deepEqual(["1", "2", "3", "4", "5"].map((d) => key(d, { code: `Numpad${d}` }).speed), SPEEDS);
  assert.equal(key("-", { code: "Digit6" }), null);
  assert.equal(key("é", { code: "KeyE" }), null);
});

test("touche maintenue : une seule commande (réserve A3)", () => {
  assert.equal(key(" ", { code: "Space", repeat: true }), null);
  assert.equal(key("1", { code: "Digit1", repeat: true }), null);
});

test("ignoré dans un champ de saisie et avec une touche de modification", () => {
  for (const tagName of ["INPUT", "TEXTAREA", "SELECT"]) assert.equal(key(" ", { target: { tagName } }), null);
  assert.equal(key("1", { target: { tagName: "DIV", isContentEditable: true } }), null);
  assert.equal(key("1", { ctrlKey: true }), null);
  assert.equal(key(" ", { metaKey: true }), null);
  assert.equal(key("2", { altKey: true }), null);
});

test("libellés des vitesses à la française", () => {
  assert.deepEqual(SPEEDS.map(speedLabel), ["×1", "×1,5", "×2", "×8", "×32"]);
});
