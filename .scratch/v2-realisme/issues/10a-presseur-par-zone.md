# 10a: Choix du presseur selon la zone et la responsabilité

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un défenseur central ne doit pas être aspiré loin de sa ligne). **Catégorie :** décision.

**Constat vérifié :** `defense.py:316-317` : le presseur est le joueur de champ qui arrive le premier sur le porteur, quel que soit son poste ou sa zone (règle de capacité R5).

**What to build:** Restreindre les candidats au pressing à ceux dont la zone de responsabilité (ligne et couloir de leur place de référence) contient le porteur, sauf si aucun d'eux n'arrive dans une marge validée ; à égalité de zone, le premier arrivé.

**Attributs :** aucun

**Lien avec l'existant :** complète `v2-collectif/07` et `08` (livrés, non modifiés) ; à coordonner avec `v2-collectif/27` (à faire).

**Blocked by:** 02e (Place de référence sans ballon selon le rôle).

**Bloque :** 10b, 10j.

**Status:** livré (18/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : zone définie à partir de la place de référence sans ballon.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** porteur au rond central, DC à 25 m, milieu à 12 m : le milieu presse ; porteur dans la zone du DC : le DC presse
- **Statistiques (séries de matchs) :** 50 matchs : distance moyenne du presseur à sa place de référence par poste

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Zone de responsabilité tracée avec le presseur
- [x] Défenseurs centraux pressant hors de leur zone en baisse mesurée
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Réalisation (18/11/2026)

**Constantes validées par le propriétaire le 18/11/2026** (chiffres réels non trouvés, ordres de grandeur calés sur le
bloc sans ballon de 32 x 40 m) : zone = rectangle centré sur la place de référence sans ballon (`Bloc.reference`, ballon
au porteur), `ZONE_DEPTH_M` = 8 m en profondeur et `ZONE_WIDTH_M` = 10 m en largeur de chaque côté ; bords ouverts
(dernière ligne vers son but, ligne la plus avancée vers l'avant, joueur le plus excentré de sa bande vers sa touche) ;
`PRESS_ZONE_MARGIN_S` = 1 s : un joueur de la zone presse s'il arrive au plus 1 s après le plus rapide de tous, sinon le
plus rapide presse. Critères posés avant le code : DC pressant hors de leur zone en baisse d'au moins 50 % ; tacles,
tirs et buts dans ± 10 %.

**Code** : `defense.in_zone`, `DefensiveRoles._press_pool` (candidats, aussi pour le relais du ticket 08) ;
`Assignment.zone` et `Assignment.reference` pour le presseur ; trace `MatchTrace.pressers` (`PressRecord` à chaque
changement de presseur d'une équipe : joueur, poste, porteur dans sa zone, distance du point pressé à sa place),
écrite par `match._record_pressers`, lecture seule. Sans bloc (scènes de test) : comportement d'avant.

**Écart en cours de route** : première version, le titulaire sortait des candidats dès que le porteur quittait sa zone :
va-et-vient du presseur (retour du précédent dans la seconde) 21,6 % des relais contre 1,9 % avant (30 minutes, graine
du banc + 30). Corrigé sans constante : le titulaire reste candidat, la mémoire validée `HOLD_MARGIN_S` (0,3 s) joue
contre le meilleur candidat de la zone ; va-et-vient 2,6 %. La zone décide de la prise du porteur, pas de sa poursuite.

**Mesure, 50 matchs** (graines du banc `AUDIT_SEED + k`, `.scratch/v2-realisme/mesures/10a-presseur-zone.py` et
`10a-comparaison.py`, sortie `10a-comparaison.txt` ; « avant » = marge à - inf, empreintes identiques au moteur d'avant
le ticket vérifiées sur deux matchs de 15 min) :

| | avant | après |
|---|---|---|
| DC pressant hors de sa zone (min par match) | 5,30 | 1,96 (- 63 %) |
| part hors zone, DC | 56,4 % | 23,9 % |
| part hors zone, tous postes | 54,3 % | 30,0 % |
| distance du point pressé à sa place, DC / MC / MDC | 10,9 / 10,8 / 10,2 m | 8,7 / 8,6 / 8,4 m |
| distance, latéraux / ailiers | 12,9-13,1 / 14,0-14,1 m | 10,8-11,1 / 11,9-12,4 m |
| buts / tirs par match | 5,16 / 40,4 | 5,16 / 40,1 |
| tacles / fautes par match | 40,96 / 19,9 | 38,76 (- 5,4 %) / 19,24 |
| hors-jeu par match | 4,20 | 3,82 (- 9 %) |
| changements de presseur par match | 1 545 | 1 619 (+ 4,8 %) |

Les ailiers et latéraux restent les plus souvent hors zone (42 à 54 %) : leur zone est étroite en profondeur et le
porteur adverse passe vite dans leur couloir ; le repli faute de candidat dans la marge (1 s) reste fréquent.

**Suite complète** (18/11/2026, session cloud) : 3 400 passés, 0 ignoré, 14 désélectionnés (3 390 attendus + 10 tests
ajoutés, `tests/test_v2engine_presseur_zone.py`), 18 min 38 ; V1 inchangée (aucun fichier hors `v2engine/` et le test).

**Durée** : estimée 2 h (25/45/30/20), réelle environ 2 h 10 (25/35/25/45), + 8 %, sous le seuil de 30 %. L'intégration
a dépassé (va-et-vient découvert à la mesure, corrigé et remesuré). Durée estimée à l'horloge de la session, hors
attentes machine. Temps machine hors total : 50 matchs « avant » (deux lots, dont un relancé après interruption),
50 matchs « après » (relancés après le correctif), deux mesures de va-et-vient de 30 min, deux paires d'empreintes,
suite complète (18 min 38).

**18/11/2026, statut corrigé.** Clôture journalisée `VALIDÉ` le 18/11/2026 (sous-étape `v2-realisme/10a/cloture`), code commité en `ef46bb4` ; la ligne de statut était restée « implémenté » (mise à jour oubliée après la clôture). Garde-fou : ticket `expert-dispositif/07`.
