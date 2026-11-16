# 21c1: Prudence de surface commune aux fautes hors tacle

**Chantier :** `v2-realisme`, découpage du ticket 21c (16/11/2026, validé par le propriétaire). **Priorité :** P1. **Catégorie :** arbitrage.

**Constat vérifié :** la prudence de surface (Decisions 99 -> 0,35, 55 -> 0,5, 11 -> 0,75) n'existe qu'à l'intérieur de `duel.tackle_attempt_factor` (11h). La faute de charge du duel d'épaule (11c, `duel.shoulder_foul_probability`) ne l'applique pas : un défenseur charge aussi fautivement dans sa surface qu'au milieu de terrain.

**What to build:** Extraire la prudence de surface en une fonction publique unique de `duel` (une seule courbe Decisions, règle R1), réutilisée par le tacle (comportement du 11h inchangé) et par toutes les fautes hors tacle. Première application : la faute de charge du duel d'épaule, quand le contact a lieu dans la surface que défend le chargeur. Les sous-tickets 21c2 à 21c7 s'y branchent.

**Attributs :** Decisions (prudence de surface, même courbe que le 11h, pas de seconde courbe).

**Blocked by:** aucun (11c et 11h livrés).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 15 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **50 min** |

Confiance : élevée. Hypothèses : extraction sans changement du tacle ; un seul point d'application (duel d'épaule).
Temps machine, non compté : suite complète (environ 10 min) ; mesure 50 matchs.

## Tests

- **Unitaires :** `tackle_attempt_factor` inchangé (mêmes valeurs qu'avant l'extraction) ; probabilité de faute de charge dans sa surface = hors surface x prudence (Decisions 11, 55, 99) ; jamais nulle
- **Statistiques :** 50 matchs : fautes de charge par match, dans et hors surface, avant et après

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Une seule courbe de prudence de surface dans le moteur, utilisée par le tacle et par la charge
- [ ] Charge dans sa surface plus rare qu'ailleurs à situation égale, jamais nulle
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md` ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
