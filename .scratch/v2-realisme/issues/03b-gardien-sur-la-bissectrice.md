# 03b: Gardien : placement sur la bissectrice ballon-poteaux

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (la position du gardien entre déjà dans la chance de chaque tir (`keeper_position_factor`)). **Catégorie :** placement.

**Constat vérifié :** la place du gardien est fixe (coup d'envoi, axe, 5 m devant sa ligne) quelle que soit la position du ballon ; `shooting.keeper_position_factor` (`shooting.py:121`) compare pourtant sa position réelle à une position de référence sur l'axe du tir.

**What to build:** Dans l'état « placement », le gardien vise un point de la bissectrice de l'angle ballon-poteaux, à une distance de sa ligne qui dépend de la distance du ballon (court quand le ballon est proche, plus avancé quand il est loin, borné par sa surface). Il s'y déplace avec `movement.step` (inertie existante).

**Hors de ce ticket :** hauteur liée à la ligne défensive (03c). le ticket `v2-attributs-restants/03b` ajoutera les tendances et notes du gardien (Rushing Out, Eccentricity, One on Ones…) sur ces mécanismes neutres ; aucun attribut de gardien ici.

**Attributs :** aucun

**Blocked by:** 03a (Gardien : sous-système propre, fin du presseur générique).

**Bloque :** 03c, 03e, 03f, 03g, 05b.

**Status:** livré (07/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : distance à la ligne en fonction de la distance du ballon : courbe simple à valider.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** ballon immobile en 5 points (axe, angle fermé à gauche et à droite, loin, près) : gardien à moins de 0,5 m du point visé après 3 s
- **Statistiques (séries de matchs) :** 20 matchs : écart moyen du gardien à la bissectrice au moment des tirs

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (proposées par Claude, validées par délégation, voir Comments ; chiffres réels non trouvés)
- [x] Écart à la bissectrice au moment des tirs inférieur au seuil validé dans 90 % des cas (20 matchs) : seuil 2 m, 98,1 % des tirs (61,1 % avant)
- [x] Chance moyenne des tirs (`shot_probability`) avant / après rapportée : 0,0804 → 0,0611
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`952bbc9b2c7427ae`, 15 minutes, graine 20260923)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 488 passés, 14 désélectionnés (07/11/2026, 27 min 46 s, état final) ; attendu 2 478 + 10 nouveaux

## Comments

- 07/11/2026 : **Constantes proposées avant le code** (par Claude, validées par délégation du propriétaire, consigne du 06/11/2026 ; chiffres réels non trouvés, ordres de grandeur) : distance du gardien à sa ligne de **1,5 m** quand le ballon est à **12 m ou moins** de son but, jusqu'à **8 m** quand il est à **40 m ou plus**, interpolée entre les deux, toujours dans la surface de réparation ; écart toléré à la bissectrice au moment des tirs **2 m**. 1,5 m est proche de `shooting.KEEPER_REFERENCE_M` (1 m, gardien « bien placé » du modèle de tir) ; 8 m reste dans la moitié de la surface. **Critères chiffrés** : (1) gardien à moins de 0,5 m du point visé après 3 s, ballon immobile, quatre points (axe, angle fermé à gauche et à droite, angle intermédiaire) ; (2) part des tirs à moins de 2 m de la bissectrice d'au moins 90 % sur 20 matchs ; (3) chance moyenne des tirs avant / après ; (4) deux exécutions, même empreinte.
- 07/11/2026 : **Réalisé** (`v2engine/gardien.py` : `bisector_direction`, `depth_for_ball`, `bisector_point`, `placement(player, ball)` ; `cerveau._keeper` ; `scripts/v2_indicators.py` et `measure_v2.py` : `on_shot_context`). Point de la bissectrice de l'angle ballon-poteaux à la profondeur voulue ; si le ballon est plus près de la ligne que cette profondeur, profondeur minimale ; latéralement borné à la surface. Il s'y déplace par `movement.step` (inertie existante), sans changer l'état de sortie ni les autres états du 03a.
- 07/11/2026 : **Mesure (20 matchs, graine d'audit, avant = 03a `0b0aacb` + indicateurs du banc ; après = 03b)** : écart du gardien à la bissectrice au moment du tir **1,84 → 0,25 m**, part des tirs à moins de 2 m **61,1 → 98,1 %** ; écart au point visé 3,64 → 1,76 m (le gardien suit le ballon avec son inertie) ; chance moyenne des tirs (`shot_probability`) **0,0804 → 0,0611** (− 24 %), qualité moyenne de l'occasion 0,066 → 0,050 ; buts **4,45 → 2,75** par match (fourchette réelle 2-3,5), tirs tracés par équipe 29,95 → 27,0, conversion 7,4 → 5,1 %, arrêts 14,9 → 14,2 par match, corners 14,0 → 13,0, temps de jeu effectif 68,8 → 70,7 %, passes 1 025 → 1 039 par match, solutions de passe ouvertes 2,16 → 2,15, hors-jeu 1,05 → 0,95 ; distance du gardien à son but : maximale 47,9 → 54,1 m (sorties sur ballon libre, réserve A1 du 03a), moyenne 5,8 → 7,8 m (il s'avance quand le ballon est loin). La chute des buts vient du modèle de tir, qui compare la position du gardien à celle d'un gardien bien placé (`keeper_position_factor`) : un gardien sur la bissectrice couvre mieux l'angle qu'un gardien figé à 5 m dans l'axe. Réserve A2 du 03a : écarts mesurés sur 20 matchs, l'écart-type d'un match étant de 2,1 buts (0,47 sur la moyenne), la baisse de 1,7 but vaut plus de deux fois l'écart-type de la différence de deux moyennes (0,47 × √2 = 0,66), donc au-delà du bruit, mais le niveau absolu est à confirmer sur 50 à 100 matchs avant tout calage du tir.
- Tests : 10 nouveaux (`tests/test_v2engine_gardien.py`, 9 : point sur la bissectrice, profondeur croissante et bornée à la surface, symétrie gauche / droite et miroir de l'équipe visiteuse, ballon près de la ligne de but, état de placement, arrivée en 3 s sur quatre ballons ; `tests/test_v2_indicators.py`, 1 : chance du tir et écart à la bissectrice) ; 3 tests du 03a adaptés (cible = point de la bissectrice au lieu de la place de départ).
- Durée : estimée 2 h (120 min ; 20/45/35/20), réelle environ 1 h 40 (100 min ; 15/35/30/20, non chronométrée), écart environ − 17 % : géométrie écrite d'un seul jet, scène d'arrivée réutilisant `tests/scenes.py`. Temps machine, hors total : deux mesures de 20 matchs environ 10 min chacune, suite complète 27 min 46 s.
- 07/11/2026 : **Clôture.** Expert `APPROVED` (empreinte `5b31f3c1`), QC `VALIDÉ` (un seul passage), clôture `VALIDÉ` (journal). Aucune réserve. Facultatifs de l'expert : **A1** saut de la cible (d'environ 5 m en x) quand le ballon passe près de la touche et de la ligne de but (profondeur voulue ~6,6 m puis 1,5 m), local et lissé par l'inertie, à traiter au 03c si la profondeur y grandit ; **A2** cas d'arrivée en 3 s avec le ballon proche (par exemple en (10, 34)). À surveiller : niveau absolu des buts (2,75 par match) à confirmer sur 50 à 100 matchs avant tout calage du modèle de tir ; lien entre `KEEPER_REFERENCE_M` (1 m) et la profondeur minimale de 1,5 m (deux constantes indépendantes) ; sorties du gardien sur ballon libre (réserve A1 du 03a, tickets 03d et 03e).
