# 01g: Analyse des écarts entre durées estimées et réelles par catégorie

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (à lancer après 20 à 30 tickets clôturés). **Catégorie :** mesure.

**Constat vérifié :** la règle d'estimation est ajoutée à `CLAUDE.md` le 05/11/2026 avec le registre `docs/agents/suivi-estimations.md` ; aucune analyse n'existe encore.

**What to build:** Script qui lit le registre et donne, par catégorie (mesure, placement, décision, exécution, physique, perception, validation, documentation), le rapport réel / estimé médian, la dispersion et les postes (analyse, développement, tests, intégration) les plus sous-estimés. Proposer un coefficient de correction par catégorie, à valider par le propriétaire.

**Attributs :** aucun

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : registre tenu à jour depuis le premier ticket du chantier.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** registre factice : ratios et médianes exacts

## Acceptance criteria

- [ ] Analyse produite sur au moins 20 tickets clôturés
- [ ] Coefficients proposés au propriétaire
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
