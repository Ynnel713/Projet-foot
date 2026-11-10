# 19a: Performance momentanée : un seul point d'entrée pour lire une note

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P0 (avant 18a : sans lui, fatigue, forme et blessures devraient être rebranchées dans chaque module). **Catégorie :** architecture.

**Constat vérifié :** les modules lisent la note brute par `attributes.player_attribute` : environ 50 appels dans 12 fichiers (`decision.py` 9, `defense.py` 7, `off_ball.py` 6, `shooting.py` 6, `possession.py` 5, `match.py` 5, `anticipation.py` 3, `bloc.py` 3, `duel.py` 3, `offside.py`, `restart.py`). Pace, Acceleration et Stamina ne passent pas par cette fonction : ils sont lus comme champs de `PlayerState` (`p.pace`, `p.acceleration`, `p.stamina`) dans `defense.py:121`, `decision.py:304` et `316`, `anticipation.py:65` et `85`, `occasion.py:59`, `bloc.py:227-228`, `movement.py:101` et `122` : ce sont les temps d'arrivée du pressing, de la couverture et de la décision. La fatigue ne passe que par `movement.stamina_factor` (`movement.py:60`), qui ne réduit que la vitesse maximale. Il n'existe aucun endroit où l'état du joueur (fatigue, forme du jour, coup reçu) peut changer ce qu'il exprime de sa note sans modifier chaque module.

**What to build:** Créer `v2engine/condition.py` : une fonction unique `effective_rating(player, attribute, context)` qui renvoie la note **exprimée** à cet instant, et un état `PlayerCondition` porté par `PlayerState` (vide pour l'instant). Dans ce ticket, la fonction renvoie la note brute (identité exacte). Chaque attribut reçoit sa famille (physique, technique, mentale, gardien), lue dans `docs/CARTE_ATTRIBUTS_V2.md`, pour que les tickets 20 puissent moduler une famille sans toucher les autres. Tous les appels de résolution et de décision de `v2engine/` passent par la façade ; `player_attribute` reste réservé au chargement et à la façade. Les lectures directes de `p.pace`, `p.acceleration` et `p.stamina` hors de `movement.py` passent aussi par `condition.py` (`effective_rating(p, "Pace", ctx)` ou un accesseur unique de vitesse atteignable), pour que 12e, 20e et 20g n'aient qu'un endroit à modifier. La note intrinsèque ne change jamais : seule son expression pourra changer.

**Hors de ce ticket :** tout effet de la condition (exécution technique 20a, lucidité 20b, forme du jour 20f, joueur touché 20g).

**Attributs :** aucun (tous les attributs passent par la façade)

**Lien avec l'existant :** exigence du propriétaire du 10/11/2026 (distinguer attribut intrinsèque et performance momentanée) ; règle anti double comptage de `v2-collectif/18`.

**Blocked by:** 05e (en cours, modifie `shooting.py`) ; 01f (fabrique de scènes, livré).

**Bloque :** 18a ; 20a, 20b, 20f, 20g ; 23a (ajouté le 10/11/2026) ; par convention, tout ticket qui lit une note après lui.

**Status:** livré (10/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 1 h 05 |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : élevée. Hypothèses : remplacement mécanique d'environ 50 appels et 12 lectures de champs physiques sur 10 lignes, aucun changement de comportement.
Temps machine, non compté : suite complète (environ 40 min) ; 20 matchs à graine fixée, avant et après.

## Tests

- **Unitaires :** identité exacte de `effective_rating` pour chaque attribut, notes 11, 55, 99 et joueur sans données
- **Garde statique :** aucun appel à `player_attribute` dans `v2engine/` hors `attributes.py` et `condition.py`, et aucune lecture de `.pace`, `.acceleration` ou `.stamina` hors `movement.py` et `condition.py` (même principe que `tests/test_v2engine_rayon_attributs.py`)
- **Statistiques (séries de matchs) :** 20 matchs à graine fixée : traces identiques avant et après (empreinte des positions et des événements)

## Acceptance criteria

- [ ] Façade unique et état `PlayerCondition` en place ; famille de chaque attribut documentée
- [ ] Garde statique verte
- [ ] Jeu inchangé : 20 traces identiques à graine fixée
- [ ] Règle ajoutée à `docs/CARTE_ATTRIBUTS_V2.md` : un ticket qui lit une note passe par la façade
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 10/11/2026, implémentation : `v2engine/condition.py` (`effective_rating`, `intrinsic_rating`, `PlayerCondition` vide porté par `PlayerState`, `FAMILIES` d'après les sections A à D de la carte). Toutes les lectures de notes de `v2engine/` passent par la façade : 50 appels de `player_attribute` dans 11 modules (dont 3 de chargement dans `match.py`) et 9 lectures des champs `.pace` / `.acceleration` (anticipation, bloc, decision, defense, occasion) ; chargement des joueurs par `intrinsic_rating` (`match.py`) ; seul `movement.step` lit encore les champs (chemin chaud). Garde : `tests/test_v2engine_condition.py` (9 tests). Garde du rayon (`tests/test_v2engine_rayon_attributs.py`) adaptée : elle compte les appels de la façade ; les capacités physiques passent de `PHYSICAL_ALLOWED` à `ALLOWED` ; dérogation ajoutée pour le temps d'arrivée Pace + Acceleration de `defense.arrival_time_s` (somme de deux capacités en secondes, déjà présente, invisible tant qu'elle lisait les champs). Bancs : `scripts/measure_v2.py` force les notes en patchant `condition.player_attribute` (inchangé : il patche tout module qui l'expose) ; `scripts/measure_v2_decisions.py` patche désormais `condition.player_attribute`, donc une note forcée vaut dans tout le moteur et non plus dans trois modules. Règle R6 ajoutée à `docs/CARTE_ATTRIBUTS_V2.md`.
- Mesures : 20 matchs à graine fixée (`AUDIT_SEED + k`, k = 0 à 19), empreinte sha256 de la trace : **20 sur 20 identiques avant et après** (`.scratch/v2-realisme/mesures/19a-empreintes-avant.txt`, `-apres.txt`) ; match 0 rejoué deux fois avant : même empreinte (déterminisme). Suite complète : 2 655 passés, 14 désélectionnés (2 646 + 9) (`19a-suite.txt`).
- Durée : estimée 140 min, réelle environ 125 min (analyse 25, développement 45, tests 35, intégration 20 ; estimée, non chronométrée), − 11 %. Temps machine hors total : 2 × 8 min d'empreintes, 19 min de suite.
- 10/11/2026, clôture : expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ, clôture VALIDÉ. Réserves acceptées par délégation du propriétaire (« Considère que je valide automatiquement toutes tes recommandations et celles des experts », 05/11/2026) : A1, hunks 19a de la carte, du ticket et du registre commités avec le code (suivi documentaire admis par le verrou, vérifié sans hunk étranger) ; A2, puce de la garde remise à sa place. À surveiller : le premier ticket qui module Pace, Acceleration ou Stamina (12e, 20e, 20g) fait lire `movement.step` par le même accesseur que `effective_rating` (R5) ; `measure_v2_decisions` force désormais les notes dans tout le moteur.
