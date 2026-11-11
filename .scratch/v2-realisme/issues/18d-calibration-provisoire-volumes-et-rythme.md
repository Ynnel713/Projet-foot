# 18d: Calibration provisoire 1 : volumes de course et rythme après les fondations P0

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (garder des matchs regardables et mesurables pendant les développements P1, sans figer de valeur). **Catégorie :** validation.

**Constat vérifié :** le point d'étape 18a rapporte les écarts sans régler ; sans calibration intermédiaire, les tickets P1 se mesureraient sur des volumes éloignés du réel (dernières mesures publiées : 20,7 km par joueur, 37 % du temps au-dessus de 19,8 km/h, 10,3 passes par minute).

**What to build:** Régler provisoirement, sur 500 matchs (01e), les constantes de course, d'intensité par rôle (12d si livré, sinon celles du 02f), de réception et de rythme de décision, pour ramener km, haute intensité, appels et passes par minute dans l'ordre de grandeur des repères du 01c. Règles d'une calibration provisoire (décision du propriétaire du 05/11/2026) : seules les constantes des mécanismes concernés bougent, dans leurs fourchettes validées ; chaque valeur est marquée « provisoire » dans le code et dans `docs/INDICATEURS_V2.md` avec la date et la mesure ; aucun réglage ne masque une lacune de mécanisme (un écart dû à un mécanisme absent devient un ticket) ; la calibration finale (`v2-collectif/22a` à `22c`) repart de ces valeurs et peut toutes les revoir.

**Hors de ce ticket :** tirs, buts et gardien (18e) ; calibration finale (`v2-collectif/22a`).

**Attributs :** aucun

**Blocked by:** 18a (Point d'étape après les fondations P0); 01e (Banc : séries de 500 à 2 000 matchs, parallélisées, avec intervalles de confiance); 12d (Intensité de course selon le rôle); 12e (Réserve d'énergie) (ajouté le 10/11/2026, audit de la roadmap).

**Bloque :** 18e, `v2-collectif/22a`.

**Status:** livré (11/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : leviers existants seulement ; temps machine important.
Temps machine, non compté : suite complète (environ 40 min) ; séries de 500 matchs.

## Tests

- **Statistiques (séries de matchs) :** 500 matchs avant / après, intervalles de confiance ; profils A/B inchangés en sens (Work Rate, Off the Ball, Stamina)

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Chaque constante modifiée marquée « provisoire », avec date et mesure
- [x] Écarts restants attribués (mécanisme ou calibration finale)
- [x] Aucun effet d'attribut inversé ni annulé (scènes A/B rejouées)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Complément de l'audit de la roadmap (10/11/2026)

Source : `docs/AUDIT_ROADMAP_V2.md`. 12d et 12e passent avant ce ticket : calibrer les volumes de course alors que toutes les intentions visent la vitesse maximale (`cerveau.Intention.intensity`) et que la fatigue ne dépend que de la minute reviendrait à masquer deux mécanismes absents, ce que la règle des calibrations provisoires interdit. La mention « 12d si livré » du « What to build » devient « 12d et 12e livrés ».

## Constat de la garde probabiliste (10/11/2026, ticket `v2-realisme/19c`)

À First Touch 99, le contrôle le plus difficile (ballon à 28 m/s, adversaire à 0,5 m) touche le plafond de la courbe (0,97) comme le plus facile : la difficulté ne mord plus sur un très bon joueur. La garde tient (3 % d'échec). À examiner à la calibration ; test `test_finding_the_hardest_control_does_not_bite_on_a_99` (`tests/test_v2engine_garde_probabiliste.py`), qui échouera si la difficulté se remet à mordre.

## Complément du point d'étape 18a (11/11/2026)

Source : `docs/INDICATEURS_V2.md` section 25. Le choix du porteur (conduite 73 % des décisions) et le rythme de décision sont la cause commune du volume de tirs (R1, 24,3 par équipe) et du manque de passes (R7, 844 par match, 11,9 par minute de jeu effectif) : à inclure au réglage. Relire après réglage : tacles (43,9), fautes (14,1), possession d'équipe (17,6 s), passes visées vers les DC (environ 12 par match).

## Découpage (11/11/2026)

L'estimation dépassait 2 h avec le volet « choix du porteur et rythme de décision » ajouté par le 18a : ce volet passe au ticket 18f (`18f-calibration-provisoire-choix-du-porteur-et-rythme.md`), qui bloque désormais le 18e. Ce ticket règle la course et les appels.

## Constantes proposées et retenues (11/11/2026)

Retenues par délégation du propriétaire (« Considère que je valide automatiquement toutes les recommandations, tous les conseils d'expert et tous les commits si la situation est favorable », 11/11/2026).

| Constante | Avant | Après | Statut | Source |
|---|---|---|---|---|
| `defense.FOLLOW_CATCH_UP` (marquage et couverture : allure de l'adversaire suivi + part de sa vitesse max, plancher `replacement_intensity`, plafond 1,0) | sprint (1,0) quelle que soit l'allure | 0,10 (3 km/h pour un joueur moyen) | **provisoire**, 11/11/2026, `docs/INDICATEURS_V2.md` section 28 | non trouvée (valeur de modèle) ; un défenseur reste au contact en suivant l'allure de son adversaire et ne sprinte que si l'adversaire sprinte ; 0,20 essayé, sans effet mesurable sur les défenseurs |
| `off_ball.RUN_INTERVAL_S` | 1,0 s | 1,0 s (inchangé) | essai 2,5 s écarté | sans effet sur la course rapide des attaquants (l'appel poursuit un espace qui bouge) : mécanisme, 12f |

## Réalisation (11/11/2026)

- **Diagnostic** (12e, 6 matchs, script de répartition de la course au-dessus de 19,8 km/h par intention) : le marquage portait 32 à 38 % de la course rapide des défenseurs et des milieux, le ballon libre 27 à 52 % (sprint réaliste, gardé), les appels 33 à 44 % de celle des attaquants.
- **Code** : `v2engine/defense.py` (`FOLLOW_CATCH_UP`, `follow_intensity`) ; `v2engine/cerveau.py` (marquage et couverture lisent `follow_intensity` avec la vitesse de l'adversaire suivi, `Assignment.target_velocity`).
- **Tests** : `tests/test_v2engine_intensite_role.py` (adversaire arrêté → course sans ballon ; adversaire à 0,5 de la vitesse max → 0,5 + marge ; adversaire au-delà de la vitesse max → sprint ; intensité portée par `cerveau.decide` pour un marquage).
- **Mesure** (`docs/INDICATEURS_V2.md` section 28) : 500 matchs, distance au-dessus de 19,8 km/h 14,4 % → 9,9 % (repère 6 à 10 %), sprints 34,2 → 18,6, milieux au réel ; passes 916, tirs tracés 21,9, tacles 47,1, fautes 14,6, bloc 31,9 m, possession 17,1 s, sans écart nouveau ; baisse de fin de match − 22 %.
- **Écarts attribués** : attaquants au double du réel et appels 23,9 par 90 min (mécanisme : pas de récupération entre deux efforts, 12f) ; défenseurs sous le réel (mécanisme : passes en profondeur 0,4 %, `v2-collectif/32a`) ; passes par minute de jeu effectif 12,6 (temps de jeu effectif 73 %, calibration finale) ; passes par possession et tirs (18f puis 18e).
- **Attributs** : Work Rate fixe le plancher du marquage (0,45 / 0,55 / 0,65 à 5 / 50 / 99, adversaire arrêté) ; Off the Ball et Stamina non touchés ; `tests/test_v2engine_rayon_attributs.py` inchangé.
- **Déterminisme** : `18d-det2.json`, 10 matchs rejoués contre les 10 premiers de `18d-500.json`, 2 432 clés identiques.
- **Suite complète** : 2 753 passés, 14 désélectionnés (`18d-suite.txt`) ; premier passage : 2 échecs des tests de garde (vitesse lue par `player.pace` au lieu de la façade `effective_rating`), corrigé sans effet sur le jeu (la façade rend la même valeur).
- **Durée** : estimée 1 h 50, réelle environ 2 h 10 (+ 18 %, sous le seuil de 30 %) : diagnostic par intention plus long que prévu, deux essais écartés (marge 0,20, délai entre appels 2,5 s). Temps machine hors total : séries de 50 matchs (trois), série de 500 matchs (environ 6 h 30), série de 10 matchs, deux suites complètes (18 min chacune).

## Comments

- 11/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS (rapport réémis sur le périmètre code, `CLAUDE.md`, `defense.py`, `cerveau.py`, test ; documentation hors revue) ; QC VALIDÉ ; clôture VALIDÉ. Aucune anomalie bloquante. Réserves acceptées par délégation du propriétaire (« Considère que je valide automatiquement toutes tes recommandations et celles des experts », 05/11/2026) :
  - A1 : `follow_intensity` ignore la fatigue du marqueur (divise par la vitesse max nominale, alors que `step` applique `energy_factor`) ; à corriger au 12f ou au plus tard au 22a (diviser par la vitesse max effective).
  - A2 : pas de terme d'écart, un marqueur distancé ne reprend que 0,10 ; vérifier au 32a ou au 22a si un terme d'écart relève les DC avant d'attribuer tout leur déficit aux passes en profondeur.
  - Facultatif A3 : suivre R6 par poste, pas seulement la part globale (9,9 % = attaquants au double compensés par des DC sous le réel). Remarques du QC : constante 0,10 non sourcée (déclarée), scènes A/B non relues en match.
