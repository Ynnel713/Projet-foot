# 01g: Lecteur : barre de progression et surimpressions

**Chantier :** `v2-mise-en-scene` (audit du mode « moments clés », 26/11/2026). **Catégorie :** écran.

**Constat vérifié (26/11/2026) :** score, minute et badge d'état sont au HUD (EM-08, EM-13) ; la possession est calculée au temps lu par `ui/src/utils/matchStats.js` (EM-14a) ; la frise de momentum (EM-11) couvre tout le match.

**What to build:**
1. **Barre de progression du mode** : durée totale du mode, un segment par moment ; les repères d'un moment n'apparaissent qu'une fois ce moment joué (sans spoiler) ; clic sur un repère déjà vu pour y revenir.
2. **Surimpressions pendant un moment** : score et minute (existants, inchangés) ; possession au temps lu (`matchStats`) ; xG neutre du tir quand l'ancre est un tir, affiché après le départ du tir seulement.
3. **Tier 3** (fautes, corners, hors-jeu, dès qu'ils tombent dans la fenêtre lue) : courte étiquette en surimpression, jamais un moment à part.

**Attributs :** aucun.

**Constantes à proposer avant le code :** place et durée des étiquettes du Tier 3 ; format de l'xG (décimale ou pourcentage).

**Blocked by:** 01f.

**Bloque :** 03.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : composants existants réutilisés (HUD, `matchStats`) ; captures à 4 tailles comme les tickets EM.
Temps machine, non compté : suite complète (environ 10 min).

## Tests

- Repères révélés au fil de la lecture (test du calcul sous node) ; aucun repère au-delà du moment en cours.
- xG absent avant le départ du tir, présent après.
- Captures à 4 tailles ; fluidité mesurée comme EM-07 (médiane par image).

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Aucun repère ni xG futur visible (tests et captures)
- [ ] Étiquettes du Tier 3 uniquement dans la fenêtre lue, jamais comme moment
- [ ] Fluidité inchangée (médiane par image comparée à avant)
- [ ] `npm run build` OK, `npm run lint` sans erreur nouvelle
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
