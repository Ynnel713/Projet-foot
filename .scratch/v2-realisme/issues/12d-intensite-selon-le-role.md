# 12d: Intensité de course selon le rôle

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (tout le monde ne sprinte pas : trot, course, sprint selon ce qu'il fait). **Catégorie :** physique. **Promu P0 le 10/11/2026** (audit de la roadmap) : à faire après 18a et avant 18d.

**Constat vérifié :** hors presseur et repli (Work Rate, tickets 08 et 10), remises en jeu et réception, les intentions visent l'intensité 1,0, c'est-à-dire la vitesse maximale (`cerveau.Intention.intensity`) ; mesure de référence : 37 % du temps au-dessus de 19,8 km/h (26/10/2026) contre 2-5 % au réel.

**What to build:** Chaque rôle a une intensité de base (tenir sa place : trot ; replacement : course ; appel dans la profondeur, presseur, repli urgent : sprint) ; l'attribut mental qui gouverne le rôle module (Work Rate sans ballon, Off the Ball pour les appels) sans recompter les effets déjà branchés.

**Attributs :** Work Rate, Off the Ball (rayons existants)

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-collectif/12` : intensité par rôle.

**Blocked by:** 02f (Tenir sa position en possession).

**Bloque :** 12e, 12g, 18d (ajouté le 10/11/2026, audit de la roadmap).

**Status:** livré (11/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : intensités de base proposées.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** joueur qui tient sa place loin du ballon : vitesse sous le seuil de trot
- **Statistiques (séries de matchs) :** 50 matchs : temps au-dessus de 19,8 km/h, km par joueur

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Intensité par rôle documentée et tracée
- [x] Temps à haute intensité en baisse mesurée
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Complément de l'audit de la roadmap (10/11/2026)

Source : `docs/AUDIT_ROADMAP_V2.md`. Promu P0 et placé avant 18d : la calibration provisoire des volumes de course doit porter sur le vrai modèle d'intensité. Toute note lue passe par la façade `v2-realisme/19a`.

## Constantes proposées et retenues (11/11/2026)

Retenues par délégation du propriétaire (« Considère que je valide automatiquement toutes les recommandations, tous les conseils d'expert et tous les commits si la situation est favorable », 11/11/2026). Part de la vitesse max (joueur moyen, Pace 55 à 60 : 30 à 31 km/h). Classes de vitesse réelles : marche sous 7 km/h, trot 7 à 14,4, course 14,4 à 19,8, course rapide 19,8 à 25,1, sprint au-delà (Bradley et al. 2009, *Journal of Sports Sciences* 27(2), seuils déjà cités en section 6). Courbe partagée `success_probability` (baseline à la note 55).

| Rôle, action | Base | Note qui module (11 → 99) | km/h, joueur moyen | Classe visée |
|---|---|---|---|---|
| Tenir sa place en possession, se replacer (`TENIR`) | 0,40 | Work Rate (0,32 → 0,48) | 12 | trot |
| Sans ballon, se replacer dans le bloc (`REPLACEMENT`) | 0,55 | Work Rate (0,45 → 0,65) | 16,5 | course |
| Appel vers un espace libre (`APPEL`) | 0,75 | Off the Ball (0,65 → 0,85) | 22,5 | course rapide |
| Appel dans la profondeur ou de contre-attaque | 1,0 | aucune | sprint | sprint |
| Presseur, repli | inchangé (`_PRESS_INTENSITY`, Work Rate 0,55 → 1,0) | | | sprint |
| Receveur, lecture de passe, ballon libre, soutien, couverture, marquage, compensation, porteur, gardien, remises | inchangé | | | |

Hors du ticket, gardés à leur valeur : les rôles où arriver le premier décide de l'action (ballon libre, interception, réception) et les rôles défensifs qui suivent un adversaire (couverture, marquage), dont la vitesse est bornée par celle du joueur suivi. Pas de double comptage : Work Rate gouverne déjà l'intensité du presseur et du repli (efforts sans ballon) et s'étend ici au replacement, autre effort sans ballon ; Off the Ball gouverne le choix et le moment de l'appel et s'étend à son intensité, sans Work Rate.

## Réalisation (11/11/2026)

- **Code** : `v2engine/defense.py` (`replacement_intensity`, courbes `_REPLACE_INTENSITY` et `_HOLD_INTENSITY` sur Work Rate) ; `v2engine/off_ball.py` (`run_intensity`, `_RUN_INTENSITY` sur Off the Ball, `DEEP_RUN_INTENSITY`) ; `v2engine/cerveau.py` (`decide` : se replacer en possession et sans ballon, appel). L'intensité est portée par l'intention (`Intention.intensity`), donc tracée avec elle.
- **Tests** : `tests/test_v2engine_intensite_role.py` (4 tests : joueur loin du ballon qui rejoint sa place en course, entre 14,4 et 19,8 km/h ; trot en possession sous 14,4 km/h ; Work Rate et Off the Ball modulent ; appel vers un espace en course rapide, dans la profondeur au sprint). Test adapté : `tests/test_v2_tranches.py`, scène A/B du 19d, mesurée sur 2 s de conduite (après sa passe le joueur suit l'intensité de son rôle).
- **Mesure, 50 matchs** (`docs/INDICATEURS_V2.md` section 26) : distance au-dessus de 19,8 km/h 36,9 % → 15,6 %, km par joueur 14,0 → 12,5, sprints 123 → 39, appels 41 → 24 par 90 min ; bloc inchangé ; passes 844 → 894 ; buts 4,8 → 3,6 ; conversion 9,9 → 7,8 %. Baisse de fin de match de la course au-dessus de 19,8 km/h : − 20 %.
- **Déterminisme** : `12d-det2.json`, 10 matchs, 2 444 clés identiques.
- **Durée** : estimée 2 h, réelle environ 1 h 55 (− 4 %). Temps machine hors total : série de 50 matchs (71 min), série de 10 (15 min), deux suites complètes (29 min chacune ; la première a révélé la scène A/B à adapter).

## Comments

- 11/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS ; QC VALIDÉ ; clôture VALIDÉ, réserves acceptées par le propriétaire (« Considère que je valide automatiquement toutes les recommandations, tous les conseils d'expert et tous les commits si la situation est favorable », 11/11/2026).
  - A1 : conversion 9,9 → 7,8 % (sous R2) et tacles 46,5 ; condition reportée au 18e : relire R2 sur l'état après 12d, 12e et 18d, pas sur le 9,9 % de la section 25.
  - A2 : documentation du 12d (ticket, section 26, carte des attributs, plan, registre des durées) commitée avec le code.
  - A3 (facultatif) : sprint de l'appel dans la profondeur non testé de bout en bout (encodage par la longueur du tuple `runs`) ; non fait.
  - A4 (facultatif) : mentions de la carte harmonisées (ligne Off the Ball, combinaison Work Rate + Stamina).
  - Remarque du QC : import de `replacement_intensity` hors de l'ordre alphabétique (style).
