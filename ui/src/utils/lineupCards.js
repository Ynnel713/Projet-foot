// Gabarit des cartes de composition (ticket v2-ecran-match/10a, constantes validées par le propriétaire le 19/11/2026).
// La spec prévoyait 36 px par carte : incompatible avec 11 titulaires + 9 remplaçants sans défilement dans une colonne
// de 570 px (1366×768). Un seul gabarit en largeur, sans palier grand écran (décision du 19/11/2026).
//
// Ticket v2-ecran-match/10b (validé par le propriétaire le 19/11/2026) : la place manque en HAUTEUR, pas en largeur.
// La colonne mesure sa hauteur et prend le niveau le plus aéré qui tient (`lineupDensity`) : complet (10a), compact,
// serré (titulaires toujours visibles, remplaçants atteints en défilant, entraîneur au survol).
export const STARTER_CARD_PX = 26;
export const BENCH_CARD_PX = 20;
export const NUMBER_PX = 20; // pastille du numéro, titulaire
export const BENCH_NUMBER_PX = 16; // pastille du numéro, remplaçant (carte de 20 px ; réserve A1 acceptée le 19/11/2026)
export const POSTE_PX = 28;
export const EDGE_PX = 3; // liseré à la couleur d'équipe
export const CREST_PX = 28;
export const BENCH_TEXT_OPACITY = 0.6;

// Hauteurs fixes des autres blocs de la colonne (px), pour le budget vertical. Elles pilotent aussi le rendu
// (`LineupPanel` lit `DENSITIES`), ce qui lie le budget à l'écran (réserve A3 de 10a).
export const PADDING_Y_PX = 12; // 6 px en haut et en bas
export const HEADER_PX = 44; // écusson + club (28), formation · entraîneur (16)
export const HEADER_GAP_PX = 4;
export const SECTION_TITLE_PX = 16;
export const BENCH_GAP_PX = 4;

export const DENSITIES = {
  complet: { starter: STARTER_CARD_PX, bench: BENCH_CARD_PX, number: NUMBER_PX, benchNumber: BENCH_NUMBER_PX, header: HEADER_PX, crest: CREST_PX },
  compact: { starter: 22, bench: 18, number: 18, benchNumber: 16, header: HEADER_PX, crest: CREST_PX },
  serre: { starter: 20, bench: 18, number: 16, benchNumber: 16, header: 28, crest: 20 }, // en-tête sur une ligne
};
export const DENSITY_ORDER = ["complet", "compact", "serre"];

// Hauteur de la colonne pour n titulaires et b remplaçants (section des remplaçants absente si b = 0).
export function lineupColumnHeight(starters, bench, density = "complet") {
  const d = DENSITIES[density];
  const benchBlock = bench > 0 ? BENCH_GAP_PX + SECTION_TITLE_PX + bench * d.bench : 0;
  return PADDING_Y_PX + d.header + HEADER_GAP_PX + SECTION_TITLE_PX + starters * d.starter + benchBlock;
}

// Niveau le plus aéré dont la colonne entière tient dans `available` px ; sinon « serré » (le banc défile).
export function lineupDensity(available, starters, bench) {
  return DENSITY_ORDER.find((d) => lineupColumnHeight(starters, bench, d) <= available) ?? "serre";
}

// Ligne d'en-tête sous le club : « 4-3-3 · Entraîneur », l'entraîneur seulement s'il est connu.
export function lineupSubtitle(lineup) {
  return [lineup.formation, lineup.coach].filter(Boolean).join(" · ");
}
