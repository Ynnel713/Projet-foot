# 21c3: Charge dans le dos du porteur

**Chantier :** `v2-realisme`, découpage du ticket 21c (16/11/2026, validé par le propriétaire). **Priorité :** P1. **Catégorie :** arbitrage.

**Constat vérifié :** un défenseur qui arrive derrière le porteur n'a que le tacle (11h : par derrière en dernier recours) ; aucune charge irrégulière au sol.

**What to build:** Défenseur au contact derrière le porteur (angle d'approche du 11d) : charge dans le dos possible, fréquence par Aggression (inchangée), discernement par Decisions (même logique que le 11h, pas de nouvelle courbe), prudence de surface du 21c1. Avantage et coup de sifflet comme `match._foul`. Le volet aérien (sauter dans le dos) va au 21c7.

**Attributs :** Aggression (fréquence) ; Decisions (discernement, prudence de surface ; réutilise les courbes existantes).

**Blocked by:** 21c1.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 25** |

Confiance : moyenne. Hypothèses : l'angle d'approche du 11d sert de critère « derrière ».
Temps machine, non compté : suite complète (environ 10 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** défenseur derrière le porteur : charge possible, plus fréquente avec Aggression haute ; même scène dans sa surface : plus rare, jamais nulle ; défenseur de face : jamais de charge dans le dos
- **Statistiques :** 50 matchs : charges dans le dos par match

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Source tracée (« charge dans le dos »)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md` ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
