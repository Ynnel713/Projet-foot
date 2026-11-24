# 15b2: Fautes du duel aérien : bascule, charge sans jouer le ballon, appui par derrière

**Chantier :** `v2-realisme` (découpe du `15b`, validée par le propriétaire le 24/11/2026). **Priorité :** P2. **Catégorie :** exécution.

**Constat vérifié :** aucune faute dans un duel aérien (seules fautes : tacle, charge du duel d'épaule à la course `11c`).

**What to build:** dans un duel aérien (`15b1`), le fautif possible est tiré selon la situation, sa probabilité = facteur × probabilité de faute d'un tacle (Aggression, `duel.foul_probability`), × prudence de surface dans la sienne (`21c1`) :
- épaule contre épaule, de côté, les deux sautent (jeu à l'épaule) : 0,10 (3 % à Aggression moyenne) ;
- contact par derrière en sautant (appui sur l'adversaire, poussée dans le dos) : 0,50 (15 %) ;
- ne saute pas ou ne peut pas atteindre le ballon et reste sous le sauteur (bascule), ou charge sans jouer le ballon : 0,80 (24 %).
Gravité propre au duel aérien : 20 % d'inconsidérées (jaune), 1 % d'excès d'engagement (coude). Coup franc sifflé tout de suite (ballon libre : pas d'avantage, comme le `11c`). Sans faute, celui qui ne saute pas perd le duel.

**Attributs :** Aggression (risque de faute, son seul rôle ici), Decisions (prudence de surface, existante).

**Constantes :** validées par le propriétaire le 24/11/2026 (ci-dessus). Chiffres réels : part des fautes nées des duels aériens non trouvée ; Stats Perform : 19,9 % des duels sont des fautes, tous duels confondus.

**Blocked by:** `15b1`. **Bloque :** `15f`.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Temps machine, non compté : série de 50 matchs (environ 48 min), suite complète (environ 22 min).

## Acceptance criteria

- [ ] Facteurs par situation tenus en scène ; Aggression seule règle le risque
- [ ] Fautes aériennes par match mesurées (rapportées, non réglées) ; cartons par gravité
- [ ] Déterminisme à graine fixée ; suite complète au compte attendu
- [ ] Durée réelle relevée, comparée à l'estimation

## Comments
