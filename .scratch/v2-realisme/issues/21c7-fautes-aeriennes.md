# 21c7: Fautes aériennes : charge dans le dos au saut, sortie aérienne du gardien

**Chantier :** `v2-realisme`, découpage du ticket 21c (16/11/2026, validé par le propriétaire). **Priorité :** P1. **Catégorie :** arbitrage.

**Constat vérifié :** pas de duel aérien dans le moteur (découpé en 15a-15f).

**What to build:** Sauter dans le dos de l'adversaire au duel aérien (15b) ; gardien qui percute l'attaquant en sortie aérienne (poing ou sortie). Penalty dans la surface ; prudence de surface du 21c1.

**Attributs :** à trancher avec le jeu aérien (Jumping Reach, Strength, Aggression ; gardien : Rushing Out, Aerial Reach / Command of Area selon la carte des attributs).

**Blocked by:** 21c1, 15b.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 25** |

Confiance : faible (le jeu aérien n'est pas écrit).
Temps machine, non compté : suite complète (environ 10 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** saut dans le dos : faute ; sortie aérienne du gardien qui percute : penalty
- **Statistiques :** 50 matchs : fautes aériennes par match

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Sources tracées (« charge aérienne », « faute du gardien en sortie aérienne »)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
