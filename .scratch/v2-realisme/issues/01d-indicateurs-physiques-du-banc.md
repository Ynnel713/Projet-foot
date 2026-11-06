# 01d: Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (les volumes de course sont le premier symptôme de C5). **Catégorie :** mesure.

**Constat vérifié :** la dernière mesure de distance publiée (ticket 07, 30/10/2026) donne 20,7 km par joueur de champ ; « appels par joueur » 156 à 507 (référence du 26/10/2026) contre 5,5 à 19,2 au réel, avec une définition à confirmer (01c).

**What to build:** Aligner les indicateurs physiques du banc (`scripts/v2_indicators.py`) sur les définitions retenues au 01c : km par joueur de champ et par poste, part du temps et de la distance au-dessus de 19,8 et de 25 km/h, nombre de sprints, appels par joueur selon la définition sourcée. Mesure de référence sur 50 matchs, graine d'audit.

**Attributs :** aucun

**Blocked by:** 01c (Repères de calibration : sources, définitions, compatibilité avec le banc).

**Bloque :** 02h, 03g, 04c, 05g, 07g, 08f, 09a, 12g.

**Status:** livré (06/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : élevée. Hypothèses : les observateurs du banc exposent déjà positions et vitesses à chaque pas.
Temps machine, non compté : suite complète (environ 40 min) ; mesure de référence sur 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** trajectoires synthétiques (joueur à 20 km/h pendant 10 s, puis à 10 km/h) : distances et temps au-dessus des seuils exacts
- **Statistiques (séries de matchs) :** référence 50 matchs publiée dans `docs/INDICATEURS_V2.md`

## Acceptance criteria

- [x] Indicateurs définis par écrit (formule, unité) avant le code (`docs/INDICATEURS_V2.md`, sections 1 et 3)
- [x] Tests sur trajectoires synthétiques (`tests/test_v2_indicators.py`, 5 tests)
- [x] Référence 50 matchs publiée, par poste (`docs/INDICATEURS_V2.md`, section 7)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`measure_v2 2` lancé deux fois : sorties identiques, empreinte 3abfd02d)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 394 passés, 14 désélectionnés, contre 2 389 et 14 : 5 tests ajoutés)

## Rapport d'implémentation (06/11/2026)

**Définitions retenues (avant le code, d'après le 01c) :**
- distance : km par joueur de champ, par poste (inchangé) ;
- haute intensité : part de la **distance** au-dessus de 19,8 km/h (nouvelle, repère R6) et part du temps (gardée) ; distance au-dessus de 19,8 km/h par joueur, par poste (nouvelle, en mètres, à côté des km : point A1 de l'expert au 01c) ;
- au-dessus de 25 km/h : part de la distance (inchangée) et part du temps (nouvelle) ;
- sprints : passage au-dessus de 25 km/h tenu au moins 1 s, par joueur et par match, et par poste (nouveau ; un sprint en cours au coup de sifflet final compte ; seuil de 1 s proposé, accepté d'office par le propriétaire) ;
- appels : définition du banc gardée (l'option de passe reste jugée par la réception, R5 indicatif au 01c), ajout du taux par 90 min comme la source (× 5 400 s / durée du match) ;
- passes (R7) : passes par match et passes par minute de jeu effectif (durée réelle du match, temps additionnel compris, moins le ballon mort), dans le rapport du banc ; « temps de jeu effectif (part) » passe aussi sur la durée réelle (réserve A2 de l'expert).

**Livré :** `scripts/v2_indicators.py` (constantes `SPRINT_MIN_S`, `MATCH_90_S`, comptage des sprints, nouvelles statistiques de fin de match) ; `scripts/measure_v2.py` (passes par match et par minute de jeu effectif, jeu effectif sur la durée réelle) ; `durée de match (s)` cumulée par le collecteur ; `docs/INDICATEURS_V2.md` (définitions en sections 1 et 3, nom exact de l'indicateur R4 et distances par poste de la source pour R6, points A1 et A2 de l'expert au 01c ; nouvelle section 7, référence de 50 matchs par poste). Aucun fichier du moteur touché.

**Tests ajoutés :** durée de match temps additionnel compris ; trajectoire synthétique de 10 s à 20 km/h puis 10 s à 10 km/h (parts exactes de la distance et du temps, distance au-dessus de 19,8 km/h du poste, aucun sprint) ; sprints de 1,5 s, 0,5 s (non compté) et 1 s en cours au coup de sifflet final (compté) ; appel ramené à 90 min (1 appel en 45 min : 2 par 90 min) ; passes par match et par minute de jeu effectif sur des comptes connus.

**Référence 50 matchs (section 7) :** 17,45 km par joueur de champ ; 39,3 % de la distance au-dessus de 19,8 km/h ; 146,5 sprints par joueur ; 49,4 appels par joueur et par 90 min ; 990 passes par match (14,9 par minute de jeu effectif, temps de jeu effectif 66,5 %) ; aucun ordre des postes (16,96 à 17,72 km). Volumes de course très au-delà du réel (symptôme C5), à traiter aux calibrations provisoires (18d, 18e), pas ici.

**Tests :** réussis 2 394 (suite complète, après correction du passage 1) ; échoués : aucun ; non exécutés : marqueur `integration` (moteur non touché). À l'écran : rien (le banc n'est pas affiché).

**Durée :** estimée 2 h (120 min ; 20/50/30/20), réelle environ 1 h 55 (115 min ; 15/35/30/35). Écart − 4 %. Les observateurs exposaient déjà vitesse et distance par joueur (hypothèse confirmée) ; intégration plus longue (dénominateur du jeu effectif corrigé après le passage 1, référence republiée).

## Comments

- 06/11/2026, passage 1 : expert REJECTED (empreinte 2e022c07). A1 bloquant : « passes par minute de jeu effectif » divisait par 90 min alors que passes et ballon mort couvrent la durée réelle du match (99,8 min en moyenne) : 17,5 publié au lieu de 14,9. A2 réserve : même défaut sur « temps de jeu effectif (part) » (62,8 % au lieu de 66,5 %). Facultatifs : A3 appels par 90 min à rapporter au temps de jeu du joueur quand le V2 aura des remplacements ; A4 pas d'hystérésis sur les sprints, à surveiller quand les vitesses baisseront (18d, 18e). À surveiller : ordre des postes sur les sprints inversé par rapport au réel. QC VALIDÉ (remarque : attendu de `CLAUDE.md`). Corrections : A1 et A2 (durée réelle cumulée par le collecteur, `durée de match (s)`, test adapté et test de durée ajouté), référence de 50 matchs relancée (seules les deux valeurs visées changent, toutes les autres identiques : reproductibilité sur 50 matchs), section 6 et section 7 republiées, attendu de `CLAUDE.md` mis à jour (recommandations acceptées d'office par le propriétaire).
- 06/11/2026, passage 2 : expert APPROVED (empreinte 02214199), A1 et A2 du passage 1 corrigés. Facultatifs : ligne « Haute intensité » de la section 1 à renvoyer vers la ligne en distance (prochain ticket documentaire) ; appels par 90 min au temps de jeu du joueur quand le V2 aura des remplacements ; hystérésis des sprints à revoir en 18d et 18e. À surveiller en 18d et 18e : ordre des postes (distance, sprints), jeu effectif 66,5 % contre 53-56 %. QC VALIDÉ. **Clôture VALIDÉ.**
