# 05i: But sur ballon dévié, but contre son camp

**Chantier :** `v2-realisme` (découpé du `19b` le 10/11/2026, recommandation de l'architecte validée par délégation du propriétaire). **Priorité :** P1. **Catégorie :** moteur (change le jeu).

**Constat vérifié (architecte, 10/11/2026) :** un tir contré (`match._blocked`) ou arrêté perd son vol (`shot_flight` remis à vide) ; un ballon libre qui franchit ensuite la ligne entre les poteaux passe par la branche « sortie » et devient corner ou sortie de but (`restart.award`). Un but sur déviation, et donc un but contre son camp, est impossible. Les seuls buts sont un tir en vol et un penalty.

**What to build:** Un ballon libre (dévié, repoussé, dégagé) qui franchit la ligne de but entre les poteaux et sous la barre compte comme but de l'équipe qui attaque ce but. Il faut une hauteur pour le ballon dévié (`v2-hauteur-ballon/02a` si livré, sinon règle provisoire à proposer). Le buteur est le dernier toucheur ; si son équipe n'est pas celle qui marque, c'est un but contre son camp (`GoalEvent.own_goal`, champ créé au 19b).

**Attributs :** aucun

**Blocked by:** 19b ; `v2-hauteur-ballon/02a` (hauteur du ballon dévié, ou règle provisoire validée).

**Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 00** |

Confiance : moyenne. Hypothèses : hauteur disponible ou règle provisoire acceptée.
Temps machine, non compté : suite complète (environ 25 min) ; mesure 50 matchs avant / après.

## Tests

- **Unitaires (scène contrôlée) :** tir dévié par un défenseur dans son propre but : but contre son camp, dernier toucheur défenseur ; ballon dévié au-dessus de la barre : corner
- **Statistiques (séries de matchs) :** 50 matchs avant / après : buts par match, part des buts contre son camp (repère réel sourcé ou « non trouvé »), corners

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Buts contre son camp reconnus et tracés
- [ ] Buts par match et corners mesurés avant / après sur 50 matchs ; écart expliqué
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
