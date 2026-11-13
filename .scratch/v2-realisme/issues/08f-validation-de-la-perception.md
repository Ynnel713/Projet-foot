# 08f: Validation de la perception

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (contrôle des erreurs de perception). **Catégorie :** validation.

**Constat vérifié :** aucun indicateur de perception.

**What to build:** Indicateurs : part des adversaires proches non vus au moment d'une décision, pertes de balle sur adversaire non vu, scans par minute par poste. Rapport sur 50 matchs.

**Attributs :** aucun

**Blocked by:** 08d (Le porteur décide sur ce qu'il perçoit); 08e (Le défenseur ne voit pas toujours l'appel dans son dos); 01d (Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée).

**Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : lecture de la trace.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : rapport publié

## Acceptance criteria

- [ ] Indicateurs définis et ajoutés
- [ ] Rapport publié
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

**Repris du 08d (réserve A1, acceptée le 13/11/2026).** Le taux de meilleur choix est passé sous la courbe validée du ticket 33 avec la décision sur le monde perçu (8 matchs : 49,8 % pour 67,5 %, 61,4 % pour 69,9 %, 66,4 % pour 70,1 %, 67,2 % pour 70,9 %, 74,6 % pour 73,9 %) ; le recalage de l'erreur propre de Decisions est prévu avec la calibration provisoire `v2-realisme/18d` : vérifier ici qu'il est fait (écart à la courbe sous environ 2 points par tranche, `scripts/measure_v2_meilleur_choix.py`).
