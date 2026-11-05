# 13g: Consigne de largeur

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (jouer large ou resserré change l'occupation des couloirs). **Catégorie :** placement.

**Constat vérifié :** voir 13a ; la largeur avec ballon est une constante (`SHAPE_WITH_BALL`, `bloc.py:52`).

**What to build:** La consigne de largeur modifie la largeur de la forme avec ballon et la règle d'occupation des couloirs (09b), dans des bornes validées.

**Attributs :** aucun

**Blocked by:** 13a (Consignes d'équipe : lecture des styles et structure neutre); 09b (Occuper la largeur en possession).

**Bloque :** 13i.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 25** |

Confiance : élevée. Hypothèses : aucun style V1 ne porte cette consigne : valeur neutre par défaut, réglable.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Comportementaux (profils comparés) :** large contre resserré : largeur moyenne avec ballon plus grande

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Écart mesuré dans le sens attendu
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
