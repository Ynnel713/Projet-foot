# 01b: Flux aléatoires : duels, passes, tirs, placement, arbitrage

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (termine l'isolation des tirages). **Catégorie :** mesure.

**Constat vérifié :** voir 01a : `duel.py`, `possession.py`, `shooting.py`, `bloc.py`, `defense.py`, `cerveau.py`, `match.py`, `restart.py`, `added_time.py`, `off_ball.py` tirent dans le flux global.

**What to build:** Migrer tous les tirages restants vers les flux nommés du 01a (duel, passe, tir, placement, rôles défensifs, arbitrage, remises en jeu). Ajouter un test qui interdit `random.random`, `random.uniform`, `random.gauss` et `random.choice` directs dans `v2engine/` (recherche dans le source).

**Attributs :** aucun

**Blocked by:** 01a (Flux aléatoires par sous-système : fondation, perception et décision).

**Bloque :** 01e.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : moyenne. Hypothèses : migration mécanique ; aucun changement de loi de probabilité.
Temps machine, non compté : suite complète (environ 40 min) ; mesure de contrôle sur 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** test de garde : aucun appel direct au module `random` dans `v2engine/`
- **Comportementaux (profils comparés) :** profil Aggression 99 contre 11 : le nombre de tirages consommés par le flux « tir » est indépendant du profil d'Aggression
- **Intégration :** déterminisme à graine fixée sur 2 matchs complets

## Acceptance criteria

- [ ] Plus aucun tirage direct dans le flux global (test de garde)
- [ ] Indicateurs principaux sur 20 matchs dans l'intervalle de confiance de la version 01a
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
