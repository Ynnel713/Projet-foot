# 21e: Passe en retrait au gardien (loi 12.2)

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P1 (source naturelle de boulettes : le gardien doit jouer au pied sous pression). **Catégorie :** arbitrage.

**Constat vérifié :** pour une passe d'un coéquipier, le moteur ne distingue pas la prise à la main du contrôle au pied (la seule règle de main du gardien, `match.py:341-342`, interdit de capter un tir hors de sa surface ; absence de passe en retrait vérifiée par recherche dans `v2engine/`) : la règle de la passe en retrait n'existe pas.

**What to build:** Une passe volontaire du pied d'un coéquipier ne peut pas être prise à la main : le gardien la contrôle au pied (First Touch du gardien, pression du presseur adverse), avec la vraie possibilité d'un contrôle raté devant son but. Prise à la main fautive : coup franc indirect (rare).

**Attributs :** aucun nouveau (First Touch, Composure du gardien déjà lus par le contrôle).

**Blocked by:** 16h ; `v2-attributs-restants/03c` (relances) ou `v2-collectif/32a` (passe en retrait), le premier livré des deux.

**Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : le contrôle au pied du gardien réutilise `possession.attempt_control`.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** passe en retrait sous pression : contrôle au pied, perte possible, chaîne tracée (19b)
- **Statistiques (séries de matchs) :** 50 matchs : passes en retrait au gardien, pertes qui en découlent

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Règle appliquée ; aucun gardien ne prend à la main une passe en retrait volontaire sans faute
- [ ] Erreurs du gardien au pied possibles et tracées
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
