# 03m: Plafond d'écart de Work Rate : confirmer l'écart de buts entre 99 et 11

**Origine :** ticket 03 mis en attente le 17/11/2026 (décision du propriétaire : « Mesurer le plafond d'abord »). **Chantier :** `v2-attributs-contextes`. **Priorité :** P1. **Catégorie :** mesure.

**Constat :** sur 10 matchs, une équipe à Work Rate 99 marque 2,4 buts de plus par match qu'une équipe à 11 (4,5 contre 2,1, IC 95 % de 0,5 à 4,3) et tire 11,6 fois de plus ; km + 11 %, course intense + 77 %, repli + 46 %, appels + 28 %.

**What to build:** aucune modification du moteur. Banc de profils Work Rate sur 30 matchs (`scripts/measure_v2.py 30 --profil "Work Rate"`) pour resserrer l'intervalle ; décomposer l'écart de buts par la mesure existante (tirs, qualité des tirs, contres, récupérations hautes, pressing) ; comparer aux repères réels trouvés ; proposer au propriétaire, chiffres à l'appui : (a) écart acceptable, le ticket 03 reprend ; (b) écart trop fort, ticket de réduction à ouvrir (quel effet de Work Rate réduire, de combien) avant tout nouveau branchement.

**Hors de ce ticket :** toute modification du moteur ; les branchements du ticket 03.

**Attributs :** Work Rate (mesure seule).

**Blocked by:** aucun.

**Status:** terminé (17/11/2026) — décision du propriétaire : « Accepter, 03 réduit »

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

- [x] Écart de buts et de tirs entre 99 et 11 sur 30 matchs, avec IC 95 %
- [x] Décomposition de l'écart par les indicateurs existants
- [x] Repères réels sourcés ou « non trouvé »
- [x] Proposition chiffrée soumise au propriétaire : reprise du 03 ou ticket de réduction
- [x] Aucun fichier du moteur modifié

## Résultats (17/11/2026, `scripts/measure_v2.py 30 --profil "Work Rate"`, 90 min 43 de calcul)

| Indicateur | 99 | 11 | Écart (IC 95 %) |
|---|---|---|---|
| Buts par match | 3,90 | 2,17 | + 1,73 (0,68 à 2,78), significatif |
| Tirs par match | 28,0 | 17,2 | + 10,8 (5,1 à 16,5), significatif |
| Buts moins qualité des tirs | 0,11 | 0,27 | − 0,16 (− 0,76 à 0,44), non significatif |
| Interceptions par match | 90,1 | 81,9 | + 8,2 (3,3 à 13,1), significatif |
| Passes réussies (part) | 0,864 | 0,849 | + 0,015, significatif |
| Temps de pressing par match | 1 020 s | 925 s | + 10 % |
| Course intense par joueur | 1 277 m | 718 m | + 78 % |
| km par joueur | 12,76 | 11,47 | + 11 % |
| Vitesse de repli à 1,5 s | 2,19 m/s | 1,50 m/s | + 46 % |
| Appels par joueur | 45,2 | 35,0 | + 29 % |

Décomposition : qualité de tir égale (buts moins qualité des tirs non significatif) ; l'écart de buts vient du volume de tirs, nourri par les récupérations (interceptions, pressing), cohérent avec le rayon de Work Rate (pressing, repli, couverture). Repère réel liant volume d'effort et écart de buts : non trouvé. Banc extrême (onze joueurs à 99 contre onze à 11) ; niveau de buts élevé dans ce mode (6,1 par match, 4,4 à 4,7 en série normale), sujet de calibration distinct.

Décision du propriétaire (17/11/2026, « Accepter, 03 réduit ») : écart accepté ; le ticket 03 ne garde que le repli après la perte mis au registre (Work Rate + Teamwork) ; le soutien offensif est abandonné (il ajouterait des tirs) ; Work Rate reste dans la liste de transition jusqu'à un second contexte sans effet sur les buts.

Durée : estimée 55 min ; réelle environ 30 min (− 45 %) : la sortie du banc suffisait, aucune recherche supplémentaire. Temps machine : banc de 30 matchs (90 min 43, plus long que prévu : un seul processus).
