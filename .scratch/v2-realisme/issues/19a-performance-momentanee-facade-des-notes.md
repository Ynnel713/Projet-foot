# 19a: Performance momentanée : un seul point d'entrée pour lire une note

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P0 (avant 18a : sans lui, fatigue, forme et blessures devraient être rebranchées dans chaque module). **Catégorie :** architecture.

**Constat vérifié :** les modules lisent la note brute par `attributes.player_attribute` : environ 50 appels dans 12 fichiers (`decision.py` 9, `defense.py` 7, `off_ball.py` 6, `shooting.py` 6, `possession.py` 5, `match.py` 5, `anticipation.py` 3, `bloc.py` 3, `duel.py` 3, `offside.py`, `restart.py`). Pace, Acceleration et Stamina ne passent pas par cette fonction : ils sont lus comme champs de `PlayerState` (`p.pace`, `p.acceleration`, `p.stamina`) dans `defense.py:121`, `decision.py:304` et `316`, `anticipation.py:65` et `85`, `occasion.py:59`, `bloc.py:227-228`, `movement.py:101` et `122` : ce sont les temps d'arrivée du pressing, de la couverture et de la décision. La fatigue ne passe que par `movement.stamina_factor` (`movement.py:60`), qui ne réduit que la vitesse maximale. Il n'existe aucun endroit où l'état du joueur (fatigue, forme du jour, coup reçu) peut changer ce qu'il exprime de sa note sans modifier chaque module.

**What to build:** Créer `v2engine/condition.py` : une fonction unique `effective_rating(player, attribute, context)` qui renvoie la note **exprimée** à cet instant, et un état `PlayerCondition` porté par `PlayerState` (vide pour l'instant). Dans ce ticket, la fonction renvoie la note brute (identité exacte). Chaque attribut reçoit sa famille (physique, technique, mentale, gardien), lue dans `docs/CARTE_ATTRIBUTS_V2.md`, pour que les tickets 20 puissent moduler une famille sans toucher les autres. Tous les appels de résolution et de décision de `v2engine/` passent par la façade ; `player_attribute` reste réservé au chargement et à la façade. Les lectures directes de `p.pace`, `p.acceleration` et `p.stamina` hors de `movement.py` passent aussi par `condition.py` (`effective_rating(p, "Pace", ctx)` ou un accesseur unique de vitesse atteignable), pour que 12e, 20e et 20g n'aient qu'un endroit à modifier. La note intrinsèque ne change jamais : seule son expression pourra changer.

**Hors de ce ticket :** tout effet de la condition (exécution technique 20a, lucidité 20b, forme du jour 20f, joueur touché 20g).

**Attributs :** aucun (tous les attributs passent par la façade)

**Lien avec l'existant :** exigence du propriétaire du 10/11/2026 (distinguer attribut intrinsèque et performance momentanée) ; règle anti double comptage de `v2-collectif/18`.

**Blocked by:** 05e (en cours, modifie `shooting.py`) ; 01f (fabrique de scènes, livré).

**Bloque :** 18a ; 20a, 20b, 20f, 20g ; par convention, tout ticket qui lit une note après lui.

**Status:** à faire

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
