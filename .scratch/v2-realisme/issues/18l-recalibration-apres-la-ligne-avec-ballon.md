# 18l: Recalibration des volumes après la ligne avec ballon

**Chantier :** `v2-realisme` (suite du ticket 09j, décision du propriétaire du 16/11/2026 : « Clôturer + ticket suivi »). **Priorité :** P1. **Catégorie :** mesure.

**Constat (16/11/2026, série de 20 matchs, `scripts/bench_series`, indicatif) :** le calage de la dernière ligne avec ballon (09j) remonte tout le bloc qui attaque (centraux à 37 m de leur but au lieu de 19 m, ballon entre 40 et 55 m), comme voulu, mais déplace les volumes :

| Par match | Avant 09j | Après 09j | Repère réel (ordre de grandeur, non vérifié dans une source) |
|---|---|---|---|
| Buts | 4,35 | 6,8 | environ 2,7 |
| Hors-jeu | 0,7 | 4,1 | environ 4 |
| xG neutre / après frappe | 5,0 / 4,5 | 6,5 / 6,6 | |
| Tirs par équipe | 21,0 | 22,2 | |
| Tirs de près (16 m) par équipe | 4,8 | 7,3 | |
| Tirs après récupération dans le camp adverse | 24,5 | 12,8 | |
| Passes | 1 089 | 1 280 | |
| Pertes de balle | 215 | 259 | |

Ballon dans son propre tiers (10 à 25 m) : centraux à peine plus bas avec ballon que sans (18,4 contre 18,9 m) ; relève du placement de construction (25b).

**What to build :** d'abord chercher d'où viennent les buts en plus (tirs de près, contres dans le dos de la ligne haute, gardien, défense préventive absente : 09g), sur une série d'au moins 50 matchs, après 09e et 25b qui changent encore le bloc. Puis proposer au propriétaire la correction (constantes ou ticket de comportement) ; aucune constante changée sans son accord.

**Attributs :** aucun nouveau.

**Blocked by:** `v2-realisme/09e`, `v2-realisme/25b` (le bloc avec ballon change encore) ; `v2-realisme/09g` (défense préventive) à planifier avant ou pendant ce ticket (réserve A3 du 09j, acceptée par le propriétaire le 16/11/2026). Reprend aussi la réserve A2 du 09j : centraux à vérifier dans le tiers défensif avec ballon.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement (diagnostic) | 30 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications (séries avant et après) | 45 min |
| **Total (travail effectif)** | **2 h** |

Confiance : faible (la cause n'est pas connue). Temps machine, non compté : séries de 50 matchs avant et après (environ 40 min chacune sur 4 cœurs).

## Acceptance criteria

- [ ] Origine des buts en plus décomposée (situations, distances, origines des tirs) sur 50 matchs au moins
- [ ] Correction proposée au propriétaire et validée avant le code
- [ ] Buts, xG, tirs, hors-jeu, passes rapportés avant et après
- [ ] Durée réelle relevée et comparée à l'estimation
