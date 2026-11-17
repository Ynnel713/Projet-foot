# 21c5: Contact irrégulier à la protection du ballon

**Chantier :** `v2-realisme`, découpage du ticket 21c (16/11/2026, validé par le propriétaire). **Priorité :** P1. **Catégorie :** arbitrage.

**Constat vérifié :** la protection du ballon n'existe pas encore (04i) ; le contact irrégulier du duel d'épaule existe déjà (11c, `duel.shoulder_foul_probability`).

**What to build:** Faute du défenseur qui pousse le porteur qui protège son ballon (04i), sur le modèle de la charge du 11c ; prudence de surface du 21c1.

**Attributs :** Aggression (fréquence) ; Decisions (prudence de surface, 21c1).

**Blocked by:** 21c1, 04i.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 20 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h** |

Confiance : faible (le 04i n'est pas écrit). Hypothèses : le 04i expose un duel de protection où brancher la faute.
Temps machine, non compté : suite complète (environ 10 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** porteur qui protège, défenseur qui pousse : faute possible ; dans sa surface : plus rare, jamais nulle
- **Statistiques :** 50 matchs : fautes à la protection par match

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Source tracée (« contact irrégulier »)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
