# 02a: Côté gauche ou droit selon le poste, et non selon le nom

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (toute la structure en hérite (latéraux, compensations, couloirs)). **Catégorie :** placement.

**Constat vérifié :** `v2engine/formation.py:50` place les joueurs d'une même bande de gauche à droite dans l'ordre alphabétique de leur nom (`enumerate(sorted(names))`) ; les postes de la base sont `GK, DC, LB, RB, MDC, MC, MOC, AG, AD, SA, BU, ATT` (`ligue1sim/players.py`), et `formation` ne lit pas le poste.

**What to build:** Ordonner chaque bande par côté : LB et AG à gauche de l'équipe (vu de son propre but), RB et AD à droite, les postes axiaux au centre ; à poste égal, l'ordre des places de l'onglet « Dispositifs tactiques » s'il est connu, sinon un ordre stable (et non le nom). « Gauche » se convertit en y selon le sens d'attaque.

**Hors de ce ticket :** largeur propre à chaque poste (02b).

**Attributs :** aucun

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** 02b, 02c, 02h.

**Status:** livré (06/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : élevée. Hypothèses : la place d'origine dans l'onglet est récupérable sans modifier `ligue1sim` (lecture seule, D-V02) ; sinon repli sur le poste seul.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** 4-4-2 dont les noms inversent l'ordre alphabétique : LB et AG à gauche, RB et AD à droite, pour les deux sens d'attaque
- **Intégration :** toutes les compositions de la base : 100 % des LB/AG du côté gauche et RB/AD du côté droit au coup d'envoi

## Acceptance criteria

- [ ] Aucun placement ne dépend plus du nom
- [ ] 100 % des postes latéraux du bon côté sur la base complète
- [ ] Test de la mi-temps (`test_v2engine_mi_temps.py`) inchangé
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 06/11/2026 : expert `APPROVED_WITH_RESERVATIONS`, QC `VALIDÉ`, clôture `VALIDÉ` (journal). Réserve A1 : à poste égal, l'ordre suit la note du joueur (ordre de `lineup.players`) et non la place de l'onglet « Dispositifs tactiques », que `Lineup` ne conserve pas ; repli prévu par le ticket. Si 02b ou 02c ont besoin des places, exposer l'indice de place dans `Lineup` (lecture seule, D-V02). Réserve A2 : graine de `test_the_match_hands_the_team_choice_to_the_holder_decision` passée de 20260923 à 20260925 (test dépendant du tirage, logique inchangée) ; à surveiller aux tickets 02b et 02c. Facultatif A3 non traité (variable inutilisée dans le test d'intégration). Réserves acceptées d'office, selon la règle permanente du propriétaire sur les recommandations des experts.
- Durée : estimée 1 h 45, réelle environ 1 h (non chronométrée), écart environ − 43 % : changement de dix lignes, fabrique de scènes déjà en place, cas de la base complète écrit d'un trait. Temps machine : suite complète 14 min 16 s, hors total.
