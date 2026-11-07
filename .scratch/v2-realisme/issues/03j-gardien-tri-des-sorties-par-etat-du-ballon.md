# 03j: Gardien : trier les sorties par état du ballon (tir en vol, rebond, passe, autre)

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (sans ce tri, le 71 % de « tirs » du 03i ne peut pas guider un réglage). **Catégorie :** validation.

**Constat vérifié :** au 03i, 70,9 % des ballons où le gardien sort sont classés « issus d'un tir adverse » parce qu'un tir adverse a eu lieu dans les 5 s qui précèdent sa sortie. C'est une proximité dans le temps, pas l'état du ballon : un rebond ou un ballon contré y sont aussi classés « tir ». Sur les ballons hors tir (10,2 par match), 45,5 % finissent en corner sans explication (réserve A1 de l'expert du 03i, acceptée avec la condition de trier par état du ballon avant tout réglage au `05b` ou au `18e`).

**What to build:** Classer chaque ballon avec sortie **au moment de la première sortie**, par l'état du ballon lu dans le moteur (`BallState`) :
- **tir en vol** : `shot_for` renseigné (le ballon est en route vers le but) ;
- **rebond ou ballon contré** : `rebound` vrai ;
- **passe ou centre** : `receiver` renseigné, ou `last_pass_team` de l'adversaire, sans tir en vol ;
- **autre** (dégagement, déviation, ballon perdu).
Pour chaque catégorie : nombre par match, issue à 3 s (gardien, coéquipier, adversaire, libre, sortie de but, corner, engagement), part qui finit en corner. Dire combien des 71 % du 03i sont de vrais tirs en vol, et lesquels des 45,5 % de corners hors tir sont des centres, des corners joués longs ou des dégagements. Lecture seule : aucune constante recalée, aucun réglage du filtre de portée, de `gardien.race` ni de la sortie sur tir ; le rapport propose, le propriétaire tranche.

**Attributs :** aucun

**Blocked by:** 03i (Gardien : issue du ballon après une sortie).

**Bloque :** 18e (calibration provisoire tirs et gardien) ; à lire avant tout réglage de la sortie sur tir au 05b.

**Status:** à faire (créé le 07/11/2026, réserve A1 de l'expert du 03i)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement (classement de l'état du ballon à la sortie) | 30 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications (rapport) | 15 min |
| **Total (travail effectif)** | **1 h 20** |

Confiance : moyenne. Hypothèses : lecture seule de `BallState` au moment de la première sortie, dans `scripts/v2_indicators.py`, comme le 03i. Si `shot_for` ne distingue pas un tir en vol d'un tir déjà dévié, le dire dans le rapport au lieu d'ajouter un champ au moteur.
Temps machine, non compté : suite complète (environ 15 à 40 min) ; série de 50 matchs (environ 24 min).

## Tests

- **Unitaires (scène contrôlée) :** un ballon dans chaque état (tir en vol, rebond, passe, autre) classé dans la bonne catégorie ; la somme des catégories égale le nombre de ballons avec sortie
- **Statistiques (séries de matchs) :** 50 matchs, rapport dans `docs/INDICATEURS_V2.md`

## Acceptance criteria

- [ ] Seuils et définitions de classement proposés avant le code (voir Comments)
- [ ] Chaque ballon avec sortie classé dans une seule catégorie d'état ; la somme des catégories égale le nombre de ballons avec sortie du 03i (35,0 par match sur la graine d'audit 20260923)
- [ ] Issue à 3 s et part de corners par catégorie, sur 50 matchs, avec intervalles de confiance à 95 %
- [ ] Les 71 % de « tirs » du 03i et les 45,5 % de corners hors tir sont répartis par catégorie (ce qui est un vrai tir en vol, un rebond, une passe, autre)
- [ ] Aucune constante du moteur ni aucun fichier protégé modifié ; le rapport propose, le propriétaire tranche
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- **Origine (07/11/2026).** Réserve A1 de l'expert du ticket 03i, acceptée par délégation du propriétaire. Complète la réserve A2 (compteur « non résolus » à afficher au rapport) : à ajouter dans ce même ticket puisqu'il touche le même rapport de bancs.
