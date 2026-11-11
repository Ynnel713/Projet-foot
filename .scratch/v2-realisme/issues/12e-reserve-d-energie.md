# 12e: Réserve d'énergie qui dépend de l'effort

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (la fatigue vient de ce qu'on a couru, pas seulement de la minute). **Catégorie :** physique. **Promu P0 le 10/11/2026** (audit de la roadmap) : à faire après 12d et avant 18d.

**Constat vérifié :** `movement.stamina_factor` (`movement.py:60`) ne dépend que de la minute et de Stamina, pas des efforts fournis.

**What to build:** Chaque joueur a une réserve d'énergie qui baisse avec l'intensité de course et remonte au repos ; Stamina règle la taille de la réserve et la recharge ; la vitesse maximale baisse quand la réserve est basse (remplace la baisse par la minute).

**Attributs :** Stamina

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-collectif/12` : réserve d'énergie.

**Blocked by:** 12d (Intensité de course selon le rôle).

**Bloque :** 12f, 12g, 13b, 18d, 20a, 20b, 20c, 20e, 20g ; `v2-coach-et-gestion-de-match/05a` (ajouté le 10/11/2026, audit de la roadmap).

**Status:** livré (11/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : modèle simple à deux paramètres (réserve, recharge).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** joueur qui sprinte 60 s : vitesse maximale réduite ; après 60 s de marche : remontée partielle
- **Comportementaux (profils comparés) :** Stamina 99 contre 11 : baisse plus tardive

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Réserve tracée
- [x] Baisse de la course intense en fin de match rapportée (repère 10-30 %)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Complément de l'audit de la roadmap (10/11/2026)

Source : `docs/AUDIT_ROADMAP_V2.md`. Promu P0 et placé avant 18d. Précisions : (1) la réserve est un état de `PlayerCondition` (`v2-realisme/19a`), tracé par joueur ; (2) elle remplace `movement.stamina_factor` pour la vitesse maximale, et c'est elle que liront les effets techniques (20a), mentaux (20b) et tactiques (20e) : Stamina n'agit qu'ici (taille et recharge), jamais une seconde fois ailleurs ; (3) la recharge pendant les arrêts de jeu et à la mi-temps est traitée au 20c ; (4) recommandation de modèle : deux composantes seulement, endurance (ce ticket) et explosivité (12f) ; pas de fatigue musculaire ni neuromusculaire séparée, qui ne produirait pas de différence observable distincte.

- [x] Test : joueur très sollicité contre joueur économe, même Stamina : réserve plus basse à la 70e

## Constantes proposées et retenues (11/11/2026)

Retenues par délégation du propriétaire (« Considère que je valide automatiquement toutes les recommandations, tous les conseils d'expert et tous les commits si la situation est favorable », 11/11/2026).

**Modèle** (famille vitesse critique / D', « W' balance » de Skiba 2012, réduit à l'endurance : l'explosivité est au 12f) : `PlayerCondition.energy`, part de réserve restante (0 à 1). Chaque pas, la course au-dessus de 14,4 km/h (`AEROBIC_SPEED_MPS` = 4,0 m/s, haut du trot de Bradley 2009) vide la réserve de l'excès de vitesse multiplié par la durée (m) ; la course en dessous la recharge à un débit fixe. Vitesse max multipliée par `energy_factor` : 1 au-dessus de 80 % de réserve (`FATIGUE_KNEE`), puis baisse linéaire jusqu'à 0,6 réserve vide (`FATIGUE_FLOOR`, plancher de l'ancien modèle pour Stamina 5). La minute ne fatigue plus (`movement.stamina_factor` supprimé).

| Constante | Stamina 5 | Stamina 55 | Stamina 99 | Source |
|---|---|---|---|---|
| Taille de la réserve (m d'excès au-dessus de 14,4 km/h) | 500 | 1 000 | 1 500 | non trouvée (valeur de modèle) ; calée sur l'effort mesuré après 12d : médiane 1 035 m d'excès par match et par joueur de champ (1er décile 552, 9e décile 1 880), 6 matchs |
| Recharge sous 14,4 km/h (m/s) | 0,06 | 0,15 | 0,30 | non trouvée ; 5 080 s par match sous 14,4 km/h (médiane) ; rapportée à la réserve, elle croît avec Stamina ; choisie sur 6 matchs entre trois candidates (0,03/0,08/0,16 ; 0,05/0,12/0,24 ; 0,06/0,15/0,30) : la plus lente donnait − 38 % de course rapide en fin de match sur 50 matchs (au-delà du repère 10 à 30 %) et − 27 % aux Stamina de 75 et plus ; celle retenue donne − 21 % pour tous, − 27 % sous 75, − 7 % à 75 et plus |
| Genou ; plancher | 0,8 ; 0,6 | | | non trouvés ; genou relevé de 0,5 à 0,8 pour qu'un sprint de 60 s réduise la vitesse max (scène du ticket) |

Recherche de valeurs réelles : les études de vitesse critique au football (tests de 3 minutes, données GPS de match) relient D' aux courses rapides et aux sprints, sans valeurs reprises ici telles quelles (recherche du 11/11/2026, non concluante pour des valeurs chiffrées).

## Réalisation (11/11/2026)

- **Code** : `v2engine/movement.py` (`spend_energy`, `energy_factor`, constantes de la réserve ; `stamina_factor` et la baisse par la minute supprimés) ; `v2engine/condition.py` (`PlayerCondition.energy`) ; `v2engine/trace.py` et `v2engine/match.py` (réserve tracée dans `PlayerSnapshot.energy`) ; commentaires de `added_time.played_minute` et de `match._step_player` mis à jour (le temps joué ne sert plus la fatigue ; paramètre `minute` de `step` gardé pour ses appelants).
- **Tests** : `tests/test_v2engine_movement.py` (sprint de 60 s puis 60 s de marche ; Stamina 99 contre 11 ; joueur très sollicité contre joueur économe, même Stamina, à la 70e ; réserve tracée sur un match court), remplaçant le test de la baisse par la minute ; `tests/test_v2engine_condition.py` (la réserve suit le joueur d'un pas à l'autre) ; `tests/test_v2_tranches.py` (scène A/B : réserve pleine contre réserve basse au lieu de la minute).
- **Réglage** : premier passage (recharge 0,03 / 0,08 / 0,16 m/s) mesuré sur 50 matchs : − 38 % de course rapide en fin de match, − 36 % aux Stamina de 70 et plus ; trois recharges comparées sur 6 matchs, la plus rapide retenue (0,06 / 0,15 / 0,30).
- **Mesure, 50 matchs** (`docs/INDICATEURS_V2.md` section 27) : baisse de fin de match − 23 % (repère 10 à 30 %), progressive dès le deuxième quart d'heure ; Stamina 0,62 à 0,82 ; distance au-dessus de 19,8 km/h 14,4 % ; buts 3,5 ; bloc inchangé.
- **Déterminisme** : `12e-det2.json`, 10 matchs rejoués, 2 450 clés identiques. Suite complète : 2 751 passés, 14 désélectionnés (`12e-suite.txt`).
- **Durée** : estimée 2 h, réelle environ 2 h 30 (+ 25 %, sous le seuil de 30 %) : un passage de réglage de plus (première série trop fatigante). Temps machine hors total : séries de 50 matchs (75 et 71 min), comparaison de trois recharges (6 matchs chacune, environ 30 min), série de 10 matchs, suite complète.

## Comments

- 11/11/2026, passage 1 : expert APPROVED ; QC VALIDÉ ; clôture VALIDÉ. Aucune anomalie bloquante, aucune réserve. Améliorations facultatives de l'expert : A1 pas de recharge à la mi-temps (renvoyé au 20c, comme le prévoit l'audit) ; A2 la réserve se comporte comme un budget de match (recharge lente) plutôt qu'un W' rapide : la composante rapide relève du 12f, ne pas compter deux fois l'excès au-dessus de 14,4 km/h ; A3 paramètre `minute` de `step` non lu (documenté) et commentaires à reformuler. Remarques du QC : commentaire de constantes long. À surveiller : distance au-dessus de 19,8 km/h 14,4 % (repère 6 à 10 %, 18d) ; Stamina 40 à 55 à 0,62 en fin de match.
