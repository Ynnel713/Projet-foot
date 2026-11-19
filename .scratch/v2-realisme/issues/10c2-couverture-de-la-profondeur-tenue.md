# 10c2: Couverture de la profondeur tenue pendant la passe, stable et efficace

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2. **Catégorie :** placement.

**Origine :** réserves A1 à A3 de l'expert au ticket 10c (19/11/2026), acceptées par le propriétaire (« Je valide automatiquement toutes tes recommandations et celles de l'expert », 19/11/2026).

**Constat vérifié (10c) :**
- **A1 :** le couvreur de la profondeur (`Bloc.depth_cover`) est réévalué à chaque tick et exige un porteur. Dès que la passe en profondeur part, le recul de 3 m disparaît et sa place remonte, au moment même où l'espace dans le dos est attaqué (`bloc.py`, désignation dans `Bloc.update`).
- **A2 :** la désignation n'a aucune stabilité dans le temps : trois seuils nets, et le défenseur le plus éloigné change de côté quand le ballon traverse l'axe. Le nombre de changements par match n'a pas été mesuré.
- **A3 :** aucun effet démontré sur le jeu, sur 100 matchs. Passes en profondeur réussies − 0,9 %, IC [− 10,5 ; + 8,6], et appels dans le dos − 2,2 %. Le recul de 3 m est inférieur à la tolérance de replacement du Teamwork (2 à 9 m) et à l'erreur de Positioning. Les conditions ne sont réunies que 9,6 % du temps où l'adversaire porte le ballon.

**What to build:**
1. Garder le couvreur désigné pendant le vol du ballon ou quand il est libre, si la dernière possession était adverse, jusqu'au contrôle suivant ; la condition du hors-jeu a été jugée au départ de la passe.
2. Mesurer `MatchTrace.depth_covers` : nombre de changements par match et durée médiane d'un épisode. Sous environ 1 s, ajouter une hystérésis (maintien minimal, ou changement de couvreur seulement au-delà d'un écart de largeur), à proposer au propriétaire.
3. Recalibrer `DEPTH_DROP_M` face à la tolérance du Teamwork, ou assouplir la condition « personne au-delà de la ligne » : reculer seulement jusqu'au niveau de l'attaquant le plus avancé. Valeurs à proposer au propriétaire, mesure du hors-jeu obligatoire.

**Attributs :** aucun

**Blocked by:** 10c (Couverture de la profondeur derrière la ligne).

**Bloque :** 10j.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : la mesure du 10c (`10c-profondeur.py`) sert de banc.
Temps machine, non compté : 100 matchs appariés (environ 2 h 30) ; suite complète (environ 15 min).

## Tests

- **Unitaires (scène contrôlée) :** porteur libre et couverture active, puis ballon en vol sans porteur : le couvreur reste désigné et sa place reste reculée.
- **Statistiques (séries de matchs) :** 100 matchs : passes en profondeur réussies, appels dans le dos, hors-jeu, changements de couvreur par match.

## Acceptance criteria

- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Couverture gardée pendant la passe (test)
- [ ] Changements de couvreur par match et durée médiane rapportés
- [ ] Hors-jeu par match rapporté (pas de chute non expliquée)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
