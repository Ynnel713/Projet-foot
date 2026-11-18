// Couleurs d'équipe de l'écran V2 (ticket v2-ecran-match/03, règle de la spec du chantier, section 2.2 ; constantes
// validées par le propriétaire le 14/11/2026). Entrée : les feuilles de match de l'API (`color`, `secondary`,
// `known_kit`, ticket EM-02). Sortie, pour chaque équipe : `fill` (couleur du joueur), `ink` (numéro) et `ring`
// (anneau). Fonction pure : même entrée, même résultat (aucun aléa, aucune horloge).

export const DELTA_E_MIN = 25; // écart minimal entre les deux équipes (CIEDE2000)
export const LIGHTNESS_STEP = 5; // pas de clarté L* quand l'extérieur garde sa teinte
export const RING_WIDTH_M = 0.12; // anneau autour du joueur, en mètres du terrain
export const INK_LIGHT = "#ffffff";
export const INK_DARK = "#000000"; // noir pur (et non #0b0f14) : numéro à 4,5:1 au moins sur toute couleur (propriétaire, 14/11/2026)
export const OFF_WHITE = "#f2efe6"; // dernier recours, avec INK_DARK
// Gazon de l'écran (bandes de tonte, source unique lue par V2Pitch) : la secondaire n'est prise que si elle s'en détache.
// Teintes sobres de la spec du chantier écran (§2.2), ticket v2-ecran-match/05, validées par le propriétaire le 18/11/2026
// avec leur effet sur cette règle (avant : #2f7d32 / #3a8f3c ; 15 kits sur 341 changent, liste dans le ticket).
export const PITCH_COLORS = ["#24603a", "#2a6b3f"];
// Repli quand la feuille de match n'a pas de couleur (traces enregistrées avant EM-02) ou que le club n'a pas de kit
// connu (`known_kit` faux, gris par défaut pour 656 clubs sur 816) : les couleurs historiques de l'écran.
export const FALLBACK = { home: "#4f8ef7", away: "#e0b84a" };
// Variante d'interface (texte, barres du momentum) : la couleur d'équipe sur le fond de l'écran doit atteindre ce
// contraste (WCAG, texte), sinon on l'éclaircit par pas de LIGHTNESS_STEP en gardant sa teinte (propriétaire, 14/11/2026 ;
// rejet A1 de l'expert : un club sombre, PSG ou Angers, devenait illisible sur le fond). Le jeton garde la vraie couleur.
export const UI_BACKGROUND = "#0b0f14";
export const UI_CONTRAST_MIN = 4.5;

// --- conversions sRGB <-> CIELAB (D65) ----------------------------------------------------------------------------

function hexToRgb(hex) {
  const v = hex.replace("#", "");
  const full = v.length === 3 ? [...v].map((c) => c + c).join("") : v;
  return [0, 2, 4].map((i) => parseInt(full.slice(i, i + 2), 16));
}

function rgbToHex(rgb) {
  return `#${rgb.map((c) => Math.round(Math.min(255, Math.max(0, c))).toString(16).padStart(2, "0")).join("")}`;
}

const toLinear = (c) => {
  const s = c / 255;
  return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
};
const fromLinear = (l) => 255 * (l <= 0.0031308 ? 12.92 * l : 1.055 * l ** (1 / 2.4) - 0.055);
const WHITE = [0.95047, 1.0, 1.08883];
const f = (t) => (t > 216 / 24389 ? Math.cbrt(t) : (24389 / 27 * t + 16) / 116);
const fInv = (t) => (t ** 3 > 216 / 24389 ? t ** 3 : (116 * t - 16) / (24389 / 27));

export function hexToLab(hex) {
  const [r, g, b] = hexToRgb(hex).map(toLinear);
  const xyz = [
    0.4124564 * r + 0.3575761 * g + 0.1804375 * b,
    0.2126729 * r + 0.7151522 * g + 0.072175 * b,
    0.0193339 * r + 0.119192 * g + 0.9503041 * b,
  ];
  const [fx, fy, fz] = xyz.map((v, i) => f(v / WHITE[i]));
  return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)];
}

export function labToHex([L, a, b]) {
  const fy = (L + 16) / 116;
  const [x, y, z] = [fInv(fy + a / 500), fInv(fy), fInv(fy - b / 200)].map((v, i) => v * WHITE[i]);
  const lin = [
    3.2404542 * x - 1.5371385 * y - 0.4985314 * z,
    -0.969266 * x + 1.8760108 * y + 0.041556 * z,
    0.0556434 * x - 0.2040259 * y + 1.0572252 * z,
  ];
  return rgbToHex(lin.map((l) => fromLinear(Math.min(1, Math.max(0, l)))));
}

// --- écart CIEDE2000 (Sharma, Wu et Dalal, 2005) ----------------------------------------------------------------

const rad = (d) => (d * Math.PI) / 180;
const deg = (r) => (r * 180) / Math.PI;

export function deltaE2000(hexA, hexB) {
  return deltaE2000Lab(hexToLab(hexA), hexToLab(hexB));
}

export function deltaE2000Lab([L1, a1, b1], [L2, a2, b2]) {
  const C1 = Math.hypot(a1, b1);
  const C2 = Math.hypot(a2, b2);
  const Cm = (C1 + C2) / 2;
  const G = 0.5 * (1 - Math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)));
  const a1p = (1 + G) * a1;
  const a2p = (1 + G) * a2;
  const C1p = Math.hypot(a1p, b1);
  const C2p = Math.hypot(a2p, b2);
  const h = (a, b) => (a === 0 && b === 0 ? 0 : (deg(Math.atan2(b, a)) + 360) % 360);
  const h1p = h(a1p, b1);
  const h2p = h(a2p, b2);
  const dLp = L2 - L1;
  const dCp = C2p - C1p;
  let dhp = 0;
  if (C1p * C2p !== 0) {
    dhp = h2p - h1p;
    if (dhp > 180) dhp -= 360;
    else if (dhp < -180) dhp += 360;
  }
  const dHp = 2 * Math.sqrt(C1p * C2p) * Math.sin(rad(dhp / 2));
  const Lpm = (L1 + L2) / 2;
  const Cpm = (C1p + C2p) / 2;
  let hpm = h1p + h2p;
  if (C1p * C2p !== 0) {
    if (Math.abs(h1p - h2p) <= 180) hpm = (h1p + h2p) / 2;
    else hpm = h1p + h2p < 360 ? (h1p + h2p + 360) / 2 : (h1p + h2p - 360) / 2;
  }
  const T = 1 - 0.17 * Math.cos(rad(hpm - 30)) + 0.24 * Math.cos(rad(2 * hpm)) + 0.32 * Math.cos(rad(3 * hpm + 6))
    - 0.2 * Math.cos(rad(4 * hpm - 63));
  const dTheta = 30 * Math.exp(-(((hpm - 275) / 25) ** 2));
  const Rc = 2 * Math.sqrt(Cpm ** 7 / (Cpm ** 7 + 25 ** 7));
  const Sl = 1 + (0.015 * (Lpm - 50) ** 2) / Math.sqrt(20 + (Lpm - 50) ** 2);
  const Sc = 1 + 0.045 * Cpm;
  const Sh = 1 + 0.015 * Cpm * T;
  const Rt = -Math.sin(rad(2 * dTheta)) * Rc;
  return Math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh));
}

// --- contraste WCAG ---------------------------------------------------------------------------------------------

export function luminance(hex) {
  const [r, g, b] = hexToRgb(hex).map(toLinear);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contrast(hexA, hexB) {
  const [hi, lo] = [luminance(hexA), luminance(hexB)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

// --- règle -------------------------------------------------------------------------------------------------------

const valid = (c) => typeof c === "string" && /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(c);

function primaryOf(lineup, side) {
  return lineup && lineup.known_kit !== false && valid(lineup.color) ? lineup.color.toLowerCase() : FALLBACK[side];
}

// Clarté décalée par pas de LIGHTNESS_STEP, d'abord à l'opposé de la clarté du domicile, puis de l'autre côté :
// première couleur qui passe le seuil (la teinte et la saturation du club sont gardées).
function shiftedLightness(color, home) {
  const [L, a, b] = hexToLab(color);
  const away = L >= hexToLab(home)[0] ? 1 : -1;
  for (const dir of [away, -away]) {
    for (let k = 1; L + dir * k * LIGHTNESS_STEP >= 0 && L + dir * k * LIGHTNESS_STEP <= 100; k += 1) {
      const candidate = labToHex([L + dir * k * LIGHTNESS_STEP, a, b]);
      if (deltaE2000(home, candidate) >= DELTA_E_MIN) return candidate;
    }
  }
  return null;
}

// Couleur de l'extérieur et la règle appliquée : 1 principale, 2 secondaire, 3 clarté décalée, 4 dernier recours.
export function awayColor(home, awayPrimary, awaySecondary) {
  if (deltaE2000(home, awayPrimary) >= DELTA_E_MIN) return { color: awayPrimary, rule: "principale" };
  if (valid(awaySecondary) && deltaE2000(home, awaySecondary) >= DELTA_E_MIN
      && PITCH_COLORS.every((g) => deltaE2000(g, awaySecondary) >= DELTA_E_MIN)) {
    return { color: awaySecondary.toLowerCase(), rule: "secondaire" };
  }
  const shifted = shiftedLightness(awayPrimary, home);
  if (shifted) return { color: shifted, rule: "clarté" };
  const last = [OFF_WHITE, INK_DARK].sort((x, y) => deltaE2000(home, y) - deltaE2000(home, x))[0];
  return { color: last, rule: "dernier recours" };
}

// Numéro : blanc ou fond sombre, le plus contrasté ; anneau : clair sur un maillot sombre, sombre sur un maillot clair.
export function inkOf(fill) {
  return contrast(fill, INK_LIGHT) >= contrast(fill, INK_DARK) ? INK_LIGHT : INK_DARK;
}

export function uiColor(fill) {
  const [L, a, b] = hexToLab(fill);
  for (let k = 0; L + k * LIGHTNESS_STEP <= 100 + LIGHTNESS_STEP; k += 1) {
    const candidate = k === 0 ? fill : labToHex([Math.min(100, L + k * LIGHTNESS_STEP), a, b]);
    if (contrast(candidate, UI_BACKGROUND) >= UI_CONTRAST_MIN) return candidate;
  }
  return INK_LIGHT;
}

export function teamColors(lineups) {
  const home = primaryOf(lineups?.home, "home");
  const away = lineups?.away?.known_kit === false || !valid(lineups?.away?.color)
    ? awayColor(home, FALLBACK.away, null)
    : awayColor(home, lineups.away.color.toLowerCase(), lineups.away.secondary);
  const team = (fill) => {
    const ink = inkOf(fill);
    return { fill, ink, ring: ink === INK_LIGHT ? INK_LIGHT : INK_DARK, ui: uiColor(fill) };
  };
  return { home: team(home), away: { ...team(away.color), rule: away.rule } };
}

// Variables CSS posées à la racine de l'écran de match, lues par les composants (plus aucune couleur d'équipe en dur).
export function teamColorVars(colors) {
  const edge = (ink) => (ink === INK_LIGHT ? INK_DARK : INK_LIGHT); // liseré du numéro, couleur opposée à l'encre
  return {
    "--team-home": colors.home.fill,
    "--team-home-ink": colors.home.ink,
    "--team-home-ink-edge": edge(colors.home.ink),
    "--team-home-ring": colors.home.ring,
    "--team-home-ui": colors.home.ui,
    "--team-away": colors.away.fill,
    "--team-away-ink": colors.away.ink,
    "--team-away-ink-edge": edge(colors.away.ink),
    "--team-away-ring": colors.away.ring,
    "--team-away-ui": colors.away.ui,
  };
}
