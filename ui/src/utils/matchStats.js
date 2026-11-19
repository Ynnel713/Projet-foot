// Statistiques du match filtrées sur le temps lu (ticket v2-ecran-match/14a, définitions validées par le propriétaire le
// 19/11/2026). Module sans import : testé sous node. Jamais de futur : un événement compte quand sa minute est ≤ au
// temps lu ; un tir est cadré quand son issue (but ou arrêt) est déjà lue.
const SIDES = ["home", "away"];
const zero = () => ({ home: 0, away: 0 });

// Tirs, tirs cadrés, corners, fautes (commises), hors-jeu (signalés contre l'équipe) jusqu'à `minute`.
export function eventStats(events, minute) {
  const s = { shots: zero(), onTarget: zero(), corners: zero(), fouls: zero(), offsides: zero() };
  const shots = new Map(); // tir lu : identifiant → équipe
  for (const e of events) {
    if (e.minute > minute) continue;
    if (!SIDES.includes(e.team)) continue;
    if (e.kind === "tir") {
      s.shots[e.team] += 1;
      shots.set(e.id, e.team);
    } else if ((e.kind === "but" || e.kind === "arrêt") && shots.has(e.cause)) {
      s.onTarget[shots.get(e.cause)] += 1; // équipe du tireur (un arrêt est porté par l'équipe du gardien)
    } else if (e.kind === "remise" && e.detail === "corner") s.corners[e.team] += 1;
    else if (e.kind === "faute") s.fouls[e.team] += 1;
    else if (e.kind === "hors-jeu") s.offsides[e.team] += 1;
  }
  return s;
}

// Possession « dernier porteur » : pour chaque image, l'équipe du porteur, ou à défaut celle du dernier porteur ;
// sommes cumulées (images avant la k-ième comprise) pour lire la possession à n'importe quel instant sans reparcourir
// les images. `teams[k]` : "home", "away" ou null (pas de porteur).
export function possessionPrefix(teams) {
  const home = new Uint32Array(teams.length + 1);
  const away = new Uint32Array(teams.length + 1);
  let last = null;
  for (let k = 0; k < teams.length; k++) {
    if (teams[k]) last = teams[k];
    home[k + 1] = home[k] + (last === "home" ? 1 : 0);
    away[k + 1] = away[k] + (last === "away" ? 1 : 0);
  }
  return { home, away };
}

// Équipe du porteur à chaque image d'une trace V2 (`tick.ball.holder` est un nom de joueur).
export function holderTeams(ticks) {
  return ticks.map((t) => (t.ball.holder ? (t.players.find((p) => p.name === t.ball.holder)?.team ?? null) : null));
}

// Possession en % (entiers, total 100) sur les images 0 à `index` ; null tant qu'aucune équipe n'a eu le ballon.
export function possessionAt(prefix, index) {
  const k = Math.max(0, Math.min(prefix.home.length - 1, index + 1));
  const h = prefix.home[k];
  const a = prefix.away[k];
  if (h + a === 0) return null;
  const home = Math.round((100 * h) / (h + a));
  return { home, away: 100 - home };
}

// Toutes les statistiques à `minute` (temps lu) : `prefix` de `possessionPrefix`, `tickSeconds` : pas des images.
// Cartons : null (« — ») tant que le moteur n'en produit pas (ticket v2-attributs-restants/09a).
export function matchStats({ events, prefix, minute, tickSeconds }) {
  return {
    possession: possessionAt(prefix, Math.floor((minute * 60) / tickSeconds + 1e-9)),
    ...eventStats(events, minute),
    cards: null,
  };
}
