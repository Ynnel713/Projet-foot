// Règle de couleurs d'équipe (ticket v2-ecran-match/03) : `node --test` (script `npm test`).
// Échantillon : les 341 kits connus de `ligue1sim.kits.CLUB_KIT` (principale, secondaire), exportés dans
// teamColors.sample.json le 14/11/2026 ; toutes les paires domicile / extérieur ordonnées sont testées.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  DELTA_E_MIN, FALLBACK, INK_DARK, INK_LIGHT, PITCH_COLORS, UI_BACKGROUND, UI_CONTRAST_MIN, awayColor, contrast, deltaE2000,
  deltaE2000Lab, labToHex, hexToLab, teamColors, teamColorVars, uiColor,
} from "./teamColors.js";

const SAMPLE = JSON.parse(readFileSync(new URL("./teamColors.sample.json", import.meta.url), "utf-8"));
const lineup = (k) => ({ color: k.color, secondary: k.secondary, known_kit: true });

test("CIEDE2000 redonne les paires de référence de Sharma, Wu et Dalal (2005)", () => {
  const pairs = [
    [[50, 2.6772, -79.7751], [50, 0, -82.7485], 2.0425],
    [[50, -1.3802, -84.2814], [50, 0, -82.7485], 1.0],
    [[50, 2.49, -0.001], [50, -2.49, 0.0009], 7.1792],
    [[50, 0, 0], [50, -1, 2], 2.3669],
    [[60.2574, -34.0099, 36.2677], [60.4626, -34.1751, 39.4387], 1.2644],
    [[22.7233, 20.0904, -46.694], [23.0331, 14.973, -42.5619], 2.0373],
    [[90.9257, -0.5406, -0.9208], [88.6381, -0.8985, -0.7239], 1.5381],
  ];
  for (const [a, b, expected] of pairs) assert.ok(Math.abs(deltaE2000Lab(a, b) - expected) < 1e-4, `${a} ${b}`);
});

test("conversion Lab aller-retour à une unité près", () => {
  for (const hex of ["#000000", "#ffffff", "#e51b33", "#293657", "#2f7d32", "#0b0f14"]) {
    assert.equal(labToHex(hexToLab(hex)), hex);
  }
});

test("l'échantillon compte au moins 40 clubs, dont des cas pathologiques", () => {
  assert.ok(SAMPLE.length >= 40);
  const lab = SAMPLE.map((k) => hexToLab(k.color));
  assert.ok(lab.some(([L]) => L > 90), "club blanc");
  assert.ok(lab.some(([L]) => L < 15), "club noir");
  assert.ok(lab.some(([, a, b]) => a > 40 && b > 20), "club rouge");
  assert.ok(lab.some(([, a]) => a < -25), "club vert");
});

test("toutes les paires de l'échantillon : équipes distinctes, domicile intact, numéro lisible", () => {
  const rules = {};
  let worstInk = Infinity;
  for (const h of SAMPLE) {
    for (const a of SAMPLE) {
      const c = teamColors({ home: lineup(h), away: lineup(a) });
      assert.equal(c.home.fill, h.color);
      assert.ok(deltaE2000(c.home.fill, c.away.fill) >= DELTA_E_MIN, `${h.club} / ${a.club}`);
      rules[c.away.rule] = (rules[c.away.rule] || 0) + 1;
      worstInk = Math.min(worstInk, contrast(c.home.fill, c.home.ink), contrast(c.away.fill, c.away.ink));
    }
  }
  assert.ok(worstInk >= 4.5, `contraste du numéro le plus faible : ${worstInk.toFixed(2)}`);
  assert.ok(rules.principale > 0 && rules.secondaire > 0, JSON.stringify(rules));
});

test("paires pathologiques : blanc contre blanc, rouge contre rouge, même club", () => {
  const white = { color: "#fdfdfd", secondary: "#8993bd", known_kit: true };
  const white2 = { color: "#f0eeee", secondary: "#e2e2e2", known_kit: true };
  const red = { color: "#e51b33", secondary: "#f0eeee", known_kit: true };
  const red2 = { color: "#dd131c", secondary: "#dd131c", known_kit: true };
  for (const [home, away] of [[white, white2], [red, red2], [red, red], [white, white]]) {
    const c = teamColors({ home, away });
    assert.equal(c.home.fill, home.color);
    assert.ok(deltaE2000(c.home.fill, c.away.fill) >= DELTA_E_MIN);
  }
  // rouge contre rouge sans secondaire utilisable : la teinte rouge est gardée, seule la clarté change
  const shifted = awayColor("#e51b33", "#dd131c", "#dd131c");
  assert.equal(shifted.rule, "clarté");
  const [, a, b] = hexToLab(shifted.color);
  assert.ok(a > 30 && b > 10, shifted.color);
});

test("la secondaire n'est pas prise si elle se confond avec le gazon", () => {
  // le vert du gazon dessiné (ticket v2-ecran-match/05 : la constante, plus une teinte écrite en dur)
  for (const grass of PITCH_COLORS) {
    const r = awayColor("#e51b33", "#dd131c", grass);
    assert.notEqual(r.color, grass);
  }
});

test("repli sans couleur ou sans kit connu : couleurs historiques de l'écran", () => {
  assert.deepEqual([teamColors(null).home.fill, teamColors(null).away.fill], [FALLBACK.home, FALLBACK.away]);
  const unknown = { color: "#6b7280", secondary: "#d1d5db", known_kit: false };
  const c = teamColors({ home: unknown, away: unknown });
  assert.deepEqual([c.home.fill, c.away.fill], [FALLBACK.home, FALLBACK.away]);
  const mixed = teamColors({ home: { color: "#293657", secondary: "#7d2537", known_kit: true }, away: unknown });
  assert.equal(mixed.home.fill, "#293657");
  assert.ok(deltaE2000(mixed.home.fill, mixed.away.fill) >= DELTA_E_MIN);
});

test("encre et anneau : blanc sur un maillot sombre, sombre sur un maillot clair", () => {
  const c = teamColors({ home: { color: "#191919", known_kit: true }, away: { color: "#fdfdfd", known_kit: true } });
  assert.deepEqual([c.home.ink, c.home.ring], [INK_LIGHT, INK_LIGHT]);
  assert.deepEqual([c.away.ink, c.away.ring], [INK_DARK, INK_DARK]);
});

test("variante d'interface : 4,5:1 sur le fond de l'écran pour tous les kits, teinte gardée", () => {
  let worstHue = 0;
  for (const k of SAMPLE) {
    for (const color of [k.color, k.secondary]) {
      const ui = uiColor(color);
      assert.ok(contrast(ui, UI_BACKGROUND) >= UI_CONTRAST_MIN, `${k.club} ${color} -> ${ui}`);
      if (contrast(color, UI_BACKGROUND) >= UI_CONTRAST_MIN) assert.equal(ui, color); // déjà lisible : inchangée
      const [, a1, b1] = hexToLab(color);
      const [, a2, b2] = hexToLab(ui);
      if (Math.hypot(a1, b1) > 15 && Math.hypot(a2, b2) > 15) {
        const d = Math.abs(Math.atan2(b1, a1) - Math.atan2(b2, a2)) * 180 / Math.PI;
        worstHue = Math.max(worstHue, Math.min(d, 360 - d));
      }
    }
  }
  assert.ok(worstHue <= 20, `écart de teinte maximal ${worstHue.toFixed(1)}°`);
  // les deux cas du rejet : PSG (marine) et Angers (noir), illisibles avant la variante
  assert.ok(contrast("#293657", UI_BACKGROUND) < 2 && contrast(uiColor("#293657"), UI_BACKGROUND) >= 4.5);
  assert.ok(contrast("#191919", UI_BACKGROUND) < 2 && contrast(uiColor("#191919"), UI_BACKGROUND) >= 4.5);
});

test("déterministe : même entrée, même résultat, variables CSS complètes", () => {
  const input = { home: lineup(SAMPLE[3]), away: lineup(SAMPLE[17]) };
  assert.deepEqual(teamColors(input), teamColors(structuredClone(input)));
  const vars = teamColorVars(teamColors(input));
  assert.deepEqual(Object.keys(vars).sort(), ["--team-away", "--team-away-ink", "--team-away-ink-edge",
    "--team-away-ring", "--team-away-ui", "--team-home", "--team-home-ink", "--team-home-ink-edge", "--team-home-ring",
    "--team-home-ui"]);
  assert.notEqual(vars["--team-home-ink"], vars["--team-home-ink-edge"]);
});
