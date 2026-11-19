// Gabarit des cartes de composition (ticket v2-ecran-match/10a, constantes validées par le propriétaire le 19/11/2026).
// La spec prévoyait 36 px par carte : incompatible avec 11 titulaires + 9 remplaçants sans défilement dans une colonne
// de 576 px (1366×768). Un seul gabarit, sans palier grand écran (décision du 19/11/2026).
export const STARTER_CARD_PX = 26;
export const BENCH_CARD_PX = 20;
export const NUMBER_PX = 20; // pastille du numéro, titulaire
export const BENCH_NUMBER_PX = 16; // pastille du numéro, remplaçant (carte de 20 px)
export const POSTE_PX = 28;
export const EDGE_PX = 3; // liseré à la couleur d'équipe
export const CREST_PX = 28;
export const BENCH_TEXT_OPACITY = 0.6;

// Hauteurs fixes des autres blocs de la colonne (px), pour le budget vertical.
export const PADDING_Y_PX = 12; // 6 px en haut et en bas
export const HEADER_PX = 44; // écusson + club (28), formation · entraîneur (16)
export const HEADER_GAP_PX = 4;
export const SECTION_TITLE_PX = 16;
export const BENCH_GAP_PX = 4;

// Hauteur de la colonne pour n titulaires et b remplaçants (section des remplaçants absente si b = 0).
export function lineupColumnHeight(starters, bench) {
  const benchBlock = bench > 0 ? BENCH_GAP_PX + SECTION_TITLE_PX + bench * BENCH_CARD_PX : 0;
  return PADDING_Y_PX + HEADER_PX + HEADER_GAP_PX + SECTION_TITLE_PX + starters * STARTER_CARD_PX + benchBlock;
}

// Ligne d'en-tête sous le club : « 4-3-3 · Entraîneur », l'entraîneur seulement s'il est connu.
export function lineupSubtitle(lineup) {
  return [lineup.formation, lineup.coach].filter(Boolean).join(" · ");
}
