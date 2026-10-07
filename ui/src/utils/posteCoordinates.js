// Position indicative d'un poste sur un terrain vertical (0-100, 0 = ligne
// de but propre, 100 = ligne de but adverse) -- purement illustratif pour la
// fiche joueur (un point sur un mini-terrain), PAS le placement tactique
// réel du moteur (voir ligue1sim.pitch_layout, qui calcule un placement
// dynamique à partir du XI complet, pas d'un poste isolé).
export const POSTE_COORDINATES = {
  GK: { x: 50, y: 8 },
  DC: { x: 50, y: 22 },
  LB: { x: 14, y: 30 },
  RB: { x: 86, y: 30 },
  MDC: { x: 50, y: 42 },
  MC: { x: 50, y: 55 },
  MOC: { x: 50, y: 68 },
  AG: { x: 14, y: 78 },
  AD: { x: 86, y: 78 },
  SA: { x: 35, y: 88 },
  BU: { x: 50, y: 92 },
  ATT: { x: 65, y: 90 },
};

export function posteCoordinates(poste) {
  return POSTE_COORDINATES[poste] ?? { x: 50, y: 50 };
}
