# 28a: Qualité de l'occasion et décision de tirer

**Découpé du ticket 28 le 04/11/2026** (audit de granularité). Détail et points de vigilance : `28-occasion-et-issue-du-tir.md`, points 1, 3, 4 et 8.

**What to build:**

1. **Qualité de l'occasion, géométrique, pour chaque attaquant** : angle sous lequel il voit le but entre les poteaux, défenseurs dans ce cône, position du gardien, distance. « S'il touchait le ballon ici, quelle serait sa chance de marquer ? », y compris pour un joueur qui ne tire pas. Remplace la chance de but héritée du ticket 33 (divisée par deux tous les 5 m au-delà de 6 m).
2. **Tirer ou jouer encore** : le tireur décide sur la qualité **perçue** de l'occasion, comparée à la passe, dans le cadre du ticket 33.
3. **Fin de la dérogation A2** : Finishing seul règle la qualité d'exécution ; Composure réduit seulement la part de difficulté due à la pression. Nouvelle constante : pression sur le tir.
4. **Frontière Finishing / Long Shots** tranchée ici (distance liée à la surface, sans zone où les deux comptent) ; la frappe de loin est résolue par le même calcul.

L'issue reste celle d'aujourd'hui (but ou ballon au gardien, contre minimal du 33) jusqu'au 28b.

**Attributs :** Finishing, Composure (pression seulement), Long Shots, Decisions.

**Blocked by:** 33, 16, 29 (tous livrés) : démarrable.

**Bloque :** 28b, 28c ; `v2-attributs-restants/01` (l'issue d'une tête passe par ce calcul), `v2-attributs-restants/10a` ; 17, 19, 22a.

**Status:** livré (05/11/2026), validé expert + QC

## Acceptance criteria

- [x] Constantes produit (pression sur le tir, frontière Long Shots, perception de l'occasion) et critères chiffrés, sourcés ou « non trouvé », validés par le propriétaire avant le code
- [x] Scène contrôlée : à distance égale, un défenseur dans le cône ou un angle fermé baisse mesurablement la qualité de l'occasion ; un gardien avancé la change
- [x] Scène contrôlée : un porteur à faibles Decisions tire plus souvent sur une occasion médiocre qu'un porteur à Decisions élevées, à situation égale
- [x] A2 levée : Composure n'agit que sous pression (test) ; test de rayon des attributs et carte (`docs/CARTE_ATTRIBUTS_V2.md`) à jour, sans double comptage Finishing / Long Shots
- [x] En match (50 matchs, graine d'audit) : part des tirs dans la surface et qualité moyenne d'un tir hors penalty rapportées, comparées aux indicateurs à sourcer (ordres de grandeur du ticket 28) ; nombre de tirs par équipe rapporté (33 au ticket 33)
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique avant le ticket 22
- [x] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée

## Constantes (révisées le 05/11/2026 après la recherche du propriétaire ; validées par délégation)

| Constante | Valeur | Source |
|---|---|---|
| Chance de base d'un tir non contré | logit = -3,3608 + 2,5068 x angle (rad) + 0,0303 x distance - 0,0023 x distance² ; face au but 37 % à 6 m, 15,5 % à 11 m, 8,8 % à 16 m, 5,9 % à 20 m, 3,5 % à 25 m, 2,0 % à 30 m ; angle fermé (103 ; 26) 6,8 % | forme classique d'un modèle xG, ajustée sur la **table cible du propriétaire** (testée). La moyenne des deux modèles Soccermatics (Wyscout PL 2017-18) donnait 12,7 % en angle fermé ; aucune repondération des deux (avec ou sans décalage) ne tenait toute la table : recommandation du porteur |
| Bornes de la chance | 0,01 à 0,9 | jamais nulle, jamais garantie |
| Pression sur le tir | défenseur de champ le plus proche, dans le rayon 0,15 x distance au but + 0,85 m (4,5 m au plus) ; -40 % à moins de 1 m, -25 % à 1-2 m, -10 % à 2-3,5 m ; moitié dans le dos (`SHOT_PRESSURE_BEHIND`, non trouvé) ; paliers indépendants de l'axe du tir (déjà compté dans le contre) ; gardien exclu (compté par sa position) | StatsBomb, « Closing down: how defensive pressure impacts shots » (environ 65 % des tirs sous pression) |
| Composure sur le tir | courbe propre : 99 garde 2/3 de la pénalité, 55 5/6, 11 la totalité ; celle de la passe inchangée | propriétaire |
| `KEEPER_REACH_M`, `KEEPER_REFERENCE_M`, `KEEPER_COVER_MAX`, `KEEPER_OPEN_GOAL_MAX` | 1,5 m de part et d'autre ; référence 1 m devant la ligne dans l'axe ; couverture plafonnée à 80 % ; but vide au plus 2,5 fois la chance de base (testé) | propriétaire (2 à 3 fois) ; portée non trouvée |
| `BLOCK_WIDTH_M`, `BLOCK_CHANCE` | 1 m de part et d'autre du corps ; 0,6 x part du but cachée | repère : 22,5 % de tirs contrés (Bundesliga 2015-16, 189 sur 840) |
| Frontière Finishing / Long Shots | la surface de réparation : Finishing dedans, Long Shots dehors, jamais les deux | décision de modélisation |
| Exécution | tireur : racine de `duel_probability(note, 60) / 0,5` (99 contre 57 : 1,32, testé entre 1,15 et 1,45) ; gardien : `duel_probability(60, note A8) / 0,5`, à part, inchangé jusqu'au 03b | repère : Messi +21 % sur sa carrière (arXiv 2301.13052), un maximum |
| Perception de l'occasion | pas de nouvelle constante : le bruit de Decisions du ticket 33 suffit (scène contrôlée) | — |

Première version (même jour, avant la recherche) : moyenne des deux modèles Soccermatics, pression 0,4 au contact sur 5 m amortie par `possession.composure_factor`, exécution `duel_probability / 0,5` (rapport 1,7), pas de plafond du but vide. Mesure de cette version : 4,44 buts par match, 38,5 tirs par équipe, 21 % dans la surface, 19 % contrés, chance moyenne 0,069.

## Réalisation

- `v2engine/shooting.py` : `base_chance`, `keeper_position_factor`, `shooting_note`, `shot_probability` (nouvelle signature : gardien et adversaires), `occasion_quality` (chance x non contré, vaut pour un joueur qui ne tire pas) ; contre par l'ombre angulaire du défenseur sur le cône de tir. `in_penalty_area` déplacée de `restart.py` vers `geometry.py`.
- `v2engine/decision.py` : la valeur du tir est `occasion_quality` ; `v2engine/match.py` : `attempt_shot` reçoit les adversaires.
- Tests : `tests/test_v2engine_occasion.py` (8 scènes : table cible, cône, gardien et but vide, paliers de pression, Composure, rapport d'exécution, frontière Finishing / Long Shots, Decisions), `test_v2engine_shooting.py` et `test_v2engine_rayon_attributs.py` adaptés (A2 levée, Long Shots branché, Composure admise dans `possession`, `decision` et `shooting`). `test_v2engine_meilleur_choix.py` : la scène « entrée de surface » est revue, car le tir de 15 m vaut désormais moins que la passe vers un partenaire démarqué plus près du but (D3 était dans le cône) ; elle devient deux tests (bon finisseur tire, mauvais cherche autre chose ; partenaire libre plus près du but préféré au tir).
- Carte des attributs : Composure, Finishing, Long Shots, A2, A14 à jour.

## Mesure en match (50 matchs, graine d'audit 20260923 + i, 05/11/2026, constantes révisées)

| Indicateur | Avant (614b1d5) | Après | Réel (repères du propriétaire) |
|---|---|---|---|
| Buts par match | 2,96 | 4,44 | 2,7-2,8 |
| Tirs par équipe | 36,1 | 37,5 | 12-15 |
| Part des tirs dans la surface | 23 % | 22 % | environ 68 % (Ligue 1 2024-25) |
| Tirs contrés | 12 % | 19 % | 22,5 % (Bundesliga 2015-16) |
| Distance moyenne du tir | 23,0 m | 23,3 m | — |
| Chance moyenne d'un tir non contré / qualité de l'occasion | — | 0,066 / 0,056 | environ 0,09 hors penalty |
| Chance moyenne dans la surface / dehors | — | 0,183 / 0,033 | — |
| Part des buts attendus venant de la surface | — | 63 % | 80-90 % des buts |

Lecture : par tir, la chance est réaliste selon l'endroit (table cible testée) ; les moyennes s'écartent du réel parce que 78 % des tirs partent de loin. La hausse des buts vient du volume de tirs, trois fois le réel, et de leur éloignement : la chance de loin était auparavant écrasée, ce qui masquait ce volume. Pas de réglage générique ici (critère du ticket) : volume et part dans la surface reviennent aux tickets 22a et 22c, arrêts du gardien au 28b. Recommandation du porteur, validée par délégation du propriétaire.

Déterminisme : deux exécutions du match 0 de la mesure (graine 20260923), trace des tirs identique (3-2, 59 tirs). Suite complète : 2 372 passés, 13 désélectionnés, aucun échec (05/11/2026, 26 min ; le compte de référence de `CLAUDE.md`, 2 281, date du 02/11, avant les tickets livrés depuis).

## Comments

- 05/11/2026, clôture : expert APPROVED_WITH_RESERVATIONS (deux passages, le second sur les 9 fichiers de code et de tests seulement, le suivi documentaire étant hors empreinte ; empreinte b8719fea) ; QC VALIDÉ ; clôture VALIDÉ (journal `v2-collectif/28a/cloture`).
- Réserve A1 (score du match dégradé, 4,44 buts : xG du tir ≥ xT moyen de la conservation entre 12 et 27 m) : acceptée. Reportée au ticket 22a comme critère ; 4,44 n'est pas une référence calibrée.
- Réserve A2 (tir manqué sans coût de perte dans la décision, antérieur au 33) : acceptée. À reprendre au 28b, sinon au 22a (critère ajouté).
- Facultatif A3 (carte : A14 et définition de Long Shots) : corrigé. A4 (plafond du but vide de loin) : à revoir au `v2-attributs-restants/03b`. A5 (plancher à angle nul) : à surveiller à l'écran.
- Réserves acceptées par le propriétaire, ses mots du 05/11/2026 : « Considère que je valide automatiquement toutes tes recommandations et celles des expert ».
- À surveiller : part des tirs dans la surface et tirs par équipe à chaque ticket touchant la décision ; à l'écran, tirs de 25 m en série et saut d'exécution à la limite de la surface.
