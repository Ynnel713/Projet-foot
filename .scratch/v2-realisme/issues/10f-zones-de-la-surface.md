# 10f: Défense de la surface : premier poteau, second poteau, point de penalty, retrait

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (les buts se marquent surtout dans ces quatre zones). **Catégorie :** placement.

**Constat vérifié :** dans les 25 m, le défenseur libre le plus proche marque un attaquant côté but (`defense.py:341-350`) ; aucune zone de surface n'est tenue.

**What to build:** Quand le ballon est dans un couloir extérieur du dernier tiers défensif, attribuer des zones de surface (premier poteau, second poteau, point de penalty, zone de retrait) aux défenseurs libres après le presseur et la couverture, selon une priorité validée.

**Attributs :** aucun

**Blocked by:** 02e (Place de référence sans ballon selon le rôle).

**Bloque :** 10g, 10h, 16b.

**Status:** livré (21/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : valable sur passes au sol en attendant les centres (`v2-attributs-restants/01`).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** ballon sur l'aile à 10 m de la ligne de but : quatre zones tenues si quatre défenseurs libres

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Zones attribuées et tracées
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**Entrée du 18m (21/11/2026, réserve A1 acceptée par le propriétaire).** Après la sélection des frappes de loin (`docs/INDICATEURS_V2.md` section 57, 50 matchs) : conversion dans la surface 16,1 % (réel 14,7 %), hors surface 13,3 % (réel 4,2 %), part des buts hors surface 25,1 % (réel 11,7 %), 4,86 buts par match. Les frappes de loin gardées partent ligne de tir libre, tireur peu gêné à 20 m : la défense de la surface et de ses abords doit fermer ces lignes. Mesurer avant / après sur ces chiffres.

**Constantes (21/11/2026).** Proposées après un diagnostic de 4 matchs (ballon sur l'aile du dernier tiers 3,0 % du temps de possession, 1 tir sur 116 dans les 10 s qui suivent, 0,49 défenseur de champ dans la surface) ; le propriétaire a retenu le ticket tel quel (« Oui ok avec ta recommandation »), la baisse des buts étant renvoyée au nouveau ticket `10k`. Chiffres réels : non trouvés (ordres de grandeur des guides d'entraînement). Déclenchement : ballon ou point de réception à `WIDE_LAST_THIRD_M` = 35 m ou moins de la ligne défendue, hors largeur de la surface. `BOX_ZONES`, par priorité : premier poteau (4 m de la ligne, 3 m côté ballon), point de penalty (11 m, axe), second poteau (5 m, 4 m côté opposé), retrait (13 m, 6 m côté ballon).

**Implémentation (21/11/2026).** `defense.py` : rôle `ZONE_SURFACE`, `box_zone_spots`, attribution dans `DefensiveRoles.update` après les marqueurs et les compensations (ordre corrigé le 21/11/2026, voir plus bas), aux libres de leur propre camp (non réservés par une sortie de central), premier arrivé avec la mémoire du titulaire (`_keep`, clé (rôle, zone)), Positioning pour la précision du placement (`Bloc.placement_error`) ; les points sont plus près du but que toute place de référence : pas de sortie de ligne (10b). `cerveau.py` : intention « tenir sa zone » (tracée dans `PlayerSnapshot.intention`). Aucun attribut nouveau. Tests : `tests/test_v2engine_zones_surface.py` (7 : constantes, déclenchement et géométrie des deux côtés, quatre zones tenues par quatre libres après presseur et couverture, priorité à deux libres, aucune zone ballon dans l'axe, joueur hors de son camp exclu, intention tracée).

**Ordre des rôles corrigé (21/11/2026).** Premier essai : zones avant les compensations ; la suite complète échouait sur `test_v2engine_compensations.py::test_a_pressed_holder_still_threatens_the_empty_place` (le milieu défensif partait au premier poteau au lieu de boucher le couloir du latéral monté, règle du `v2-collectif/09`). Le propriétaire a retenu les zones après les compensations (« Ok avec ta recommandation ») ; série refaite.

**Passage 1 de la revue (21/11/2026).** Expert : **APPROVED_WITH_RESERVATIONS** (empreinte `8dfc932b…`) ; QC : **VALIDÉ**. Réserves : A1, profondeur des zones fixe (ballon à 35 m, un défenseur au premier poteau tire la ligne de hors-jeu à 4 m) ; A2, déclenchement sans hystérésis (zones allumées et éteintes au seuil) ; A3 et A4 facultatives (aucun filtre de poste ; documentation hors FICHIERS). Le propriétaire a demandé de corriger A1 et A2 (« Ok corrige les ») et validé les constantes proposées : poteaux seulement ballon à `POST_ZONES_MAX_M` = 20 m ou moins ; zone active gardée jusqu'à `ZONE_HOLD_MARGIN_M` = 2 m au-delà de ses seuils (`DefensiveRoles.zones_held`, effacé quand le ballon est libre). 2 tests ajoutés (poteaux à 30 m, oscillation au seuil). Série refaite avec la profondeur de la ligne et les hors-jeu (demande de l'expert).

**Mesures (`docs/INDICATEURS_V2.md` section 58, 50 matchs appariés, `.scratch/v2-realisme/mesures/10f-*`).** Ballon sur l'aile du dernier tiers : 0,50 → 1,43 défenseur de champ dans la surface ; avant-dernier défenseur à 21,2 → 16,5 m ; zones tenues aux instants où la règle les demande : premier poteau 4,2 → 43,8 %, penalty 2,8 → 33,0 %, second poteau 4,9 → 19,2 %, retrait 5,3 → 26,0 %. Aucun écart significatif : buts 4,86 → 5,42 (+ 0,56 ± 0,89 ; même sens dans les deux versions précédentes, + 0,54 et + 0,82, à surveiller au `10g` et au `10k`), tirs + 0,72 ± 0,97, xG + 0,29 ± 0,44, hors-jeu − 0,60 ± 0,77, pertes + 2 ± 6 ; qualité moyenne d'un tir dans la surface 0,186 → 0,183. « Avant » (`BOX_ZONES` vide) identique au moteur du 18m.

**Vérifications.** Suite complète : 3 467 passés, 0 ignoré, 14 désélectionnés (3 458 + 9 tests ajoutés). Déterminisme : match 0 du banc, deux exécutions sur le code final, même empreinte (1-0, 22 tirs, `f52496b10050e7e8`, intentions comprises). V1 non touchée.

**Durée.** Estimée 2 h (25 / 45 / 30 / 20 min) ; réelle environ 2 h 50 (analyse et diagnostic préalable 35, développement 40, tests 35, intégration : trois séries, conflit avec les compensations, réserves de l'expert, documentation 60), hors temps machine (diagnostic de 4 matchs, cinq séries de 50 matchs, trois suites complètes) : + 42 %. Cause : deux reprises imprévues, l'ordre des rôles (test des compensations en échec) puis les réserves A1 et A2 de l'expert, chacune avec sa série refaite.

**Clôture (21/11/2026, passage 2).** Expert : **APPROVED** (empreinte `a51a7fe9…`, FICHIERS : `v2engine/defense.py`, `v2engine/cerveau.py`, `tests/test_v2engine_zones_surface.py`, `10f-serie.py`, `10f-synthese.py`). QC : **VALIDÉ**. Clôture journalisée : VALIDÉ.
- Facultatifs de l'expert : A1, `zones_held` non remis à zéro au changement de possession sans ballon libre (au plus un tick, négligeable) ; A2, aucun filtre de poste sur les candidats aux zones (répartition par poste à surveiller) ; A3, ligne de synthèse pytest à joindre au fichier de tests.
- À surveiller au `10g` et au `10k` : buts par match (écart positif persistant, non significatif), conversion hors surface (13,0 % contre 4,2 %), part des instants sur l'aile du dernier tiers (− 9,9 ± 8,9 par match).

