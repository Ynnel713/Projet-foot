# 09e: Distances entre les lignes en possession

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (des lignes trop écartées coupent l'équipe en deux). **Catégorie :** placement.

**Constat vérifié :** les distances défense-milieu et milieu-attaque découlent de la mise à l'échelle de la forme de départ (`bloc.py`) ; mesurées 13,0 / 13,4 m sans ballon (ticket 05), aucune règle avec ballon.

**What to build:** Avec ballon, les écarts entre lignes restent dans des bornes validées (contrainte sur la mise à l'échelle par bande) ; les rôles de 02d gardent leurs décalages à l'intérieur.

**Attributs :** aucun

**Blocked by:** 02d (Place de référence avec ballon selon le rôle).

**Bloque :** 09h.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : bornes à sourcer (repères existants : 10,2 / 13,3 m sans ballon, `docs/INDICATEURS_V2.md`).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** forme très étirée : écarts ramenés dans les bornes
- **Statistiques (séries de matchs) :** 50 matchs : écarts entre lignes avec ballon

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Écarts avec ballon dans les bornes validées (50 matchs)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
