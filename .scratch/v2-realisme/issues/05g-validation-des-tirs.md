# 05g: Validation des tirs : trajectoire, cadrage, contres, arrêts

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (contrôle des mécanismes avant toute calibration (22c)). **Catégorie :** validation.

**Constat vérifié :** le banc rapporte les issues du tir (28b) mais pas leur cohérence avec la distance, l'angle ou le tireur.

**What to build:** Rapport sur 50 matchs : issues par tranche de distance et d'angle, cadrés par tranche de Finishing / Long Shots, contrés selon le nombre de défenseurs dans le cône, taux d'arrêt selon la vitesse. Scènes de référence rejouées. Aucun réglage pour viser 8-15 tirs ou 10-11 % de conversion (repères vérifiés au 01c, réglage au 22c).

**Attributs :** aucun

**Blocked by:** 05a (Tir : le ballon part vers son point d'arrivée, le but n'est plus tiré au départ); 05b (Arrêt : le gardien atteint ou non le ballon); 05c (Contre : le défenseur touche réellement le tir); 05d (Déviation du ballon au contact d'un corps); 05e (La valeur du tir dans la décision suit la résolution physique); 01d (Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée); 05h (Allumer le tir physique, découpé du 05b le 08/11/2026).

**Bloque :** 18a, 18e.

**Status:** livré (10/11/2026), validé expert + QC (critère « cadrage croissant avec la note » non tenu en match, écart accepté)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : élevée. Hypothèses : lecture de la trace des tirs.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

**Estimation révisée (10/11/2026, avant le code)** : 2 h 30, confiance moyenne (+ 55 min : reprise A1 du 05d dans `match._blocked`, mesure A2 du 05d, relevé du biais de 12 à 16 m du 05e). Au-delà du seuil indicatif de 2 h, examiné pour découpage : non découpé, les trois parties partagent le même relevé de 50 matchs (le découper doublerait le temps machine). Temps machine, hors total : 50 matchs (environ 40 min sur 7 processus), suite complète (environ 50 min).

## Critères chiffrés (posés le 10/11/2026, avant le code)

- **Rapport** sur 50 matchs (graines 2400 à 2449, `scripts/shot_calibration.py rapport`), publié au §22 de `docs/INDICATEURS_V2.md` : issues par tranche de distance et d'angle, cadrage par tranche de Finishing (surface) et de Long Shots (dehors), part de tirs contrés selon le nombre de défenseurs dans le cône, part de tirs cadrés arrêtés selon la vitesse au gardien.
- **Tendances attendues, vérifiées sans réglage** : taux de buts décroissant avec la distance (tranches de 8 m et plus, tranches voisines avec intervalles disjoints ou tendance monotone) ; cadrage croissant avec la note (tranche la plus basse sous la plus haute, intervalles disjoints) ; part contrée croissante avec le nombre de défenseurs dans le cône ; arrêts décroissant avec la vitesse. Écarts au réel listés (repères du 01c : 8 à 15 tirs et 10 à 11 % de conversion, environ 33 % de cadrés, environ 70 % d'arrêts des cadrés, 20 à 28 % de contrés, environ 10 corners par match), aucun réglage (22c).
- **Scènes de référence rejouées** : grille du 05e (`shot_calibration.py scenes 2000`), 20 positions sur 20 dans l'intervalle à 95 %.
- **Réserve A1 du 05d** : point de contact et déviation pris à la position du défenseur au contact ; test : défenseur qui traverse l'axe à 5 m/s, ballon dévié du côté du décalage au contact dans au moins 36 cas sur 40 (échoue sans la correction).
- **Réserve A2 du 05d** : part des contres qui sortent directement (corner, touche, sortie de but, dans les 5 s) et corners par match venus des contres et des tirs claqués ; cause identifiée ; aucun recalage compensatoire.
- **Réserve A1 du 05e** : par tranche de distance, contre prévu contre observé, chance hors contre contre buts des non contrés, écart moyen au gardien ; localiser l'étage du biais de 12 à 16 m, sans réglage.

## Reprises du 05e (réserves de l'expert, 10/11/2026)

- **A1** : biais résiduel de l'estimateur de 12 à 16 m (0,191 évalué contre 0,146 observé sur 120 matchs) : relever l'écart au gardien selon la distance avant tout réglage.
- À surveiller : tranche de contre prévue sous 0,05 (1,5 % contre 4,1 % observés) ; non-monotonie de la résolution entre 6 et 11 m (tir axial 0,235 à 6 m, 0,336 à 11 m, gardien bien placé ; courbe d'arrêt au 35a et au 03b).

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : conversion décroissante avec la distance, cadrage croissant avec la note

## Mesures (10/11/2026, `.scratch/v2-realisme/mesures/05g-*`, détail : `docs/INDICATEURS_V2.md`, §22)

- **Rapport** (50 matchs, 2400 à 2449, 2 383 tirs, `05g-rapport.json`) : publié au §22.
- **Tendances** : conversion décroissante avec la distance (0,337 sous 8 m ; 0,231 ; 0,207 ; 0,107 ; 0,049 ; 0,031 de 25 à 30 m) ; buts croissants avec l'angle (0,035 à 0,325) ; contrés croissants avec les défenseurs dans le cône (0,076 ; 0,280 ; 0,388 ; 0,50) ; arrêts décroissants avec la vitesse au gardien (0,911 sous 20 m/s ; 0,816 ; 0,527 ; 0,370 au-delà de 27 m/s). **Cadrage par note : critère non tenu en match** (Finishing 0,667 sous 55 sur 54 tirs, 0,439 de 55 à 70, 0,500 à 70 et plus ; Long Shots 0,30 à 0,32) : distance, angle et pression moyens identiques, cadrage prévu tir par tir de 0,521 à 0,547 (environ 3 points entre tranches, sous le bruit de 50 matchs). Vérifié en scène de référence à la place (`05g-scenes-note.txt`, test ajouté) : 0,398, 0,563, 0,694 à 14 m pour 25, 60, 95 ; 0,243, 0,344, 0,432 à 24 m. Le poids de la note sur le cadrage en match est faible : signalé pour le 22c, sans réglage.
- **Écart au critère** : le critère « cadrage croissant avec la note » reste non tenu ; la scène de référence le complète sans le remplacer (QC du 10/11/2026). L'inversion entre [40 ; 55[ (0,681, 47 tirs) et [55 ; 70[ (0,439, 139 tirs), z ≈ 2,9, dépasse l'effet prévu (environ 0) : fluctuation probable, à revérifier sur un échantillon plus grand. Cause du faible effet (expert) : `duel_probability` cubique et exposant 0,5 de l'exécution, skill 0,979 à 45 et 1,049 à 80 (± 3,5 % sur l'écart du ballon) ; reporté au 22c (`v2-collectif/22c`, reprise du 05g).
- **Écarts au réel, sans réglage (22c)** : 23,8 tirs par équipe (8 à 15), conversion 8,6 % (10 à 11 %), 27,2 % de cadrés (environ 33 %), 68,3 % des cadrés arrêtés (environ 70 %), 20,8 % de contrés (20 à 28 %), 6,3 corners par match (environ 10).
- **Réserve A1 du 05d** : `match._blocked` prend la place du défenseur au contact (`position − vitesse·dt·(1 − entrée)`) pour le point de contact et `deflect` ; test `test_the_deflection_side_is_that_of_the_defender_at_the_contact_not_at_the_end_of_the_step` (36 cas sur 40 au moins ; échoue sans la correction).
- **Réserve A2 du 05d** : suite directe d'un contre : corner 25,9 %, touche 13,3 %, en jeu 60,4 % ; 2,56 corners par match après un contre, 0,94 après un tir claqué, 6,3 au total. Cause : 53 % des contres repartent vers le tireur (angle de sortie au-delà de 90°, 85 % en jeu) avec la déviation à plat ; ni hauteur (ballon contré au-dessus de la barre) ni orientation du corps : traitement à `v2-hauteur-ballon/02a` et 07a, aucun recalage compensatoire.
- **Réserve A1 du 05e** : biais de 12 à 16 m non reproduit sur ces 50 matchs (évalué environ 0,19, buts 0,207) ; l'étage le plus faux est le contre sous 8 m (0,19 prévu, 0,35 observé) ; le tir non contré reste juste à toutes les distances (écart au plus 0,03).
- **Scènes de référence rejouées** (`05g-scenes.txt`) : 20 positions sur 20 calibrées.
- **Tests** : `tests/test_validation_tirs.py` (rapport sur tirs synthétiques ; cadrage par note en scène), test A1 dans `tests/test_v2engine_contre.py`.
- **Déterminisme** : 3 matchs (2400 à 2402) joués deux fois, mêmes 130 tirs, empreinte `664a9a991c15`, identiques à la série.
- **Suite complète** (`05g-suite.txt`) : 2 646 passés, 14 désélectionnés = 2 643 + 3 tests du 05g.
- **Durée** : estimée 1 h 35, révisée 2 h 30 avant le code ; réelle environ 2 h 45 (+ 10 % sur la révisée), non chronométrée.

## Acceptance criteria

- [x] Rapport publié dans `docs/INDICATEURS_V2.md`
- [ ] Tendances attendues vérifiées (distance, note, contreurs) ; écarts au réel listés sans réglage — **non tenu pour la note** : distance, angle, contreurs et vitesse vérifiés ; cadrage croissant avec la note non vérifié en match (critère chiffré non tenu, écart consigné, non reformulé ; scène de référence en complément, pas en remplacement) ; écarts au réel listés sans réglage
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Reprises du 05d (réserves de l'expert, 09/11/2026)

- **A2** : corners par match 8,6 → 6,6 avec la déviation physique des contres (repère réel environ 10) : mesurer la part des contres qui sortent derrière la ligne et en touche, et en traiter la cause (hauteur, orientation du corps) avant tout recalage compensatoire.
- **A1** : dans `match._blocked`, prendre la position du défenseur à l'instant du contact (`player.position − player.velocity·dt·(1 − entry)`) pour le point de contact et `deflect` ; test : défenseur qui traverse l'axe à 5 m/s, côté de la déviation celui du décalage au contact. À faire avant que la parade ou le contrôle raté n'adoptent `deflect`.

## Comments

- 10/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS (empreinte 5cecd8cd) ; QC REFUSÉ (critère « cadrage croissant avec la note » non tenu en match, remplacé a posteriori par une scène, case cochée). Correction documentaire seulement (empreinte inchangée) : case décochée, écart consigné sans reformulation, scène étiquetée en complément, report au 22c.
- 10/11/2026, passage 2, clôture : QC VALIDÉ ; clôture VALIDÉ (journal `v2-realisme/05g/cloture`). Réserves de l'expert : A1, critère « note » non tenu en match (cause : `duel_probability` cubique et exposant 0,5, ± 3,5 % sur l'écart du ballon entre les notes 45 et 80), acceptée au titre de la consigne du propriétaire (« Je valide toutes tes recommandations et les avis d'expert », 10/11/2026), écart à revoir au 22c ; A2, report du faible poids de la note dans un ticket aval, fait (`v2-collectif/22c`, reprise du 05g) ; A3 (facultatif), `exit_after` à revoir quand la V2 aura des remplacements.
