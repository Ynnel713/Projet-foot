# 13h: Rôles cohérents avec la formation

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un 3-5-2 n'a pas les mêmes rôles qu'un 4-3-3). **Catégorie :** données.

**Constat vérifié :** les rôles par défaut (02c) dépendent du poste seul, pas de la formation.

**What to build:** Table des rôles par défaut selon la formation (par exemple pistons offensifs dans une défense à trois, ailiers de couloir dans un 4-4-2) et règle de cohérence : au moins un rôle de couverture par côté.

**Attributs :** aucun

**Blocked by:** 02c (Rôle de poste par défaut, porté par le joueur et tracé); 13a (Consignes d'équipe : lecture des styles et structure neutre).

**Bloque :** 13i.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Hypothèses : formations lues dans la composition V1.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** chaque formation de la base reçoit des rôles cohérents (au moins un rôle défensif par côté)

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Table documentée et testée sur toutes les formations de la base
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
