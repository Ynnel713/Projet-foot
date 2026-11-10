# 21d: La main (loi 12)

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P2 (une main n'est pas toujours sanctionnée). **Catégorie :** arbitrage.

**Constat vérifié :** aucune notion de bras ni de main dans `v2engine/` (absence vérifiée par recherche) ; le ballon n'a de hauteur qu'après `v2-hauteur-ballon/02a`.

**What to build:** Le ballon peut toucher un bras selon sa hauteur et la position du corps (orientation 07a). Sanction selon la loi 12 : bras qui agrandit le corps ou au-dessus de l'épaule, sauf ballon joué par soi-même ou dévié de tout près ; main d'un attaquant juste avant un but : but refusé. Main dans la surface : penalty. Fait et décision séparés (21a).

**Attributs :** aucun

**Blocked by:** `v2-realisme/07a` (orientation du corps), 21a ; `v2-hauteur-ballon/02a`.

**Bloque :** 21g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** |

Confiance : faible. Hypothèses : bras modélisé comme une extension latérale du corps, selon l'action en cours.
Temps machine, non compté : suite complète (environ 40 min) ; 200 matchs (événement rare).

## Tests

- **Unitaires (scène contrôlée) :** contre de tir bras le long du corps contre bras écarté : sanction seulement dans le second cas
- **Statistiques (séries de matchs) :** 200 matchs : mains par match, penalties pour main

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Cas de la loi 12 couverts par des scènes
- [ ] Fréquences rapportées ; une main non sanctionnée existe
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
