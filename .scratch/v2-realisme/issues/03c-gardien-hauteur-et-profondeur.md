# 03c: Gardien : hauteur selon le ballon et la ligne défensive (couverture de la profondeur)

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (l'espace dans le dos d'une ligne haute doit être couvert). **Catégorie :** placement.

**Constat vérifié :** la ligne défensive peut monter jusqu'à 35 m et plus (`bloc.py:59`, ticket 05) tandis que le gardien reste à 5 m de sa ligne : l'espace entre les deux n'est couvert par personne.

**What to build:** Quand le ballon est loin et la ligne haute, le point de placement du 03b avance vers l'espace derrière la ligne, sans dépasser une distance maximale de sa ligne (valeur validée). La hauteur suit celle de la ligne avec retard nul (pas d'attribut).

**Hors de ce ticket :** aller chercher le ballon en profondeur (03d). le ticket `v2-attributs-restants/03b` ajoutera les tendances et notes du gardien (Rushing Out, Eccentricity, One on Ones…) sur ces mécanismes neutres ; aucun attribut de gardien ici.

**Attributs :** aucun

**Blocked by:** 03b (Gardien : placement sur la bissectrice ballon-poteaux).

**Bloque :** 03d, 03g.

**Status:** livré (07/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : la hauteur de ligne est lue dans `Bloc.lines`.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** ligne à 40 m de son but, ballon au milieu : gardien plus avancé qu'avec une ligne à 20 m
- **Statistiques (séries de matchs) :** 20 matchs : distance moyenne gardien-ligne selon la hauteur de ligne

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (proposées par Claude, validées par délégation, voir Comments ; chiffres réels non trouvés)
- [x] Hauteur du gardien croissante avec la hauteur de la ligne, bornée (test : 0,4 x ligne, plafond 16 m ; 20 matchs : de 7,1 à 7,7 m de sa ligne contre 11,5 à 13,4 m, ballon à 40 m ou plus)
- [x] Aucune perte de la bissectrice quand le ballon approche (tests du 03b toujours verts ; ballon à 12 m : point identique avec ou sans ligne ; 98,2 % des tirs à moins de 2 m de la bissectrice)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`8f06c8bda8ae58e7`, 15 minutes, graine d'audit, rapport sans la ligne du temps de calcul)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 493 passés, 14 désélectionnés (07/11/2026, 16 min 55 s, état final) ; attendu 2 488 + 5 nouveaux

## Comments

- 07/11/2026 : **Constantes proposées avant le code** (par Claude, validées par délégation du propriétaire, consigne du 06/11/2026 ; chiffres réels non trouvés, ordres de grandeur) : profondeur visée = **0,4 x hauteur de la ligne défensive** (depuis son but), plafonnée à **16 m** (dans la surface de 16,5 m, donc jamais hors de sa surface) ; elle ne compte que si elle dépasse les 8 m du 03b, et **au prorata de l'éloignement du ballon** (même pente que le 03b : rien à 12 m ou moins, plein effet à 40 m ou plus). Ligne à 20 m ou moins : aucun effet (0,4 x 20 = 8 m) ; ligne à 40 m ou plus : 16 m. **Critères chiffrés** : (1) ligne à 40 m contre 20 m, ballon loin : gardien d'au moins 5 m plus avancé ; (2) ballon à 12 m : point identique avec ou sans ligne ; (3) point toujours sur la bissectrice ; (4) 20 matchs : distance gardien-ligne de but selon la hauteur de la ligne, avant / après ; part des tirs à moins de 2 m de la bissectrice toujours d'au moins 90 % ; (5) deux exécutions, même empreinte.
- 07/11/2026 : **Réalisé** (`v2engine/gardien.py` : `LINE_RATIO`, `DEPTH_LINE_MAX_M`, `depth_for_ball(distance, line_m)`, `bisector_point` et `placement` prennent la hauteur de ligne ; `cerveau._keeper` lit `bloc.lines[son équipe]` à l'instant, sans le retard de `line_lag_s` ; sans bloc ou sans ligne : comportement du 03b). Banc : `v2_indicators._keeper_behind_line`, ballon à 40 m ou plus de son but, distance du gardien à sa ligne et écart à la ligne défensive réelle, par tranche de ligne.
- 07/11/2026 : **Mesure (20 matchs, graine d'audit ; avant = même code avec `LINE_RATIO = 0`, qui redonne exactement les 2,75 buts du 03b)**, ballon à 40 m ou plus : distance du gardien à sa ligne **7,1 à 7,7 m → 11,5 à 13,4 m** (ligne sous 25 m : 7,56 → 11,50 ; 25 à 35 m : 7,73 → 13,37 ; 35 m et plus : 7,10 → 12,12) ; écart gardien-ligne défensive réelle **ligne sous 25 m : 11,1 → 7,0 m ; 25 à 35 m : 22,4 → 16,8 m ; 35 m et plus : 40,1 → 35,2 m**. Distance moyenne du gardien à son but 7,84 → 11,67 m, maximale 54,1 → 49,6 m. Bissectrice au moment des tirs : écart 0,25 → 0,35 m, 98,05 → 98,15 % des tirs à moins de 2 m (écart au point visé 1,76 → 2,52 m : il arrive plus tard sur un point plus loin). Effets de jeu : chance moyenne des tirs **0,0611 → 0,0813** (environ 2,6 écarts-types de la différence : réel), buts **2,75 → 3,60** par match (environ 1,5 écart-type : dans le bruit), tirs par équipe 21,8 → 22,9, arrêts 14,2 → 15,3, conversion 5,1 → 6,3 %, corners 12,95 → 13,6.
- 07/11/2026 : **Limites et points à surveiller.** (1) L'écart gardien-ligne reste de 35 m quand la ligne est haute : le plafond de 16 m (surface) empêche de la couvrir ; aller plus loin suppose de sortir de la surface, ce qui relève du 03d. (2) La profondeur des tranches n'est pas strictement croissante (11,5 ; 13,4 ; 12,1 m) : le banc classe par la ligne défensive réelle, le gardien lit la ligne de référence du bloc (qui monte avec le ballon) ; les deux ne se confondent pas. (3) La chance des tirs monte alors que, sur une scène statique, un gardien avancé sur la bissectrice la fait baisser (tir de 20 m axial : 0,055 → 0,049 ; tir de 25 m en angle : 0,018 → 0,013) : la hausse vient donc de la dynamique (le gardien est loin de son point au moment du tir, 2,5 m contre 1,8 m) ou d'un autre mélange de tirs, pas du modèle de tir ; à reprendre sur 50 à 100 matchs et au 03g avant tout calage. (4) Réserve A1 du 03b (saut de la cible quand le ballon passe entre la ligne de but et la profondeur voulue) non traitée : le saut passe de 5 à 11 m environ dans ce cas rare, lissé par l'inertie ; à regarder au 03g.
- Tests : 5 nouveaux (`tests/test_v2engine_gardien.py` : ligne haute contre basse et sans ligne, croissance bornée à la surface, effet proportionnel à l'éloignement du ballon et nul à 12 m, point toujours sur la bissectrice, lecture de la ligne de son équipe par le cerveau). Aucun test du 03b modifié.
- Durée : estimée 1 h 45 (105 min ; 15/40/30/20), réelle environ 1 h 25 (85 min ; 10/25/30/20, non chronométrée), écart environ − 19 % : le 03b avait déjà posé la géométrie et la scène de test. Temps machine, hors total : deux séries de 20 matchs d'environ 10 min, suite complète 16 min 55 s (`03c-suite.txt`).
- 07/11/2026 : **Clôture.** Expert `APPROVED_WITH_RESERVATIONS` (empreinte `9b005696`), QC `VALIDÉ` (un seul passage), clôture `VALIDÉ` (journal). Réserves acceptées d'office par le propriétaire, selon sa consigne permanente (« Considère que je valide automatiquement toutes tes recommandations et celles des experts », 05/11/2026) : **A1** hausse non expliquée de la chance des tirs (0,061 → 0,081) et des buts (2,75 → 3,60) : à décomposer sur 50 à 100 matchs (chance avec la position réelle du gardien, puis sur la bissectrice, et mélange de tirs) au 03g, sans recaler d'autres constantes d'ici là ; **A2** le gardien lit la ligne de référence du bloc, pas la ligne réelle des défenseurs, et le plafond de 16 m laisse environ 35 m découverts derrière une ligne très haute : suite au 03d (sortie de la surface) ou au 03g, ne pas présenter le 03c comme une couverture complète de la profondeur ; **A3** saut de cible entre la ligne de but et la profondeur visée (réserve A1 du 03b, 5 → 11 m environ) : à regarder au 03g. Facultatifs de l'expert : A4 formulation « distance maximale de sa ligne » (le code borne la distance à la ligne de but), A5 pas de scène dynamique du gardien qui avance avec la ligne. Réserves du QC, non bloquantes : tranches de ligne non strictement croissantes au banc, déterminisme (empreinte `8f06c8bda8ae58e7`) non relu par lui.
