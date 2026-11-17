# 03m: Plafond d'écart de Work Rate : confirmer l'écart de buts entre 99 et 11

**Origine :** ticket 03 mis en attente le 17/11/2026 (décision du propriétaire : « Mesurer le plafond d'abord »). **Chantier :** `v2-attributs-contextes`. **Priorité :** P1. **Catégorie :** mesure.

**Constat :** sur 10 matchs, une équipe à Work Rate 99 marque 2,4 buts de plus par match qu'une équipe à 11 (4,5 contre 2,1, IC 95 % de 0,5 à 4,3) et tire 11,6 fois de plus ; km + 11 %, course intense + 77 %, repli + 46 %, appels + 28 %.

**What to build:** aucune modification du moteur. Banc de profils Work Rate sur 30 matchs (`scripts/measure_v2.py 30 --profil "Work Rate"`) pour resserrer l'intervalle ; décomposer l'écart de buts par la mesure existante (tirs, qualité des tirs, contres, récupérations hautes, pressing) ; comparer aux repères réels trouvés ; proposer au propriétaire, chiffres à l'appui : (a) écart acceptable, le ticket 03 reprend ; (b) écart trop fort, ticket de réduction à ouvrir (quel effet de Work Rate réduire, de combien) avant tout nouveau branchement.

**Hors de ce ticket :** toute modification du moteur ; les branchements du ticket 03.

**Attributs :** Work Rate (mesure seule).

**Blocked by:** aucun.

**Status:** en cours (17/11/2026 : banc de 30 matchs lancé)

## Estimation

| Poste | Durée |
|---|---|
| Analyse des résultats et décomposition de l'écart | 25 min |
| Recherche de repères réels | 15 min |
| Rédaction de la proposition | 15 min |
| **Total (travail effectif)** | **55 min** |

Confiance : moyenne. Hypothèses : la sortie JSON du banc suffit à décomposer l'écart (tirs, pressing, récupérations) ; sans script nouveau.
Temps machine, non compté : banc de profils de 30 matchs (environ 45 min).

## Acceptance criteria

- [ ] Écart de buts et de tirs entre 99 et 11 sur 30 matchs, avec IC 95 %
- [ ] Décomposition de l'écart par les indicateurs existants
- [ ] Repères réels sourcés ou « non trouvé »
- [ ] Proposition chiffrée soumise au propriétaire : reprise du 03 ou ticket de réduction
- [ ] Aucun fichier du moteur modifié
