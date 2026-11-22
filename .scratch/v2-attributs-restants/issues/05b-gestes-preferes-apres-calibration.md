# 05b: Gestes préférés, lignes branchées après la calibration

**Découpé du ticket 05 le 22/11/2026** (décision du propriétaire). Catalogue, règles et paires contradictoires : `05-catalogue-gestes-preferes.md`.

**What to build:** brancher comme **biais de probabilité** les gestes préférés dont le ticket porteur passe après la calibration (décision du 03/11/2026 : contrôle de non-régression), avec leur porteur :

| Mécanisme | Gestes | Ticket porteur |
|---|---|---|
| Finitions | Places Shots, Shoots With Power, Tries First Time Shots, Likes To Round Keeper, Likes To Lob Keeper, Curls Ball (tirs) | 10a, 10b |
| Pied | Avoids Using Weaker Foot, Moves Ball To Left Foot / Right Foot Before Dribble Attempt, Uses Outside Of Foot (pied faible) | 04a |
| Tacle | Dives Into Tackles, Does Not Dive Into Tackles | 09a (branchement et mesure, déjà prévus par le 09a) |
| Discipline | Argues With Officials, Winds Up Opponents | 09a, 09c |
| Ambiance | Gets Crowd Going (célébrations, sans effet sur le jeu) | `v2-mise-en-scene/04` |

**Attributs :** Preferred moves.

**Blocked by:** 05a (même mécanisme de biais) ; chaque ligne est branchée quand son ticket porteur est livré (04a, 09a, 09c, 10a, 10b ; `v2-mise-en-scene/04`) ; passe après `v2-collectif/22c` (contrôle de non-régression).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : faible. Hypothèses : le mécanisme de biais existe depuis le 05a ; chaque porteur expose son choix.
Temps machine, non compté : banc de profils par geste, contrôle de non-régression de la calibration, suite complète.

## Acceptance criteria

- [ ] Pour chaque geste branché : fréquence du choix concerné mesurablement plus haute (ou plus basse) qu'un joueur aux mêmes attributs sans ce geste ; jamais systématique
- [ ] Réussite du geste inchangée à attributs égaux
- [ ] Indicateurs de la calibration (22a à 22c) toujours dans leurs fourchettes
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
