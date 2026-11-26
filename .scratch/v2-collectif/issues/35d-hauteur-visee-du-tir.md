# 35d: Hauteur visée du tir

**Origine (26/11/2026, ticket `v2-hauteur-ballon/02a2`, décision du propriétaire) :** depuis que les tirs ont une vraie hauteur, la loi du `35b` (visée à `SHOT_AIM_HEIGHT_M` 1,0 m, écart gaussien `SHOT_ERROR_SIGMA_RAD` 0,18 rad) envoie 35,4 % des tirs en vol sur une droite qui passe sous le sol avant la ligne (50 matchs, graines 0 à 49). Ils touchent le sol puis roulent : 27 % des tirs qui franchissent la ligne y arrivent en roulant, et 47 % des tirs cadrés étaient visés sous le sol. Le 22c ne doit pas être calibré sur cette base.

**What to build:** revoir la loi de hauteur du tir pour que la part des tirs rasants corresponde à un repère réel (à sourcer, sinon le noter « non trouvé ») sans changer la répartition des issues (cadré, à côté, au-dessus, dévissé) fixée par le `35b`. Pistes à proposer au propriétaire avant le code : hauteur visée, écart vertical distinct de l'écart horizontal, troncature basse de la visée. Toute constante nouvelle ou modifiée est proposée avant d'être codée.

**Attributs :** aucun nouveau (Finishing et Long Shots restent lus par `shooting` seul, voir `docs/CARTE_ATTRIBUTS_V2.md`).

**Blocked by:** 35b ; `v2-hauteur-ballon/02a2`.

**Bloque :** 22c.

**Status:** à faire (constantes à proposer avant le code)

**Hors de ce ticket :** le choix du geste (placée, rasante : `v2-attributs-restants/10a`, après la calibration) ; pied fort et pied faible (`04a`) ; poteaux et barre (`35c`).

## Estimation

| Poste | Durée |
|---|---|
| Analyse et recherche du repère réel | 25 min |
| Développement | 25 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications (série de 50 matchs, histogramme, bruit) | 45 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : base de 1 h 20, majorée de 50 % (règle du 26/11/2026 pour les tickets ballon et tirs) ; l'outil de tolérance et le relevé des hauteurs du 02a2 se réutilisent (`.scratch/v2-hauteur-ballon/mesures/02a2-*.py`). Au seuil de 2 h : découpage examiné, pas de coupe naturelle (loi et mesure vont ensemble).
Temps machine, non compté : une série de 50 matchs, relevé des hauteurs, suite complète.

## Acceptance criteria

- [ ] Repère réel de la part des tirs rasants, sourcé ou « non trouvé », et constantes validés par le propriétaire avant le code
- [ ] 50 matchs : part des tirs visés sous le sol et part des tirs qui arrivent en roulant à la ligne dans la cible validée ; histogramme des hauteurs à la ligne sans pic construit
- [ ] Répartition des issues (cadré, à côté, au-dessus, dévissé) dans le bruit des séries de référence du 02a1 ; critère 1 du 02a2 toujours à 100 %
- [ ] Déterminisme à graine fixée ; suite complète au compte attendu ; V1 inchangée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
