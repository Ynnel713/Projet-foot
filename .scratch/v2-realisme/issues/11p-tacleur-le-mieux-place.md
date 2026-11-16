# 11p: Le tacleur le mieux placé tente, pas seulement le plus proche

**Chantier :** `v2-realisme` (réserve A1 de l'expert à la clôture du 11h, acceptée par le propriétaire le 16/11/2026 : « Accepter + nouveau ticket »). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (11h, 50 matchs appariés) :** les tacles tombent de 37,3 à 22,1 par match, sous le repère réel de 30 à 40 (`docs/INDICATEURS_V2.md`, réserve du ticket 22). Une cause antérieure au 11h amplifie la baisse : un seul tirage de tentative par pas, pour l'adversaire **le plus proche** du porteur à portée (`match._nearest_opponent_in_range`, appelé dans `_step_ball`). Un défenseur placé dans le dos du porteur, devenu prudent (facteur 0,15 à Decisions 55), occupe ce tirage ; un coéquipier de face, à portée lui aussi, ne peut pas tenter.

**What to build:** parmi les défenseurs à portée de tacle, celui qui tente est le mieux placé : soit un tirage par défenseur à portée (chacun à son taux, facteur 11h compris ; au plus un tacle par pas), soit le choix du défenseur au plus grand facteur de tentative. À trancher par le propriétaire.

**Attributs :** aucun nouveau (Aggression : fréquence ; Decisions : discernement du 11h).

**Constantes à proposer avant le code :** aucune si l'option « un tirage par défenseur » est retenue ; sinon la règle de choix. Chiffre réel : tacles par match 30 à 40 (repère du ticket 22).

**Lien avec l'existant :** complète le 11h ; volume de fautes suivi au `21c` (retour vers 21-26).

**Blocked by:** 11h.

**Bloque :** rien.

**Status:** à faire (option à trancher par le propriétaire avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 25 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 40 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : changement local dans `_step_ball` ; quelques tests qui supposent un seul tacleur à adapter.
Temps machine, non compté : série appariée de 50 matchs ; suite complète.

## Tests

- **Unitaires (scène contrôlée) :** un défenseur dans le dos et un défenseur de face, tous deux à portée : celui de face peut tenter ; un seul tacle par pas.
- **Statistiques :** 50 matchs appariés : tacles par match, part par angle, fautes, buts et tirs.

## Acceptance criteria

- [ ] Option et règle validées par le propriétaire avant le code
- [ ] Scène : le défenseur de face à portée tente malgré un défenseur plus proche dans le dos
- [ ] Tacles par match rapportés, comparés au repère réel 30 à 40 ; fautes, buts et tirs rapportés
- [ ] Déterminisme à graine fixée ; suite complète comparée à l'attendu de `CLAUDE.md`
- [ ] Durée réelle relevée et comparée à l'estimation (`docs/agents/suivi-estimations.md`)
