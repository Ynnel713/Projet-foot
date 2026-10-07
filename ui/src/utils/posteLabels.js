// Libellés français des tags de poste internes au moteur (voir le
// commentaire d'en-tête de players.py pour la liste faisant foi : GK, RB,
// LB, DC, MDC, MC, MOC, AD, AG, SA, BU, ATT). Distinct de `postes_fm`
// (codes FM26 bruts type "DR"/"WBR", affichés tels quels, jamais traduits
// ici -- vocabulaire FM non documenté côté projet, risque de mistraduction).
export const POSTE_LABELS = {
  GK: "Gardien",
  DC: "Défenseur central",
  LB: "Latéral gauche",
  RB: "Latéral droit",
  MDC: "Milieu défensif",
  MC: "Milieu central",
  MOC: "Milieu offensif",
  AG: "Ailier gauche",
  AD: "Ailier droit",
  SA: "Second attaquant",
  BU: "Buteur",
  ATT: "Attaquant",
};

export function posteLabel(poste) {
  return POSTE_LABELS[poste] ?? poste;
}
