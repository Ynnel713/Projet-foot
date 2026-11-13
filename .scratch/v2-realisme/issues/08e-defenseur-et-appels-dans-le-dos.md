# 08e: Le défenseur ne voit pas toujours l'appel dans son dos

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (l'appel dans le dos réussit quand le défenseur regarde le ballon). **Catégorie :** perception.

**Constat vérifié :** le marquage et la ligne défensive lisent les positions réelles des attaquants (`defense.update`, `bloc.update`).

**What to build:** Le marqueur et la ligne défensive utilisent les positions perçues des attaquants (08b) : un appel dans le dos d'un défenseur qui regarde le ballon est vu en retard. Positioning et Marking gardent leur rayon (placement, distance) ; aucun nouvel attribut.

**Attributs :** aucun

**Blocked by:** 08b (Mémoire de perception : positions vues, datées et vieillissantes); 08c (Scan visuel avant la réception).

**Bloque :** 08f, 09i (ajouté le 10/11/2026, audit de la roadmap).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : seuls marquage et ligne lisent la perception, pas l'attribution des rôles.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** attaquant qui part dans le dos d'un défenseur tourné vers le ballon : marquage réagit avec retard
- **Statistiques (séries de matchs) :** 50 matchs : hors-jeu et passes en profondeur réussies avant / après

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Retard de réaction mesuré en scène
- [ ] Hors-jeu par match rapporté (repère 3,2-3,5 indicatif)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

**Repris du 08c (réserves A1 et A2, acceptées le 13/11/2026 ; A1 déplacée du 08d au 08e avec l'accord du propriétaire).** Brancher le coût du scan : un défenseur qui scanne ne suit pas le ballon pendant 0,3 s (`scan.SCAN_DURATION_S`), avec un test ; recaler la fréquence des scans (2,65 scans en 10 s avant réception contre environ 3 en réel) sur l'effet observé dans le jeu.

**Repris du 08d (réserve A2, acceptée le 13/11/2026).** Mesurer la fréquence des scans dans le jeu et vérifier si les passes jugées sûres à tort (talonnades non perdues 75,5 %, passes à moins de 30 % de réussite réelle 5,9 % des passes) baissent ; sinon envisager un plafond de confiance sur la mémoire très vieille (fantômes : 6,4 % des décisions).
